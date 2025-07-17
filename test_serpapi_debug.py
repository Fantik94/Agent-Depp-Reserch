#!/usr/bin/env python3
"""Script de test pour diagnostiquer les problèmes SerpApi"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

import logging
from agent.config import Config
from agent.search_api import SearchAPI

# Configuration des logs pour voir les détails
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_serpapi():
    """Test de base de SerpApi"""
    print("🔍 Test de diagnostic SerpApi")
    print("=" * 50)
    
    # 1. Vérifier la configuration
    config = Config()
    print(f"📋 Clé SerpApi configurée: {'Oui' if config.SERP_API_KEY else 'Non'}")
    if config.SERP_API_KEY:
        print(f"🔐 Début de clé: {config.SERP_API_KEY[:10]}...")
        print(f"📏 Longueur clé: {len(config.SERP_API_KEY)} caractères")
    
    # 2. Test d'import du package
    try:
        from serpapi import GoogleSearch
        print("✅ Package serpapi importé avec succès")
    except ImportError as e:
        print(f"❌ Erreur import serpapi: {e}")
        return
    
    # 3. Test de recherche simple
    print("\n🧪 Test de recherche simple...")
    search_api = SearchAPI()
    
    # Test avec différentes requêtes
    test_queries = [
        "Python programming",
        "intelligence artificielle",
        "France",
        "test"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Test avec requête: '{query}'")
        try:
            results = search_api.search_serpapi_simple(query, max_results=3)
            print(f"   ✅ Résultats: {len(results)}")
            if results:
                for i, result in enumerate(results, 1):
                    print(f"      {i}. {result.get('title', 'Pas de titre')[:50]}...")
            else:
                print("   ⚠️ Aucun résultat trouvé")
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # 4. Test direct avec SerpApi
    print("\n🧪 Test direct SerpApi...")
    if config.SERP_API_KEY:
        try:
            params = {
                "engine": "google",
                "q": "test",
                "api_key": config.SERP_API_KEY
            }
            search = GoogleSearch(params)
            results = search.get_dict()
            print(f"   ✅ Réponse SerpApi reçue")
            print(f"   📊 Clés disponibles: {list(results.keys())}")
            if 'organic_results' in results:
                print(f"   📝 Nombre organic_results: {len(results['organic_results'])}")
            if 'error' in results:
                print(f"   ❌ Erreur dans réponse: {results['error']}")
        except Exception as e:
            print(f"   ❌ Erreur test direct: {e}")

if __name__ == "__main__":
    test_serpapi() 