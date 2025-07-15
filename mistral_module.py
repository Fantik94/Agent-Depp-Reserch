import os
from mistralai import Mistral
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"
client = Mistral(api_key=api_key)

def generateText(prompt: str) -> dict:
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Génère un plan de recherche web pour la question suivante : {prompt}. "
                    "Retourne le résultat au format JSON avec les champs suivants : "
                    'plan : une liste structurée des étapes de recherche, '
                    'keywords : une liste de mots-clés ou requêtes Google pertinentes (en français), '
                    'questions_secondaires : une liste de questions secondaires à explorer.\n'
                    "Exemple de format attendu :\n"
                    '{"plan": ["Étape 1...", "Étape 2..."], "keywords": ["mot-clé 1", "mot-clé 2"], "questions_secondaires": ["question 1", "question 2"]}'
                ),
            },
        ],
        response_format={"type": "json_object"}
    )
    # On tente de parser la réponse en JSON
    try:
        return json.loads(chat_response.choices[0].message.content)
    except Exception:
        # Si le format n'est pas respecté, on retourne le texte brut dans un champ 'raw'
        return {"raw": chat_response.choices[0].message.content}

def resumeText(text: str) -> str:
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    "Résume le texte suivant en français de façon simple et concise, en 5 phrases maximum :\n" + text
                ),
            },
        ]
    )
    return chat_response.choices[0].message.content 