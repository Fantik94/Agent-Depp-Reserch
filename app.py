import streamlit as st
import re
import os
from mistral_module import generateText, resumeText
from serpapi_module import google_search
from scraping_module import scrap_url

st.set_page_config(page_title="Agent deep research", layout="centered")
st.markdown("""
<style>
.big-title {font-size:2.5em; font-weight:bold; color:#3B82F6; text-align:center; margin-bottom:0.2em;}
.sub {color:#666; text-align:center; margin-bottom:2em;}
.result-box {background-color:#F1F5F9; border-radius:10px; padding:1em; margin-bottom:1em;}
hr {margin: 1.5em 0;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="big-title">Agent Deep Research</div>', unsafe_allow_html=True)

# Curseur stylisé
nb_results = st.slider("Nombre de résultats Google à analyser", min_value=1, max_value=10, value=3)

prompt = st.text_input("Entrez votre question ou sujet de recherche :")

if st.button("Rechercher"):
    with st.spinner("Recherche, scraping et synthèse en cours..."):
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
            global_resume = resumeText("\n\n".join(all_contents), prompt)
        else:
            global_resume = "Aucun contenu à résumer."

    st.markdown(
        f'''
        <div class="result-box">
            <h3 style='color:#16A34A;'>Résumé :</h3>
            {global_resume}
        </div>
        ''',
        unsafe_allow_html=True
    )

    with st.expander("Voir le détail de la recherche"):
        if "raw" in plan_data:
            st.subheader("Plan généré (format brut)")
            st.write(plan_data["raw"])
            st.warning("Le format JSON n'a pas été respecté. Veuillez reformuler la question ou améliorer le prompt.")
        else:
            st.markdown('<h4 style="color:#3B82F6;">Plan généré</h4>', unsafe_allow_html=True)
            st.write(plan_data.get("plan", []))
            st.markdown('<h4 style="color:#3B82F6;">Mots-clés proposés</h4>', unsafe_allow_html=True)
            st.write(plan_data.get("keywords", []))
            st.markdown('<h4 style="color:#3B82F6;">Questions secondaires</h4>', unsafe_allow_html=True)
            st.write(plan_data.get("questions_secondaires", []))
        st.markdown('<hr>', unsafe_allow_html=True)
        st.markdown('<h4 style="color:#F59E42;">Liens trouvés et scrappés</h4>', unsafe_allow_html=True)
        for i, link in enumerate(links[:nb_results]):
            st.markdown(f"<b>Lien {i+1} :</b> <a href='{link}' target='_blank'>{link}</a>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#FFF7ED; border-radius:8px; padding:0.5em; margin-bottom:1em;'>{all_contents[i] if i < len(all_contents) else '(Pas de contenu)'}</div>", unsafe_allow_html=True) 