#!/usr/bin/env python3
"""
Script de lancement de l'agent de recherche avec diagnostic
"""

import streamlit as st
import sys
import os
import logging

# Ajouter le dossier agent au PATH
sys.path.append(os.path.join(os.path.dirname(__file__), 'agent'))

# Configuration du logging pour plus de détails
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Point d'entrée principal"""
    st.set_page_config(
        page_title="🔍 Agent de Recherche Intelligent",
        page_icon="🔍",
        layout="wide"
    )
    
    # Afficher les diagnostics
    with st.sidebar:
        st.title("🔧 Diagnostics")
        
        if st.button("🧪 Test de fonctionnement"):
            with st.spinner("Test en cours..."):
                try:
                    # Import des modules
                    from search_api import SearchAPI
                    from llm_universal import UniversalLLMClient
                    st.success("✅ Modules importés avec succès")
                    
                    # Test LLM
                    llm = UniversalLLMClient(provider="mistral")
                    plan = llm.generate_search_plan("test simple")
                    st.success(f"✅ LLM fonctionne: {len(plan.get('requetes_recherche', []))} requêtes générées")
                    
                    # Test recherche
                    search_api = SearchAPI()
                    results = search_api.search_web("test", max_results=2, enabled_engines=["SerpApi"])
                    st.success(f"✅ Recherche fonctionne: {len(results)} résultats trouvés")
                    
                    # Afficher les détails
                    st.write("**Plan de test:**")
                    for i, query in enumerate(plan.get('requetes_recherche', []), 1):
                        st.write(f"{i}. {query}")
                    
                    st.write("**Résultats de test:**")
                    for i, result in enumerate(results, 1):
                        st.write(f"{i}. {result['title'][:50]}... [{result['source']}]")
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
                    st.code(str(e))
        
        st.markdown("---")
        st.markdown("**Status des moteurs:**")
        st.markdown("🟢 SerpApi: Configuré")  
        st.markdown("🟡 Google-HTML: Expérimental")
        st.markdown("🟢 SearXNG: Disponible")
        st.markdown("🔴 Serper: Non configuré")
    
    # Interface principale
    try:
        from app import main as app_main
        app_main()
    except Exception as e:
        st.error(f"❌ Erreur de chargement de l'application: {e}")
        st.code(str(e))
        
        # Afficher les détails pour debug
        with st.expander("🔍 Détails de l'erreur"):
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    main() 