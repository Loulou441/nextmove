from src.agents.agentmanager.agent import Agent
import json
from pathlib import Path

from src.config import MODEL_NAME_FOOTBALL

class FootballCoachAI(Agent):
    def __init__(self, context, user_prompt):
        super().__init__()
        self.context = context
        self.user_prompt = user_prompt

    def generate_recommendations(self, match_data):
        """
        Script get advices from match analysis
        Get the analysis as a json as a list and return advices as a json
        """

        # Get the GROQ API response:
        advices_response = self.client.chat.completions.create(
            messages = [
                {"role": "system", "content": self.context},
                {"role": "user", "content": self.user_prompt},
        ],
        model=MODEL_NAME_FOOTBALL,
        temperature=0.0,
        response_format={"type": "json_object"}
        )

        advices = advices_response.choices[0].message.content
        if advices is None:
            raise ValueError("The model returned an empty response.")

        return json.loads(advices)

# --- MAIN PROCESS ---
def main():
    #get the context, user_prompt and match_data
    base_dir = Path(__file__).resolve().parent

    with open(base_dir / "example_entry.json", encoding="utf-8") as fichier:
        match_stats = json.load(fichier)

    with open(base_dir / "context_football.txt", "r", encoding="utf-8") as f:
        context = f.read()

    with open(base_dir / "user_prompt_football.txt", "r", encoding="utf-8") as f:
        prompt = f.read()

    user_prompt = f"{prompt}\nVoici les données du match : {match_stats}"

    # 1. Envoyer au Coach IA
    coach = FootballCoachAI(context, user_prompt)
    recommandations = coach.generate_recommendations(match_stats)
    
    # 2. Afficher le résultat
    print("\n" + "="*30)
    coach.afficher_rapport(recommandations)
    print("="*30)

if __name__ == "__main__":
    main()
