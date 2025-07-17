import os
from mistralai import Mistral
from dotenv import load_dotenv
import json

load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"
client = Mistral(api_key=api_key)

def generateText(prompt: str, nb_results: int) -> dict:
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Pour la question suivante : {prompt}, génère un plan de recherche web structuré "
                    f"en exactement {nb_results} étapes, chaque étape correspondant à l'exploitation d'une source Google différente. "
                    "Retourne le résultat au format JSON avec les champs suivants : "
                    f'plan : une liste de {nb_results} étapes, '
                    f'keywords : une liste de {nb_results} mots-clés ou requêtes Google pertinentes (en français).\n '
                    "Exemple de format attendu :\n"
                    '{"plan": ["Étape 1...", "Étape 2..."], "keywords": ["mot-clé 1", "mot-clé 2"]}'
                ),
            },
        ],
        response_format={"type": "json_object"}
    )
    try:
        return json.loads(chat_response.choices[0].message.content)
    except Exception:
        return {"raw": chat_response.choices[0].message.content}

def resumeText(text: str, question: str) -> str:
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    f"En te basant sur la question suivante : '{question}', résume le texte ci-dessous de façon simple, concise et directement orientée pour répondre à la question. Limite-toi à 5 phrases maximum.\n\nTexte à résumer :\n{text}"
                ),
            },
        ]
    )
    return chat_response.choices[0].message.content 