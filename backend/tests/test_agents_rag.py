"""
Tests hors-ligne des agents coach et du RAG.

Ni Groq ni Hugging Face ne sont contactés :
  - le client Groq est remplacé par un faux client scripté ;
  - l'embedding sentence-transformers est remplacé par un embedder
    déterministe (hachage de mots) afin de tester la plomberie ChromaDB
    (construction, persistance, recherche, enrichissement) sans télécharger
    le modèle. La QUALITÉ sémantique du vrai modèle n'est donc pas évaluée ici
    (voir scripts/eval_rag_live.py).
"""
import copy
import hashlib
import json
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
from groq import RateLimitError
from tenacity import wait_none

from backend.agents.agentmanager import agent as agent_module
from backend.agents.agentmanager import rag
from backend.agents.agentmanager.exceptions import EmptyResponseError, InvalidResponseError

AGENTS_DIR = Path(__file__).resolve().parents[1] / "agents"

# (clé de sport, dossier, suffixe des fichiers, module, classe)
SPORTS = [
    ("padel", "agentpadel", "padel", "agent_recommendation_padel", "PadelCoachAI"),
    ("tennis", "agenttennis", "tennis", "agent_recommendation_tennis", "TennisCoachAI"),
    ("pickleball", "agentpickelball", "pickelball", "agent_recommendation_pickelball", "PickelballCoachAI"),
]

VALID_REPLY = {
    "recommandations_coach": [
        {
            "timestamp": "14:20",
            "titre": "Montée au filet trop précoce",
            "contenu": {
                "constat": "Faute directe au filet.",
                "analyse": "Déséquilibre vers l'avant.",
                "action_corrective": "Travailler le timing de montée.",
                "pro_tip": None,
                "exercice_source_id": None,
            },
        }
    ]
}


# --------------------------------------------------------------------------
# Doubles de test
# --------------------------------------------------------------------------
class HashingEmbedding:
    """Embedder déterministe : sac de mots haché, normalisé L2."""

    DIM = 256

    def __init__(self):
        pass

    @staticmethod
    def name():
        return "hashing-test"

    def get_config(self):
        return {}

    @staticmethod
    def build_from_config(config):
        return HashingEmbedding()

    def default_space(self):
        return "cosine"

    def supported_spaces(self):
        return ["cosine", "l2", "ip"]

    def is_legacy(self):
        return False

    def _embed(self, text):
        vec = [0.0] * self.DIM
        for word in re.findall(r"\w+", text.lower()):
            h = int(hashlib.md5(word.encode()).hexdigest(), 16)
            vec[h % self.DIM] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        return [v / norm for v in vec]

    def __call__(self, input):
        return [self._embed(t) for t in input]

    def embed_query(self, input):
        return self(input)


class FakeGroq:
    """Faux client Groq : renvoie, dans l'ordre, les réponses/erreurs scriptées."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        item = self.script.pop(0)
        if isinstance(item, Exception):
            raise item
        content = item if (item is None or isinstance(item, str)) else json.dumps(item)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


def _rate_limit_error():
    import httpx

    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, request=request)
    return RateLimitError("rate limited", response=response, body=None)


def _bad_request_error(message):
    import httpx
    from groq import BadRequestError

    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(400, request=request)
    return BadRequestError(message, response=response, body=None)


@pytest.fixture
def fake_embeddings(monkeypatch, tmp_path):
    """Isole ChromaDB (dossier temporaire) et remplace le modèle d'embedding."""
    monkeypatch.setattr(rag, "CHROMA_PERSIST_DIR", tmp_path / "chroma")
    monkeypatch.setattr(rag, "_chroma_client", None)
    monkeypatch.setattr(rag, "_embedding_fn", HashingEmbedding())
    monkeypatch.setattr(rag, "_kb_cache", {})
    monkeypatch.setattr(rag, "_get_embedding_fn", lambda: rag._embedding_fn)
    yield
    rag._chroma_client = None


@pytest.fixture
def fake_groq(monkeypatch):
    """Installe un faux client Groq et supprime les attentes de retry."""
    holder = {}

    def install(script):
        client = FakeGroq(script)
        holder["client"] = client
        monkeypatch.setattr(agent_module, "Groq", lambda api_key=None: client)
        return client

    monkeypatch.setattr(agent_module.Agent._call_groq.retry, "wait", wait_none())
    return install


# --------------------------------------------------------------------------
# Intégrité des bases de connaissances
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sport,folder,suffix,_m,_c", SPORTS)
def test_knowledge_base_json_is_well_formed(sport, folder, suffix, _m, _c):
    path = AGENTS_DIR / folder / f"knowledge_{suffix}.json"
    drills = json.loads(path.read_text(encoding="utf-8"))

    assert len(drills) == 50
    ids = [d["id"] for d in drills]
    assert len(ids) == len(set(ids)), "identifiants d'exercices dupliqués"
    for d in drills:
        for field in ("id", "pilier", "titre", "probleme_associe", "description"):
            assert d.get(field), f"{d.get('id')} : champ '{field}' vide ou absent"
    assert {d["pilier"] for d in drills} == {"Technique", "Tactique", "Physique", "Mental"}


@pytest.mark.parametrize("sport,folder,suffix,_m,_c", SPORTS)
def test_prompt_files_and_example_entry_exist(sport, folder, suffix, _m, _c):
    base = AGENTS_DIR / folder
    assert (base / f"context_{suffix}.txt").read_text(encoding="utf-8").strip()
    assert (base / f"user_prompt_{suffix}.txt").read_text(encoding="utf-8").strip()
    example = json.loads((base / "example_entry.json").read_text(encoding="utf-8"))
    assert example["donnees_sequences"], "example_entry.json sans séquence"


# --------------------------------------------------------------------------
# RAG
# --------------------------------------------------------------------------
def test_rag_builds_collection_and_retrieves_top_k(fake_embeddings):
    path = AGENTS_DIR / "agentpadel" / "knowledge_padel.json"
    kb = rag.get_knowledge_base("padel", path)

    assert kb.collection.count() == 50
    results = kb.retrieve("Sortie de vitre manquée mauvaise anticipation du rebond", k=3)

    assert len(results) == 3
    assert results[0]["id"] == "padel_tech_001"
    scores = [r["score_pertinence"] for r in results]
    assert scores == sorted(scores, reverse=True)
    assert set(results[0]) == {"id", "pilier", "titre", "description", "pro_tip", "score_pertinence"}


def test_rag_empty_pro_tip_is_returned_as_none(fake_embeddings):
    path = AGENTS_DIR / "agentpickelball" / "knowledge_pickelball.json"
    kb = rag.get_knowledge_base("pickleball", path)

    result = kb.retrieve("Faute au filet Kitchen Violation équilibre du corps", k=1)[0]
    assert result["id"] == "pb_tech_001"
    assert result["pro_tip"] is None


def test_rag_collection_is_persisted_not_rebuilt(fake_embeddings, monkeypatch):
    path = AGENTS_DIR / "agenttennis" / "knowledge_tennis.json"
    rag.KnowledgeBase("tennis", path)

    populate_calls = []
    monkeypatch.setattr(rag.KnowledgeBase, "_populate", lambda self, c: populate_calls.append(1))
    kb2 = rag.KnowledgeBase("tennis", path)

    assert populate_calls == [], "la collection existante ne doit pas être ré-embeddée"
    assert kb2.collection.count() == 50


def test_rag_force_rebuild_resyncs_with_json(fake_embeddings, tmp_path):
    src = tmp_path / "k.json"
    drills = [
        {"id": "a", "pilier": "Technique", "titre": "A", "probleme_associe": "alpha", "description": "d", "pro_tip": None},
        {"id": "b", "pilier": "Mental", "titre": "B", "probleme_associe": "beta", "description": "d", "pro_tip": "x"},
    ]
    src.write_text(json.dumps(drills), encoding="utf-8")
    assert rag.get_knowledge_base("demo", src).collection.count() == 2

    drills.append({"id": "c", "pilier": "Physique", "titre": "C", "probleme_associe": "gamma", "description": "d", "pro_tip": None})
    src.write_text(json.dumps(drills), encoding="utf-8")

    assert rag.get_knowledge_base("demo", src).collection.count() == 2  # cache / pas de resync auto
    assert rag.get_knowledge_base("demo", src, force_rebuild=True).collection.count() == 3


def test_rag_knowledge_base_is_cached_per_sport(fake_embeddings):
    path = AGENTS_DIR / "agentpadel" / "knowledge_padel.json"
    assert rag.get_knowledge_base("padel", path) is rag.get_knowledge_base("padel", path)


def test_enrich_adds_references_without_mutating_input(fake_embeddings):
    path = AGENTS_DIR / "agentpadel" / "knowledge_padel.json"
    kb = rag.get_knowledge_base("padel", path)
    match_data = json.loads((AGENTS_DIR / "agentpadel" / "example_entry.json").read_text(encoding="utf-8"))
    original = copy.deepcopy(match_data)

    enriched = rag.enrich_match_data_with_drills(match_data, kb, k=2)

    assert match_data == original
    for seq in enriched["donnees_sequences"]:
        assert len(seq["exercices_references"]) == 2
    assert enriched["donnees_sequences"][1]["exercices_references"][0]["id"] == "padel_tech_001"


def test_enrich_handles_match_without_sequences(fake_embeddings):
    path = AGENTS_DIR / "agentpadel" / "knowledge_padel.json"
    kb = rag.get_knowledge_base("padel", path)
    assert rag.enrich_match_data_with_drills({"match_id": "x"}, kb) == {"match_id": "x"}


# --------------------------------------------------------------------------
# Agent de base : résilience Groq
# --------------------------------------------------------------------------
def test_call_and_validate_returns_validated_model(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([VALID_REPLY])
    result = agent_module.Agent().call_and_validate(
        messages=[{"role": "user", "content": "x"}], model="m", temperature=0, schema=RecommandationsCoach
    )

    assert result.recommandations_coach[0].titre == "Montée au filet trop précoce"
    assert client.calls[0]["response_format"] == {"type": "json_object"}


def test_call_and_validate_retries_on_rate_limit(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([_rate_limit_error(), _rate_limit_error(), VALID_REPLY])
    result = agent_module.Agent().call_and_validate(
        messages=[], model="m", temperature=0, schema=RecommandationsCoach
    )

    assert len(client.calls) == 3
    assert result.recommandations_coach


def test_call_and_validate_gives_up_after_max_network_attempts(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([_rate_limit_error()] * agent_module.GROQ_MAX_ATTEMPTS)
    with pytest.raises(RateLimitError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)
    assert len(client.calls) == agent_module.GROQ_MAX_ATTEMPTS


def test_call_and_validate_retries_once_on_invalid_json(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq(["pas du json {", VALID_REPLY])
    result = agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)

    assert len(client.calls) == 2
    assert result.recommandations_coach


def test_call_and_validate_retries_when_groq_rejects_malformed_json(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([_bad_request_error("json_validate_failed: Failed to generate JSON"), VALID_REPLY])
    result = agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)

    assert len(client.calls) == 2
    assert result.recommandations_coach


def test_call_and_validate_gives_up_when_groq_keeps_rejecting_json(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([_bad_request_error("json_validate_failed")] * agent_module.MAX_VALIDATION_ATTEMPTS)
    with pytest.raises(InvalidResponseError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)
    assert len(client.calls) == agent_module.MAX_VALIDATION_ATTEMPTS


def test_call_and_validate_does_not_retry_other_bad_requests(fake_groq):
    from groq import BadRequestError
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    client = fake_groq([_bad_request_error("model_not_found"), VALID_REPLY])
    with pytest.raises(BadRequestError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)
    assert len(client.calls) == 1


def test_call_and_validate_rejects_out_of_schema_reply(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    bad = {"recommandations_coach": [{"timestamp": "1:00", "titre": "t", "contenu": {"constat": "c"}}]}
    fake_groq([bad] * agent_module.MAX_VALIDATION_ATTEMPTS)
    with pytest.raises(InvalidResponseError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)


def test_call_and_validate_rejects_empty_recommendation_list(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    fake_groq([{"recommandations_coach": []}] * agent_module.MAX_VALIDATION_ATTEMPTS)
    with pytest.raises(InvalidResponseError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)


def test_call_and_validate_raises_on_empty_content(fake_groq):
    from backend.agents.agentmanager.schemas import RecommandationsCoach

    fake_groq([None] * agent_module.MAX_VALIDATION_ATTEMPTS)
    with pytest.raises(EmptyResponseError):
        agent_module.Agent().call_and_validate(messages=[], model="m", temperature=0, schema=RecommandationsCoach)


# --------------------------------------------------------------------------
# Agents coach (RAG + Groq simulé)
# --------------------------------------------------------------------------
@pytest.mark.parametrize("sport,folder,suffix,module,cls", SPORTS)
def test_coach_agent_end_to_end_with_rag(fake_embeddings, fake_groq, sport, folder, suffix, module, cls):
    import importlib

    mod = importlib.import_module(f"backend.agents.{folder}.{module}")
    client = fake_groq([VALID_REPLY])
    base = AGENTS_DIR / folder
    context = (base / f"context_{suffix}.txt").read_text(encoding="utf-8")
    user_prompt = (base / f"user_prompt_{suffix}.txt").read_text(encoding="utf-8")
    match_data = json.loads((base / "example_entry.json").read_text(encoding="utf-8"))

    coach = getattr(mod, cls)(context, user_prompt)
    result = coach.generate_recommendations(match_data)

    assert result.recommandations_coach
    sent = client.calls[0]["messages"]
    assert sent[0] == {"role": "system", "content": context}
    assert "exercices_references" in sent[1]["content"]
    assert sent[1]["content"].startswith(user_prompt)
    assert "exercices_references" not in json.dumps(match_data), "l'entrée de l'appelant ne doit pas être modifiée"


def test_coach_agent_propagates_invalid_response(fake_embeddings, fake_groq):
    from backend.agents.agentpadel.agent_recommendation_padel import PadelCoachAI

    fake_groq(["{}"] * agent_module.MAX_VALIDATION_ATTEMPTS)
    match_data = json.loads((AGENTS_DIR / "agentpadel" / "example_entry.json").read_text(encoding="utf-8"))
    with pytest.raises(InvalidResponseError):
        PadelCoachAI("ctx", "prompt").generate_recommendations(match_data)


# --------------------------------------------------------------------------
# Modérateur
# --------------------------------------------------------------------------
def test_moderator_returns_model_verdict(fake_groq):
    from backend.agents.agentmoderator.agent_moderator import Moderator

    fake_groq([{"is_prompt_injection": False, "off_topic": True}])
    verdict = Moderator().moderate("Donne-moi une recette de gâteau.")
    assert verdict.off_topic is True and verdict.is_prompt_injection is False


def test_moderator_fails_closed_when_model_is_unusable(fake_groq):
    from backend.agents.agentmoderator.agent_moderator import Moderator

    fake_groq(["pas du json"] * agent_module.MAX_VALIDATION_ATTEMPTS)
    assert Moderator().moderate("Pourquoi je perds mes balles ?").is_prompt_injection is True


def test_moderator_sends_system_prompt_then_question(fake_groq):
    from backend.agents.agentmoderator.agent_moderator import Moderator

    client = fake_groq([{"is_prompt_injection": False}])
    Moderator().moderate("Ma question")

    messages = client.calls[0]["messages"]
    assert messages[0]["role"] == "system" and messages[0]["content"].strip()
    assert messages[1] == {"role": "user", "content": "Ma question"}