#!/usr/bin/env python3
"""
Test de la nouvelle version Google ultra-optimisée
"""

import sys
import os

# Ajouter le dossier agent
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agent'))

def test_new_google_search():
    """Test de la nouvelle recherche Google"""
    print("🧪 Test de la nouvelle recherche Google ultra-optimisée...")
    
    try:
        # Forcer le rechargement du module
        import importlib
        if 'smart_search' in sys.modules:
            importlib.reload(sys.modules['smart_search'])
        
        from smart_search import SmartSearch
        
        # Créer une instance
        smart = SmartSearch()
        print(f"✅ Instance créée: {smart.__class__.__doc__}")
        
        # Test avec une requête simple
        print("🔍 Test avec 'python programming'...")
        results = smart.search_comprehensive("python programming", 3)
        
        print(f"📊 Résultats trouvés: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result.get('title', 'N/A')[:60]}...")
            print(f"      Source: {result.get('source', 'N/A')}")
            print(f"      URL: {result.get('url', 'N/A')[:80]}...")
            print()
        
        # Vérifier que c'est bien la nouvelle version
        has_google_advanced = hasattr(smart, 'search_google_advanced')
        has_user_agents = hasattr(smart, 'user_agents')
        
        print(f"🔍 Nouvelle méthode Google avancée: {'✅' if has_google_advanced else '❌'}")
        print(f"🔍 Pool User Agents: {'✅' if has_user_agents else '❌'}")
        
        if has_user_agents:
            print(f"🔍 Nombre d'User Agents: {len(smart.user_agents)}")
        
        return len(results) > 0
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_search_api_integration():
    """Test de l'intégration avec SearchAPI"""
    print("\n🧪 Test de l'intégration SearchAPI...")
    
    try:
        # Forcer le rechargement
        import importlib
        if 'search_api' in sys.modules:
            importlib.reload(sys.modules['search_api'])
        
        from search_api import SearchAPI
        
        # Créer une instance
        search_api = SearchAPI(search_engines=["Smart-Search"])
        
        # Test
        print("🔍 Test SearchAPI avec Smart-Search...")
        results = search_api.search_web("test query", max_results=2)
        
        print(f"📊 SearchAPI résultats: {len(results)}")
        for result in results:
            print(f"   - {result.get('source', 'N/A')}: {result.get('title', 'N/A')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur SearchAPI: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Test de la nouvelle version Google")
    print("=" * 50)
    
    # Test 1: Smart Search direct
    google_works = test_new_google_search()
    
    # Test 2: Intégration avec SearchAPI
    api_works = test_search_api_integration()
    
    print("\n📊 RÉSULTATS:")
    print(f"   Google direct: {'✅ FONCTIONNE' if google_works else '❌ ÉCHEC'}")
    print(f"   SearchAPI:     {'✅ FONCTIONNE' if api_works else '❌ ÉCHEC'}")
    
    if google_works and api_works:
        print("\n🎉 SUCCÈS ! La nouvelle version Google est opérationnelle !")
        print("💡 Redémarrez maintenant votre application Streamlit pour utiliser la nouvelle version.")
    else:
        print("\n⚠️ Il y a encore des problèmes à résoudre.") 