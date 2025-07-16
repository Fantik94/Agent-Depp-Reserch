import streamlit as st
import re
import os
from mistral_module import generateText, resumeText
from serpapi_module import google_search
from scraping_module import scrap_url

# Streamlit
st.set_page_config(page_title="Agent deep research")
st.title("Agent deep research")

nb_results = st.slider("Nombre de résultats Google à analyser", min_value=1, max_value=10, value=3)

prompt = st.text_input("Entrez votre question ou sujet de recherche :")

if st.button("Générer le plan et scrapper le web"):
    with st.spinner("Recherche en cours..."):
        plan_data = generateText(prompt, nb_results)
        if "raw" in plan_data:
            keywords = [prompt]
        else:
            keywords = plan_data.get("keywords", [prompt])
        search_query = keywords[0] if keywords else prompt
        links = google_search(search_query)
        all_contents = []
        for link in links[:nb_results]:
            content = scrap_url(link)
            all_contents.append(content)
        if all_contents:
            global_resume = resumeText("\n\n".join(all_contents))
        else:
            global_resume = "Aucun contenu à résumer."
    st.markdown(f"## Résumé global simplifié :\n{global_resume}")
    with st.expander("Voir le détail de la recherche et des sources"):
        if "raw" in plan_data:
            st.subheader("Plan généré (format brut) :")
            st.write(plan_data["raw"])
            st.warning("Le format JSON n'a pas été respecté. Veuillez reformuler la question ou améliorer le prompt.")
        else:
            st.subheader("Plan généré :")
            st.write(plan_data.get("plan", []))
            st.subheader("Mots-clés proposés :")
            st.write(plan_data.get("keywords", []))
            st.subheader("Questions secondaires :")
            st.write(plan_data.get("questions_secondaires", []))
        st.subheader("Liens trouvés et extraits scrappés :")
        for i, link in enumerate(links[:nb_results]):
            st.write(f"[Lien]({link})")
            st.write(all_contents[i] if i < len(all_contents) else "(Pas de contenu)") 