import streamlit as st
import pandas as pd
import logging
import sys
import os
import time
from datetime import datetime
from typing import Dict, List
from research_agent import ResearchAgent
from link_ranker import *
from config import Config
from link_ranker import display_ranked_links
import json
import threading
import threading
from datetime import datetime
import pandas as pd
from typing import List

# Configuration du logging avec plus de détails
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration Streamlit
st.set_page_config(
    page_title="Agent de Recherche",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé amélioré
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    .search-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .result-box {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin: 1rem 0;
        border-left: 5px solid #28a745;
    }
    
    .step-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .step-box {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-left: 4px solid #6c757d;
        transition: all 0.3s ease;
        position: relative;
    }
    
    .step-waiting {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-left: 4px solid #6c757d;
        opacity: 0.6;
    }
    
    .step-active {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        border-left: 4px solid #2196f3;
        box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
        animation: pulse 2s ease-in-out infinite alternate;
    }
    
    .step-completed {
        background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
        border-left: 4px solid #4caf50;
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.2);
    }
    
    .step-error {
        background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
        border-left: 4px solid #f44336;
        box-shadow: 0 4px 15px rgba(244, 67, 54, 0.2);
    }
    
    .step-title {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .step-details {
        font-size: 0.9rem;
        color: #6c757d;
        margin-top: 0.5rem;
    }
    
    .step-time {
        position: absolute;
        top: 0.5rem;
        right: 1rem;
        font-size: 0.8rem;
        color: #6c757d;
    }
    
    .log-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        max-height: 300px;
        overflow-y: auto;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
    }
    
    .source-item {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        border-left: 4px solid #17a2b8;
        transition: transform 0.2s ease;
    }
    
    .source-item:hover {
        transform: translateX(5px);
    }
    
    @keyframes pulse {
        from { 
            box-shadow: 0 4px 15px rgba(33, 150, 243, 0.3);
        }
        to { 
            box-shadow: 0 4px 25px rgba(33, 150, 243, 0.6);
        }
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialise l'état de session"""
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'last_result' not in st.session_state:
        st.session_state.last_result = None
    if 'search_running' not in st.session_state:
        st.session_state.search_running = False
    if 'search_steps' not in st.session_state:
        st.session_state.search_steps = {}
    if 'search_logs' not in st.session_state:
        st.session_state.search_logs = []
    if 'search_start_time' not in st.session_state:
        st.session_state.search_start_time = None
    
    # Nouveaux états pour la prévisualisation du plan
    if 'preview_plan' not in st.session_state:
        st.session_state.preview_plan = None
    if 'plan_approved' not in st.session_state:
        st.session_state.plan_approved = False
    if 'regenerate_plan' not in st.session_state:
        st.session_state.regenerate_plan = False
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    if 'current_config' not in st.session_state:
        st.session_state.current_config = {}
    
    # Nouveaux états pour la recherche contextuelle
    if 'research_context' not in st.session_state:
        st.session_state.research_context = None
    if 'followup_query' not in st.session_state:
        st.session_state.followup_query = ""
    if 'research_chain' not in st.session_state:
        st.session_state.research_chain = []
    if 'contextual_search_active' not in st.session_state:
        st.session_state.contextual_search_active = False

def get_agent(llm_provider: str, search_engines: List[str], scraping_method: str):
    """Obtient un agent configuré selon les paramètres"""
    # Clé pour identifier la configuration
    config_key = f"{llm_provider}_{'-'.join(search_engines)}_{scraping_method}"
    
    # Vérifier si on a déjà un agent avec cette configuration
    if 'agent_config' not in st.session_state or st.session_state.agent_config != config_key:
        # Créer un nouvel agent avec les bons paramètres
        st.session_state.agent = ResearchAgent(
            llm_provider=llm_provider,
            search_engines=search_engines,
            scraping_method=scraping_method
        )
        st.session_state.agent_config = config_key
        logger.info(f"🔧 Agent reconfiguré: LLM={llm_provider}, Moteurs={search_engines}")
    
    return st.session_state.agent

def display_header():
    """Affiche l'en-tête de l'application"""
    st.markdown("""
    <div class="main-header">
        <h1>🔍 Agent de Recherche Intelligent</h1>
        <p>Recherche intelligente avec analyse multi-sources et synthèse IA</p>
    </div>
    """, unsafe_allow_html=True)

def display_search_interface():
    """Affiche l'interface de recherche"""
    st.markdown('<div class="search-box">', unsafe_allow_html=True)
    
    # Input principal avec gestion de l'historique
    default_query = ""
    if 'selected_query' in st.session_state:
        default_query = st.session_state.selected_query
        del st.session_state.selected_query  # Nettoyer après utilisation
    
    user_query = st.text_input(
        "🔍 Votre question de recherche :",
        value=default_query,
        placeholder="Ex: Intelligence artificielle avantages et inconvénients",
        help="Posez une question claire et précise pour obtenir les meilleurs résultats"
    )
    
    # Options avancées
    with st.expander("⚙️ Options avancées"):
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            deep_search = st.checkbox(
                "🔬 Recherche approfondie", 
                value=False,
                help="Génère plus de requêtes et analyse plus d'articles (plus lent mais plus complet)"
            )
        
        with col_opt2:
            max_articles = st.slider(
                "📰 Nombre max d'articles", 
                min_value=3, 
                max_value=15, 
                value=5,
                help="Nombre maximum d'articles à analyser en détail"
            )
        
        # Configuration moteurs de recherche et scraping
        col_llm, col_search = st.columns(2)
        
        with col_llm:
            # Sélecteur de modèle LLM
            llm_provider = st.selectbox(
                "🤖 Modèle LLM",
                ["groq", "mistral", "ollama"],
                index=0,  # Groq par défaut
                help="Groq: Gratuit et rapide | Mistral: Payant mais puissant | Ollama: Local et gratuit"
            )
            
            # Informations sur le modèle sélectionné
            if llm_provider == "groq":
                st.info("🚀 **Groq**: Modèle Llama gratuit et très rapide")
            elif llm_provider == "mistral":
                st.warning("💳 **Mistral**: Modèle puissant mais payant")
            elif llm_provider == "ollama":
                st.info("🏠 **Ollama**: Modèle local gratuit")
        
        with col_search:
            # Sélecteur de moteurs de recherche
            search_engines = st.multiselect(
                "🔍 Moteurs de recherche",
                ["SerpApi"],
                default=["SerpApi"],
                help="SerpApi = Google Search via API officielle (fiable et rapide)"
            )
            
            # Méthode de scraping
            scraping_method = st.selectbox(
                "📰 Méthode de scraping",
                ["newspaper", "beautifulsoup", "both"],
                index=2,  # Both par défaut
                help="Newspaper: Plus rapide | BeautifulSoup: Plus robuste | Both: Les deux"
            )
    
    # Configuration avancée avec presets intelligents
    st.markdown("### ⚙️ Configuration avancée")
    
    # Utiliser les presets de la sidebar si disponibles
    if 'preset_config' in st.session_state:
        preset = st.session_state.preset_config
        default_results = preset['max_results']
        default_articles = preset['max_articles']
        default_queries = preset['max_queries']
        st.info(f"🎯 Configuration optimisée activée: {default_results} résultats, {default_articles} articles, {default_queries} requêtes")
    else:
        default_results = 10
        default_articles = 5
        default_queries = 6
    
    col_results, col_queries, col_articles = st.columns(3)
    
    with col_results:
        max_results = st.slider(
            "🔢 Résultats par recherche",
            min_value=3,
            max_value=20,
            value=default_results,
            step=1,
            help="Nombre de résultats à récupérer pour chaque requête de recherche"
        )
    
    with col_queries:
        max_queries = st.slider(
            "📋 Requêtes dans le plan",
            min_value=2,
            max_value=10,
            value=default_queries,
            step=1,
            help="Nombre maximum de requêtes générées dans le plan de recherche"
        )
    
    with col_articles:
        max_articles = st.slider(
            "📰 Articles à analyser",
            min_value=2,
            max_value=15,
            value=default_articles,
            step=1,
            help="Nombre d'articles à scraper et analyser en détail"
        )
    
    # Boutons et options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        search_button = st.button("🚀 Lancer la recherche", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Effacer", use_container_width=True, help="Efface les résultats et arrête la recherche en cours"):
            # Arrêter la recherche en cours
            st.session_state.search_running = False
            
            # Nettoyer complètement l'interface
            st.session_state.last_result = None
            st.session_state.search_steps = {}
            st.session_state.search_logs = []
            
            # Nettoyer l'historique si souhaité
            # st.session_state.search_history = []
            
            # Afficher un message de confirmation
            st.success("🧹 Interface nettoyée ! Recherche arrêtée.")
            st.rerun()
    
    with col3:
        show_logs = st.checkbox("📋 Logs", value=False)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return user_query, search_button, show_logs, deep_search, max_articles, llm_provider, search_engines, scraping_method, max_results, max_queries

def add_search_log(message: str, level: str = "info"):
    """Ajoute un log à la liste des logs de recherche"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = {
        "time": timestamp,
        "message": message,
        "level": level
    }
    st.session_state.search_logs.append(log_entry)
    
    # Garder seulement les 50 derniers logs
    if len(st.session_state.search_logs) > 50:
        st.session_state.search_logs = st.session_state.search_logs[-50:]

def update_search_step(step_id: str, status: str, title: str, details: str = "", duration: str = ""):
    """Met à jour une étape de recherche"""
    st.session_state.search_steps[step_id] = {
        "status": status,
        "title": title,
        "details": details,
        "duration": duration,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }
    
    # Ajouter au log
    if status == "active":
        add_search_log(f"🔄 {title} - {details}", "info")
    elif status == "completed":
        add_search_log(f"✅ {title} terminé - {details}", "success")
    elif status == "error":
        add_search_log(f"❌ {title} échoué - {details}", "error")

def display_search_progress():
    """Affiche le progrès de la recherche en temps réel"""
    if not st.session_state.search_steps:
        return
    
    st.markdown("### 🚀 Progression de la recherche")
    
    steps_config = [
        {"id": "plan", "icon": "📋", "default_title": "Génération du plan"},
        {"id": "search", "icon": "🔍", "default_title": "Recherche web"},
        {"id": "scraping", "icon": "📰", "default_title": "Analyse des articles"},
        {"id": "synthesis", "icon": "✍️", "default_title": "Synthèse finale"}
    ]
    
    # Afficher les étapes en grille 2x2
    st.markdown('<div class="step-container">', unsafe_allow_html=True)
    
    for i, step_config in enumerate(steps_config):
        step_id = step_config["id"]
        step_data = st.session_state.search_steps.get(step_id, {})
        
        status = step_data.get("status", "waiting")
        title = step_data.get("title", step_config["default_title"])
        details = step_data.get("details", "")
        duration = step_data.get("duration", "")
        timestamp = step_data.get("timestamp", "")
        
        # Définir la classe CSS selon le statut
        if status == "active":
            step_class = "step-active"
            icon = "⏳"
        elif status == "completed":
            step_class = "step-completed"
            icon = "✅"
        elif status == "error":
            step_class = "step-error"
            icon = "❌"
        else:
            step_class = "step-waiting"
            icon = "⏸️"
        
        # Afficher l'étape
        st.markdown(f"""
        <div class="{step_class} step-box">
            <div class="step-time">{timestamp}</div>
            <div class="step-title">
                {icon} {step_config['icon']} {title}
            </div>
            <div class="step-details">
                {details}
                {f"<br><small>⏱️ {duration}</small>" if duration else ""}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_logs(show_logs: bool):
    """Affiche les logs de recherche"""
    if show_logs and st.session_state.search_logs:
        st.markdown("### 📋 Logs de recherche")
        
        # Conteneur de logs
        log_html = '<div class="log-container">'
        
        for log in st.session_state.search_logs[-20:]:  # 20 derniers logs
            color = {
                "info": "#17a2b8",
                "success": "#28a745", 
                "error": "#dc3545",
                "warning": "#ffc107"
            }.get(log["level"], "#6c757d")
            
            log_html += f"""
            <div style="margin: 0.2rem 0; color: {color};">
                <span style="color: #6c757d;">[{log['time']}]</span> {log['message']}
            </div>
            """
        
        log_html += '</div>'
        st.markdown(log_html, unsafe_allow_html=True)

class SearchProgressTracker:
    """Classe pour suivre le progrès de recherche"""
    
    def __init__(self):
        self.start_time = time.time()
        st.session_state.search_start_time = self.start_time
        st.session_state.search_logs = []
        st.session_state.search_steps = {}
        
    def get_duration(self, start_time):
        """Calcule la durée écoulée"""
        duration = time.time() - start_time
        return f"{duration:.1f}s"
    
    def start_step(self, step_id: str, title: str, details: str = ""):
        """Démarre une étape"""
        self.step_start_time = time.time()
        update_search_step(step_id, "active", title, details)
        
    def complete_step(self, step_id: str, title: str, details: str = ""):
        """Termine une étape"""
        duration = self.get_duration(self.step_start_time)
        update_search_step(step_id, "completed", title, details, duration)
    
    def error_step(self, step_id: str, title: str, details: str = ""):
        """Marque une étape comme échouée"""
        duration = self.get_duration(self.step_start_time)
        update_search_step(step_id, "error", title, details, duration)
    
    def mark_error(self, step_id: str, title: str, details: str = ""):
        """Alias pour error_step pour compatibilité"""
        self.error_step(step_id, title, details)
    
    def get_total_duration(self):
        """Calcule la durée totale depuis le début"""
        total_duration = time.time() - self.start_time
        return f"{total_duration:.1f}s"

def research_with_progress_tracking(agent, query, deep_search=False, max_articles=5, search_engines=None, scraping_method="both", max_results=10, max_queries=6, predefined_plan=None):
    """Effectue la recherche avec suivi du progrès"""
    tracker = SearchProgressTracker()
    
    if search_engines is None:
        search_engines = ["SerpApi", "SearXNG"]
    
    try:
        # Vérifier si la recherche doit continuer
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue par l'utilisateur")
            return None
        
        # Étape 1: Utiliser le plan prédéfini ou en générer un nouveau
        if predefined_plan:
            # Utiliser le plan approuvé par l'utilisateur
            tracker.start_step("plan", "Utilisation du plan approuvé", "Plan de recherche validé par l'utilisateur")
            plan = predefined_plan
            tracker.complete_step("plan", "Plan utilisé", "Plan de recherche approuvé utilisé")
        else:
            # Génération du plan (mode legacy)
            tracker.start_step("plan", "Génération du plan", "Analyse de votre question avec Mistral AI")
            
            # Générer un plan intelligent (toujours approfondi maintenant)
            plan = agent.llm_client.generate_deep_search_plan(query)
            
            queries_count = len(plan.get("requetes_recherche", [query]))
            mode_text = "approfondie" if deep_search else "standard"
            tracker.complete_step("plan", "Plan généré", f"{queries_count} requêtes de recherche créées (mode {mode_text})")
        
        # Limiter le nombre de requêtes selon la configuration
        all_queries = plan.get("requetes_recherche", [query])
        limited_queries = all_queries[:max_queries]
        queries_count = len(limited_queries)
        
        # Étape 2: Recherche web
        tracker.start_step("search", "Recherche web", f"Exécution de {queries_count} requêtes de recherche")
        all_search_results = []
        
        for i, search_query in enumerate(limited_queries, 1):
            # Vérifier si la recherche doit continuer
            if not st.session_state.get('search_running', True):
                logger.info("🛑 Recherche interrompue pendant la recherche web")
                return None
                
            add_search_log(f"🔍 Requête {i}/{queries_count}: {search_query}")
            results = agent.search_api.search_web(search_query, max_results=max_results, enabled_engines=search_engines)
            all_search_results.extend(results)
            
            # Mise à jour du progrès
            progress_details = f"Requête {i}/{queries_count} - {len(results)} résultats trouvés"
            update_search_step("search", "active", "Recherche web", progress_details)
        
        # Supprimer les doublons
        unique_results = []
        seen_urls = set()
        for result in all_search_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        tracker.complete_step("search", "Recherche terminée", f"{len(unique_results)} résultats uniques trouvés")
        
        # Étape 3: Scraping
        # Vérifier si la recherche doit continuer
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue avant le scraping")
            return None
            
        tracker.start_step("scraping", "Analyse des articles", f"Extraction du contenu de {len(unique_results)} sources")
        urls_to_scrape = [result['url'] for result in unique_results[:max_articles * 2]]
        scraped_articles = agent.scraper.scrape_multiple_urls(urls_to_scrape, max_articles=max_articles, method=scraping_method)
        tracker.complete_step("scraping", "Articles analysés", f"{len(scraped_articles)} articles extraits avec succès")
        
        # Étape 4: Synthèse
        # Vérifier si la recherche doit continuer
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue avant la synthèse")
            return None
            
        tracker.start_step("synthesis", "Synthèse finale", "Génération de la réponse avec Mistral AI")
        synthesis = agent.llm_client.synthesize_results(query, unique_results, scraped_articles)
        
        total_duration = tracker.get_duration(tracker.start_time)
        tracker.complete_step("synthesis", "Synthèse terminée", f"Recherche complète en {total_duration}")
        
        return {
            "user_query": query,  # Nom cohérent pour le classement
            "query": query,
            "plan": plan,
            "search_results": unique_results,
            "scraped_articles": scraped_articles,
            "synthesis": synthesis,
            "stats": {
                "search_results_count": len(unique_results),
                "scraped_articles_count": len(scraped_articles),
                "search_queries_used": queries_count,
                "total_duration": total_duration
            }
        }
        
    except Exception as e:
        tracker.error_step("synthesis", "Erreur", str(e))
        raise e

def display_results(result):
    """Affiche les résultats de recherche"""
    if not result:
        return
    
    # Synthèse principale
    st.markdown('<div class="result-box">', unsafe_allow_html=True)
    st.markdown("## 📝 Synthèse des résultats")
    st.markdown(result['synthesis'])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Statistiques en cartes
    st.markdown("### 📊 Statistiques de la recherche")
    stats = result['stats']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #2196f3; margin: 0;">🔍</h3>
            <h2 style="margin: 0.5rem 0;">{stats['search_results_count']}</h2>
            <p style="margin: 0; color: #6c757d;">Sources trouvées</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #4caf50; margin: 0;">📰</h3>
            <h2 style="margin: 0.5rem 0;">{stats['scraped_articles_count']}</h2>
            <p style="margin: 0; color: #6c757d;">Articles analysés</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #ff9800; margin: 0;">🎯</h3>
            <h2 style="margin: 0.5rem 0;">{stats['search_queries_used']}</h2>
            <p style="margin: 0; color: #6c757d;">Requêtes utilisées</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #9c27b0; margin: 0;">⏱️</h3>
            <h2 style="margin: 0.5rem 0;">{stats.get('total_duration', 'N/A')}</h2>
            <p style="margin: 0; color: #6c757d;">Durée totale</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Plan de recherche
    with st.expander("🗂️ Plan de recherche utilisé"):
        plan = result['plan']
        st.write("**Stratégie :**", plan.get('strategie', 'Non disponible'))
        
        if 'requetes_recherche' in plan:
            st.write("**Requêtes exécutées :**")
            for i, query in enumerate(plan['requetes_recherche'], 1):
                st.write(f"{i}. `{query}`")
    
    # Sources consultées
    with st.expander(f"📚 Sources consultées ({len(result['search_results'])})"):
        for i, source in enumerate(result['search_results'][:15], 1):
            st.markdown(f"""
            <div class="source-item">
                <strong>{i}. {source['title']}</strong><br>
                <small style="color: #6c757d;">{source['url']}</small><br>
                <span style="background: #e3f2fd; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.8rem;">
                    {source['source']}
                </span><br>
                <div style="margin-top: 0.5rem;">
                    {source['snippet'][:250]}...
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Articles analysés
    if result['scraped_articles']:
        with st.expander(f"📰 Articles analysés en détail ({len(result['scraped_articles'])})"):
            for i, article in enumerate(result['scraped_articles'], 1):
                st.markdown(f"**{i}. {article['title']}**")
                st.write(f"🔗 Source: {article['url']}")
                if article.get('publish_date'):
                    st.write(f"📅 Date: {article['publish_date']}")
                st.write(f"📄 Extrait: {article['content'][:400]}...")
                st.markdown("---")
    
    # Nouveaux tableaux et analyses détaillées
    st.markdown("---")
    
    # Onglets pour organiser les analyses détaillées
    tab1, tab2, tab3, tab4 = st.tabs(["🔗 Liens classés", "📊 Tableau détaillé", "🔬 Analyse approfondie", "📈 Métriques avancées"])
    
    with tab1:
        display_ranked_links(result)
    
    with tab2:
        display_detailed_results_table(result)
    
    with tab3:
        display_research_insights(result)
    
    with tab4:
        display_advanced_metrics(result)
    
    # NOUVELLE SECTION : Interface de questions de suivi
    display_followup_interface(result)

def display_sidebar():
    """Affiche la sidebar simplifiée et efficace"""
    with st.sidebar:
        # 🚀 Header simple
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 1rem;">
            <h2 style="color: white; margin: 0;">⚙️ Contrôle</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 📊 STATUS DES APIS
        st.markdown("### 📊 Status")
        
        config = Config()
        col1, col2 = st.columns(2)
        
        with col1:
            if config.SERP_API_KEY:
                st.success("🟢 SerpApi")
            else:
                st.error("🔴 SerpApi")
        
        with col2:
            if config.MISTRAL_API_KEY:
                st.success("🤖 Mistral")
            else:
                st.warning("⚠️ Mistral")
        
        # 📈 STATISTIQUES SESSION
        if 'search_history' in st.session_state:
            searches_count = len(st.session_state.search_history)
        else:
            searches_count = 0
        
        # Status actuel
        if st.session_state.get('search_running', False):
            status_text = "🔄 Recherche en cours..."
            status_color = "#fff3cd"
        elif st.session_state.get('last_result'):
            status_text = "✅ Dernière recherche OK"
            status_color = "#d4edda"
        else:
            status_text = "💤 En attente"
            status_color = "#e2e3e5"
        
        st.markdown(f"""
        <div style="background: {status_color}; padding: 0.8rem; border-radius: 8px; margin: 1rem 0; text-align: center;">
            <div style="font-weight: bold;">{status_text}</div>
            <div style="font-size: 0.8rem; opacity: 0.8;">Session: {searches_count} recherches</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 🔧 PRESETS RAPIDES
        st.markdown("### 🔧 Configuration")
        
        col_preset1, col_preset2 = st.columns(2)
        
        with col_preset1:
            if st.button("🚀 Rapide", help="5 résultats, 3 articles", use_container_width=True):
                st.session_state.preset_config = {
                    'max_results': 5,
                    'max_articles': 3,
                    'max_queries': 3,
                    'deep_search': False
                }
                st.success("✅ Mode Rapide")
        
        with col_preset2:
            if st.button("🔬 Complet", help="15 résultats, 8 articles", use_container_width=True):
                st.session_state.preset_config = {
                    'max_results': 15,
                    'max_articles': 8,
                    'max_queries': 6,
                    'deep_search': True
                }
                st.success("✅ Mode Complet")
        
        # Affichage config active
        if 'preset_config' in st.session_state:
            config = st.session_state.preset_config
            st.info(f"📊 {config['max_results']} résultats | 📰 {config['max_articles']} articles")
        
        # 🗂️ HISTORIQUE
        st.markdown("### 🗂️ Historique")
        
        if st.session_state.get('search_history'):
            # Bouton nettoyer
            if st.button("🗑️ Nettoyer", help="Supprimer l'historique"):
                st.session_state.search_history = []
                st.success("🧹 Nettoyé")
                st.rerun()
            
            # Liste des recherches récentes
            history = st.session_state.search_history
            recent_searches = history[-8:] if len(history) > 8 else history
            
            for i, query in enumerate(reversed(recent_searches), 1):
                # Icône selon le type
                if any(word in query.lower() for word in ['prix', 'acheter', 'meilleur']):
                    icon = "🛒"
                elif any(word in query.lower() for word in ['actualité', 'news', '2024']):
                    icon = "📰"
                else:
                    icon = "🔍"
                
                # Bouton pour relancer
                query_short = query[:30] + "..." if len(query) > 30 else query
                
                if st.button(f"{icon} {query_short}", key=f"hist_{i}", help=f"Relancer: {query}"):
                    st.session_state.selected_query = query
                    st.rerun()
        else:
            st.markdown("""
            <div style="text-align: center; padding: 1rem; background: #f8f9fa; border-radius: 8px; color: #6c757d;">
                <div style="font-size: 1.5rem;">📭</div>
                <div style="font-size: 0.9rem;">Aucune recherche</div>
            </div>
            """, unsafe_allow_html=True)
        
        # 📈 DERNIÈRE RECHERCHE (si disponible)
        if st.session_state.get('last_result'):
            st.markdown("### 📈 Dernière Recherche")
            
            result = st.session_state.last_result
            stats = result.get('stats', {})
            
            # Métriques simples
            col_stat1, col_stat2 = st.columns(2)
            
            with col_stat1:
                st.metric("🔍 Sources", stats.get('search_results_count', 0))
                st.metric("⏱️ Durée", stats.get('total_duration', 'N/A'))
            
            with col_stat2:
                st.metric("📰 Articles", stats.get('scraped_articles_count', 0))
                st.metric("🎯 Requêtes", stats.get('search_queries_used', 0))
        
        # Footer simple
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; font-size: 0.7rem; color: #6c757d;">
            Agent v2.0 - SerpApi & Mistral AI
        </div>
        """, unsafe_allow_html=True)

def display_ranked_links(result):
    """Affiche les liens classés par pertinence avec détails"""
    st.markdown("### 🔗 Liens trouvés classés par pertinence")
    
    if not result.get('search_results'):
        st.warning("Aucun lien trouvé")
        return
    
    # Classifier les liens par pertinence
    ranked_links = rank_links_by_relevance(result['search_results'], result.get('user_query', ''))
    
    # Afficher les statistiques
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🔗 Total liens", len(ranked_links))
    with col2:
        e_commerce_count = sum(1 for link in ranked_links if is_ecommerce_link(link['url']))
        st.metric("🛒 Sites e-commerce", e_commerce_count)
    with col3:
        amazon_count = sum(1 for link in ranked_links if 'amazon' in link['url'].lower())
        st.metric("📦 Amazon", amazon_count)
    
    # Affichage des liens classés
    st.markdown("#### 🏆 Classement des résultats (du meilleur au moins bon)")
    
    for i, link in enumerate(ranked_links, 1):
        # Calculer le score de pertinence
        relevance_score = calculate_relevance_score(link, result.get('user_query', ''))
        
        # Déterminer les badges
        badges = get_link_badges(link['url'])
        if badges is None:
            badges = []
        
        # Créer une carte pour chaque lien
        with st.container():
            # En-tête avec rang et score
            col_rank, col_content = st.columns([1, 9])
            
            with col_rank:
                # Médaille pour les 3 premiers
                if i == 1:
                    st.markdown("# 🥇")
                elif i == 2:
                    st.markdown("# 🥈")
                elif i == 3:
                    st.markdown("# 🥉")
                else:
                    st.markdown(f"## #{i}")
            
            with col_content:
                # Titre avec lien cliquable
                st.markdown(f"**[{link['title']}]({link['url']})**")
                
                # Badges
                if badges:  # Vérifier que badges n'est pas vide
                    badge_html = " ".join([f'<span style="background: {color}; color: white; padding: 2px 6px; border-radius: 10px; font-size: 10px; margin-right: 4px;">{text}</span>' 
                                         for text, color in badges])
                    if badge_html:
                        st.markdown(badge_html, unsafe_allow_html=True)
                
                # Description/snippet
                if link.get('snippet'):
                    st.write(f"📝 {link['snippet'][:200]}{'...' if len(link['snippet']) > 200 else ''}")
                
                # Informations techniques
                col_tech1, col_tech2, col_tech3 = st.columns(3)
                with col_tech1:
                    st.caption(f"⭐ Score: {relevance_score:.1f}/10")
                with col_tech2:
                    domain = extract_domain(link['url'])
                    st.caption(f"🌐 {domain}")
                with col_tech3:
                    st.caption(f"🔍 Via {link.get('source', 'N/A')}")
        
                    st.markdown("---")
     
    # Actions sur les liens
    st.markdown("#### 💾 Actions")
    col_action1, col_action2, col_action3 = st.columns(3)
     
    with col_action1:
        if st.button("📋 Copier le top 5", help="Copier les 5 meilleurs liens"):
            top_5_text = create_top_links_text(ranked_links[:5])
            st.code(top_5_text)
     
    with col_action2:
        if st.button("📄 Exporter CSV", help="Télécharger au format CSV"):
            csv_data = create_csv_export(ranked_links)
            st.download_button(
                label="💾 Télécharger",
                data=csv_data,
                file_name="liens_classes.csv",
                mime="text/csv"
            )
     
    with col_action3:
        if st.button("🔗 URLs uniquement", help="Liste simple des URLs"):
            urls_text = "\n".join([link['url'] for link in ranked_links[:10]])
            st.code(urls_text)
     
    # Section filtres
    with st.expander("�� Filtrer les résultats"):
        col_filter1, col_filter2 = st.columns(2)
        
        with col_filter1:
            # Filtre par type de site
            site_types = st.multiselect(
                "Type de site",
                ["E-commerce", "Blog", "News", "Forum", "Officiel"],
                help="Filtrer par type de site"
            )
        
        with col_filter2:
            # Filtre par domaine
            domains = list(set([extract_domain(link['url']) for link in ranked_links]))
            selected_domains = st.multiselect(
                "Domaines",
                domains[:10],  # Top 10 domaines
                help="Filtrer par domaine spécifique"
            )

def rank_links_by_relevance(links, query):
    """Classe les liens par pertinence"""
    scored_links = []
    
    for link in links:
        score = calculate_relevance_score(link, query)
        scored_links.append({**link, 'relevance_score': score})
    
    # Trier par score décroissant
    return sorted(scored_links, key=lambda x: x['relevance_score'], reverse=True)

def calculate_relevance_score(link, query):
    """Calcule un score de pertinence pour un lien"""
    score = 0
    query_words = query.lower().split()
    
    title = link.get('title', '').lower()
    snippet = link.get('snippet', '').lower()
    url = link.get('url', '').lower()
    
    # Points pour les mots de la requête dans le titre (poids fort)
    for word in query_words:
        if word in title:
            score += 3
        if word in snippet:
            score += 2
        if word in url:
            score += 1
    
    # Bonus pour sites e-commerce si c'est une recherche produit
    if is_product_query(query) and is_ecommerce_link(url):
        score += 2
    
    # Bonus spécial Amazon
    if 'amazon' in url:
        score += 1.5
    
    # Bonus pour les sites populaires
    popular_domains = ['amazon.fr', 'amazon.com', 'leboncoin.fr', 'fnac.com', 'darty.com', 'boulanger.com']
    domain = extract_domain(url)
    if domain in popular_domains:
        score += 1
    
    # Malus pour les liens trop courts (peu d'info)
    if len(snippet) < 50:
        score -= 0.5
    
    return max(0, score)  # Score minimum 0

def is_product_query(query):
    """Détecte si c'est une recherche de produit"""
    product_keywords = ['meilleur', 'acheter', 'prix', 'pas cher', 'promo', 'solde', 'euro', '€', 'test', 'avis', 'comparatif']
    return any(keyword in query.lower() for keyword in product_keywords)

def is_ecommerce_link(url):
    """Détecte si c'est un site e-commerce"""
    ecommerce_domains = ['amazon', 'fnac', 'darty', 'boulanger', 'cdiscount', 'leboncoin', 'rakuten', 'zalando', 'decathlon']
    return any(domain in url.lower() for domain in ecommerce_domains)

def extract_domain(url):
    """Extrait le domaine d'une URL"""
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('www.', '')
    except:
        return url.split('/')[2] if '/' in url else url

def get_link_badges(url):
    """Retourne les badges appropriés pour un lien"""
    badges = []
    url_lower = url.lower()
    
    if 'amazon' in url_lower:
        badges.append(("AMAZON", "#ff9900"))
    elif any(shop in url_lower for shop in ['fnac', 'darty', 'boulanger']):
        badges.append(("E-COMMERCE", "#007bff"))
    elif 'leboncoin' in url_lower:
        badges.append(("OCCASION", "#28a745"))
    
    if any(word in url_lower for word in ['test', 'review', 'avis']):
        badges.append(("AVIS", "#6f42c1"))
    
    if any(word in url_lower for word in ['promo', 'solde', 'reduction']):
        badges.append(("PROMO", "#dc3545"))
    
    return badges

def create_top_links_text(links):
    """Crée un texte formaté avec les meilleurs liens"""
    text = "🏆 TOP LIENS TROUVÉS\n" + "="*50 + "\n\n"
    
    for i, link in enumerate(links, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} {link['title']}\n"
        text += f"   🔗 {link['url']}\n"
        if link.get('snippet'):
            text += f"   📝 {link['snippet'][:100]}...\n"
        text += "\n"
    
    return text

def create_csv_export(links):
    """Crée un export CSV des liens"""
    import io
    import csv
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(['Rang', 'Titre', 'URL', 'Domaine', 'Score', 'Snippet', 'Source'])
    
    # Données
    for i, link in enumerate(links, 1):
        writer.writerow([
            i,
            link['title'],
            link['url'],
            extract_domain(link['url']),
            f"{link.get('relevance_score', 0):.1f}",
            link.get('snippet', '')[:200],
            link.get('source', 'N/A')
        ])
    
    return output.getvalue()

def display_detailed_results_table(result):
    """Affiche un tableau détaillé des résultats de recherche"""
    st.markdown("### 📊 Tableau détaillé des résultats")
    
    # Créer les données pour le tableau
    table_data = []
    
    # Ajouter les sources de recherche
    for i, source in enumerate(result.get('search_results', []), 1):
        table_data.append({
            'N°': i,
            'Type': '🔍 Source',
            'Titre': source.get('title', 'N/A')[:60] + '...' if len(source.get('title', '')) > 60 else source.get('title', 'N/A'),
            'URL': source.get('url', 'N/A'),
            'Moteur': source.get('source', 'N/A'),
            'Snippet': source.get('snippet', 'N/A')[:100] + '...' if len(source.get('snippet', '')) > 100 else source.get('snippet', 'N/A'),
            'Status': '✅ Trouvé'
        })
    
    # Ajouter les articles scrapés
    for i, article in enumerate(result.get('scraped_articles', []), 1):
        table_data.append({
            'N°': len(result.get('search_results', [])) + i,
            'Type': '📰 Article',
            'Titre': article.get('title', 'N/A')[:60] + '...' if len(article.get('title', '')) > 60 else article.get('title', 'N/A'),
            'URL': article.get('url', 'N/A'),
            'Moteur': 'Scraped',
            'Snippet': article.get('content', 'N/A')[:100] + '...' if len(article.get('content', '')) > 100 else article.get('content', 'N/A'),
            'Status': '✅ Analysé'
        })
    
    # Créer le DataFrame
    if table_data:
        df = pd.DataFrame(table_data)
        
        # Afficher le tableau avec style
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "N°": st.column_config.NumberColumn("N°", width="small"),
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Titre": st.column_config.TextColumn("Titre", width="medium"),
                "URL": st.column_config.LinkColumn("URL", width="medium"),
                "Moteur": st.column_config.TextColumn("Moteur", width="small"),
                "Snippet": st.column_config.TextColumn("Extrait", width="large"),
                "Status": st.column_config.TextColumn("Status", width="small")
            }
        )
        
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total résultats", len(table_data))
        with col2:
            sources_count = len(result.get('search_results', []))
            st.metric("🔍 Sources trouvées", sources_count)
        with col3:
            articles_count = len(result.get('scraped_articles', []))
            st.metric("📰 Articles analysés", articles_count)
        with col4:
            if result.get('plan'):
                queries_count = len(result['plan'].get('requetes_recherche', []))
                st.metric("🎯 Requêtes exécutées", queries_count)
    else:
        st.warning("Aucun résultat à afficher dans le tableau")

def display_research_insights(result):
    """Affiche des insights détaillés sur la recherche"""
    st.markdown("### 🔬 Analyse approfondie de la recherche")
    
    # Plan de recherche détaillé et intelligent
    if result.get('plan'):
        plan = result['plan']
        with st.expander("📋 Plan de recherche intelligent", expanded=True):
            # Analyse de la question
            if plan.get('analyse'):
                st.info(f"🧠 **Analyse de votre question :** {plan['analyse']}")
            
            # Plan d'action structuré
            if plan.get('plan_etapes'):
                st.markdown("**📊 Plan d'action en étapes :**")
                for i, etape in enumerate(plan['plan_etapes'], 1):
                    st.markdown(f"  {i}. {etape}")
                st.markdown("---")
            
            # Requêtes de recherche
            st.markdown("**🎯 Requêtes de recherche optimisées :**")
            for i, query in enumerate(plan.get('requetes_recherche', []), 1):
                st.markdown(f"  {i}. `{query}`")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if plan.get('types_sources'):
                    st.markdown("**📚 Types de sources ciblées :**")
                    for source_type in plan['types_sources']:
                        st.markdown(f"  • {source_type}")
            
            with col2:
                if plan.get('questions_secondaires'):
                    st.markdown("**❓ Questions secondaires à explorer :**")
                    for question in plan['questions_secondaires']:
                        st.markdown(f"  • {question}")
            
            if plan.get('strategie'):
                st.markdown(f"**🎲 Stratégie :** {plan['strategie']}")
    
    # Analyse des sources
    if result.get('search_results'):
        with st.expander("🔍 Analyse des sources", expanded=True):
            sources = result['search_results']
            
            # Répartition par moteur de recherche
            source_counts = {}
            for source in sources:
                engine = source.get('source', 'Inconnu')
                source_counts[engine] = source_counts.get(engine, 0) + 1
            
            st.markdown("**📊 Répartition par moteur de recherche :**")
            for engine, count in source_counts.items():
                percentage = (count / len(sources)) * 100
                st.markdown(f"  • {engine}: {count} résultats ({percentage:.1f}%)")
            
            # Analyse des domaines
            domains = {}
            for source in sources:
                url = source.get('url', '')
                if url:
                    try:
                        domain = url.split('/')[2]
                        domains[domain] = domains.get(domain, 0) + 1
                    except:
                        pass
            
            if domains:
                st.markdown("**🌐 Domaines les plus fréquents :**")
                sorted_domains = sorted(domains.items(), key=lambda x: x[1], reverse=True)
                for domain, count in sorted_domains[:10]:
                    st.markdown(f"  • {domain}: {count} résultat(s)")
    
    # Qualité du scraping
    if result.get('scraped_articles'):
        with st.expander("📰 Qualité du scraping", expanded=True):
            articles = result['scraped_articles']
            
            # Statistiques de longueur
            lengths = [len(article.get('content', '')) for article in articles]
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                st.markdown(f"**📏 Longueur moyenne des articles :** {avg_length:.0f} caractères")
                st.markdown(f"**📏 Article le plus long :** {max(lengths)} caractères")
                st.markdown(f"**📏 Article le plus court :** {min(lengths)} caractères")
            
            # Articles avec dates
            dated_articles = [a for a in articles if a.get('publish_date')]
            st.markdown(f"**📅 Articles avec date :** {len(dated_articles)}/{len(articles)}")
            
            # Articles avec auteurs
            authored_articles = [a for a in articles if a.get('authors')]
            st.markdown(f"**👤 Articles avec auteur :** {len(authored_articles)}/{len(articles)}")

def display_advanced_metrics(result):
    """Affiche des métriques avancées sur la recherche"""
    st.markdown("### 📈 Métriques avancées")
    
    # Métriques de performance
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### ⚡ Performance")
        
        # Calcul du taux de succès
        total_searches = len(result.get('search_results', []))
        successful_scrapes = len(result.get('scraped_articles', []))
        
        if total_searches > 0:
            success_rate = (successful_scrapes / total_searches) * 100
            st.metric("🎯 Taux de succès du scraping", f"{success_rate:.1f}%")
        
        # Vitesse de recherche
        if result.get('stats', {}).get('total_duration'):
            duration_str = result['stats']['total_duration']
            try:
                duration_seconds = float(duration_str.replace('s', ''))
                speed = total_searches / duration_seconds if duration_seconds > 0 else 0
                st.metric("🚀 Vitesse de recherche", f"{speed:.1f} résultats/s")
            except:
                st.metric("🚀 Vitesse de recherche", "N/A")
        
        # Efficacité du plan
        if result.get('plan'):
            queries_planned = len(result['plan'].get('requetes_recherche', []))
            queries_used = result.get('stats', {}).get('search_queries_used', 0)
            if queries_planned > 0:
                plan_efficiency = (queries_used / queries_planned) * 100
                st.metric("📋 Efficacité du plan", f"{plan_efficiency:.1f}%")
    
    with col2:
        st.markdown("#### 🔍 Qualité des données")
        
        # Richesse du contenu
        if result.get('scraped_articles'):
            articles = result['scraped_articles']
            
            # Longueur moyenne
            lengths = [len(article.get('content', '')) for article in articles]
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                st.metric("📏 Longueur moyenne", f"{avg_length:.0f} chars")
            
            # Diversité des sources
            unique_domains = set()
            for article in articles:
                url = article.get('url', '')
                if url:
                    try:
                        domain = url.split('/')[2]
                        unique_domains.add(domain)
                    except:
                        pass
            
            if unique_domains:
                diversity = len(unique_domains) / len(articles) * 100
                st.metric("🌐 Diversité des sources", f"{diversity:.1f}%")
            
            # Fraîcheur des données
            recent_articles = 0
            for article in articles:
                if article.get('publish_date'):
                    # Logique simple pour déterminer si c'est récent
                    recent_articles += 1
            
            if articles:
                freshness = (recent_articles / len(articles)) * 100
                st.metric("📅 Fraîcheur des données", f"{freshness:.1f}%")
    
    # Graphique de répartition des sources
    if result.get('search_results'):
        st.markdown("#### 📊 Répartition des sources par moteur")
        
        sources = result['search_results']
        source_counts = {}
        for source in sources:
            engine = source.get('source', 'Inconnu')
            source_counts[engine] = source_counts.get(engine, 0) + 1
        
        # Créer un DataFrame pour le graphique
        if source_counts:
            chart_data = pd.DataFrame(
                list(source_counts.items()),
                columns=['Moteur', 'Nombre']
            )
            
            # Graphique en barres
            st.bar_chart(chart_data.set_index('Moteur'))
            
            # Tableau de détail
            st.markdown("**Détail par moteur :**")
            for engine, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / len(sources)) * 100
                st.write(f"• **{engine}**: {count} résultats ({percentage:.1f}%)")
    
    # Recommandations d'amélioration
    st.markdown("#### 💡 Recommandations")
    
    recommendations = []
    
    # Analyse du taux de succès
    if total_searches > 0:
        success_rate = (successful_scrapes / total_searches) * 100
        if success_rate < 50:
            recommendations.append("🔧 Améliorer la sélection des sources pour augmenter le taux de scraping")
        elif success_rate > 80:
            recommendations.append("✅ Excellent taux de scraping ! Maintenir la qualité")
    
    # Analyse de la diversité
    if result.get('scraped_articles'):
        unique_domains = set()
        for article in result['scraped_articles']:
            url = article.get('url', '')
            if url:
                try:
                    domain = url.split('/')[2]
                    unique_domains.add(domain)
                except:
                    pass
        
        if len(unique_domains) < 3:
            recommendations.append("🌐 Diversifier les sources pour obtenir des perspectives variées")
    
    # Analyse de la longueur
    if result.get('scraped_articles'):
        lengths = [len(article.get('content', '')) for article in result['scraped_articles']]
        if lengths and sum(lengths) / len(lengths) < 500:
            recommendations.append("📏 Chercher des articles plus détaillés pour une meilleure analyse")
    
    if recommendations:
        for rec in recommendations:
            st.write(rec)
    else:
        st.write("✅ Excellente recherche ! Aucune amélioration majeure nécessaire.")

def display_plan_preview(plan, user_query):
    """Affiche la prévisualisation du plan de recherche avec options"""
    st.markdown("### 📋 Prévisualisation du plan de recherche")
    
    # Affichage du plan dans un style attractif
    with st.container():
        # En-tête avec la question
        st.info(f"🎯 **Question analysée :** {user_query}")
        
        # Analyse de la question (si disponible)
        if plan.get('analyse'):
            st.markdown(f"🧠 **Analyse :** {plan['analyse']}")
        
        # Plan d'action en étapes
        if plan.get('plan_etapes'):
            st.markdown("**📊 Plan d'action :**")
            for i, etape in enumerate(plan['plan_etapes'], 1):
                st.markdown(f"   {i}. {etape}")
        
        # Requêtes de recherche prévues
        st.markdown("**🔍 Requêtes de recherche qui seront exécutées :**")
        queries = plan.get('requetes_recherche', [])
        for i, query in enumerate(queries, 1):
            st.markdown(f"   {i}. `{query}`")
        
        # Informations complémentaires
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📚 Types de sources ciblées :**")
            for source_type in plan.get('types_sources', []):
                st.markdown(f"   • {source_type}")
        
        with col2:
            st.markdown("**❓ Questions secondaires :**")
            for question in plan.get('questions_secondaires', []):
                st.markdown(f"   • {question}")
        
        # Stratégie
        if plan.get('strategie'):
            st.markdown(f"**🎲 Stratégie :** {plan['strategie']}")
        
        st.markdown("---")
        
        # Boutons d'action
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            if st.button("✅ Accepter ce plan et lancer la recherche", type="primary", use_container_width=True):
                st.session_state.plan_approved = True
                # Ne pas effacer le plan ici - il sera effacé après la recherche
                st.rerun()
        
        with col2:
            if st.button("🔄 Générer un nouveau plan", type="secondary", use_container_width=True):
                st.session_state.regenerate_plan = True
                st.rerun()
        
        with col3:
            if st.button("❌ Annuler", use_container_width=True):
                st.session_state.preview_plan = None
                st.session_state.plan_approved = False
                st.rerun()
        
        # Message d'aide
        st.markdown("💡 **Conseil :** Vérifiez que les requêtes couvrent bien tous les aspects de votre question avant de lancer la recherche.")

def display_followup_interface(result):
    """Affiche l'interface pour poser des questions de suivi"""
    st.markdown("---")
    st.markdown("### 🔄 Questions de suivi")
    st.markdown("Posez une question complémentaire basée sur les résultats obtenus. L'IA utilisera le contexte de votre recherche précédente.")
    
    # Suggestions de questions basées sur les résultats
    with st.expander("💡 Suggestions de questions de suivi", expanded=False):
        suggestions = generate_followup_suggestions(result)
        st.markdown("**Voici quelques questions que vous pourriez poser :**")
        
        for i, suggestion in enumerate(suggestions, 1):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{i}. {suggestion}")
            with col2:
                if st.button(f"Utiliser", key=f"suggestion_{i}"):
                    st.session_state.followup_query = suggestion
                    st.rerun()
    
    # Champ de saisie pour la question de suivi
    followup_query = st.text_input(
        "🤔 Votre question de suivi :",
        value=st.session_state.get('followup_query', ''),
        placeholder="Ex: Quels sont les risques de cette approche ? / Peut-on avoir plus de détails sur... ?",
        help="Cette question sera enrichie avec le contexte de votre recherche précédente"
    )
    
    # Boutons d'action
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        if st.button("🔍 Recherche contextuelle", type="primary", use_container_width=True, disabled=not followup_query.strip()):
            # Lancer une recherche contextuelle
            st.session_state.followup_query = followup_query.strip()
            st.session_state.contextual_search_active = True
            st.session_state.research_context = result
            st.rerun()
    
    with col2:
        if st.button("🔄 Nouvelle recherche complète", type="secondary", use_container_width=True):
            # Effacer le contexte et commencer une nouvelle recherche
            st.session_state.research_context = None
            st.session_state.research_chain = []
            st.session_state.last_result = None
            st.session_state.followup_query = ""
            st.info("💫 Contexte effacé. Vous pouvez maintenant faire une nouvelle recherche complète.")
            st.rerun()
    
    with col3:
        if st.button("📋 Historique", use_container_width=True):
            show_research_chain()
    
    # Afficher la chaîne de recherches si elle existe
    if st.session_state.research_chain:
        with st.expander(f"🔗 Chaîne de recherches ({len(st.session_state.research_chain)} étapes)", expanded=False):
            for i, search_item in enumerate(st.session_state.research_chain, 1):
                st.markdown(f"**{i}. {search_item['type']}:** {search_item['query']}")
                if search_item.get('summary'):
                    st.caption(f"📝 {search_item['summary'][:100]}...")

def generate_followup_suggestions(result):
    """Génère des suggestions de questions de suivi basées sur les résultats"""
    original_query = result.get('query', '')
    plan = result.get('plan', {})
    
    suggestions = []
    
    # Suggestions basées sur les questions secondaires du plan
    if plan.get('questions_secondaires'):
        suggestions.extend(plan['questions_secondaires'][:2])
    
    # Suggestions génériques adaptatives
    if 'avantages' in original_query.lower() or 'inconvénients' in original_query.lower():
        suggestions.append("Quelles sont les alternatives à considérer ?")
        suggestions.append("Y a-t-il des études récentes sur ce sujet ?")
    elif 'comment' in original_query.lower():
        suggestions.append("Quels sont les risques ou précautions à prendre ?")
        suggestions.append("Combien de temps faut-il pour voir des résultats ?")
    elif 'comparaison' in original_query.lower() or 'vs' in original_query.lower():
        suggestions.append("Quels sont les critères de choix les plus importants ?")
        suggestions.append("Y a-t-il d'autres options à considérer ?")
    else:
        suggestions.extend([
            "Quels sont les aspects les plus importants à retenir ?",
            "Y a-t-il des développements récents sur ce sujet ?",
            "Quelles sont les meilleures pratiques recommandées ?",
            "Peut-on avoir des exemples concrets ?",
            "Quels sont les points de vigilance ?"
        ])
    
    return suggestions[:5]  # Limiter à 5 suggestions

def show_research_chain():
    """Affiche la chaîne complète des recherches dans une modal"""
    if st.session_state.research_chain:
        st.markdown("#### 🔗 Historique complet des recherches")
        for i, search_item in enumerate(st.session_state.research_chain, 1):
            with st.container():
                st.markdown(f"**Étape {i} - {search_item['type']}**")
                st.markdown(f"🎯 **Question :** {search_item['query']}")
                if search_item.get('summary'):
                    st.markdown(f"📝 **Résumé :** {search_item['summary']}")
                st.markdown("---")
    else:
        st.info("Aucun historique de recherche pour le moment.")

def contextual_research_with_progress(agent, followup_query, context_result, max_articles=5, search_engines=None, scraping_method="both", max_results=10, max_queries=6):
    """Effectue une recherche contextuelle enrichie avec les résultats précédents"""
    tracker = SearchProgressTracker()
    
    if search_engines is None:
        search_engines = ["SerpApi", "SearXNG"]
    
    try:
        # Vérifier si la recherche doit continuer
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche contextuelle interrompue par l'utilisateur")
            return None
        
        # Étape 1: Enrichissement contextuel de la question
        tracker.start_step("context", "Enrichissement contextuel", "Analyse de votre question avec le contexte précédent")
        
        # Créer un prompt enrichi qui inclut le contexte
        context_prompt = create_contextual_prompt(followup_query, context_result)
        
        # Générer un plan intelligent enrichi avec le contexte
        plan = agent.llm_client.generate_contextual_search_plan(context_prompt, context_result)
        
        # Limiter le nombre de requêtes
        all_queries = plan.get("requetes_recherche", [followup_query])
        limited_queries = all_queries[:max_queries]
        queries_count = len(limited_queries)
        
        tracker.complete_step("context", "Contexte intégré", f"{queries_count} requêtes contextuelles générées")
        
        # Étape 2: Recherche web contextuelle
        tracker.start_step("search", "Recherche contextuelle", f"Recherche enrichie avec {queries_count} requêtes")
        all_search_results = []
        
        for i, search_query in enumerate(limited_queries, 1):
            if not st.session_state.get('search_running', True):
                logger.info("🛑 Recherche interrompue pendant la recherche web contextuelle")
                return None
                
            add_search_log(f"🔍 Requête contextuelle {i}/{queries_count}: {search_query}")
            results = agent.search_api.search_web(search_query, max_results=max_results, enabled_engines=search_engines)
            all_search_results.extend(results)
            
            progress_details = f"Requête contextuelle {i}/{queries_count} - {len(results)} résultats"
            update_search_step("search", "active", "Recherche contextuelle", progress_details)
        
        # Supprimer les doublons
        unique_results = []
        seen_urls = set()
        for result in all_search_results:
            if result['url'] not in seen_urls:
                seen_urls.add(result['url'])
                unique_results.append(result)
        
        tracker.complete_step("search", "Recherche contextuelle terminée", f"{len(unique_results)} nouveaux résultats trouvés")
        
        # Étape 3: Scraping contextuel
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue avant le scraping contextuel")
            return None
            
        tracker.start_step("scraping", "Analyse contextuelle", f"Extraction de {min(len(unique_results), max_articles)} nouvelles sources")
        urls_to_scrape = [result['url'] for result in unique_results[:max_articles * 2]]
        scraped_articles = agent.scraper.scrape_multiple_urls(urls_to_scrape, max_articles=max_articles, method=scraping_method)
        
        tracker.complete_step("scraping", "Articles contextuels analysés", f"{len(scraped_articles)} nouveaux articles extraits")
        
        # Étape 4: Synthèse contextuelle enrichie
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue avant la synthèse contextuelle")
            return None
            
        tracker.start_step("synthesis", "Synthèse contextuelle", "Intégration avec les résultats précédents")
        
        # Synthèse qui intègre le contexte précédent
        synthesis = agent.llm_client.synthesize_contextual_results(
            followup_query, 
            unique_results, 
            scraped_articles, 
            context_result
        )
        
        tracker.complete_step("synthesis", "Synthèse contextuelle terminée", "Résultats intégrés avec le contexte")
        
        # Préparer le résultat final contextuel
        result = {
            "query": followup_query,
            "original_query": context_result.get('query', ''),
            "is_contextual": True,
            "context_summary": context_result.get('synthesis', '')[:300] + "...",
            "plan": plan,
            "search_results": unique_results,
            "scraped_articles": scraped_articles,
            "synthesis": synthesis,
            "stats": {
                "search_results_count": len(unique_results),
                "scraped_articles_count": len(scraped_articles),
                "search_queries_used": len(plan.get("requetes_recherche", [])),
                "total_duration": tracker.get_total_duration()
            }
        }
        
        # Ajouter à la chaîne de recherches
        add_to_research_chain("Recherche contextuelle", followup_query, synthesis[:200] + "...")
        
        logger.info("✅ Recherche contextuelle terminée avec succès")
        return result
        
    except Exception as e:
        logger.error(f"❌ Erreur recherche contextuelle: {e}")
        tracker.mark_error("synthesis", "Erreur synthèse", str(e))
        raise e

def create_contextual_prompt(followup_query, context_result):
    """Crée un prompt enrichi avec le contexte de la recherche précédente"""
    original_query = context_result.get('query', '')
    original_synthesis = context_result.get('synthesis', '')[:500]  # Limiter la taille
    
    context_prompt = f"""Question originale: "{original_query}"

Résumé des résultats précédents:
{original_synthesis}

Question de suivi: "{followup_query}"

Contexte: L'utilisateur pose cette question de suivi basée sur les résultats de sa recherche précédente. La nouvelle recherche doit être enrichie et complémentaire."""
    
    return context_prompt

def add_to_research_chain(search_type, query, summary):
    """Ajoute une recherche à la chaîne d'historique"""
    if 'research_chain' not in st.session_state:
        st.session_state.research_chain = []
    
    st.session_state.research_chain.append({
        'type': search_type,
        'query': query,
        'summary': summary,
        'timestamp': time.strftime("%H:%M:%S")
    })
    
    # Limiter à 10 éléments pour éviter une chaîne trop longue
    if len(st.session_state.research_chain) > 10:
        st.session_state.research_chain = st.session_state.research_chain[-10:]

def main():
    """Fonction principale"""
    init_session_state()
    display_header()
    display_sidebar()
    
    # Interface de recherche
    user_query, search_button, show_logs, deep_search, max_articles, llm_provider, search_engines, scraping_method, max_results, max_queries = display_search_interface()
    
    # Afficher le progrès s'il y en a un
    if st.session_state.search_steps:
        display_search_progress()
        
        # Bouton d'arrêt pendant la recherche
        if st.session_state.get('search_running', False):
            if st.button("🛑 ARRÊTER LA RECHERCHE", type="secondary", use_container_width=True):
                st.session_state.search_running = False
                add_search_log("🛑 Recherche arrêtée par l'utilisateur", "warning")
                st.warning("🛑 Arrêt de la recherche en cours...")
                st.rerun()
    
    # Afficher les logs en temps réel si recherche en cours
    if st.session_state.get('search_running', False) or show_logs:
        if st.session_state.search_logs:
            st.markdown("### 📋 Logs en temps réel")
            
            # Conteneur de logs avec scroll automatique
            log_container = st.container()
            with log_container:
                # Afficher les 15 derniers logs
                recent_logs = st.session_state.search_logs[-15:] if len(st.session_state.search_logs) > 15 else st.session_state.search_logs
                
                for log in recent_logs:
                    # Couleurs selon le niveau et contenu
                    if "✅" in log["message"] or "réussie" in log["message"]:
                        st.success(f"[{log['time']}] {log['message']}")
                    elif "🛑" in log["message"] or "interrompue" in log["message"]:
                        st.warning(f"[{log['time']}] {log['message']}")
                    elif "⚠️" in log["message"] or "erreur" in log["message"]:
                        st.warning(f"[{log['time']}] {log['message']}")
                    elif "❌" in log["message"]:
                        st.error(f"[{log['time']}] {log['message']}")
                    elif "🔍" in log["message"] or "🚀" in log["message"]:
                        st.info(f"[{log['time']}] {log['message']}")
                    else:
                        st.text(f"[{log['time']}] {log['message']}")
                
                # Auto-scroll vers le bas
                if st.session_state.get('search_running', False):
                    st.markdown('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)
    
    # ========== NOUVELLE LOGIQUE DE PRÉVISUALISATION DU PLAN ==========
    
    # 1. GÉNÉRATION DU PLAN (première étape)
    if search_button and user_query and not st.session_state.get('preview_plan'):
        # Nettoyer l'interface pour la nouvelle recherche
        st.session_state.last_result = None
        st.session_state.search_steps = {}
        st.session_state.search_logs = []
        st.session_state.plan_approved = False
        st.session_state.regenerate_plan = False
        
        # Configurer l'agent
        st.session_state.agent = get_agent(llm_provider, search_engines, scraping_method)
        st.session_state.current_query = user_query
        st.session_state.current_config = {
            'deep_search': deep_search,
            'max_articles': max_articles,
            'search_engines': search_engines,
            'scraping_method': scraping_method,
            'max_results': max_results,
            'max_queries': max_queries,
            'llm_provider': llm_provider
        }
        
        # Générer le plan de recherche
        with st.spinner("🧠 Génération du plan de recherche..."):
            try:
                plan = st.session_state.agent.llm_client.generate_deep_search_plan(user_query)
                st.session_state.preview_plan = plan
                st.success("✅ Plan de recherche généré ! Vérifiez-le ci-dessous.")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération du plan: {str(e)}")
    
    # 2. RÉGÉNÉRATION DU PLAN (si demandée)
    if st.session_state.get('regenerate_plan', False):
        st.session_state.regenerate_plan = False
        
        with st.spinner("🔄 Génération d'un nouveau plan..."):
            try:
                # Régénérer avec un prompt légèrement différent pour avoir de la variété
                plan = st.session_state.agent.llm_client.generate_deep_search_plan(st.session_state.current_query)
                st.session_state.preview_plan = plan
                st.success("✅ Nouveau plan généré !")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Erreur lors de la régénération: {str(e)}")
    
    # 3. AFFICHAGE DE LA PRÉVISUALISATION
    if st.session_state.get('preview_plan') and not st.session_state.get('plan_approved', False):
        display_plan_preview(st.session_state.preview_plan, st.session_state.current_query)
    
    # 4. LANCEMENT DE LA RECHERCHE (après approbation du plan)
    if st.session_state.get('plan_approved', False) and st.session_state.get('preview_plan'):
        # Ajouter à l'historique
        if st.session_state.current_query not in st.session_state.search_history:
            st.session_state.search_history.append(st.session_state.current_query)
        
        # Marquer le début de la recherche
        st.session_state.search_running = True
        
        # Messages de démarrage
        add_search_log("🧹 Interface nettoyée - Nouvelle recherche")
        config = st.session_state.current_config
        config_info = f"🤖 {config['llm_provider'].upper()} | 🔍 {', '.join(config['search_engines'])} | 📰 {config['scraping_method']}"
        add_search_log(f"⚙️ Configuration: {config_info}")
        add_search_log(f"🎯 Question: {st.session_state.current_query}")
        add_search_log("📋 Plan de recherche approuvé par l'utilisateur")
        
        # Ajouter à la chaîne de recherches (première recherche)
        add_to_research_chain("Recherche initiale", st.session_state.current_query, "Recherche lancée...")
        
        # Placeholder pour les mises à jour en temps réel
        progress_placeholder = st.empty()
        
        try:
            # Effectuer la recherche avec suivi (en utilisant le plan approuvé)
            with st.spinner("🔄 Recherche en cours..."):
                result = research_with_progress_tracking(
                    st.session_state.agent, 
                    st.session_state.current_query, 
                    deep_search=config['deep_search'], 
                    max_articles=config['max_articles'],
                    search_engines=config['search_engines'],
                    scraping_method=config['scraping_method'],
                    max_results=config['max_results'],
                    max_queries=config['max_queries'],
                    predefined_plan=st.session_state.preview_plan  # Passer le plan approuvé
                )
                
                # Vérifier si la recherche a été interrompue
                if result is None:
                    st.warning("🛑 Recherche interrompue par l'utilisateur")
                    st.session_state.search_running = False
                    return
                
                st.session_state.last_result = result
                
                # Mettre à jour la chaîne avec le résumé
                if st.session_state.research_chain:
                    st.session_state.research_chain[-1]['summary'] = result.get('synthesis', '')[:200] + "..."
            
            st.success("✅ Recherche terminée avec succès !")
            st.session_state.search_running = False
            
            # Nettoyer les états de plan
            st.session_state.plan_approved = False
            st.session_state.preview_plan = None
            
        except Exception as e:
            st.session_state.search_running = False
            st.error(f"❌ Erreur lors de la recherche: {str(e)}")
            logger.error(f"Erreur recherche: {e}")
            
            # Afficher les détails de l'erreur
            with st.expander("🔍 Détails de l'erreur"):
                st.code(str(e))
                st.write("**Logs de debug :**")
                for log in st.session_state.search_logs[-10:]:
                    st.write(f"[{log['time']}] {log['message']}")
    
    # ========== NOUVELLE LOGIQUE DE RECHERCHE CONTEXTUELLE ==========
    
    # 5. GESTION DE LA RECHERCHE CONTEXTUELLE
    if st.session_state.get('contextual_search_active', False):
        st.session_state.contextual_search_active = False
        
        # Nettoyer les logs et étapes pour la nouvelle recherche
        st.session_state.search_steps = {}
        st.session_state.search_logs = []
        
        # Marquer le début de la recherche contextuelle
        st.session_state.search_running = True
        
        # Configurer l'agent (utiliser la config précédente ou par défaut)
        if not hasattr(st.session_state, 'agent') or st.session_state.agent is None:
            st.session_state.agent = get_agent("mistral", ["SerpApi"], "both")
        
        # Messages de démarrage pour la recherche contextuelle
        add_search_log("🔄 Démarrage de la recherche contextuelle")
        add_search_log(f"💡 Question de suivi: {st.session_state.followup_query}")
        add_search_log(f"📚 Utilisation du contexte de: {st.session_state.research_context.get('query', 'N/A')}")
        
        try:
            # Effectuer la recherche contextuelle
            with st.spinner("🔄 Recherche contextuelle en cours..."):
                contextual_result = contextual_research_with_progress(
                    st.session_state.agent,
                    st.session_state.followup_query,
                    st.session_state.research_context,
                    max_articles=5,
                    search_engines=["SerpApi"],
                    scraping_method="both",
                    max_results=10,
                    max_queries=4  # Moins de requêtes pour les recherches de suivi
                )
                
                # Vérifier si la recherche a été interrompue
                if contextual_result is None:
                    st.warning("🛑 Recherche contextuelle interrompue par l'utilisateur")
                    st.session_state.search_running = False
                    return
                
                st.session_state.last_result = contextual_result
            
            st.success("✅ Recherche contextuelle terminée avec succès !")
            st.session_state.search_running = False
            
            # Nettoyer les états
            st.session_state.followup_query = ""
            
        except Exception as e:
            st.session_state.search_running = False
            st.error(f"❌ Erreur lors de la recherche contextuelle: {str(e)}")
            logger.error(f"Erreur recherche contextuelle: {e}")
            
            # Afficher les détails de l'erreur
            with st.expander("🔍 Détails de l'erreur"):
                st.code(str(e))
                st.write("**Logs de debug :**")
                for log in st.session_state.search_logs[-10:]:
                    st.write(f"[{log['time']}] {log['message']}")
    
    # Afficher les résultats
    if st.session_state.last_result:
        # Afficher un badge pour les résultats contextuels
        if st.session_state.last_result.get('is_contextual', False):
            st.info(f"🔗 **Résultats contextuels** basés sur votre recherche précédente: \"{st.session_state.last_result.get('original_query', 'N/A')}\"")
        
        display_results(st.session_state.last_result)
    
    # Instructions (seulement si pas de plan en cours et pas de résultats)
    if not st.session_state.last_result and not st.session_state.get('preview_plan'):
        st.markdown("""
        ### 💡 Guide d'utilisation
        
        1. **Posez votre question** dans le champ ci-dessus
        2. **Cliquez sur "Lancer la recherche"** pour générer le plan
        3. **Vérifiez le plan de recherche** proposé par l'IA
        4. **Acceptez ou régénérez** le plan selon vos besoins
        5. **Suivez le progrès** en temps réel avec les étapes colorées
        6. **Explorez les résultats** avec les sources et articles détaillés
        7. **Posez des questions de suivi** pour approfondir sans perdre le contexte
        
        **✨ Exemples de questions efficaces :**
        - `Intelligence artificielle avantages inconvénients`
        - `Télétravail impact productivité 2024`
        - `Changement climatique solutions`
        - `Jeûne intermittent effets santé`
        
        **🔄 Exemples de questions de suivi :**
        - `Quels sont les risques de cette approche ?`
        - `Peut-on avoir des exemples concrets ?`
        - `Y a-t-il des alternatives ?`
        
        **🔧 Activez les logs** pour voir les détails techniques de la recherche.
        """)

if __name__ == "__main__":
    main() 