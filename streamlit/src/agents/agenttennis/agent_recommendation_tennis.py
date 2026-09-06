import json
import logging
import sys
from pathlib import Path

if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.agents.agentmanager.agent import Agent
from src.agents.agentmanager.schemas import RecommandationsCoach
from src.agents.agentmanager.exceptions import EmptyResponseError, InvalidResponseError
from src.agents.agentmanager.rag import get_knowledge_base, enrich_match_data_with_drills
from src.config import MODEL_NAME_TENNIS, GROQ_TEMPERATURE

logger = logging.getLogger("nextmove.agents.tennis")

KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge_tennis.json"


class TennisCoachAI(Agent):
    def __init__(self, context, user_prompt):
        super().__init__()
        self.context = context
        self.user_prompt = user_prompt
        self.knowledge_base = get_knowledge_base("tennis", KNOWLEDGE_PATH)

    def generate_recommendations(self, match_data) -> RecommandationsCoach:
        """
        Interroge le coach IA tennis et renvoie des recommandations validées
        structurellement (RecommandationsCoach), ancrées sur des exercices
        réels retrouvés par recherche vectorielle dans la base de
        connaissances tennis (RAG / ChromaDB). Voir PadelCoachAI pour le
        détail du mécanisme partagé.
        """
        enriched_match_data = enrich_match_data_with_drills(match_data, self.knowledge_base)

        full_user_prompt = (
            f"{self.user_prompt}\n"
            f"Voici les données du match, enrichies pour chaque séquence "
            f"d'exercices de référence validés (champ 'exercices_references') : "
            f"{json.dumps(enriched_match_data, ensure_ascii=False)}"
        )

        messages = [
            {"role": "system", "content": self.context},
            {"role": "user", "content": full_user_prompt},
        ]

        try:
            return self.call_and_validate(
                messages=messages,
                model=MODEL_NAME_TENNIS,
                temperature=GROQ_TEMPERATURE,
                schema=RecommandationsCoach,
            )
        except (EmptyResponseError, InvalidResponseError):
            logger.exception("Échec de génération des recommandations tennis.")
            raise


# --- MAIN PROCESS ---
def main():
    base_dir = Path(__file__).resolve().parent

    with open(base_dir / "example_entry.json", encoding="utf-8") as fichier:
        match_stats = json.load(fichier)

    with open(base_dir / "context_tennis.txt", "r", encoding="utf-8") as f:
        context = f.read()

    with open(base_dir / "user_prompt_tennis.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    coach = TennisCoachAI(context, prompt)
    recommandations = coach.generate_recommendations(match_stats)

    print("\n" + "=" * 30)
    coach.afficher_rapport(recommandations)
    print("=" * 30)


if __name__ == "__main__":
    main()
