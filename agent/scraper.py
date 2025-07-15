import requests
from newspaper import Article
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
from config import Config
import time

logger = logging.getLogger(__name__)

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
        """Scraper plusieurs URLs avec méthode configurable"""
        if max_articles is None:
            max_articles = self.config.MAX_SCRAPED_ARTICLES
        
        scraped_articles = []
        
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
            
            # Pause pour éviter de surcharger les serveurs
            time.sleep(1)
        
        logger.info(f"Articles scrapés avec succès: {len(scraped_articles)}")
        return scraped_articles 