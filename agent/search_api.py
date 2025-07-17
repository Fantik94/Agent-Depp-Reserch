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
        
        # Vérifier que la clé n'est pas vide ou placeholder
        if self.config.SERP_API_KEY in ["your_serp_api_key", "", "None", "null"]:
            logger.error("❌ Clé SerpApi invalide ou placeholder")
            return []
        
        try:
            logger.info(f"🔍 SerpApi simple pour: {query}")
            logger.debug(f"🔐 Utilisation clé SerpApi: {self.config.SERP_API_KEY[:10]}...")
            
            # EXACTEMENT comme l'ami
            params = {
                "engine": "google",
                "q": query,
                "num": max_results,
                "api_key": self.config.SERP_API_KEY,
                "hl": "fr",  # Langue française
                "gl": "fr"   # Pays France pour de meilleurs résultats
            }
            
            logger.debug(f"📋 Paramètres SerpApi: {params}")
            
            search = GoogleSearch(params)
            results_dict = search.get_dict()
            
            # Debug: afficher la structure de la réponse
            logger.debug(f"🔍 Clés de réponse SerpApi: {list(results_dict.keys())}")
            
            results = []
            if 'organic_results' in results_dict:
                logger.debug(f"📊 organic_results trouvés: {len(results_dict['organic_results'])} éléments")
                for i, item in enumerate(results_dict['organic_results'][:max_results]):
                    logger.debug(f"   Élément {i+1}: {item.get('title', 'Pas de titre')[:50]}...")
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'serpapi'
                    })
            else:
                logger.warning("⚠️ Pas de 'organic_results' dans la réponse SerpApi")
                if 'error' in results_dict:
                    logger.error(f"❌ Erreur SerpApi: {results_dict['error']}")
                if 'search_information' in results_dict:
                    logger.debug(f"ℹ️ Info recherche: {results_dict.get('search_information', {})}")
            
            logger.info(f"✅ SerpApi: {len(results)} résultats")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur SerpApi: {e}")
            logger.error(f"❌ Type d'erreur: {type(e).__name__}")
            return []
    
    def search_web(self, query: str, max_results: int = None, enabled_engines: List[str] = None) -> List[Dict]:
        """Recherche web SIMPLE - juste SerpApi"""
        if max_results is None:
            max_results = self.config.MAX_SEARCH_RESULTS
        
        if enabled_engines is None:
            enabled_engines = self.search_engines
        
        logger.info(f"🚀 Recherche SIMPLE pour: '{query}'")
        
        # Nettoyer la requête de manière plus intelligente
        clean_query = query.strip()
        
        # Si la requête est très longue, la simplifier intelligemment
        if len(clean_query) > 60:  # Réduire le seuil de 80 à 60
            words = clean_query.split()
            if len(words) > 8:  # Si plus de 8 mots
                # Prendre les mots les plus importants (début + mots-clés)
                important_words = []
                
                # Prendre les 3 premiers mots (souvent les plus importants)
                important_words.extend(words[:3])
                
                # Chercher des mots-clés importants dans le reste
                keywords = ['comment', 'qui', 'quoi', 'pourquoi', 'où', 'quand', 'meilleur', 'tendance', 'évolution']
                for word in words[3:]:
                    if word.lower() in keywords or len(word) > 5:  # Mots longs souvent importants
                        important_words.append(word)
                        if len(important_words) >= 6:  # Limiter à 6 mots max
                            break
                
                clean_query = " ".join(important_words)
                logger.info(f"📝 Requête intelligemment simplifiée: '{clean_query}'")
            else:
                # Si pas trop de mots mais string longue, garder les premiers 60 caractères
                clean_query = clean_query[:60].rsplit(' ', 1)[0]  # Couper au dernier mot complet
                logger.info(f"📝 Requête raccourcie: '{clean_query}'")
        
        # Vérifier que la requête n'est pas trop courte ou vide
        if len(clean_query.strip()) < 3:
            logger.warning(f"⚠️ Requête trop courte après nettoyage: '{clean_query}' - utilisation requête originale")
            clean_query = query.strip()[:60]  # Fallback vers requête originale tronquée
        
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
                    # Si pas de résultats avec la requête nettoyée, essayer avec une version encore plus simple
                    if clean_query != query.strip()[:30]:
                        logger.info("🔄 Tentative avec requête encore plus simple...")
                        simple_query = query.strip()[:30].rsplit(' ', 1)[0]
                        if len(simple_query.strip()) >= 3:
                            fallback_results = self.search_serpapi_simple(simple_query, max_results)
                            if len(fallback_results) > 0:
                                logger.info(f"✅ Requête simplifiée a donné {len(fallback_results)} résultats")
                                results.extend(fallback_results)
                                break
            else:
                logger.warning(f"⚠️ Moteur {engine} non supporté")
        
        # PAS de sites pourris comme fallback !
        if len(results) == 0:
            logger.warning(f"⚠️ Aucun résultat trouvé pour '{clean_query}' - pas de fallback pourri")
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