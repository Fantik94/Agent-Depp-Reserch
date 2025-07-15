import logging
from typing import List, Dict, Optional
import urllib.parse
import time
import random

logger = logging.getLogger(__name__)

class HTMLSearch:
    """Recherche web avec requests-html pour contourner les limitations"""
    
    def __init__(self):
        try:
            from requests_html import HTMLSession
            self.session = HTMLSession()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            logger.info("🚀 Session requests-html initialisée")
        except ImportError:
            logger.error("❌ requests-html non disponible, fallback vers requests basique")
            import requests
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
    
    def search_google(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Google avec requests-html et contournement anti-bot"""
        try:
            # Encodage de la requête avec paramètres supplémentaires
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.google.com/search?q={encoded_query}&num={max_results}&hl=fr&lr=lang_fr"
            
            logger.info(f"🔍 Recherche Google HTML: {query}")
            logger.debug(f"URL Google: {url}")
            
            # Headers plus sophistiqués pour éviter la détection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Faire la requête avec délai aléatoire
            time.sleep(random.uniform(1, 3))
            response = self.session.get(url, headers=headers, timeout=30)
            
            logger.debug(f"Status Google: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Google HTML erreur {response.status_code}")
                logger.debug(f"Response content preview: {response.text[:500]}")
                return []
            
            # Parser avec BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: vérifier si on a du contenu
            logger.debug(f"HTML content length: {len(response.text)}")
            logger.debug(f"Title trouvé: {soup.title.string if soup.title else 'None'}")
            
            # Chercher les résultats avec différents sélecteurs (ordre de priorité)
            selectors = [
                'div.g',                    # Sélecteur principal Google
                'div[data-ved]',           # Alternative moderne
                '.tF2Cxc',                 # Nouveau format
                '.yuRUbf',                 # Conteneur de liens
                'div.ZINbbc',              # Fallback
                'div.MjjYud'               # Autre fallback
            ]
            
            search_results = []
            for selector in selectors:
                search_results = soup.select(selector)
                logger.debug(f"Sélecteur '{selector}': {len(search_results)} éléments trouvés")
                if search_results:
                    break
            
            if not search_results:
                logger.warning("⚠️ Aucun résultat trouvé avec les sélecteurs")
                # Debug: afficher le HTML pour diagnostic
                logger.debug("HTML structure preview:")
                for div in soup.find_all('div')[:5]:
                    logger.debug(f"DIV: class={div.get('class')}, id={div.get('id')}")
            
            results = []
            for i, result in enumerate(search_results[:max_results]):
                try:
                    # Chercher le titre et le lien avec plus de sélecteurs
                    link_selectors = ['a[href]', 'h3 a', '.yuRUbf a']
                    title_selectors = ['h3', '.LC20lb', '.DKV0Md', '.yuRUbf h3']
                    snippet_selectors = ['.VwiC3b', '.s3v9rd', '.aCOpRe', '.IsZvec']
                    
                    link_element = None
                    for selector in link_selectors:
                        link_element = result.select_one(selector)
                        if link_element:
                            break
                    
                    title_element = None
                    for selector in title_selectors:
                        title_element = result.select_one(selector)
                        if title_element:
                            break
                    
                    snippet_element = None
                    for selector in snippet_selectors:
                        snippet_element = result.select_one(selector)
                        if snippet_element:
                            break
                    
                    if link_element and title_element:
                        url = link_element.get('href', '')
                        title = title_element.get_text(strip=True)
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        # Nettoyer l'URL Google redirect
                        if url.startswith('/url?q='):
                            url_params = urllib.parse.parse_qs(url.split('?', 1)[1])
                            url = url_params.get('q', [url])[0]
                        elif url.startswith('/search'):
                            continue  # Ignorer les liens internes Google
                        
                        # Vérifier que l'URL est valide
                        if title and url and url.startswith('http') and not any(x in url.lower() for x in ['google.com', 'accounts.google']):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'google_html'
                            })
                            logger.debug(f"Résultat {i+1}: {title[:50]}... -> {url[:100]}")
                        else:
                            logger.debug(f"Résultat {i+1} ignoré: URL={url}, Title={title[:30] if title else 'None'}")
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat Google {i+1}: {e}")
                    continue
            
            logger.info(f"✅ Google HTML: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Google HTML: {e}")
            logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
            return []
    
    def search_bing(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Bing avec requests-html"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.bing.com/search?q={encoded_query}&count={max_results}"
            
            logger.info(f"🔍 Recherche Bing HTML: {query}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Bing HTML erreur {response.status_code}")
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            search_results = soup.select('.b_algo')
            
            for result in search_results[:max_results]:
                try:
                    link_element = result.select_one('h2 a')
                    snippet_element = result.select_one('.b_caption p, .b_caption')
                    
                    if link_element:
                        title = link_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        if title and url and not any(x in url.lower() for x in ['bing.com', 'microsoft.com']):
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'bing_html'
                            })
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat Bing: {e}")
                    continue
            
            logger.info(f"✅ Bing HTML: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Bing HTML: {e}")
            return []
    
    def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche DuckDuckGo avec requests-html"""
        try:
            # DuckDuckGo nécessite une approche différente
            # Utiliser l'API HTML de DuckDuckGo
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            logger.info(f"🔍 Recherche DuckDuckGo HTML: {query}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ DuckDuckGo HTML erreur {response.status_code}")
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # DuckDuckGo HTML utilise des sélecteurs différents
            search_results = soup.select('.result')
            
            for result in search_results[:max_results]:
                try:
                    link_element = result.select_one('.result__a')
                    title_element = result.select_one('.result__title')
                    snippet_element = result.select_one('.result__snippet')
                    
                    if link_element:
                        title = title_element.get_text(strip=True) if title_element else link_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        if title and url and 'duckduckgo.com' not in url.lower():
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'duckduckgo_html'
                            })
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat DuckDuckGo: {e}")
                    continue
            
            logger.info(f"✅ DuckDuckGo HTML: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche DuckDuckGo HTML: {e}")
            return []
    
    def search_startpage(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Startpage avec requests-html"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            url = f"https://www.startpage.com/search?q={encoded_query}"
            
            logger.info(f"🔍 Recherche Startpage HTML: {query}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Startpage HTML erreur {response.status_code}")
                return []
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            search_results = soup.select('.w-gl__result')
            
            for result in search_results[:max_results]:
                try:
                    link_element = result.select_one('.w-gl__result-title a')
                    snippet_element = result.select_one('.w-gl__description')
                    
                    if link_element:
                        title = link_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        if title and url and 'startpage.com' not in url.lower():
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'source': 'startpage_html'
                            })
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat Startpage: {e}")
                    continue
            
            logger.info(f"✅ Startpage HTML: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Startpage HTML: {e}")
            return []

def search_with_html(query: str, max_results: int = 10, engine: str = "google") -> List[Dict]:
    """Interface pour les recherches HTML"""
    searcher = HTMLSearch()
    
    # Ajouter un délai aléatoire pour éviter d'être bloqué
    time.sleep(random.uniform(0.5, 1.5))
    
    try:
        if engine == "google":
            return searcher.search_google(query, max_results)
        elif engine == "bing":
            return searcher.search_bing(query, max_results)
        elif engine == "duckduckgo":
            return searcher.search_duckduckgo(query, max_results)
        elif engine == "startpage":
            return searcher.search_startpage(query, max_results)
        else:
            logger.error(f"❌ Moteur non supporté: {engine}")
            return []
    except Exception as e:
        logger.error(f"❌ Erreur interface HTML: {e}")
        return [] 

def test_html_search():
    """Test simple de la recherche HTML"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    print("🧪 Test de recherche HTML")
    print("=" * 50)
    
    searcher = HTMLSearch()
    
    # Test Google
    print("\n🔍 Test Google HTML:")
    results = searcher.search_google("intelligence artificielle", max_results=3)
    print(f"✅ {len(results)} résultats trouvés")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['title'][:60]}...")
        print(f"   URL: {result['url'][:80]}...")
        print(f"   Snippet: {result['snippet'][:100]}...")
    
    return len(results) > 0

if __name__ == "__main__":
    test_html_search() 