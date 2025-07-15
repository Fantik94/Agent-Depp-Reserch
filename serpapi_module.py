import os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("SERPAPI_API_KEY")

def google_search(query):
    if not api_key:
        print("[ERREUR] Clé SERPAPI_API_KEY manquante dans le .env")
        return []
    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    print("[DEBUG] Résultat SerpAPI:", results)
    links = [r['link'] for r in results.get('organic_results', [])]
    return links 