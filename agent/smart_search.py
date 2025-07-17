import logging
from typing import List, Dict, Optional
import urllib.parse
import time
import random
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class SmartSearch:
    """Recherche Google ultra-optimisée avec anti-détection avancée"""
    
    def __init__(self):
        # Pool de User Agents réels et récents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.2210.133',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        ]
        
        # Pool de domaines Google pour rotation
        self.google_domains = [
            'https://www.google.com',
            'https://www.google.fr', 
            'https://google.com',
            'https://www.google.co.uk'
        ]
        
        # Créer une nouvelle session à chaque utilisation
        self.session = None
        
        logger.info("🧠 Google Search Ultra-optimisé initialisé")
    
    def _create_fresh_session(self):
        """Créer une session fraîche avec headers aléatoires"""
        if self.session:
            self.session.close()
        
        self.session = requests.Session()
        
        # User Agent aléatoire
        user_agent = random.choice(self.user_agents)
        
        # Headers variables et réalistes
        base_headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'fr,fr-FR;q=0.9,en;q=0.8',
                'en-US,en;q=0.9,fr;q=0.8'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Ajouter quelques headers aléatoires
        if random.choice([True, False]):
            base_headers['Cache-Control'] = random.choice(['no-cache', 'max-age=0', 'no-store'])
        
        if 'Chrome' in user_agent:
            base_headers.update({
                'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': random.choice(['"Windows"', '"macOS"', '"Linux"']),
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1'
            })
        
        self.session.headers.update(base_headers)
        return self.session
    
    def _get_random_search_params(self, query: str, max_results: int = 10) -> dict:
        """Générer des paramètres de recherche variables"""
        params = {
            'q': query,
            'num': min(max_results + random.randint(2, 8), 20),  # Varier le nombre
        }
        
        # Ajouter des paramètres aléatoires parfois
        if random.choice([True, False]):
            params['hl'] = random.choice(['fr', 'en', 'fr-FR'])
        
        if random.choice([True, False]):
            params['gl'] = random.choice(['FR', 'US', 'CA'])
        
        # Parfois ajouter un filtre temporel
        if random.choice([True, False, False]):  # 1/3 de chance
            params['tbs'] = random.choice(['qdr:m', 'qdr:w', 'qdr:y'])
        
        return params
    
    def search_google_advanced(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Google avec anti-détection ultra-avancée"""
        
        # Créer une session fraîche
        session = self._create_fresh_session()
        
        try:
            # Délai initial aléatoire
            time.sleep(random.uniform(1.0, 3.0))
            
            # Choisir un domaine Google aléatoire
            base_domain = random.choice(self.google_domains)
            
            # Étape 1: Visiter la page d'accueil Google d'abord (comportement humain)
            try:
                logger.info(f"🏠 Visite de la page d'accueil Google...")
                home_response = session.get(f"{base_domain}", timeout=15)
                if home_response.status_code == 200:
                    # Extraire les cookies si possible
                    logger.debug(f"✅ Page d'accueil visitée, cookies: {len(session.cookies)}")
                time.sleep(random.uniform(1.5, 4.0))
            except:
                logger.debug("⚠️ Échec visite page d'accueil (pas critique)")
            
            # Étape 2: Recherche proprement dite
            search_url = f"{base_domain}/search"
            params = self._get_random_search_params(query, max_results)
            
            logger.info(f"🔍 Recherche Google avancée: {query}")
            
            # Headers spécifiques pour la recherche
            search_headers = {
                'Referer': f"{base_domain}/",
                'Origin': base_domain
            }
            
            response = session.get(
                search_url, 
                params=params, 
                headers=search_headers,
                timeout=30,
                allow_redirects=True
            )
            
            # Gérer les redirections/erreurs
            if response.status_code == 429:
                logger.warning("⚠️ Rate limit Google détecté")
                time.sleep(random.uniform(10, 20))
                return []
            elif response.status_code == 302 or response.status_code == 301:
                logger.warning("⚠️ Redirection Google détectée (possible détection)")
                return []
            elif response.status_code != 200:
                logger.warning(f"⚠️ Google erreur {response.status_code}")
                return []
            
            # Parser la réponse
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Vérifications anti-bot
            page_title = soup.find('title')
            if page_title:
                title_text = page_title.get_text().lower()
                if any(word in title_text for word in ['captcha', 'robot', 'unusual traffic', 'verify']):
                    logger.warning(f"⚠️ Google anti-bot détecté: {title_text}")
                return []
            
            # Sélecteurs CSS mis à jour pour 2024/2025
            selectors_to_try = [
                'div.g',  # Sélecteur principal classique
                'div[data-ved]',  # Résultats avec data-ved
                '.tF2Cxc',  # Nouveau conteneur de résultats
                '.hlcw0c',  # Alternative récente
                '.yuRUbf',  # Conteneur de lien
                'div[jscontroller]',  # Résultats avec JS controller
                '.g .yuRUbf',  # Combinaison
                '[data-ved] .yuRUbf'  # Autre combinaison
            ]
            
            search_results = []
            for selector in selectors_to_try:
                search_results = soup.select(selector)
                if len(search_results) > 0:
                    logger.debug(f"✅ Sélecteur qui marche: {selector} ({len(search_results)} éléments)")
                    break
            
            # Debug amélioré
            if len(search_results) == 0:
                logger.warning(f"🐛 Google Debug - Titre: {page_title.get_text()[:100] if page_title else 'N/A'}")
                
                # Essayer de trouver d'autres éléments
                all_divs = soup.find_all('div')
                logger.warning(f"🐛 Google Debug - Total divs trouvés: {len(all_divs)}")
                
                # Chercher des patterns dans les classes
                classes_found = set()
                for div in all_divs[:50]:  # Limiter pour éviter spam
                    if div.get('class'):
                        classes_found.update(div.get('class'))
                
                logger.warning(f"🐛 Classes CSS principales: {list(classes_found)[:10]}")
                return []
            
            results = []
            
            for result in search_results[:max_results * 2]:  # Plus de marge
                try:
                    # Méthodes multiples pour trouver le lien
                    link_element = None
                    link_selectors = [
                        'h3 a', 'a h3', '.yuRUbf a', 
                        '[data-ved] a', 'a[href^="http"]',
                        '.LC20lb a', 'a[ping]'
                    ]
                    
                    for link_sel in link_selectors:
                        link_element = result.select_one(link_sel)
                        if link_element and link_element.get('href'):
                            break
                    
                    # Méthodes multiples pour le titre
                    title_element = None
                    title_selectors = ['h3', '.LC20lb', '.DKV0Md', '[role="heading"]']
                    
                    for title_sel in title_selectors:
                        title_element = result.select_one(title_sel)
                        if title_element:
                            break
                    
                    # Méthodes multiples pour le snippet
                    snippet_element = None
                    snippet_selectors = [
                        '.VwiC3b', '.s3v9rd', '.IsZvec', 
                        '.aCOpRe', '[data-content-feature]',
                        '.lEBKkf', 'span[data-ved]'
                    ]
                    
                    for snippet_sel in snippet_selectors:
                        snippet_element = result.select_one(snippet_sel)
                        if snippet_element:
                            break
                    
                    # Extraction des données
                    if link_element and title_element:
                        title = title_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title[:100]
                        
                        # Nettoyer l'URL Google
                        if url.startswith('/url?q='):
                            url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                        elif url.startswith('/search?'):
                            continue  # Ignorer les liens de recherche interne
                        
                        # Filtrage amélioré
                        if url and url.startswith('http') and not any(blocked in url.lower() for blocked in [
                            'google.com/search', 'google.fr/search',
                            'youtube.com', 'gmail.com', 'maps.google', 
                            'translate.google', 'support.google'
                        ]):
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                'source': 'google_advanced'
                                })
                            
                                if len(results) >= max_results:
                                    break
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat: {e}")
                    continue
            
            logger.info(f"✅ Google avancé: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur Google avancé: {e}")
            return []
        
        finally:
            # Fermer la session
            if session:
                session.close()
    
    def search_comprehensive(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche complète = seulement Google avancé"""
        logger.info(f"🧠 Recherche Google ultra-optimisée pour: {query}")
        
        # Détection de thème simple (pour les logs)
        theme = 'general'
        if any(word in query.lower() for word in ['chien', 'chat', 'animal']):
            theme = 'animals'
        elif any(word in query.lower() for word in ['tech', 'programming', 'code']):
            theme = 'tech'
        elif any(word in query.lower() for word in ['santé', 'maladie', 'médecin']):
            theme = 'health'
        elif any(word in query.lower() for word in ['actualité', 'news', 'info']):
            theme = 'news'
        
        logger.info(f"🎯 Thème détecté: {theme}")
        
        # Seulement Google
        results = self.search_google_advanced(query, max_results)
        
        logger.info(f"🎉 Recherche Google terminée: {len(results)} résultats uniques")
        return results
    
    def detect_theme(self, query: str) -> str:
        """Détection simple de thème"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['chien', 'chat', 'animal', 'vétérinaire']):
            return 'animals'
        elif any(word in query_lower for word in ['tech', 'programming', 'code', 'logiciel']):
            return 'tech'
        elif any(word in query_lower for word in ['santé', 'maladie', 'médecin', 'symptôme']):
            return 'health'
        elif any(word in query_lower for word in ['actualité', 'news', 'info', 'politique']):
            return 'news'
        else:
            return 'general'

def search_with_smart(query: str, max_results: int = 10) -> List[Dict]:
    """Point d'entrée pour l'utilisation externe"""
    smart_search = SmartSearch()
    return smart_search.search_comprehensive(query, max_results) 