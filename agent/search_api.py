import requests
import json
from typing import List, Dict, Optional
from config import Config
import logging
import urllib.parse
import time
import random
from smart_search import search_with_smart

logger = logging.getLogger(__name__)

class SearchAPI:
    """API de recherche utilisant SerpApi et des méthodes alternatives"""
    
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def search_serpapi_free(self, query: str, max_results: int = 10) -> List[Dict]:
        """Utilise SerpApi avec clé API personnelle"""
        try:
            # SerpApi avec clé API personnelle
            url = "https://serpapi.com/search.json"
            params = {
                'q': query,
                'engine': 'google',
                'num': max_results,
                'api_key': self.config.SERP_API_KEY
            }
            
            logger.info(f"🔍 Tentative SerpApi pour: {query}")
            response = self.session.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if 'organic_results' in data:
                    for item in data['organic_results'][:max_results]:
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': 'serpapi'
                        })
                
                logger.info(f"✅ SerpApi: {len(results)} résultats trouvés")
                return results
            else:
                logger.warning(f"⚠️ SerpApi erreur {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ Erreur SerpApi: {e}")
        
        return []
    
    def search_searxng(self, query: str, max_results: int = 10) -> List[Dict]:
        """Utilise une instance publique de SearXNG"""
        try:
            # Instance publique de SearXNG
            url = "https://search.bus-hit.me/search"
            params = {
                'q': query,
                'format': 'json',
                'engines': 'google,bing',
                'categories': 'general'
            }
            
            logger.info(f"🔍 Tentative SearXNG pour: {query}")
            response = self.session.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if 'results' in data:
                    for item in data['results'][:max_results]:
                        if item.get('url', '').startswith('http'):
                            results.append({
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'snippet': item.get('content', ''),
                                'source': 'searxng'
                            })
                
                logger.info(f"✅ SearXNG: {len(results)} résultats trouvés")
                return results
            else:
                logger.warning(f"⚠️ SearXNG erreur {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Erreur SearXNG: {e}")
        
        return []
    
    def search_smart(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche intelligente (Bing + sites spécialisés)"""
        try:
            logger.info(f"🧠 Recherche intelligente pour: {query}")
            results = search_with_smart(query, max_results)
            logger.info(f"✅ Recherche intelligente: {len(results)} résultats trouvés")
            return results
        except Exception as e:
            logger.error(f"❌ Erreur recherche intelligente: {e}")
            return []
    
    def search_serper(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche avec Serper.dev API"""
        if not self.config.SERPER_API_KEY:
            logger.debug("🔑 Pas de clé Serper configurée")
            return []
        
        try:
            headers = {
                'X-API-KEY': self.config.SERPER_API_KEY,
                'Content-Type': 'application/json'
            }
            
            payload = {
                'q': query,
                'num': max_results
            }
            
            logger.info(f"🔍 Tentative Serper pour: {query}")
            response = requests.post(
                self.config.SERPER_URL, 
                headers=headers, 
                json=payload,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if 'organic' in data:
                    for item in data['organic']:
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'source': 'serper'
                        })
                
                logger.info(f"✅ Serper: {len(results)} résultats trouvés")
                return results
            else:
                logger.warning(f"⚠️ Serper erreur {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            logger.error(f"❌ Erreur Serper: {e}")
        
        return []
    
    def create_fallback_results(self, query: str) -> List[Dict]:
        """Crée des résultats de fallback basés sur des sites populaires"""
        logger.info(f"🆘 Création de résultats de fallback pour: {query}")
        
        # Sites populaires où chercher
        sites = [
            "wikipedia.org",
            "lemonde.fr",
            "lefigaro.fr",
            "franceinfo.fr",
            "liberation.fr",
            "futura-sciences.com",
            "doctissimo.fr",
            "sante.journaldesfemmes.fr"
        ]
        
        results = []
        encoded_query = urllib.parse.quote_plus(query)
        
        for site in sites[:5]:  # Limiter à 5 sites
            results.append({
                'title': f"Recherche '{query}' sur {site}",
                'url': f"https://{site}/search?q={encoded_query}",
                'snippet': f"Résultats de recherche pour '{query}' sur {site}",
                'source': 'fallback'
            })
        
        logger.info(f"🔄 {len(results)} résultats de fallback créés")
        return results
    
    def search_web(self, query: str, max_results: int = None, enabled_engines: List[str] = None) -> List[Dict]:
        """Recherche web avec multiple APIs et fallbacks configurables"""
        if max_results is None:
            max_results = self.config.MAX_SEARCH_RESULTS
        
        if enabled_engines is None:
            enabled_engines = ["SerpApi", "SearXNG", "Serper", "Smart-Search"]
        
        logger.info(f"🚀 Début recherche pour: '{query}'")
        
        # Nettoyer la requête
        clean_query = query.strip()
        if len(clean_query) > 80:
            words = clean_query.split()
            clean_query = " ".join(words[-4:])  # 4 derniers mots
            logger.info(f"📝 Requête simplifiée: '{clean_query}'")
        
        results = []
        
        # Recherche configurable selon les moteurs sélectionnés
        for i, engine in enumerate(enabled_engines, 1):
            # Arrêter si on a assez de résultats
            if len(results) >= max_results:
                break
                
            logger.info(f"🎯 Étape {i}: Tentative {engine}")
            engine_results = []
            
            if engine == "SerpApi":
                engine_results = self.search_serpapi_free(clean_query, max_results)
            elif engine == "Serper" and self.config.SERPER_API_KEY:
                engine_results = self.search_serper(clean_query, max_results)
            elif engine == "SearXNG":
                engine_results = self.search_searxng(clean_query, max_results)
            elif engine == "Smart-Search":
                engine_results = self.search_smart(clean_query, max_results)
            else:
                logger.warning(f"⚠️ Moteur {engine} non supporté ou non configuré")
                continue
            
            results.extend(engine_results)
            
            # Arrêt anticipé si on a suffisamment de résultats
            if len(engine_results) >= max_results // 2:
                logger.info(f"✅ {engine} suffisant: {len(engine_results)} résultats - arrêt anticipé")
                break
            
            # Délai entre les moteurs
            time.sleep(0.5 if engine == "SerpApi" else 1)
        
        # Stratégie 5: Fallback avec sites populaires
        if len(results) == 0:
            logger.warning("⚠️ Aucun résultat trouvé, utilisation du fallback")
            results = self.create_fallback_results(clean_query)
        
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
            logger.info(f"   {i}. {result['title'][:50]}... [{result['source']}]")
        
        return final_results 