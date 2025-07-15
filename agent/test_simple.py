#!/usr/bin/env python3
"""
Test simple pour diagnostiquer les problèmes de l'agent
"""

import logging
from search_api import SearchAPI
from llm_universal import UniversalLLMClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_plan_generation():
    """Test de génération de plan avec différentes requêtes"""
    print("🧪 Test de génération de plan")
    print("=" * 50)
    
    llm_client = UniversalLLMClient(provider="mistral")
    
    # Tester différentes requêtes
    queries = [
        "les chats sont-ils méchants",
        "intelligence artificielle avantages",
        "recette de crêpes facile"
    ]
    
    for query in queries:
        print(f"\n🔍 Requête: {query}")
        plan = llm_client.generate_search_plan(query)
        print(f"📋 Plan généré:")
        for i, search_query in enumerate(plan.get("requetes_recherche", []), 1):
            print(f"  {i}. {search_query}")
        print(f"🎲 Stratégie: {plan.get('strategie', 'N/A')}")
    
    return True

def test_fallback_results():
    """Test des résultats de fallback"""
    print("\n🧪 Test des résultats de fallback")
    print("=" * 50)
    
    search_api = SearchAPI()
    
    # Tester différents types de requêtes
    queries = [
        "intelligence artificielle",  # Tech
        "mal de tête",               # Santé  
        "découverte scientifique",   # Science
        "recette cuisine"            # Général
    ]
    
    for query in queries:
        print(f"\n🔍 Fallback pour: {query}")
        results = search_api.create_fallback_results(query)
        print(f"📋 {len(results)} résultats de fallback:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']}")
            print(f"     URL: {result['url']}")
            print(f"     Type: {result['source']}")
    
    return True

def test_search_without_scraping():
    """Test de recherche sans scraping pour voir si les moteurs fonctionnent"""
    print("\n🧪 Test de recherche (sans scraping)")
    print("=" * 50)
    
    search_api = SearchAPI()
    
    # Test avec différents moteurs
    engines_to_test = ["SerpApi", "SearXNG"]
    query = "python programming"
    
    for engine in engines_to_test:
        print(f"\n🔍 Test moteur: {engine}")
        results = search_api.search_web(query, max_results=3, enabled_engines=[engine])
        print(f"✅ {len(results)} résultats trouvés:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title'][:60]}...")
            print(f"     Source: {result['source']}")
            print(f"     URL valide: {result['url'].startswith('http')}")

def main():
    """Test principal"""
    print("🚀 DIAGNOSTIC AGENT DE RECHERCHE")
    print("=" * 60)
    
    try:
        # Test 1: Plans de recherche
        test_plan_generation()
        
        # Test 2: Fallback
        test_fallback_results()
        
        # Test 3: Recherche de base
        test_search_without_scraping()
        
        print("\n✅ Tous les tests terminés")
        
    except Exception as e:
        print(f"\n❌ Erreur dans les tests: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 