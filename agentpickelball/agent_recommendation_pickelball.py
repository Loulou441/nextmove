import os
from groq import Groq
import json
from dotenv import load_dotenv
from afficher_rapport import afficher_rapport

# Charge les variables d'environnement du fichier .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)
model = os.getenv("MODEL_NAME")

class PickelballCoachAI:
    def __init__(self, api_key, context, user_prompt):
        self.api_key = api_key
        self.context = context
        self.user_prompt = user_prompt

    def generate_recommendations(self, match_data):
        """
        Script get advices from match analysis
        Get the analysis as a json as a list and return advices as a json
        """

        # Get the GROQ API response:
        advices_response = client.chat.completions.create(
            messages = [
                {"role": "system", "content": self.context},
                {"role": "user", "content": self.user_prompt},
        ],
        model=model,
        temperature=0.0,
        response_format={"type": "json_object"}
        )

        advices = advices_response.choices[0].message.content
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
    coach = PickelballCoachAI(api_key, context, user_prompt)
    recommandations = coach.generate_recommendations(match_stats)
    
    # 2. Afficher le résultat
    print("\n" + "="*30)
    afficher_rapport(recommandations)
    print("="*30)

if __name__ == "__main__":
    main()