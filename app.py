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

nb_results = st.slider("Nombre de résultats Google à analyser", min_value=1, max_value=10, value=3)
prompt = st.text_input("Entrez votre question ou sujet de recherche :")

# Initialisation de l'état
if 'plan_data' not in st.session_state:
    st.session_state.plan_data = None
if 'plan_validated' not in st.session_state:
    st.session_state.plan_validated = False
if 'nb_results' not in st.session_state:
    st.session_state.nb_results = nb_results
if 'prompt' not in st.session_state:
    st.session_state.prompt = prompt

if st.button("Générer un plan de recherche"):
    with st.spinner("Génération du plan en cours..."):
        st.session_state.plan_data = generateText(prompt, nb_results)
        st.session_state.plan_validated = False
        st.session_state.nb_results = nb_results
        st.session_state.prompt = prompt

if st.session_state.plan_data:
    plan_data = st.session_state.plan_data
    st.markdown('<h4 style="color:#3B82F6;">Plan généré</h4>', unsafe_allow_html=True)
    if "raw" in plan_data:
        st.write(plan_data["raw"])
        st.warning("Le format JSON n'a pas été respecté. Veuillez reformuler la question ou améliorer le prompt.")
    else:
        st.write(plan_data.get("plan", []))
        st.markdown('<h4 style="color:#3B82F6;">Mots-clés proposés</h4>', unsafe_allow_html=True)
        st.write(plan_data.get("keywords", []))
    col1, col2 = st.columns(2)
    if st.button("Valider ce plan et lancer le scraping"):
        st.session_state.plan_validated = True


if st.session_state.plan_validated and st.session_state.plan_data:
    plan_data = st.session_state.plan_data
    if "raw" in plan_data:
        keywords = [prompt]
    else:
        keywords = plan_data.get("keywords", [prompt])
    search_query = keywords[0] if keywords else prompt
    with st.spinner("Scraping et synthèse en cours..."):
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
        st.markdown('<h4 style="color:#F59E42;">Liens trouvés et scrappés</h4>', unsafe_allow_html=True)
        for i, link in enumerate(links[:nb_results]):
            st.markdown(f"<b>Lien {i+1} :</b> <a href='{link}' target='_blank'>{link}</a>", unsafe_allow_html=True)
            st.markdown(f"<div style='background:#FFF7ED; border-radius:8px; padding:0.5em; margin-bottom:1em;'>{all_contents[i] if i < len(all_contents) else '(Pas de contenu)'}</div>", unsafe_allow_html=True) 