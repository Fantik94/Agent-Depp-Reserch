import requests
import json
from typing import List, Dict, Optional
from config import Config
import logging
import urllib.parse
import time

# Import SerpApi comme l'ami
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logging.warning("⚠️ Package serpapi non disponible")

logger = logging.getLogger(__name__)

class SearchAPI:
    """API de recherche - SIMPLE et EFFICACE"""
    
    def __init__(self, search_engines: Optional[List[str]] = None):
        self.config = Config()
        self.search_engines = search_engines or ["SerpApi"]
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_serpapi_simple(self, query: str, max_results: int = 10) -> List[Dict]:
        """SerpApi SIMPLE comme l'ami - ça marche !"""
        if not SERPAPI_AVAILABLE:
            logger.error("❌ Package serpapi manquant")
            return []
        
        if not self.config.SERP_API_KEY:
            logger.error("❌ Pas de clé SerpApi")
            return []
        
        try:
            logger.info(f"🔍 SerpApi simple pour: {query}")
            
            # EXACTEMENT comme l'ami
            params = {
                "engine": "google",
                "q": query,
                "num": max_results,
                "api_key": self.config.SERP_API_KEY
            }
            
            search = GoogleSearch(params)
            results_dict = search.get_dict()
            
            results = []
            if 'organic_results' in results_dict:
                for item in results_dict['organic_results'][:max_results]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'serpapi'
                    })
            
            logger.info(f"✅ SerpApi: {len(results)} résultats")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur SerpApi: {e}")
            return []
    
    def search_web(self, query: str, max_results: int = None, enabled_engines: List[str] = None) -> List[Dict]:
        """Recherche web SIMPLE - juste SerpApi"""
        if max_results is None:
            max_results = self.config.MAX_SEARCH_RESULTS
        
        if enabled_engines is None:
            enabled_engines = self.search_engines
        
        logger.info(f"🚀 Recherche SIMPLE pour: '{query}'")
        
        # Nettoyer la requête
        clean_query = query.strip()
        if len(clean_query) > 80:
            words = clean_query.split()
            clean_query = " ".join(words[-4:])
            logger.info(f"📝 Requête simplifiée: '{clean_query}'")
        
        results = []
        
        # SEULEMENT SerpApi - simple et efficace
        for engine in enabled_engines:
            if engine == "SerpApi":
                engine_results = self.search_serpapi_simple(clean_query, max_results)
                results.extend(engine_results)
                
                # Si on a des résultats, on s'arrête
                if len(engine_results) > 0:
                    logger.info(f"✅ SerpApi a donné {len(engine_results)} résultats - on s'arrête")
                    break
            else:
                logger.warning(f"⚠️ Moteur {engine} non supporté")
        
        # PAS de sites pourris comme fallback !
        if len(results) == 0:
            logger.warning("⚠️ Aucun résultat trouvé - pas de fallback pourri")
            return []
        
        # Nettoyer et dédupliquer
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get('url', '')
            if url and url not in seen_urls and url.startswith('http'):
                seen_urls.add(url)
                unique_results.append(result)
        
        final_results = unique_results[:max_results]
        
        logger.info(f"✅ Recherche terminée: {len(final_results)} résultats finaux")
        for i, result in enumerate(final_results, 1):
            logger.info(f"   {i}. {result['title'][:50]}... [serpapi]")
        
        return final_results