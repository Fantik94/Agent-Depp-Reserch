import streamlit as st
import re
import os
from mistral_module import generateText
from serpapi_module import google_search
from scraping_module import scrap_url

# Streamlit
st.set_page_config(page_title="Agent deep research", page_icon="🤖")
st.title("Agent deep research")

serpapi_key = os.environ.get("SERPAPI_API_KEY")

prompt = st.text_input("Entrez votre question ou sujet de recherche :")

if st.button("Générer le plan et scrapper le web"):
    with st.spinner("Génération du plan en cours..."):
        plan_data = generateText(prompt)
    if "raw" in plan_data:
        st.subheader("Plan généré (format brut) :")
        st.write(plan_data["raw"])
        st.warning("Le format JSON n'a pas été respecté. Veuillez reformuler la question ou améliorer le prompt.")
        keywords = [prompt]
    else:
        st.subheader("Plan généré :")
        st.write(plan_data.get("plan", []))
        st.subheader("Mots-clés proposés :")
        st.write(plan_data.get("keywords", []))
        st.subheader("Questions secondaires :")
        st.write(plan_data.get("questions_secondaires", []))
        keywords = plan_data.get("keywords", [prompt])

    #Recherche Google
    search_query = keywords[0] if keywords else prompt
    st.info(f"Recherche Google avec : {search_query}")

    if serpapi_key:
        with st.spinner("Recherche de liens sur Google..."):
            links = google_search(search_query)
        st.subheader("Liens trouvés :")
        for link in links[:3]:
            st.write(link)
        if links:
            with st.spinner("Scraping du premier lien..."):
                content = scrap_url(links[0])
            st.subheader("Extrait du contenu scrappé :")
            st.write(content)
    else:
        st.warning("Clé SerpAPI manquante dans le .env pour la recherche Google.") 