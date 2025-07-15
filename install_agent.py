#!/usr/bin/env python3
"""
Script d'installation pour Agent Depp avec requests-html
Installation simple et rapide sans navigateur
"""

import subprocess
import sys
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_requirements():
    """Installe les dépendances Python"""
    try:
        logger.info("📦 Installation des dépendances Python...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True, capture_output=True, text=True)
        logger.info("✅ Dépendances Python installées")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erreur installation Python: {e}")
        logger.error(f"Sortie d'erreur: {e.stderr}")
        return False

def test_imports():
    """Test des imports principaux"""
    try:
        logger.info("🧪 Test des imports...")
        
        # Test requests-html
        try:
            from requests_html import HTMLSession
            logger.info("✅ requests-html OK")
        except ImportError:
            logger.warning("⚠️ requests-html non disponible, utilisation de requests")
        
        # Test BeautifulSoup
        from bs4 import BeautifulSoup
        logger.info("✅ BeautifulSoup OK")
        
        # Test Streamlit
        import streamlit
        logger.info("✅ Streamlit OK")
        
        # Test autres dépendances
        import requests
        import pandas
        logger.info("✅ Toutes les dépendances OK")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test imports échoué: {e}")
        return False

def test_search():
    """Test rapide de recherche"""
    try:
        logger.info("🔍 Test de recherche...")
        
        # Import du module de recherche
        sys.path.append(os.path.join(os.path.dirname(__file__), 'agent'))
        from html_search import search_with_html
        
        # Test simple
        results = search_with_html("test", max_results=1, engine="google")
        
        if results:
            logger.info(f"✅ Test recherche réussi: {len(results)} résultat(s)")
        else:
            logger.warning("⚠️ Test recherche: aucun résultat (normal si bloqué)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Test recherche échoué: {e}")
        return False

def main():
    """Installation complète"""
    logger.info("🚀 Début de l'installation de Agent Depp avec HTML Search")
    
    # Étape 1: Dépendances Python
    if not install_requirements():
        logger.error("❌ Échec de l'installation des dépendances Python")
        return False
    
    # Étape 2: Test des imports
    if not test_imports():
        logger.error("❌ Échec du test des imports")
        return False
    
    # Étape 3: Test de recherche
    if not test_search():
        logger.warning("⚠️ Test recherche échoué, mais l'installation peut fonctionner")
    
    logger.info("🎉 Installation terminée avec succès!")
    logger.info("💡 Vous pouvez maintenant lancer l'agent avec: python run_agent.py")
    logger.info("🔧 Moteurs disponibles: Google, Bing, DuckDuckGo, Startpage (HTML)")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 