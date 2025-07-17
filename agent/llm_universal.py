import requests
import json
import time
import logging
from typing import List, Dict, Optional
from config import Config

# Couleurs pour les logs
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    Fore = Back = Style = type('', (), {'__getattr__': lambda self, name: ''})()

logger = logging.getLogger(__name__)

def colored_log(level, message, color=None):
    """Log avec couleur si disponible"""
    if COLORS_AVAILABLE and color:
        print(f"{color}{message}{Style.RESET_ALL}")
    else:
        getattr(logger, level)(message)

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
                from mistralai import Mistral
                from mistralai.models import UserMessage
                self.client = Mistral(api_key=self.config.MISTRAL_API_KEY)
                self.UserMessage = UserMessage
                # Headers pour les requêtes directes
                self.mistral_headers = {
                    "Authorization": f"Bearer {self.config.MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                }
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
    
    def _init_groq(self):
        """Initialise Groq avec les headers nécessaires"""
        if not self.config.GROQ_API_KEY:
            logger.error("❌ Clé API Groq manquante")
            return
        
        self.groq_headers = {
            "Authorization": f"Bearer {self.config.GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        logger.info("🤖 Headers Groq initialisés")
    
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
            if not hasattr(self, 'client') or not hasattr(self, 'UserMessage'):
                logger.error("❌ Client Mistral non initialisé")
                return None
            
            # Délai plus long pour Mistral
            time.sleep(3)
            
            messages = [self.UserMessage(content=prompt)]
            
            logger.info("🤖 Requête Mistral")
            response = self.client.chat.complete(
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
    
    def generate_search_plan_legacy(self, user_query: str) -> Dict:
        """Génère un plan de recherche standard (OBSOLÈTE - utiliser generate_deep_search_plan)"""
        
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
    
    def generate_search_plan(self, user_query: str) -> Dict:
        """Méthode de compatibilité - redirige vers generate_deep_search_plan"""
        logger.info("🔄 Redirection vers plan intelligent")
        return self.generate_deep_search_plan(user_query)
    
    def generate_deep_search_plan(self, user_query: str) -> Dict:
        """Génère un plan de recherche intelligent avec analyse JSON"""
        
        prompt = f"""Génère un plan de recherche web intelligent pour la question suivante : "{user_query}"

Analyse d'abord la question pour comprendre ce que l'utilisateur demande vraiment, puis crée un plan structuré.

Retourne le résultat au format JSON strict avec les champs suivants :
- "analyse": une phrase décrivant ce que l'utilisateur cherche vraiment
- "plan": une liste de 3-4 étapes logiques de recherche  
- "requetes_recherche": une liste de 5-6 requêtes Google précises et pertinentes (en français)
- "questions_secondaires": une liste de 2-3 questions secondaires importantes
- "strategie": description de l'approche utilisée

Exemples de questions et leurs analyses :

Pour "qui est le plus riche entre elon musk et françois hollande" :
{{"analyse": "Comparaison de patrimoine entre un milliardaire américain et un ex-président français", "plan": ["Rechercher fortune actuelle Elon Musk", "Rechercher patrimoine François Hollande", "Comparer les montants", "Analyser les sources de richesse"], "requetes_recherche": ["Elon Musk fortune 2024 milliards", "François Hollande patrimoine net worth", "richest people 2024 Musk classement", "patrimoine président France Hollande", "Tesla SpaceX valeur Musk fortune", "salaire président France vs milliardaires"], "questions_secondaires": ["Quelles sont leurs sources de revenus principales ?", "Comment se situe Hollande par rapport aux autres politiques ?", "Évolution fortune Musk dernières années ?"], "strategie": "Recherche comparative de données financières publiques"}}

Pour "comment dresser un chien agressif" :
{{"analyse": "Techniques d'éducation canine pour corriger comportements agressifs", "plan": ["Identifier causes agressivité", "Techniques de dressage spécialisées", "Conseils vétérinaires/experts", "Témoignages propriétaires"], "requetes_recherche": ["chien agressif dressage techniques", "éducateur canin agression solutions", "vétérinaire comportementaliste chien", "socialisation chien adulte agressif", "méthodes éducation positive chien", "chien mord que faire conseils"], "questions_secondaires": ["Quand consulter un professionnel ?", "Quels sont les signes précurseurs ?", "Peut-on éviter l'agressivité ?"], "strategie": "Approche multi-expertise (vétérinaire, éducation, comportement)"}}

Réponds UNIQUEMENT avec le JSON valide, sans texte additionnel."""

        # Forcer le format JSON si le provider le supporte
        if self.provider == "mistral":
            content = self._make_request_mistral_json(prompt, max_tokens=800)
        else:
            content = self.generate_completion(prompt, max_tokens=800)
        
        if content:
            try:
                # Nettoyer le contenu pour extraire le JSON
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:-3]
                elif content.startswith('```'):
                    content = content[3:-3]
                
                import json
                plan_data = json.loads(content)
                
                # Validation des champs requis
                required_fields = ["analyse", "plan", "requetes_recherche", "questions_secondaires", "strategie"]
                if all(field in plan_data for field in required_fields):
                    # Limiter le nombre de requêtes
                    plan_data["requetes_recherche"] = plan_data["requetes_recherche"][:6]
                    
                    # Affichage détaillé du plan dans la console avec couleurs
                    colored_log("info", "📋 ========= PLAN DE RECHERCHE INTELLIGENT =========", Fore.CYAN + Style.BRIGHT)
                    colored_log("info", f"🎯 ANALYSE: {plan_data['analyse']}", Fore.YELLOW + Style.BRIGHT)
                    colored_log("info", "📊 ÉTAPES DU PLAN:", Fore.GREEN + Style.BRIGHT)
                    for i, etape in enumerate(plan_data['plan'], 1):
                        colored_log("info", f"   {i}. {etape}", Fore.GREEN)
                    colored_log("info", "🔍 REQUÊTES DE RECHERCHE:", Fore.BLUE + Style.BRIGHT)
                    for i, query in enumerate(plan_data['requetes_recherche'], 1):
                        colored_log("info", f"   {i}. '{query}'", Fore.BLUE)
                    colored_log("info", "❓ QUESTIONS SECONDAIRES:", Fore.MAGENTA + Style.BRIGHT)
                    for question in plan_data['questions_secondaires']:
                        colored_log("info", f"   • {question}", Fore.MAGENTA)
                    colored_log("info", f"🎲 STRATÉGIE: {plan_data['strategie']}", Fore.WHITE + Style.BRIGHT)
                    colored_log("info", "=" * 55, Fore.CYAN + Style.BRIGHT)
                    
                    return {
                        "requetes_recherche": plan_data["requetes_recherche"],
                        "types_sources": ["données officielles", "sites spécialisés", "études", "articles de référence"],
                        "questions_secondaires": plan_data["questions_secondaires"],
                        "strategie": f"Plan intelligent: {plan_data['strategie']}",
                        "analyse": plan_data["analyse"],
                        "plan_etapes": plan_data["plan"]
                    }
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Erreur parsing JSON plan: {e}")
        
        # Fallback intelligent basé sur l'analyse de la question
        logger.info("📋 Plan de fallback intelligent")
        return self._generate_smart_fallback_plan(user_query)
    
    def _make_request_mistral_json(self, prompt: str, max_tokens: int = 800) -> Optional[str]:
        """Requête Mistral avec format JSON forcé"""
        if not self.config.MISTRAL_API_KEY:
            return None
            
        try:
            self._wait_for_rate_limit()
            
            payload = {
                "model": self.config.MISTRAL_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": self.config.TEMPERATURE,
                "response_format": {"type": "json_object"}
            }
            
            logger.info("🤖 Requête Mistral JSON")
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers=self.mistral_headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                logger.info("✅ Requête Mistral JSON réussie")
                return content
            elif response.status_code == 429:
                logger.warning("⚠️ Rate limit Mistral, attente...")
                time.sleep(5)
                return None
            else:
                logger.warning(f"⚠️ Erreur Mistral JSON: {response.status_code}")
                return None
                
        except Exception as e:
            logger.warning(f"❌ Erreur requête Mistral JSON: {e}")
            return None
    
    def _generate_smart_fallback_plan(self, user_query: str) -> Dict:
        """Génère un plan de fallback intelligent basé sur l'analyse de mots-clés"""
        query_lower = user_query.lower()
        
        # Détection du type de question
        if any(word in query_lower for word in ["qui est", "plus riche", "fortune", "patrimoine", "richesse"]):
            # Question de comparaison financière
            base_terms = ["fortune", "patrimoine", "richesse", "net worth"]
            if "musk" in query_lower and "hollande" in query_lower:
                return {
                    "requetes_recherche": [
                        "Elon Musk fortune 2024 milliards",
                        "François Hollande patrimoine déclaration",
                        "richest people world 2024 Forbes",
                        "président France salaire patrimoine",
                        "Tesla SpaceX valeur Musk",
                        "comparaison fortune politiques milliardaires"
                    ],
                    "types_sources": ["Forbes", "sites financiers", "déclarations officielles"],
                    "questions_secondaires": ["Sources de revenus de chacun ?", "Évolution dans le temps ?"],
                    "strategie": "Fallback intelligent: comparaison financière",
                    "analyse": "Comparaison de patrimoine entre personnalités publiques",
                    "plan_etapes": ["Recherche fortune Musk", "Recherche patrimoine Hollande", "Comparaison", "Contexte"]
                }
        
        elif any(word in query_lower for word in ["comment", "dresser", "éduquer", "apprendre"]):
            # Question pratique/tutoriel
            return {
                "requetes_recherche": [
                    f"{user_query} guide",
                    f"{user_query} conseils experts",
                    f"{user_query} méthode étapes",
                    f"{user_query} erreurs éviter",
                    f"{user_query} témoignages",
                    f"{user_query} 2024 techniques"
                ],
                "types_sources": ["guides pratiques", "sites spécialisés", "forums"],
                "questions_secondaires": ["Quelles erreurs éviter ?", "Combien de temps ça prend ?"],
                "strategie": "Fallback intelligent: guide pratique",
                "analyse": "Recherche de conseils et méthodes pratiques",
                "plan_etapes": ["Méthodes de base", "Conseils experts", "Témoignages", "Erreurs courantes"]
            }
        
        # Fallback général
        base_query = user_query.strip()
        return {
            "requetes_recherche": [
                base_query,
                f"{base_query} guide complet",
                f"{base_query} conseils experts",
                f"{base_query} 2024 actualités",
                f"{base_query} avantages inconvénients",
                f"{base_query} témoignages avis"
            ],
            "types_sources": ["articles de référence", "sites spécialisés"],
            "questions_secondaires": ["Quels sont les points clés ?", "Quelles sont les tendances ?"],
            "strategie": "Fallback général intelligent",
            "analyse": f"Recherche d'informations complètes sur: {base_query}",
            "plan_etapes": ["Informations générales", "Avis experts", "Actualités", "Retours utilisateurs"]
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