import requests
import json
import time
import logging
from typing import List, Dict, Optional
from config import Config

logger = logging.getLogger(__name__)

class UniversalLLMClient:
    """Client LLM universel supportant Mistral, Groq et Ollama"""
    
    def __init__(self, provider: str = None):
        self.config = Config()
        self.provider = provider or self.config.LLM_PROVIDER
        self.last_request_time = 0
        self.min_delay = 1  # Délai réduit
        
        # Initialiser le client selon le provider
        if self.provider == "mistral":
            try:
                from mistralai.client import MistralClient
                from mistralai.models.chat_completion import ChatMessage
                self.client = MistralClient(api_key=self.config.MISTRAL_API_KEY)
                self.ChatMessage = ChatMessage
                logger.info(f"🤖 Client Mistral initialisé avec {self.config.MISTRAL_MODEL}")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation Mistral: {e}")
                logger.info("🔄 Basculement vers Groq")
                self.provider = "groq"  # Fallback vers Groq
                self._init_groq()
        elif self.provider == "groq":
            self._init_groq()
        elif self.provider == "ollama":
            # Ollama local
            pass
        else:
            logger.warning(f"⚠️ Provider inconnu: {self.provider}, utilisation de Groq")
            self.provider = "groq"
            self._init_groq()
            
        logger.info(f"🤖 Client LLM initialisé: {self.provider}")
    
    def _wait_for_rate_limit(self):
        """Attend avant la prochaine requête (délai réduit)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request_groq(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Requête vers Groq API (gratuit, rapide) avec fallback automatique"""
        
        # Liste des modèles Groq gratuits à tester
        groq_models = [
            "llama-3.3-70b-versatile",  # Plus récent
            "llama-3.1-8b-instant",     # Plus rapide
            "mixtral-8x7b-32768",       # Bon contexte
            "gemma2-9b-it",             # Alternative
            "llama3-groq-70b-8192-tool-use-preview"  # Spécialisé tools
        ]
        
        for model in groq_models:
            try:
                self._wait_for_rate_limit()
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": max_tokens,
                    "temperature": self.config.TEMPERATURE
                }
                
                logger.info(f"🚀 Requête Groq (gratuit) - {model}")
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers=self.groq_headers,
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    logger.info(f"✅ Requête Groq réussie avec {model}")
                    return content
                else:
                    logger.warning(f"⚠️ Groq {model} erreur {response.status_code}")
                    continue  # Essayer le modèle suivant
                    
            except Exception as e:
                logger.warning(f"❌ Erreur Groq {model}: {e}")
                continue  # Essayer le modèle suivant
        
        logger.error("❌ Tous les modèles Groq ont échoué")
        return None
    
    def _make_request_ollama(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Requête vers Ollama local (gratuit)"""
        try:
            self._wait_for_rate_limit()
            
            payload = {
                "model": self.config.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": self.config.TEMPERATURE
                }
            }
            
            logger.info("🏠 Requête Ollama (local)")
            response = requests.post(
                f"{self.config.OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("response", "")
                logger.info("✅ Requête Ollama réussie")
                return content
            else:
                logger.warning(f"⚠️ Ollama erreur {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur Ollama: {e}")
            return None
    
    def _make_request_mistral(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Requête vers Mistral (avec rate limiting amélioré)"""
        try:
            # Vérifier que Mistral est bien configuré
            if not hasattr(self, 'client') or not hasattr(self, 'ChatMessage'):
                logger.error("❌ Client Mistral non initialisé")
                return None
            
            # Délai plus long pour Mistral
            time.sleep(3)
            
            messages = [self.ChatMessage(role="user", content=prompt)]
            
            logger.info("🤖 Requête Mistral")
            response = self.client.chat(
                model=self.config.MISTRAL_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=self.config.TEMPERATURE
            )
            
            logger.info("✅ Requête Mistral réussie")
            return response.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                logger.warning("⚠️ Rate limit Mistral - basculement vers Groq")
                return self._make_request_groq(prompt, max_tokens)
            else:
                logger.error(f"❌ Erreur Mistral: {e}")
                return None
    
    def generate_completion(self, prompt: str, max_tokens: int = 500) -> Optional[str]:
        """Génère une completion avec le provider configuré"""
        
        if self.provider == "groq":
            return self._make_request_groq(prompt, max_tokens)
        elif self.provider == "ollama":
            return self._make_request_ollama(prompt, max_tokens)
        elif self.provider == "mistral":
            return self._make_request_mistral(prompt, max_tokens)
        else:
            logger.error(f"❌ Provider non supporté: {self.provider}")
            return None
    
    def generate_search_plan(self, user_query: str) -> Dict:
        """Génère un plan de recherche standard"""
        
        # Plan simple sans LLM si la requête est courte (gain de temps)
        if len(user_query.split()) <= 3:
            logger.info("📋 Plan simple généré (sans LLM)")
            base_query = user_query.strip()
            return {
                "requetes_recherche": [
                    base_query,
                    f"{base_query} avantages",
                    f"{base_query} inconvénients"
                ],
                "types_sources": ["articles spécialisés", "études", "sites d'information"],
                "questions_secondaires": ["Quels sont les aspects importants ?"],
                "strategie": "Plan simple généré automatiquement"
            }
        
        prompt = f"""Crée 3 requêtes de recherche courtes pour: "{user_query}"

Réponds UNIQUEMENT avec les requêtes séparées par des virgules:
requête1, requête2, requête3

Exemple pour "intelligence artificielle":
intelligence artificielle définition, IA avantages inconvénients, intelligence artificielle applications"""

        content = self.generate_completion(prompt, max_tokens=150)
        
        if content:
            # Extraire les requêtes
            queries = [q.strip() for q in content.split(',') if q.strip()]
            
            if len(queries) >= 2:
                logger.info(f"📋 Plan LLM généré avec {len(queries)} requêtes")
                return {
                    "requetes_recherche": queries[:4],  # Max 4 pour la vitesse
                    "types_sources": ["articles spécialisés", "études", "sites d'information"],
                    "questions_secondaires": ["Quels sont les aspects importants ?"],
                    "strategie": f"Plan généré par {self.provider.upper()}"
                }
        
        # Fallback simple
        logger.info("📋 Plan automatique généré")
        base_query = user_query.strip()
        return {
            "requetes_recherche": [
                base_query,
                f"{base_query} 2024",
                f"{base_query} avantages"
            ],
            "types_sources": ["articles", "sites web"],
            "questions_secondaires": [],
            "strategie": "Plan automatique"
        }
    
    def generate_deep_search_plan(self, user_query: str) -> Dict:
        """Génère un plan de recherche approfondi"""
        
        prompt = f"""Crée un plan de recherche approfondi pour: "{user_query}"

Génère 5-6 requêtes variées:
- Général
- Avantages/inconvénients  
- Tendances 2024
- Experts/études
- Applications pratiques

Réponds UNIQUEMENT avec les requêtes séparées par des virgules.

Exemple pour "intelligence artificielle":
intelligence artificielle définition, IA avantages inconvénients, intelligence artificielle 2024, IA experts avis, intelligence artificielle applications pratiques"""

        content = self.generate_completion(prompt, max_tokens=200)
        
        if content:
            queries = [q.strip() for q in content.split(',') if q.strip()]
            
            if len(queries) >= 3:
                logger.info(f"📋 Plan approfondi généré avec {len(queries)} requêtes")
                return {
                    "requetes_recherche": queries[:6],
                    "types_sources": ["articles spécialisés", "études", "sites d'actualité", "blogs experts"],
                    "questions_secondaires": ["Quels sont les enjeux ?", "Quelles perspectives ?"],
                    "strategie": f"Plan approfondi généré par {self.provider.upper()}"
                }
        
        # Fallback approfondi
        logger.info("📋 Plan approfondi automatique")
        base_query = user_query.strip()
        return {
            "requetes_recherche": [
                base_query,
                f"{base_query} avantages",
                f"{base_query} inconvénients", 
                f"{base_query} 2024",
                f"{base_query} tendances",
                f"{base_query} experts"
            ],
            "types_sources": ["articles", "études", "blogs"],
            "questions_secondaires": ["Quels sont les aspects ?"],
            "strategie": "Plan approfondi automatique"
        }
    
    def synthesize_results(self, query: str, search_results: List[Dict], scraped_articles: List[Dict]) -> str:
        """Synthétise les résultats de recherche"""
        
        # Préparer le contexte
        context = f"Question: {query}\n\n"
        context += "Sources trouvées:\n"
        
        for i, result in enumerate(search_results[:5], 1):
            context += f"{i}. {result.get('title', 'N/A')}\n"
            context += f"   {result.get('snippet', 'N/A')[:200]}...\n\n"
        
        if scraped_articles:
            context += "\nArticles analysés:\n"
            for i, article in enumerate(scraped_articles[:3], 1):
                context += f"{i}. {article.get('title', 'N/A')}\n"
                context += f"   {article.get('content', 'N/A')[:300]}...\n\n"
        
        prompt = f"""{context}

Basé sur ces informations, rédige une synthèse claire et structurée répondant à: "{query}"

Structure:
- Introduction courte
- Points clés (3-4 points)
- Conclusion

Reste factuel et cite les sources quand pertinent."""

        content = self.generate_completion(prompt, max_tokens=800)
        
        if content:
            return content
        else:
            # Fallback simple
            return f"""Synthèse pour: {query}

Basé sur {len(search_results)} sources trouvées et {len(scraped_articles)} articles analysés, voici les informations principales:

{search_results[0].get('snippet', 'Informations non disponibles') if search_results else 'Aucune source trouvée'}

Note: Cette synthèse a été générée automatiquement en raison d'un problème temporaire avec l'IA.""" 