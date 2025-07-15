#!/usr/bin/env python3
"""
Test simple de l'agent de recherche (sans interface)
"""

import logging
from search_api import SearchAPI
from llm_client import MistralLLMClient
import time

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_search_only():
    """Test uniquement la recherche web"""
    print("🔍 Test de la recherche web uniquement")
    print("=" * 50)
    
    search_api = SearchAPI()
    query = "intelligence artificielle"
    
    print(f"Recherche pour: {query}")
    results = search_api.search_web(query, 5)
    
    print(f"\n✅ {len(results)} résultats trouvés:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title'][:60]}...")
        print(f"   Source: {result['source']}")
        print(f"   URL: {result['url']}")
        print()
    
    return len(results) > 0

def test_llm_plan():
    """Test de génération de plan (avec gestion du rate limit)"""
    print("📋 Test de génération de plan")
    print("=" * 50)
    
    llm_client = MistralLLMClient()
    query = "intelligence artificielle"
    
    print(f"Génération de plan pour: {query}")
    plan = llm_client.generate_deep_search_plan(query)
    
    print(f"\n✅ Plan généré:")
    print(f"Stratégie: {plan['strategie']}")
    print(f"Requêtes: {plan['requetes_recherche']}")
    
    return True

def test_synthesis():
    """Test de synthèse simple"""
    print("✍️ Test de synthèse")
    print("=" * 50)
    
    llm_client = MistralLLMClient()
    
    # Données de test
    fake_results = [
        {
            'title': 'Intelligence artificielle - Définition',
            'snippet': 'L\'intelligence artificielle est une technologie...',
            'url': 'https://example.com/ia'
        }
    ]
    
    query = "intelligence artificielle"
    synthesis = llm_client.synthesize_results(query, fake_results, [])
    
    print(f"\n✅ Synthèse générée:")
    print(synthesis[:200] + "..." if len(synthesis) > 200 else synthesis)
    
    return True

def main():
    """Test principal"""
    print("🤖 Test Simple de l'Agent de Recherche")
    print("=" * 60)
    
    tests = [
        ("Recherche Web", test_search_only),
        ("Génération de Plan", test_llm_plan),
        ("Synthèse", test_synthesis)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n🚀 {test_name}...")
            success = test_func()
            results[test_name] = success
            print(f"{'✅ SUCCÈS' if success else '❌ ÉCHEC'}")
            
            # Pause entre les tests pour éviter le rate limiting
            if test_name != tests[-1][0]:  # Pas de pause après le dernier test
                print("⏳ Pause de 3 secondes...")
                time.sleep(3)
                
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            results[test_name] = False
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ SUCCÈS" if success else "❌ ÉCHEC"
        print(f"{test_name}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    
    print(f"\n🎯 Résultat global: {success_count}/{total_count} tests réussis")
    
    if success_count == total_count:
        print("🎉 Tous les tests sont passés ! L'agent fonctionne correctement.")
    elif success_count > 0:
        print("⚠️ Certains tests ont échoué, mais l'agent fonctionne partiellement.")
    else:
        print("❌ Tous les tests ont échoué. Vérifiez la configuration.")

if __name__ == "__main__":
    main() 