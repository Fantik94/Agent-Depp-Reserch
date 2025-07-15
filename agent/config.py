import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Configuration de l'agent de recherche"""
    
    # API Keys
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "OHgvSY6RrhHNkTY1M3RQ7ici0iLuDwPv")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")  # Serper.dev - pas configuré
    SERP_API_KEY = os.getenv("SERP_API_KEY", "7cf1b4ca2876139b97281a684274718633c2cd3c5d1a153c5999a16099fdfece")  # SerpApi.com
    
    # Paramètres de recherche
    MAX_SEARCH_RESULTS = 10
    MAX_SCRAPED_ARTICLES = 5
    
    # URLs API
    SERPER_URL = "https://google.serper.dev/search"
    
    # Paramètres LLM
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # "mistral", "groq", "ollama"
    MISTRAL_MODEL = "mistral-small-latest"
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = "llama-3.3-70b-versatile"  # Modèle gratuit et rapide (nouveau)
    # Alternatives: "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"
    OLLAMA_MODEL = "llama3.2"  # Modèle local gratuit
    OLLAMA_BASE_URL = "http://localhost:11434"
    MAX_TOKENS = 8000
    TEMPERATURE = 0.7
    
    # Timeouts
    REQUEST_TIMEOUT = 30
    SCRAPING_TIMEOUT = 15 