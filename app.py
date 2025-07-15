import streamlit as st
import re
import os
from mistral_module import generateText, resumeText
from serpapi_module import google_search
from scraping_module import scrap_url

# Streamlit
st.set_page_config(page_title="Agent deep research", page_icon="🤖")
st.title("Agent deep research")

serpapi_key = os.environ.get("SERPAPI_API_KEY")

prompt = st.text_input("Entrez votre question ou sujet de recherche :")

if st.button("Générer le plan et scrapper le web"):
    # Affichage du loader global tant que le résumé n'est pas prêt
    with st.spinner("Recherche, scraping et synthèse en cours..."):
        plan_data = generateText(prompt)
        if "raw" in plan_data:
            keywords = [prompt]
        else:
            keywords = plan_data.get("keywords", [prompt])
        search_query = keywords[0] if keywords else prompt
        links = google_search(search_query)
        all_contents = []
        for link in links[:3]:
            content = scrap_url(link)
            all_contents.append(content)
        if all_contents:
            global_resume = resumeText("\n\n".join(all_contents))
        else:
            global_resume = "Aucun contenu à résumer."
    # Résultat final affiché en haut
    st.markdown(f"## 📝 Résumé global simplifié :\n{global_resume}")
    # Détails dans un menu déroulant
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
        for i, link in enumerate(links[:3]):
            st.write(f"[Lien]({link})")
            st.write(all_contents[i] if i < len(all_contents) else "(Pas de contenu)") 