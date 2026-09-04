import json
import logging
from pathlib import Path

from src.agents.agentmanager.agent import Agent
from src.agents.agentmanager.schemas import RecommandationsCoach
from src.agents.agentmanager.exceptions import EmptyResponseError, InvalidResponseError
from src.config import MODEL_NAME_PICKELBALL, GROQ_TEMPERATURE

logger = logging.getLogger("nextmove.agents.pickelball")


class PickelballCoachAI(Agent):
    def __init__(self, context, user_prompt):
        super().__init__()
        self.context = context
        self.user_prompt = user_prompt

    def generate_recommendations(self, match_data) -> RecommandationsCoach:
        """
        Interroge le coach IA pickleball et renvoie des recommandations
        validées structurellement (RecommandationsCoach). Voir FootballCoachAI
        pour le détail du mécanisme de résilience partagé.
        """
        messages = [
            {"role": "system", "content": self.context},
            {"role": "user", "content": self.user_prompt},
        ]

        try:
            return self.call_and_validate(
                messages=messages,
                model=MODEL_NAME_PICKELBALL,
                temperature=GROQ_TEMPERATURE,
                schema=RecommandationsCoach,
            )
        except (EmptyResponseError, InvalidResponseError):
            logger.exception("Échec de génération des recommandations pickleball.")
            raise


# --- MAIN PROCESS ---
def main():
    base_dir = Path(__file__).resolve().parent

    with open(base_dir / "example_entry.json", encoding="utf-8") as fichier:
        match_stats = json.load(fichier)

    with open(base_dir / "context_pickelball.txt", "r", encoding="utf-8") as f:
        context = f.read()

    with open(base_dir / "user_prompt_pickelball.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    user_prompt = f"{prompt}\nVoici les données du match : {match_stats}"

    coach = PickelballCoachAI(context, user_prompt)
    recommandations = coach.generate_recommendations(match_stats)

    print("\n" + "=" * 30)
    coach.afficher_rapport(recommandations)
    print("=" * 30)


if __name__ == "__main__":
    main()