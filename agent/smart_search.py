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
    """Recherche intelligente qui combine Bing + sites spécialisés + sources directes"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # Langues acceptées
        self.accepted_languages = ['fr', 'en']
        
        # Sites spécialisés par thème
        self.specialized_sites = {
            'animals': [
                'https://wamiz.com',
                'https://www.30millionsdamis.fr', 
                'https://www.santevet.com'
            ],
            'tech': [
                'https://www.01net.com',
                'https://www.lemondeinformatique.fr',
                'https://techcrunch.com'
            ],
            'health': [
                'https://www.doctissimo.fr',
                'https://www.passeportsante.net',
                'https://www.ameli.fr'
            ],
            'science': [
                'https://www.futura-sciences.com',
                'https://www.science-et-vie.com'
            ],
            'news': [
                'https://www.lemonde.fr',
                'https://www.lefigaro.fr',
                'https://www.franceinfo.fr'
            ]
        }
        
        logger.info("🧠 Recherche intelligente initialisée")
    
    def detect_language(self, text: str) -> str:
        """Détecte la langue d'un texte (français ou anglais)"""
        if not text or len(text.strip()) < 10:
            return 'unknown'
        
        text_lower = text.lower()
        
        # Mots-clés français courants
        french_indicators = [
            'le ', 'la ', 'les ', 'de ', 'du ', 'des ', 'et ', 'est ', 'une ', 'dans ', 
            'pour ', 'avec ', 'sur ', 'par ', 'que ', 'qui ', 'sont ', 'ont ', 'peut ',
            'tout ', 'tous ', 'cette ', 'ces ', 'son ', 'ses ', 'nous ', 'vous ', 'leur ',
            'français', 'france', 'paris', 'marseille', 'lyon', 'toulouse'
        ]
        
        # Mots-clés anglais courants  
        english_indicators = [
            'the ', 'and ', 'is ', 'are ', 'was ', 'were ', 'have ', 'has ', 'had ',
            'will ', 'would ', 'could ', 'should ', 'this ', 'that ', 'these ', 'those ',
            'with ', 'from ', 'they ', 'them ', 'their ', 'there ', 'where ', 'when ',
            'english', 'america', 'american', 'british', 'london', 'new york'
        ]
        
        # Caractères spécifiques
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        if chinese_chars and len(chinese_chars) > 3:
            return 'zh'
        
        arabic_chars = re.findall(r'[\u0600-\u06ff]', text)
        if arabic_chars and len(arabic_chars) > 3:
            return 'ar'
        
        # Compter les indicateurs
        french_score = sum(1 for indicator in french_indicators if indicator in text_lower)
        english_score = sum(1 for indicator in english_indicators if indicator in text_lower)
        
        if french_score > english_score and french_score > 2:
            return 'fr'
        elif english_score > french_score and english_score > 2:
            return 'en'
        else:
            return 'unknown'
    
    def is_language_accepted(self, text: str, url: str = '') -> bool:
        """Vérifie si le contenu est dans une langue acceptée"""
        # Vérification rapide par domaine
        if any(domain in url for domain in ['.fr', '.com', '.org', '.net']):
            if '.cn' in url or '.ru' in url or '.jp' in url:
                return False
        
        # Détection de langue du contenu
        lang = self.detect_language(text)
        is_accepted = lang in self.accepted_languages
        
        if not is_accepted and lang != 'unknown':
            logger.debug(f"🚫 Contenu rejeté (langue: {lang}): {text[:50]}...")
        
        return is_accepted or lang == 'unknown'  # On garde 'unknown' par sécurité
    
    def detect_theme(self, query: str) -> str:
        """Détecte le thème principal de la requête"""
        query_lower = query.lower()
        
        # Mots-clés par thème
        themes = {
            'animals': ['chat', 'chien', 'animal', 'chiot', 'chaton', 'pet', 'animaux', 'vétérinaire'],
            'tech': ['ordinateur', 'smartphone', 'tech', 'technologie', 'software', 'hardware', 'app'],
            'health': ['santé', 'médecine', 'maladie', 'symptôme', 'traitement', 'docteur'],
            'science': ['science', 'recherche', 'étude', 'scientifique', 'expérience'],
            'news': ['actualité', 'news', 'politique', 'économie', 'société']
        }
        
        for theme, keywords in themes.items():
            if any(keyword in query_lower for keyword in keywords):
                logger.info(f"🎯 Thème détecté: {theme}")
                return theme
        
        logger.info("🎯 Thème détecté: general")
        return 'general'
    
    def search_bing(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Bing optimisée avec filtre de langue"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            # Ajouter paramètre de langue (français et anglais)
            url = f"https://www.bing.com/search?q={encoded_query}&count={max_results}&setlang=fr&mkt=fr-FR"
            
            logger.info(f"🔍 Recherche Bing: {query}")
            
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Bing erreur {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            filtered_count = 0
            
            # Chercher les résultats Bing
            search_results = soup.select('.b_algo')
            
            for result in search_results:
                try:
                    link_element = result.select_one('h2 a')
                    snippet_element = result.select_one('.b_caption p, .b_caption')
                    
                    if link_element:
                        title = link_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        # Filtrer les liens internes Bing/Microsoft
                        if url and not any(blocked in url.lower() for blocked in ['bing.com', 'microsoft.com', 'msn.com']):
                            # Vérifier la langue du titre et snippet
                            content_to_check = f"{title} {snippet}"
                            if self.is_language_accepted(content_to_check, url):
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                    'source': 'bing'
                                })
                                if len(results) >= max_results:
                                    break
                            else:
                                filtered_count += 1
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat Bing: {e}")
                    continue
            
            if filtered_count > 0:
                logger.info(f"✅ Bing: {len(results)} résultats trouvés ({filtered_count} filtrés pour langue)")
            else:
                logger.info(f"✅ Bing: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Bing: {e}")
            return []
    
    def search_google(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche Google optimisée avec anti-détection renforcée"""
        try:
            encoded_query = urllib.parse.quote_plus(query)
            # URL Google simplifiée pour éviter la détection
            url = f"https://www.google.com/search?q={encoded_query}&num={max_results + 5}"
            
            logger.info(f"🔍 Recherche Google: {query}")
            
            # Headers ultra-réalistes pour éviter la détection
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Microsoft Edge";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1'
            }
            
            # Délai aléatoire pour simuler un comportement humain
            time.sleep(random.uniform(0.5, 1.5))
            
            response = self.session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Google erreur {response.status_code}: {response.reason}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            filtered_count = 0
            
            # Debug: vérifier si Google renvoie du contenu
            title_check = soup.find('title')
            if title_check and 'captcha' in title_check.get_text().lower():
                logger.warning("⚠️ Google demande un CAPTCHA - utilisation de Bing uniquement")
                return []
            
            # Sélecteurs Google mis à jour (2024)
            search_results = soup.select('div.g, div[data-ved], .tF2Cxc, .hlcw0c')
            
            # Debug: afficher le nombre d'éléments trouvés
            logger.debug(f"Google: {len(search_results)} éléments de résultats trouvés")
            
            # Debug spécial: si pas de résultats, afficher le contenu de la page
            if len(search_results) == 0:
                page_title = soup.find('title')
                page_text = page_title.get_text() if page_title else "Pas de titre"
                logger.warning(f"🐛 Google Debug - Titre de la page: {page_text[:100]}")
                
                # Chercher s'il y a des éléments de résultats avec d'autres sélecteurs
                alt_results = soup.select('div[class*="result"], div[class*="search"], div[id*="search"]')
                logger.warning(f"🐛 Google Debug - Éléments alternatifs trouvés: {len(alt_results)}")
            
            for result in search_results:
                try:
                    # Chercher le lien principal (sélecteurs mis à jour)
                    link_element = result.select_one('h3 a, a h3, .yuRUbf a, [data-ved] a')
                    if not link_element:
                        link_element = result.find('a', href=True)
                    
                    # Chercher le titre et snippet (sélecteurs mis à jour)
                    title_element = result.select_one('h3, .LC20lb')
                    snippet_element = result.select_one('.VwiC3b, .s3v9rd, .IsZvec, span[data-ved], .aCOpRe')
                    
                    if link_element and title_element:
                        title = title_element.get_text(strip=True)
                        url = link_element.get('href', '')
                        snippet = snippet_element.get_text(strip=True) if snippet_element else title
                        
                        # Nettoyer l'URL Google
                        if url.startswith('/url?q='):
                            url = urllib.parse.unquote(url.split('/url?q=')[1].split('&')[0])
                        
                        # Filtrer les liens internes Google
                        if url and not any(blocked in url.lower() for blocked in [
                            'google.com', 'youtube.com', 'gmail.com', 'maps.google', 'translate.google'
                        ]):
                            # Vérifier la langue du titre et snippet
                            content_to_check = f"{title} {snippet}"
                            if self.is_language_accepted(content_to_check, url):
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                    'source': 'google'
                                })
                                if len(results) >= max_results:
                                    break
                            else:
                                filtered_count += 1
                            
                except Exception as e:
                    logger.debug(f"Erreur parsing résultat Google: {e}")
                    continue
            
            if filtered_count > 0:
                logger.info(f"✅ Google: {len(results)} résultats trouvés ({filtered_count} filtrés pour langue)")
            else:
                logger.info(f"✅ Google: {len(results)} résultats trouvés")
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Google: {e}")
            return []
    
    def search_specialized_sites(self, query: str, theme: str, max_results: int = 5) -> List[Dict]:
        """Recherche sur des sites spécialisés selon le thème"""
        results = []
        
        if theme not in self.specialized_sites:
            return results
        
        sites = self.specialized_sites[theme]
        logger.info(f"🎯 Recherche sites spécialisés ({theme}): {len(sites)} sites")
        
        for site in sites:
            try:
                logger.info(f"🔍 Exploration {site}")
                
                response = self.session.get(site, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Chercher des liens pertinents
                    article_links = soup.find_all('a', href=True)
                    
                    # Filtrer par mots-clés de la requête
                    query_keywords = query.lower().split()
                    relevant_links = []
                    
                    for link in article_links:
                        link_text = link.get_text().lower()
                        href = link.get('href', '')
                        
                        # Vérifier si le lien contient des mots-clés de la requête
                        if any(keyword in link_text for keyword in query_keywords):
                            # Convertir en URL absolue si nécessaire
                            if href.startswith('/'):
                                href = site + href
                            elif href.startswith('http'):
                                pass  # Déjà une URL complète
                            else:
                                continue  # Ignorer les liens relatifs non traités
                            
                            relevant_links.append({
                                'title': link.get_text(strip=True),
                                'url': href,
                                'snippet': f"Trouvé sur {site}",
                                'source': f'specialized_{theme}'
                            })
                    
                    # Prendre les meilleurs résultats
                    if relevant_links:
                        # Supprimer les doublons par URL
                        seen_urls = set()
                        unique_links = []
                        for link in relevant_links:
                            if link['url'] not in seen_urls and len(link['title']) > 10:
                                seen_urls.add(link['url'])
                                unique_links.append(link)
                        
                        results.extend(unique_links[:max_results//len(sites) + 1])
                        logger.info(f"✅ {site}: {len(unique_links)} liens pertinents")
                
                # Délai entre les sites
                time.sleep(random.uniform(0.5, 1.0))
                
            except Exception as e:
                logger.debug(f"Erreur site spécialisé {site}: {e}")
                continue
        
        logger.info(f"✅ Sites spécialisés: {len(results)} résultats au total")
        return results[:max_results]
    
    def search_comprehensive(self, query: str, max_results: int = 10) -> List[Dict]:
        """Recherche complète combinant Google + Bing + sites spécialisés"""
        
        # Détection du thème
        theme = self.detect_theme(query)
        
        all_results = []
        
        # 1. Recherche Google (source principale, mais fragile)
        google_results = self.search_google(query, max_results//3)
        all_results.extend(google_results)
        
        # Délai entre les recherches
        time.sleep(random.uniform(1.0, 2.0))
        
        # 2. Recherche Bing (source fiable)
        # Si Google échoue, compenser avec plus de résultats Bing
        bing_target = max_results//3 if len(google_results) > 0 else max_results//2
        bing_results = self.search_bing(query, bing_target)
        all_results.extend(bing_results)
        
        # Délai entre les recherches
        time.sleep(random.uniform(1.0, 2.0))
        
        # 3. Recherche sites spécialisés si thème détecté
        if theme != 'general':
            specialized_results = self.search_specialized_sites(query, theme, max_results//3)
            all_results.extend(specialized_results)
        
        # 3. Supprimer les doublons
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        # 4. Trier par pertinence (sources spécialisées en premier, puis Google)
        def sort_key(result):
            if 'specialized' in result['source']:
                return 0  # Priorité haute
            elif result['source'] == 'google':
                return 1  # Priorité élevée
            elif result['source'] == 'bing':
                return 2  # Priorité moyenne
            else:
                return 3  # Priorité basse
        
        unique_results.sort(key=sort_key)
        
        final_results = unique_results[:max_results]
        logger.info(f"🎉 Recherche complète terminée: {len(final_results)} résultats uniques")
        
        return final_results

def search_with_smart(query: str, max_results: int = 10) -> List[Dict]:
    """Interface pour la recherche intelligente"""
    searcher = SmartSearch()
    
    try:
        results = searcher.search_comprehensive(query, max_results)
        return results
    except Exception as e:
        logger.error(f"❌ Erreur recherche intelligente: {e}")
        return [] 