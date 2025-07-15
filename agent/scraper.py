import requests
from newspaper import Article
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from config import Config
import time
import re

logger = logging.getLogger(__name__)

def detect_language(text: str) -> str:
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

def is_language_accepted(text: str) -> bool:
    """Vérifie si le contenu est dans une langue acceptée (français ou anglais)"""
    accepted_languages = ['fr', 'en']
    lang = detect_language(text)
    return lang in accepted_languages or lang == 'unknown'

class WebScraper:
    """Scraper web utilisant Newspaper3k et BeautifulSoup"""
    
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_article_newspaper(self, url: str) -> Optional[Dict]:
        """Scraper un article avec Newspaper3k"""
        try:
            article = Article(url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text.strip()) < 100:
                return None
            
            # Vérifier la langue du contenu
            content_to_check = f"{article.title or ''} {article.text[:500]}"
            if not is_language_accepted(content_to_check):
                lang = detect_language(content_to_check)
                logger.debug(f"🚫 Article rejeté (langue: {lang}): {url}")
                return None
            
            return {
                'url': url,
                'title': article.title or '',
                'content': article.text[:3000],  # Limiter à 3000 caractères
                'summary': article.summary[:500] if article.summary else '',
                'authors': article.authors,
                'publish_date': str(article.publish_date) if article.publish_date else '',
                'method': 'newspaper3k'
            }
            
        except Exception as e:
            logger.error(f"Erreur Newspaper3k pour {url}: {e}")
            return None
    
    def scrape_article_beautifulsoup(self, url: str) -> Optional[Dict]:
        """Scraper un article avec BeautifulSoup (fallback)"""
        try:
            response = self.session.get(url, timeout=self.config.SCRAPING_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Supprimer les scripts et styles
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extraire le titre
            title = ""
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text().strip()
            
            # Extraire le contenu principal
            content = ""
            
            # Chercher les balises communes de contenu
            content_selectors = [
                'article', 'main', '[role="main"]',
                '.content', '.post-content', '.entry-content',
                '.article-content', '.story-content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content = content_elem.get_text(strip=True)
                    break
            
            # Si pas de contenu spécifique trouvé, prendre les paragraphes
            if not content:
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            if not content or len(content.strip()) < 100:
                return None
            
            # Vérifier la langue du contenu
            content_to_check = f"{title} {content[:500]}"
            if not is_language_accepted(content_to_check):
                lang = detect_language(content_to_check)
                logger.debug(f"🚫 Article rejeté (langue: {lang}): {url}")
                return None
            
            return {
                'url': url,
                'title': title,
                'content': content[:3000],  # Limiter à 3000 caractères
                'summary': content[:500],
                'authors': [],
                'publish_date': '',
                'method': 'beautifulsoup'
            }
            
        except Exception as e:
            logger.error(f"Erreur BeautifulSoup pour {url}: {e}")
            return None
    
    def scrape_url(self, url: str) -> Optional[Dict]:
        """Scraper une URL avec fallback automatique"""
        # Essayer Newspaper3k en premier
        result = self.scrape_article_newspaper(url)
        
        # Si échec, essayer BeautifulSoup
        if result is None:
            result = self.scrape_article_beautifulsoup(url)
        
        return result
    
    def scrape_multiple_urls(self, urls: List[str], max_articles: int = None, method: str = "both") -> List[Dict]:
        """Scraper plusieurs URLs avec méthode configurable et filtre de langue"""
        if max_articles is None:
            max_articles = self.config.MAX_SCRAPED_ARTICLES
        
        scraped_articles = []
        failed_count = 0
        
        for i, url in enumerate(urls[:max_articles * 2]):  # Essayer plus d'URLs au cas où certaines échouent
            if len(scraped_articles) >= max_articles:
                break
                
            logger.info(f"Scraping {i+1}/{min(len(urls), max_articles * 2)}: {url}")
            
            article = None
            
            if method == "newspaper":
                # Utiliser seulement Newspaper3k
                article = self.scrape_article_newspaper(url)
            elif method == "beautifulsoup":
                # Utiliser seulement BeautifulSoup
                article = self.scrape_article_beautifulsoup(url)
            else:  # method == "both"
                # Méthode par défaut (essayer les deux)
                article = self.scrape_url(url)
            
            if article:
                scraped_articles.append(article)
            else:
                failed_count += 1
            
            # Pause pour éviter de surcharger les serveurs
            time.sleep(1)
        
        # Log des statistiques finales
        if failed_count > 0:
            logger.info(f"Articles scrapés avec succès: {len(scraped_articles)} (échecs: {failed_count})")
        else:
            logger.info(f"Articles scrapés avec succès: {len(scraped_articles)}")
        
        return scraped_articles 