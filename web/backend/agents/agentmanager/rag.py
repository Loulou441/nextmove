"""
Base de connaissances (RAG) pour ancrer les recommandations des coachs
sportifs sur des exercices réels et validés, plutôt que sur des exercices
générés librement par le LLM.

Stockage vectoriel : ChromaDB (client persistant sur disque), une collection
par sport. Choix justifié par :
  - Persistance native entre redémarrages du process : les exercices ne sont
    embeddés qu'une seule fois au premier lancement, jamais recalculés au
    démarrage suivant (contrairement à une solution 100% en mémoire).
  - Recherche par similarité cosinus intégrée (index HNSW), sans avoir à
    gérer soi-même le calcul de similarité ni la normalisation des vecteurs.
  - Empreinte opérationnelle minime (pas de service externe à déployer) :
    adapté au volume actuel (50 exercices / sport), sans complexité inutile
    d'une base vectorielle managée type Pinecone/Weaviate.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

logger = logging.getLogger("nextmove.agents.rag")

# Répertoire de persistance de la base vectorielle. Un seul dossier pour
# toutes les collections (une collection = un sport), ChromaDB isole les
# données par collection à l'intérieur.
CHROMA_PERSIST_DIR = Path(__file__).resolve().parent / "chroma_store"

# Modèle d'embedding multilingue, léger, exécuté localement :
# - Pas d'appel réseau supplémentaire => n'impacte pas l'OMTM (< 10 s)
# - Pas de coût API additionnel => cohérent avec la structure de coûts visée
# - Support du français, nécessaire pour matcher les prompts en français
#
# IMPORTANT (déploiement) : ce modèle (~470 Mo) doit être pré-téléchargé
# dans l'image de déploiement (ex: étape de build Docker), jamais récupéré
# à froid en production — un téléchargement à la volée casserait l'OMTM.
EMBEDDING_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

_chroma_client: Optional[chromadb.ClientAPI] = None
_embedding_fn: Optional[SentenceTransformerEmbeddingFunction] = None
_kb_cache: Dict[str, "KnowledgeBase"] = {}


def _get_embedding_fn() -> SentenceTransformerEmbeddingFunction:
    """
    Charge la fonction d'embedding une seule fois (singleton) et la réutilise
    pour toutes les collections/sports, afin d'éviter de recharger le modèle
    sentence-transformers à chaque instanciation — c'est l'opération la plus
    coûteuse de tout le mécanisme de RAG.
    """
    global _embedding_fn
    if _embedding_fn is None:
        logger.info("Chargement du modèle d'embedding %s", EMBEDDING_MODEL_NAME)
        _embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME,
            normalize_embeddings=True,
        )
    return _embedding_fn


def _get_chroma_client() -> chromadb.ClientAPI:
    """Client ChromaDB persistant, partagé par toutes les KnowledgeBase."""
    global _chroma_client
    if _chroma_client is None:
        CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
    return _chroma_client


# Champs stockés en métadonnées ChromaDB (hors "id", géré séparément par
# Chroma, et hors "probleme_associe", déjà intégré au texte embeddé).
_METADATA_FIELDS = ("pilier", "titre", "description", "pro_tip")


def _drill_to_metadata(drill: Dict[str, Any]) -> Dict[str, str]:
    """
    Convertit un exercice en dict de métadonnées ChromaDB.

    ChromaDB n'accepte que des valeurs scalaires (str/int/float/bool) en
    métadonnées et rejette explicitement `None` — `pro_tip`, optionnel dans
    notre schéma métier, est donc stocké comme chaîne vide et reconverti en
    `None` à la lecture (voir `_metadata_to_drill`).
    """
    return {field: (drill.get(field) or "") for field in _METADATA_FIELDS}


def _metadata_to_drill(drill_id: str, metadata: Dict[str, Any], score: float) -> Dict[str, Any]:
    """Reconstruit un exercice exploitable à partir des métadonnées ChromaDB."""
    return {
        "id": drill_id,
        "pilier": metadata.get("pilier", ""),
        "titre": metadata.get("titre", ""),
        "description": metadata.get("description", ""),
        "pro_tip": metadata.get("pro_tip") or None,
        "score_pertinence": round(score, 3),
    }


class KnowledgeBase:
    """
    Base de connaissances d'exercices validés pour un sport donné, adossée
    à une collection ChromaDB persistante.

    Au premier chargement pour un sport donné, la collection est construite
    à partir du fichier JSON source et les exercices sont embeddés une seule
    fois. Aux lancements suivants, la collection existante est réutilisée
    telle quelle : aucun ré-embedding, aucun redémarrage du modèle.
    """

    def __init__(self, sport: str, knowledge_path: Path, force_rebuild: bool = False):
        self.sport = sport
        self.knowledge_path = knowledge_path
        self.collection_name = f"nextmove_drills_{sport}"
        self.collection = self._get_or_build_collection(force_rebuild=force_rebuild)

    def _get_or_build_collection(self, force_rebuild: bool):
        client = _get_chroma_client()

        if force_rebuild:
            try:
                client.delete_collection(self.collection_name)
                logger.info("Collection '%s' supprimée pour reconstruction forcée.", self.collection_name)
            except Exception:
                pass  # la collection n'existait pas encore, rien à faire

        existing_names = {c.name for c in client.list_collections()}
        already_built = self.collection_name in existing_names

        collection = client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=_get_embedding_fn(),
            # Similarité cosinus explicite plutôt que la distance L2 par
            # défaut de ChromaDB : plus adaptée aux embeddings de texte,
            # et cohérente avec l'usage de embeddings normalisés.
            metadata={"hnsw:space": "cosine"},
        )

        if not already_built:
            self._populate(collection)

        return collection

    def _populate(self, collection) -> None:
        """Charge le JSON source et embedde chaque exercice dans la collection."""
        logger.info("Construction de la collection '%s' depuis %s", self.collection_name, self.knowledge_path)

        with open(self.knowledge_path, encoding="utf-8") as f:
            drills = json.load(f)

        # On embeddé la concaténation du "problème associé" et du titre :
        # c'est ce texte qui doit matcher sémantiquement l'événement du
        # match, pas la description complète de l'exercice (plus bruitée
        # et donc moins discriminante pour la recherche).
        documents = [f"{d['probleme_associe']} {d['titre']}" for d in drills]
        ids = [d["id"] for d in drills]
        metadatas = [_drill_to_metadata(d) for d in drills]

        collection.add(documents=documents, ids=ids, metadatas=metadatas)
        logger.info("%d exercices embeddés dans '%s'.", len(drills), self.collection_name)

    def retrieve(self, query: str, k: int = 2) -> List[Dict[str, Any]]:
        """
        Retourne les k exercices les plus proches sémantiquement de `query`,
        recherchés par similarité cosinus dans l'index ChromaDB.
        """
        if self.collection.count() == 0:
            return []

        results = self.collection.query(
            query_texts=[query],
            n_results=min(k, self.collection.count()),
        )

        ids = results["ids"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        return [
            # Avec la distance cosinus de ChromaDB (0 = identique, 2 = opposé),
            # on reconvertit en score de similarité (1 = identique) pour
            # rester cohérent avec la sémantique "score plus haut = plus
            # pertinent" utilisée dans le reste du pipeline.
            _metadata_to_drill(drill_id, meta, score=1 - dist)
            for drill_id, meta, dist in zip(ids, metadatas, distances)
        ]


def get_knowledge_base(sport: str, knowledge_path: Path, force_rebuild: bool = False) -> KnowledgeBase:
    """
    Retourne une instance mise en cache de KnowledgeBase pour un sport donné,
    plutôt que d'en recréer une à chaque instanciation d'agent coach.

    `force_rebuild=True` permet de forcer la reconstruction de la collection
    ChromaDB (utile en développement après une modification du fichier JSON
    source) — sans cela, la collection persistée sur disque n'est jamais
    automatiquement resynchronisée avec le fichier JSON.
    """
    if force_rebuild or sport not in _kb_cache:
        _kb_cache[sport] = KnowledgeBase(sport, knowledge_path, force_rebuild=force_rebuild)
    return _kb_cache[sport]


def enrich_match_data_with_drills(
    match_data: Dict[str, Any], knowledge_base: KnowledgeBase, k: int = 2
) -> Dict[str, Any]:
    """
    Retourne une copie de match_data où chaque séquence est enrichie d'un
    champ "exercices_references", contenant les k exercices de la base de
    connaissances les plus pertinents pour l'événement de cette séquence.

    Cet enrichissement se fait AVANT l'appel au LLM : le modèle reçoit ainsi,
    pour chaque événement analysé, des exercices réels et validés sur
    lesquels ancrer son "action_corrective", plutôt que de devoir en
    inventer un à partir de rien.
    """
    import copy
    enriched = copy.deepcopy(match_data)

    for sequence in enriched.get("donnees_sequences", []):
        query = f"{sequence.get('evenement_cle', '')} {sequence.get('contexte_tactique', '')}"
        sequence["exercices_references"] = knowledge_base.retrieve(query, k=k)

    return enriched