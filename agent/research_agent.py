from typing import Dict, List
import logging
from search_api import SearchAPI
from scraper import WebScraper
from llm_universal import UniversalLLMClient
from config import Config

logger = logging.getLogger(__name__)

class ResearchAgent:
    """Agent de recherche principal qui coordonne toutes les étapes"""
    
    def __init__(self, llm_provider: str = None, search_engines: List[str] = None, scraping_method: str = "both"):
        self.config = Config()
        self.search_api = SearchAPI()
        self.scraper = WebScraper()
        self.llm_client = UniversalLLMClient(provider=llm_provider)
        self.search_engines = search_engines
        self.scraping_method = scraping_method
    
    def research(self, user_query: str) -> Dict:
        """Effectue une recherche complète basée sur la requête utilisateur"""
        
        logger.info(f"Début de la recherche pour: {user_query}")
        
        # Étape 1: Génération du plan de recherche
        logger.info("📋 Génération du plan de recherche...")
        plan = self.llm_client.generate_search_plan(user_query)
        
        # Étape 2: Recherche web pour chaque requête du plan
        logger.info("🔍 Recherche web en cours...")
        all_search_results = []
        
        for query in plan.get("requetes_recherche", [user_query]):
            results = self.search_api.search_web(query)
            all_search_results.extend(results)
            logger.info(f"  - '{query}': {len(results)} résultats")
        
        # Supprimer les doublons
        unique_results = []
        seen_urls = set()
        for result in all_search_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        # Étape 3: Scraping des articles les plus pertinents
        logger.info("📰 Scraping des articles...")
        urls_to_scrape = [result['url'] for result in unique_results[:self.config.MAX_SCRAPED_ARTICLES * 2]]
        scraped_articles = self.scraper.scrape_multiple_urls(urls_to_scrape)
        
        # Étape 4: Synthèse des résultats
        logger.info("✍️ Synthèse des résultats...")
        synthesis = self.llm_client.synthesize_results(user_query, unique_results, scraped_articles)
        
        # Préparer le résultat final
        result = {
            "query": user_query,
            "plan": plan,
            "search_results": unique_results,
            "scraped_articles": scraped_articles,
            "synthesis": synthesis,
            "stats": {
                "search_results_count": len(unique_results),
                "scraped_articles_count": len(scraped_articles),
                "search_queries_used": len(plan.get("requetes_recherche", []))
            }
        }
        
        logger.info("✅ Recherche terminée avec succès")
        return result
    
    def quick_search(self, query: str) -> str:
        """Recherche rapide qui retourne directement la synthèse"""
        result = self.research(query)
        return result["synthesis"] 