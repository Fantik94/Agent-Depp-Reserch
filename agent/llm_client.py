from mistralai import Mistral
from mistralai.models import UserMessage
from typing import List, Dict
import logging
from config import Config
import json
import re
import time
import random

logger = logging.getLogger(__name__)

class MistralLLMClient:
    """Client Mistral pour la planification et synthèse avec gestion du rate limiting"""
    
    def __init__(self):
        self.config = Config()
        self.client = Mistral(api_key=self.config.MISTRAL_API_KEY)
        self.last_request_time = 0
        self.min_delay = 5  # Délai minimum entre requêtes (secondes) - augmenté pour Mistral
    
    def _wait_for_rate_limit(self):
        """Attend avant la prochaine requête pour respecter le rate limit"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            wait_time = self.min_delay - time_since_last
            logger.info(f"⏳ Attente {wait_time:.1f}s pour respecter le rate limit")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request_with_retry(self, messages: List[UserMessage], max_tokens: int = 500, temperature: float = 0.3, max_retries: int = 3):
        """Effectue une requête avec retry automatique en cas d'erreur 429"""
        
        for attempt in range(max_retries):
            try:
                self._wait_for_rate_limit()
                
                logger.info(f"🤖 Requête Mistral (tentative {attempt + 1}/{max_retries})")
                
                response = self.client.chat.complete(
                    model=self.config.MISTRAL_MODEL,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                logger.info("✅ Requête Mistral réussie")
                return response.choices[0].message.content
                
            except Exception as e:
                error_str = str(e)
                
                if "429" in error_str or "Too Many Requests" in error_str:
                    wait_time = (2 ** attempt) * 10  # Backoff exponentiel: 10s, 20s, 40s
                    logger.warning(f"⚠️ Rate limit atteint, attente {wait_time}s...")
                    time.sleep(wait_time)
                    
                    if attempt == max_retries - 1:
                        logger.error("❌ Échec après tous les retries, utilisation du fallback")
                        return None
                else:
                    logger.error(f"❌ Erreur Mistral: {e}")
                    return None
        
        return None
    
    def generate_deep_search_plan(self, user_query: str) -> Dict:
        """Génère un plan de recherche approfondi avec plus de requêtes"""
        
        prompt = f"""Crée un plan de recherche approfondi pour: "{user_query}"

Génère 5-7 requêtes de recherche variées pour explorer tous les aspects:
- Requêtes générales
- Requêtes spécialisées 
- Requêtes sur les avantages/inconvénients
- Requêtes sur les tendances récentes
- Requêtes d'experts/études

Réponds UNIQUEMENT avec les requêtes séparées par des virgules:
requête1, requête2, requête3, requête4, requête5, requête6, requête7

Exemple pour "intelligence artificielle":
intelligence artificielle définition, IA avantages inconvénients, intelligence artificielle applications 2024, IA éthique risques, intelligence artificielle emploi impact, IA experts opinions, intelligence artificielle futur tendances"""

        content = self._make_request_with_retry(
            [UserMessage(content=prompt)],
            max_tokens=200,
            temperature=0.5
        )
        
        if content:
            # Extraire les requêtes
            queries = [q.strip() for q in content.split(',') if q.strip()]
            
            # Validation et nettoyage
            if len(queries) >= 3:
                logger.info(f"📋 Plan approfondi généré avec {len(queries)} requêtes")
                return {
                    "requetes_recherche": queries[:7],  # Max 7 requêtes
                    "types_sources": ["articles spécialisés", "études académiques", "sites d'actualité", "blogs d'experts"],
                    "questions_secondaires": ["Quels sont les enjeux actuels ?", "Quelles sont les perspectives d'avenir ?"],
                    "strategie": "Plan approfondi généré par LLM"
                }
        
        # Fallback: plan approfondi manuel
        logger.info("📋 Génération de plan approfondi automatique")
        base_query = user_query.strip()
        return {
            "requetes_recherche": [
                base_query,
                f"{base_query} avantages",
                f"{base_query} inconvénients",
                f"{base_query} 2024",
                f"{base_query} tendances",
                f"{base_query} experts avis",
                f"{base_query} futur"
            ],
            "types_sources": ["articles spécialisés", "études", "sites d'information", "blogs experts"],
            "questions_secondaires": ["Quels sont les aspects importants ?", "Quelles sont les tendances ?"],
            "strategie": "Plan approfondi automatique"
        }
    
    def generate_search_plan(self, user_query: str) -> Dict:
        """Génère un plan de recherche basé sur la requête utilisateur"""
        
        # Plan simple sans LLM si la requête est courte
        if len(user_query.split()) <= 3:
            logger.info("📋 Génération de plan simple (sans LLM)")
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

        content = self._make_request_with_retry(
            [UserMessage(content=prompt)],
            max_tokens=150,
            temperature=0.3
        )
        
        if content:
            # Parser les requêtes
            queries = [q.strip() for q in content.split(',') if q.strip()]
            
            if queries and len(queries) >= 2:
                plan = {
                    "requetes_recherche": queries[:4],  # Max 4 requêtes
                    "types_sources": ["articles spécialisés", "études", "sites d'information"],
                    "questions_secondaires": ["Quels sont les aspects importants ?"],
                    "strategie": f"Plan LLM avec {len(queries)} requêtes"
                }
                
                logger.info(f"📋 Plan LLM généré avec {len(queries)} requêtes")
                return plan
        
        # Fallback si LLM échoue
        logger.warning("⚠️ Fallback: génération de plan simple")
        base_terms = user_query.split()[-3:]  # 3 derniers mots
        base_query = " ".join(base_terms)
        
        return {
            "requetes_recherche": [
                base_query,
                f"{base_query} définition",
                f"{base_query} avantages"
            ],
            "types_sources": ["tous types"],
            "questions_secondaires": [],
            "strategie": "Plan de fallback (LLM indisponible)"
        }
    
    def synthesize_results(self, user_query: str, search_results: List[Dict], scraped_articles: List[Dict]) -> str:
        """Synthétise les résultats de recherche et articles scrapés"""
        
        # Si pas de données, retourner directement
        if not search_results and not scraped_articles:
            return f"""**Aucune information trouvée pour : "{user_query}"**

Cela peut être dû à :
- Des termes de recherche trop spécifiques
- Des restrictions d'accès aux sites web
- Des problèmes de connectivité

💡 **Suggestion :** Essayez avec des termes plus généraux ou reformulez votre question."""

        # Préparer un contexte très concis pour éviter les tokens excessifs
        context_parts = []
        
        if search_results:
            context_parts.append("**Sources trouvées :**")
            for i, result in enumerate(search_results[:3], 1):
                context_parts.append(f"{i}. {result['title']}: {result['snippet'][:100]}...")
        
        if scraped_articles:
            context_parts.append("\n**Articles analysés :**")
            for i, article in enumerate(scraped_articles[:2], 1):
                context_parts.append(f"{i}. {article['title']}: {article['content'][:200]}...")
        
        context = "\n".join(context_parts)
        
        # Requête très simple pour économiser les tokens
        prompt = f"""Question: {user_query}

{context}

Fais une synthèse en français, courte et claire."""

        content = self._make_request_with_retry(
            [UserMessage(content=prompt)],
            max_tokens=800,
            temperature=0.5
        )
        
        if content:
            # Ajouter les sources
            synthesis = content
            
            if search_results:
                synthesis += f"\n\n**📚 Sources consultées :**"
                for i, result in enumerate(search_results[:3], 1):
                    synthesis += f"\n{i}. {result['title']} - {result['url']}"
            
            return synthesis
        
        # Fallback manuel si LLM échoue
        logger.warning("⚠️ Synthèse manuelle (LLM indisponible)")
        
        fallback = f"**Résultats de recherche pour : {user_query}**\n\n"
        
        if search_results:
            fallback += "**🔍 Sources trouvées :**\n"
            for i, result in enumerate(search_results[:5], 1):
                fallback += f"{i}. **{result['title']}**\n"
                fallback += f"   {result['snippet'][:200]}...\n"
                fallback += f"   🔗 {result['url']}\n\n"
        
        if scraped_articles:
            fallback += "**📰 Articles analysés :**\n"
            for i, article in enumerate(scraped_articles[:3], 1):
                fallback += f"{i}. **{article['title']}**\n"
                fallback += f"   {article['content'][:300]}...\n"
                fallback += f"   🔗 {article['url']}\n\n"
        
        fallback += "*Note : Synthèse automatique temporairement indisponible (rate limit API)*"
        
        return fallback 