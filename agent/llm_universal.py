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
    
    def generate_contextual_search_plan(self, context_prompt: str, context_result: Dict) -> Dict:
        """Génère un plan de recherche enrichi avec le contexte précédent"""
        
        # Extraire des informations du contexte
        original_query = context_result.get('query', '')
        original_plan = context_result.get('plan', {})
        
        prompt = f"""Génère un plan de recherche contextuel intelligent basé sur ce contexte :

{context_prompt}

La nouvelle recherche doit être COMPLÉMENTAIRE et ENRICHIR les résultats précédents, pas les répéter.

Retourne le résultat au format JSON strict avec les champs suivants :
- "analyse": analyse de la question de suivi dans son contexte
- "plan": liste de 3 étapes logiques pour cette recherche contextuelle
- "requetes_recherche": liste de 4-5 requêtes Google SPÉCIFIQUES à la question de suivi (éviter de répéter les requêtes déjà faites)
- "questions_secondaires": 2 questions secondaires pour approfondir
- "strategie": description de l'approche contextuelle utilisée

Exemple de réponse pour une question de suivi "Quels sont les risques ?" après une recherche sur "intelligence artificielle avantages" :
{{"analyse": "L'utilisateur veut maintenant connaître les risques de l'IA après avoir vu les avantages", "plan": ["Identifier les risques principaux de l'IA", "Rechercher des cas concrets de problèmes", "Analyser les mesures de prévention"], "requetes_recherche": ["intelligence artificielle risques dangers", "IA biais algorithmes problèmes", "intelligence artificielle éthique limites", "AI safety sécurité risques", "intelligence artificielle emploi menaces"], "questions_secondaires": ["Comment minimiser ces risques ?", "Quels secteurs sont le plus à risque ?"], "strategie": "Recherche contextuelle ciblée sur les aspects négatifs pour compléter la vision précédente"}}

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
                    plan_data["requetes_recherche"] = plan_data["requetes_recherche"][:5]
                    
                    # Affichage du plan contextuel dans la console
                    colored_log("info", "🔗 ========= PLAN DE RECHERCHE CONTEXTUEL =========", Fore.CYAN + Style.BRIGHT)
                    colored_log("info", f"🎯 CONTEXTE: Basé sur \"{original_query}\"", Fore.YELLOW + Style.BRIGHT)
                    colored_log("info", f"🧠 ANALYSE: {plan_data['analyse']}", Fore.YELLOW + Style.BRIGHT)
                    colored_log("info", "📊 ÉTAPES CONTEXTUELLES:", Fore.GREEN + Style.BRIGHT)
                    for i, etape in enumerate(plan_data['plan'], 1):
                        colored_log("info", f"   {i}. {etape}", Fore.GREEN)
                    colored_log("info", "🔍 NOUVELLES REQUÊTES:", Fore.BLUE + Style.BRIGHT)
                    for i, query in enumerate(plan_data['requetes_recherche'], 1):
                        colored_log("info", f"   {i}. '{query}'", Fore.BLUE)
                    colored_log("info", f"🎲 STRATÉGIE CONTEXTUELLE: {plan_data['strategie']}", Fore.WHITE + Style.BRIGHT)
                    colored_log("info", "=" * 55, Fore.CYAN + Style.BRIGHT)
                    
                    return {
                        "requetes_recherche": plan_data["requetes_recherche"],
                        "types_sources": ["sources complémentaires", "nouveaux points de vue", "analyses spécialisées"],
                        "questions_secondaires": plan_data["questions_secondaires"],
                        "strategie": f"Plan contextuel: {plan_data['strategie']}",
                        "analyse": plan_data["analyse"],
                        "plan_etapes": plan_data["plan"],
                        "is_contextual": True
                    }
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"⚠️ Erreur parsing JSON plan contextuel: {e}")
        
        # Fallback contextuel intelligent
        logger.info("📋 Plan contextuel de fallback")
        return self._generate_contextual_fallback_plan(context_prompt, context_result)

    def _generate_contextual_fallback_plan(self, context_prompt: str, context_result: Dict) -> Dict:
        """Génère un plan de fallback contextuel basé sur l'analyse de la question de suivi"""
        
        # Extraire la question de suivi du prompt
        followup_query = ""
        lines = context_prompt.split('\n')
        for line in lines:
            if line.startswith('Question de suivi:'):
                followup_query = line.replace('Question de suivi:', '').strip().strip('"')
                break
        
        query_lower = followup_query.lower()
        original_query = context_result.get('query', '')
        
        # Prendre seulement les 2-3 premiers mots de la requête originale pour éviter les requêtes trop longues
        base_terms = original_query.split()[:3]  
        base_query = " ".join(base_terms)
        
        # Extraire les mots-clés principaux de la question de suivi
        followup_keywords = []
        words = followup_query.split()[:3]  # Limiter à 3 mots
        for word in words:
            if len(word) > 2 and word.lower() not in ['les', 'des', 'une', 'est', 'sont', 'avec', 'dans', 'pour']:
                followup_keywords.append(word)
        
        # Générer des requêtes simples et efficaces
        if any(word in query_lower for word in ["risque", "danger", "problème", "inconvénient"]):
            # Question sur les risques - requêtes courtes et ciblées
            return {
                "requetes_recherche": [
                    f"{base_query} risques",
                    f"{base_query} dangers",
                    f"{base_query} problèmes",
                    f"{base_query} précautions"
                ],
                "types_sources": ["études sur les risques", "rapports de sécurité"],
                "questions_secondaires": ["Comment minimiser les risques ?", "Dans quels cas éviter ?"],
                "strategie": "Fallback contextuel: focus sur les aspects négatifs",
                "analyse": f"Recherche des risques liés à {base_query}",
                "plan_etapes": ["Identifier les risques", "Analyser les causes", "Trouver des solutions"],
                "is_contextual": True
            }
        
        elif any(word in query_lower for word in ["exemple", "cas", "concret", "pratique"]):
            # Question sur des exemples pratiques
            return {
                "requetes_recherche": [
                    f"{base_query} exemples",
                    f"{base_query} cas pratiques",
                    f"{base_query} témoignages",
                    f"{base_query} expériences"
                ],
                "types_sources": ["témoignages", "études de cas"],
                "questions_secondaires": ["Quels sont les résultats ?", "Combien de temps ?"],
                "strategie": "Fallback contextuel: recherche d'exemples concrets",
                "analyse": f"Recherche d'exemples pratiques pour {base_query}",
                "plan_etapes": ["Trouver des cas concrets", "Analyser les résultats", "Identifier les facteurs"],
                "is_contextual": True
            }
        
        elif any(word in query_lower for word in ["alternative", "autre", "différent", "comparaison"]):
            # Question sur les alternatives
            return {
                "requetes_recherche": [
                    f"{base_query} alternatives",
                    f"{base_query} options",
                    f"{base_query} comparaison",
                    f"alternative {base_query}"
                ],
                "types_sources": ["guides comparatifs", "analyses d'alternatives"],
                "questions_secondaires": ["Quels critères choisir ?", "Quelle est la meilleure option ?"],
                "strategie": "Fallback contextuel: recherche d'alternatives",
                "analyse": f"Recherche d'alternatives à {base_query}",
                "plan_etapes": ["Identifier alternatives", "Comparer options", "Évaluer critères"],
                "is_contextual": True
            }
        
        # Fallback général contextuel - requêtes très simples
        main_keyword = followup_keywords[0] if followup_keywords else "informations"
        
        return {
            "requetes_recherche": [
                f"{base_query} {main_keyword}",
                f"{main_keyword} {base_query}",
                f"{base_query} guide",
                f"{base_query} conseils"
            ],
            "types_sources": ["informations complémentaires", "guides pratiques"],
            "questions_secondaires": ["Quels autres aspects ?", "Nuances importantes ?"],
            "strategie": "Fallback contextuel général",
            "analyse": f"Approfondissement de {base_query} avec focus sur {main_keyword}",
            "plan_etapes": ["Recherche complémentaire", "Analyse", "Synthèse"],
            "is_contextual": True
        }

    def synthesize_contextual_results(self, followup_query: str, search_results: List[Dict], scraped_articles: List[Dict], context_result: Dict) -> str:
        """Synthétise les résultats d'une recherche contextuelle en intégrant le contexte précédent"""
        
        original_query = context_result.get('query', '')
        original_synthesis = context_result.get('synthesis', '')
        
        # Préparer le contexte pour le prompt
        context_summary = original_synthesis[:500] + "..." if len(original_synthesis) > 500 else original_synthesis
        
        # Préparer les résultats de recherche
        search_summary = self._prepare_search_summary(search_results)
        articles_content = self._prepare_articles_content(scraped_articles)
        
        prompt = f"""Tu es un expert en recherche et synthèse d'informations. 

CONTEXTE DE LA RECHERCHE PRÉCÉDENTE:
Question originale: "{original_query}"
Synthèse précédente: {context_summary}

NOUVELLE QUESTION DE SUIVI: "{followup_query}"

NOUVEAUX RÉSULTATS DE RECHERCHE:
{search_summary}

NOUVEAUX ARTICLES ANALYSÉS:
{articles_content}

INSTRUCTIONS:
1. Réponds SPÉCIFIQUEMENT à la question de suivi "{followup_query}"
2. INTÈGRE intelligemment les informations de la recherche précédente quand c'est pertinent
3. METS EN ÉVIDENCE les connexions entre les résultats précédents et les nouveaux
4. Structure ta réponse de manière claire et complète
5. Indique quand tu enrichis ou nuances les informations précédentes

Format de réponse souhaité:
- Introduction rappelant le lien avec la recherche précédente
- Réponse détaillée à la question de suivi
- Connexions et nuances par rapport aux résultats précédents
- Conclusion synthétique

Écris en français et sois précis et informatif."""

        try:
            synthesis = self.generate_completion(prompt, max_tokens=1000)
            
            if synthesis:
                # Ajouter un header contextuel
                contextual_header = f"**🔗 Recherche contextuelle basée sur:** \"{original_query}\"\n\n"
                return contextual_header + synthesis
            else:
                return self._generate_fallback_contextual_synthesis(followup_query, original_query, search_results, scraped_articles)
                
        except Exception as e:
            logger.error(f"❌ Erreur synthèse contextuelle: {e}")
            return self._generate_fallback_contextual_synthesis(followup_query, original_query, search_results, scraped_articles)

    def _generate_fallback_contextual_synthesis(self, followup_query: str, original_query: str, search_results: List[Dict], scraped_articles: List[Dict]) -> str:
        """Génère une synthèse contextuelle de fallback"""
        
        synthesis = f"**🔗 Recherche contextuelle basée sur:** \"{original_query}\"\n\n"
        synthesis += f"**Réponse à votre question de suivi:** {followup_query}\n\n"
        
        if search_results:
            synthesis += f"**📊 Nouveaux résultats trouvés:** {len(search_results)} sources analysées\n\n"
            
            # Résumé des points clés des résultats
            synthesis += "**🔍 Points clés identifiés:**\n"
            for i, result in enumerate(search_results[:5], 1):
                snippet = result.get('snippet', '')[:150] + "..." if len(result.get('snippet', '')) > 150 else result.get('snippet', '')
                synthesis += f"{i}. {snippet}\n"
            synthesis += "\n"
        
        if scraped_articles:
            synthesis += f"**📰 Articles analysés en détail:** {len(scraped_articles)} articles\n\n"
            
            # Extraits des articles les plus pertinents
            synthesis += "**💡 Informations complémentaires:**\n"
            for i, article in enumerate(scraped_articles[:3], 1):
                content = article.get('content', '')[:200] + "..." if len(article.get('content', '')) > 200 else article.get('content', '')
                synthesis += f"• **{article.get('title', 'Article')}:** {content}\n"
            synthesis += "\n"
        
        synthesis += "**🎯 Cette recherche contextuelle vient enrichir vos connaissances précédentes "
        synthesis += f"sur \"{original_query}\" en apportant des éléments spécifiques à votre question de suivi.**"
        
        return synthesis

    def _prepare_search_summary(self, search_results: List[Dict]) -> str:
        """Prépare un résumé des résultats de recherche pour le prompt"""
        if not search_results:
            return "Aucun résultat de recherche trouvé."
        
        summary = f"Résultats trouvés ({len(search_results)} sources):\n"
        for i, result in enumerate(search_results[:10], 1):  # Limiter à 10 pour éviter un prompt trop long
            title = result.get('title', 'Titre non disponible')
            snippet = result.get('snippet', 'Extrait non disponible')[:200]
            summary += f"{i}. {title}\n   {snippet}...\n"
        
        return summary

    def _prepare_articles_content(self, scraped_articles: List[Dict]) -> str:
        """Prépare le contenu des articles scrapés pour le prompt"""
        if not scraped_articles:
            return "Aucun article analysé en détail."
        
        content = f"Articles analysés ({len(scraped_articles)} articles):\n"
        for i, article in enumerate(scraped_articles[:5], 1):  # Limiter à 5 articles
            title = article.get('title', 'Titre non disponible')
            article_content = article.get('content', 'Contenu non disponible')[:300]  # Limiter la taille
            content += f"{i}. {title}\n   {article_content}...\n"
        
        return content

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