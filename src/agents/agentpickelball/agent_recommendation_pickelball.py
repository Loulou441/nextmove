from src.agents.agentmanager.agent import Agent
import json
from src.agents.agentpickelball.afficher_rapport import afficher_rapport

from src.config import MODEL_NAME_PICKELBALL

class PickelballCoachAI(Agent):
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
        model=MODEL_NAME_PICKELBALL,
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

    with open('agentpickelball/example_entry.json') as fichier:
        match_stats = json.load(fichier)

    f = open('agentpickelball/context_pickelball.txt', 'r')
    context = f.read()
    f.close()

    f = open('agentpickelball/user_prompt_pickelball.txt', 'r')
    prompt = f.read()
    f.close()

    user_prompt = f"{prompt}\nVoici les données du match : {match_stats}"

    # 1. Envoyer au Coach IA
    coach = PickelballCoachAI(context, user_prompt)
    recommandations = coach.generate_recommendations(match_stats)
    
    # 2. Afficher le résultat
    print("\n" + "="*30)
    afficher_rapport(recommandations)
    print("="*30)

if __name__ == "__main__":
    main()