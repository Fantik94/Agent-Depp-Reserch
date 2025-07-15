import streamlit as st
import logging
import time
from research_agent import ResearchAgent
from config import Config
from link_ranker import display_ranked_links
import json
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
    
    # Input principal
    user_query = st.text_input(
        "🔍 Votre question de recherche :",
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
                ["SerpApi", "Serper", "SearXNG", "Google-HTML", "Bing-HTML", "DuckDuckGo-HTML", "Startpage-HTML"],
                default=["SerpApi", "Google-HTML"],
                help="Choisissez les moteurs à utiliser (dans l'ordre). HTML contourne les limitations."
            )
            
            # Méthode de scraping
            scraping_method = st.selectbox(
                "📰 Méthode de scraping",
                ["newspaper", "beautifulsoup", "both"],
                index=2,  # Both par défaut
                help="Newspaper: Plus rapide | BeautifulSoup: Plus robuste | Both: Les deux"
            )
    
    # Boutons et options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
    
    with col1:
        search_button = st.button("🚀 Lancer la recherche", type="primary", use_container_width=True)
    
    with col2:
        if st.button("🗑️ Effacer", use_container_width=True):
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
    
    return user_query, search_button, show_logs, deep_search, max_articles, llm_provider, search_engines, scraping_method

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

def research_with_progress_tracking(agent, query, deep_search=False, max_articles=5, search_engines=None, scraping_method="both"):
    """Effectue la recherche avec suivi du progrès"""
    tracker = SearchProgressTracker()
    
    if search_engines is None:
        search_engines = ["SerpApi", "SearXNG"]
    
    try:
        # Vérifier si la recherche doit continuer
        if not st.session_state.get('search_running', True):
            logger.info("🛑 Recherche interrompue par l'utilisateur")
            return None
        # Étape 1: Génération du plan
        tracker.start_step("plan", "Génération du plan", "Analyse de votre question avec Mistral AI")
        
        # Générer un plan plus détaillé en mode approfondi
        if deep_search:
            plan = agent.llm_client.generate_deep_search_plan(query)
        else:
            plan = agent.llm_client.generate_search_plan(query)
            
        queries_count = len(plan.get("requetes_recherche", []))
        mode_text = "approfondie" if deep_search else "standard"
        tracker.complete_step("plan", "Plan généré", f"{queries_count} requêtes de recherche créées (mode {mode_text})")
        
        # Étape 2: Recherche web
        tracker.start_step("search", "Recherche web", f"Exécution de {queries_count} requêtes de recherche")
        all_search_results = []
        
        for i, search_query in enumerate(plan.get("requetes_recherche", [query]), 1):
            # Vérifier si la recherche doit continuer
            if not st.session_state.get('search_running', True):
                logger.info("🛑 Recherche interrompue pendant la recherche web")
                return None
                
            add_search_log(f"🔍 Requête {i}/{queries_count}: {search_query}")
            results = agent.search_api.search_web(search_query, enabled_engines=search_engines)
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
        
        # Filtrer les résultats fallback pour le scraping
        scrapable_results = [result for result in unique_results if result['source'] != 'fallback']
        fallback_count = len(unique_results) - len(scrapable_results)
        
        if fallback_count > 0:
            logger.info(f"⚠️ {fallback_count} résultats de fallback ignorés pour le scraping")
            add_search_log(f"⚠️ {fallback_count} résultats génériques ignorés (évite les erreurs)")
        
        if scrapable_results:
            urls_to_scrape = [result['url'] for result in scrapable_results[:max_articles * 2]]
            scraped_articles = agent.scraper.scrape_multiple_urls(urls_to_scrape, max_articles=max_articles, method=scraping_method)
        else:
            logger.warning("⚠️ Aucune URL scrapable trouvée, utilisation de la synthèse basique")
            add_search_log("⚠️ Aucun article à scraper - synthèse basée sur les snippets seulement")
            scraped_articles = []
        
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

def display_sidebar():
    """Affiche la barre latérale"""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        config = Config()
        st.write(f"**🤖 Modèle LLM :** {config.MISTRAL_MODEL}")
        st.write(f"**🔍 Max résultats :** {config.MAX_SEARCH_RESULTS}")
        st.write(f"**📰 Max articles :** {config.MAX_SCRAPED_ARTICLES}")
        
        # Status des API
        st.markdown("### 🔌 Status des APIs")
        
        # LLM APIs
        if config.MISTRAL_API_KEY:
            st.success("✅ Mistral AI")
        else:
            st.error("❌ Mistral AI")
        
        # Moteurs de recherche
        st.markdown("**🔍 Moteurs de recherche :**")
        if config.SERP_API_KEY:
            st.success("✅ SerpApi (clé personnelle)")
        else:
            st.error("❌ SerpApi")
        
        if config.SERPER_API_KEY:
            st.success("✅ Serper.dev")
        else:
            st.info("ℹ️ Serper.dev non configuré")
        
        st.success("✅ SearXNG (gratuit)")
        st.success("✅ Google HTML (gratuit)")
        st.success("✅ Bing HTML (gratuit)")
        st.success("✅ DuckDuckGo HTML (gratuit)")
        st.success("✅ Startpage HTML (gratuit)")
        
        # Méthodes de scraping
        st.markdown("**📰 Scraping disponible :**")
        st.success("✅ Newspaper3k")
        st.success("✅ BeautifulSoup")
        
        # Historique
        st.markdown("### 📜 Historique")
        if st.session_state.search_history:
            for i, query in enumerate(reversed(st.session_state.search_history[-5:]), 1):
                if st.button(f"{i}. {query[:25]}...", key=f"history_{i}"):
                    st.session_state.selected_query = query
        else:
            st.write("Aucune recherche")

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
    with st.expander("🔧 Filtrer les résultats"):
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
    
    # Plan de recherche détaillé
    if result.get('plan'):
        plan = result['plan']
        with st.expander("📋 Plan de recherche généré", expanded=True):
            st.markdown("**🎯 Requêtes de recherche :**")
            for i, query in enumerate(plan.get('requetes_recherche', []), 1):
                st.markdown(f"  {i}. `{query}`")
            
            if plan.get('types_sources'):
                st.markdown("**📚 Types de sources ciblées :**")
                for source_type in plan['types_sources']:
                    st.markdown(f"  • {source_type}")
            
            if plan.get('questions_secondaires'):
                st.markdown("**❓ Questions secondaires :**")
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

def main():
    """Fonction principale"""
    init_session_state()
    display_header()
    display_sidebar()
    
    # Interface de recherche
    user_query, search_button, show_logs, deep_search, max_articles, llm_provider, search_engines, scraping_method = display_search_interface()
    
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
    
    # Gérer la recherche
    if search_button and user_query:
        # Ajouter à l'historique
        if user_query not in st.session_state.search_history:
            st.session_state.search_history.append(user_query)
        
        # Marquer le début de la recherche
        st.session_state.search_running = True
        
        # Configurer le provider LLM sélectionné
        st.session_state.agent = get_agent(llm_provider, search_engines, scraping_method)
        
        # Afficher la configuration utilisée
        config_info = f"🤖 {llm_provider.upper()} | 🔍 {', '.join(search_engines)} | 📰 {scraping_method}"
        add_search_log(f"⚙️ Configuration: {config_info}")
        
        # Placeholder pour les mises à jour en temps réel
        progress_placeholder = st.empty()
        
        try:
            # Effectuer la recherche avec suivi
            with st.spinner("🔄 Recherche en cours..."):
                result = research_with_progress_tracking(
                    st.session_state.agent, 
                    user_query, 
                    deep_search=deep_search, 
                    max_articles=max_articles,
                    search_engines=search_engines,
                    scraping_method=scraping_method
                )
                
                # Vérifier si la recherche a été interrompue
                if result is None:
                    st.warning("🛑 Recherche interrompue par l'utilisateur")
                    st.session_state.search_running = False
                    return
                
                st.session_state.last_result = result
            
            st.success("✅ Recherche terminée avec succès !")
            st.session_state.search_running = False
            
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
    
    # Afficher les résultats
    if st.session_state.last_result:
        display_results(st.session_state.last_result)
    
    # Instructions
    if not st.session_state.last_result:
        st.markdown("""
        ### 💡 Guide d'utilisation
        
        1. **Posez votre question** dans le champ ci-dessus
        2. **Cliquez sur "Lancer la recherche"** pour démarrer
        3. **Suivez le progrès** en temps réel avec les étapes colorées
        4. **Explorez les résultats** avec les sources et articles détaillés
        
        **✨ Exemples de questions efficaces :**
        - `Intelligence artificielle avantages inconvénients`
        - `Télétravail impact productivité 2024`
        - `Changement climatique solutions`
        - `Jeûne intermittent effets santé`
        
        **🔧 Activez les logs** pour voir les détails techniques de la recherche.
        """)

if __name__ == "__main__":
    main() 