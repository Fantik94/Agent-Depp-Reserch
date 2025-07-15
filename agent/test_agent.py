#!/usr/bin/env python3
"""
Script de test pour l'agent de recherche
"""

import sys
import logging
from research_agent import ResearchAgent

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_agent():
    """Test simple de l'agent de recherche"""
    
    print("🔍 Test de l'Agent de Recherche Intelligent")
    print("=" * 50)
    
    try:
        # Initialiser l'agent
        print("Initialisation de l'agent...")
        agent = ResearchAgent()
        print("✅ Agent initialisé avec succès")
        
        # Question de test
        test_query = "Qu'est-ce que l'intelligence artificielle ?"
        print(f"\n🔍 Test de recherche: '{test_query}'")
        
        # Effectuer la recherche
        result = agent.research(test_query)
        
        # Afficher les résultats
        print("\n📊 Résultats:")
        print(f"- Requêtes de recherche: {len(result['plan'].get('requetes_recherche', []))}")
        print(f"- Résultats trouvés: {result['stats']['search_results_count']}")
        print(f"- Articles scrapés: {result['stats']['scraped_articles_count']}")
        
        print("\n📝 Synthèse (extrait):")
        synthesis = result['synthesis']
        print(synthesis[:500] + "..." if len(synthesis) > 500 else synthesis)
        
        print("\n✅ Test réussi !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_agent()
    sys.exit(0 if success else 1) 