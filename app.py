import streamlit as st
import os
from mistralai import Mistral
from dotenv import load_dotenv

# Charger la clé API depuis le fichier .env
load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]
model = "mistral-small-latest"  # Tu peux changer le modèle ici
client = Mistral(api_key=api_key)

def generateText(prompt: str) -> str:
    chat_response = client.chat.complete(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Génère un plan détaillé pour réalisé une recherche sur le web de cette question : {prompt}",
            },
        ]
    )
    return chat_response.choices[0].message.content

# Interface Streamlit
st.set_page_config(page_title="Agent Planneur", page_icon="🤖")
st.title("Générateur de plan")

prompt = st.text_input("Entrez votre question ou sujet de recherche :")

if st.button("Générer le plan"):
    with st.spinner("Génération du plan en cours..."):
        plan = generateText(prompt)
    st.subheader("Plan généré :")
    st.write(plan) 