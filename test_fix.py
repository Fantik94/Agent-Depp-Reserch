#!/usr/bin/env python3
"""
Test après les corrections - SerpApi doit marcher maintenant
"""

import sys
import os

# Ajouter le dossier agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

def test_search_api_fixed():
    """Test SearchAPI avec SerpApi seulement"""
    print("🧪 Test SearchAPI corrigé...")
    
    try:
        from search_api import SearchAPI
        
        # Créer SearchAPI avec SerpApi seulement
        search_api = SearchAPI(search_engines=["SerpApi"])
        print("✅ SearchAPI créé avec SerpApi")
        
        # Test de recherche
        print("🔍 Test recherche 'python programming'...")
        results = search_api.search_web("python programming", max_results=3, enabled_engines=["SerpApi"])
        
        print(f"📊 Résultats trouvés: {len(results)}")
        
        if len(results) > 0:
            for i, result in enumerate(results, 1):
                print(f"   {i}. {result['title'][:60]}...")
                print(f"      Source: {result['source']}")
                print(f"      URL: {result['url'][:80]}...")
            return True
        else:
            print("❌ Aucun résultat trouvé")
            return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_research_agent_fixed():
    """Test ResearchAgent avec les corrections"""
    print("\n🧪 Test ResearchAgent corrigé...")
    
    try:
        from research_agent import ResearchAgent
        
        # Créer agent avec SerpApi seulement
        agent = ResearchAgent(search_engines=["SerpApi"])
        print("✅ ResearchAgent créé")
        
        # Test recherche simple (sans plan compliqué)
        print("🔍 Test recherche simple...")
        
        # Simuler une recherche directe
        results = agent.search_api.search_web("test query", max_results=2, enabled_engines=["SerpApi"])
        
        print(f"📊 Agent résultats: {len(results)}")
        if len(results) > 0:
            print("✅ L'agent peut maintenant faire des recherches !")
            return True
        else:
            print("❌ Aucun résultat de l'agent")
            return False
        
    except Exception as e:
        print(f"❌ Erreur agent: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Test des corrections SerpApi")
    print("=" * 40)
    
    # Test 1: SearchAPI direct
    api_works = test_search_api_fixed()
    
    # Test 2: ResearchAgent
    agent_works = test_research_agent_fixed()
    
    print("\n📊 RÉSULTATS DES CORRECTIONS:")
    print(f"   SearchAPI:     {'✅ MARCHE' if api_works else '❌ ÉCHOUE'}")
    print(f"   ResearchAgent: {'✅ MARCHE' if agent_works else '❌ ÉCHOUE'}")
    
    if api_works and agent_works:
        print("\n🎉 PARFAIT ! Les corrections ont marché !")
        print("💡 Redémarrez votre app Streamlit, elle devrait maintenant utiliser SerpApi.")
    else:
        print("\n⚠️ Il reste des problèmes.") 