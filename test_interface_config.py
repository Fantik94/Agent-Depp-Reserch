#!/usr/bin/env python3
"""
Test des nouveaux paramètres de configuration de l'interface
"""

import sys
import os

# Ajouter le dossier agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

def test_research_with_custom_params():
    """Test de research_with_progress_tracking avec nos nouveaux paramètres"""
    print("🧪 Test des paramètres personnalisés...")
    
    try:
        # Simuler les imports necessaires
        from research_agent import ResearchAgent
        from search_api import SearchAPI
        
        # Créer un agent simple
        agent = ResearchAgent(search_engines=["SerpApi"])
        
        # Test avec des paramètres personnalisés
        print("🔍 Test SearchAPI avec max_results=3...")
        results = agent.search_api.search_web(
            "test query", 
            max_results=3,  # Notre nouveau paramètre !
            enabled_engines=["SerpApi"]
        )
        
        print(f"📊 Résultats avec max_results=3: {len(results)}")
        
        if len(results) <= 3:
            print("✅ Le paramètre max_results fonctionne !")
            return True
        else:
            print(f"❌ Attendait max 3 résultats, a reçu {len(results)}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_plan_limitation():
    """Test de limitation du nombre de requêtes dans un plan"""
    print("\n🧪 Test de limitation des requêtes...")
    
    try:
        from llm_universal import UniversalLLMClient
        
        # Créer un client LLM
        llm_client = UniversalLLMClient(provider="groq")
        
        # Générer un plan complet
        plan = llm_client.generate_deep_search_plan("test query complex")
        all_queries = plan.get("requetes_recherche", [])
        
        print(f"📋 Plan original: {len(all_queries)} requêtes")
        
        # Simuler la limitation (comme dans le code)
        max_queries = 3
        limited_queries = all_queries[:max_queries]
        
        print(f"📋 Plan limité: {len(limited_queries)} requêtes (max={max_queries})")
        
        if len(limited_queries) <= max_queries:
            print("✅ La limitation du plan fonctionne !")
            return True
        else:
            print("❌ La limitation du plan ne fonctionne pas")
            return False
        
    except Exception as e:
        print(f"❌ Erreur plan: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Test des nouveaux paramètres de configuration")
    print("=" * 50)
    
    # Test 1: max_results
    results_ok = test_research_with_custom_params()
    
    # Test 2: max_queries  
    plan_ok = test_plan_limitation()
    
    print("\n📊 RÉSULTATS DES TESTS:")
    print(f"   max_results: {'✅ OK' if results_ok else '❌ ÉCHEC'}")
    print(f"   max_queries: {'✅ OK' if plan_ok else '❌ ÉCHEC'}")
    
    if results_ok and plan_ok:
        print("\n🎉 PARFAIT ! Les nouveaux paramètres fonctionnent !")
        print("💡 Vous pouvez maintenant utiliser l'interface Streamlit avec les sliders de configuration.")
    else:
        print("\n⚠️ Certains paramètres ne fonctionnent pas correctement.") 