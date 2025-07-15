# 🔍 Agent de Recherche Intelligent

Un mini agent de recherche qui prend en entrée une question et génère automatiquement un plan de recherche, scrape le web pour collecter des informations, puis produit une synthèse complète.

## ✨ Fonctionnalités

- **Planification automatique** : Génère un plan de recherche intelligent basé sur votre question
- **Recherche multi-sources** : Utilise DuckDuckGo (gratuit) et Serper.dev comme fallback
- **Scraping intelligent** : Extrait le contenu des articles avec Newspaper3k et BeautifulSoup
- **Synthèse IA** : Produit une synthèse complète avec Mistral AI
- **Interface moderne** : Application Streamlit avec loader et design responsive
- **Historique** : Garde en mémoire vos recherches précédentes

## 🚀 Installation

1. **Cloner le repository**
```bash
git clone <repository-url>
cd Agent-Depp-Reserch
```

2. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration des clés API**

Créez un fichier `.env` dans le dossier `agent/` :
```bash
MISTRAL_API_KEY=OHgvSY6RrhHNkTY1M3RQ7ici0iLuDwPv
SERPER_API_KEY=your_serper_api_key_here  # Optionnel
```

- **Mistral API** : Déjà configurée avec votre clé
- **Serper API** : Optionnelle (version gratuite disponible sur serper.dev)

## 🎯 Utilisation

### Lancer l'application

```bash
cd agent
streamlit run app.py
```

L'application sera accessible sur `http://localhost:8501`

### Interface utilisateur

1. **Posez votre question** dans le champ de recherche
2. **Cliquez sur "Lancer la recherche"**
3. **Attendez** pendant que l'agent :
   - 📋 Génère un plan de recherche
   - 🔍 Recherche sur le web
   - 📰 Scrape les articles pertinents
   - ✍️ Synthétise les résultats
4. **Consultez** la synthèse et explorez les sources détaillées

### Exemples de questions

- "Quels sont les effets du jeûne intermittent ?"
- "Comment fonctionne l'intelligence artificielle ?"
- "Quelles sont les dernières actualités sur le changement climatique ?"
- "Avantages et inconvénients du télétravail"

## 🏗️ Architecture

```
agent/
├── app.py              # Interface Streamlit principale
├── research_agent.py   # Agent principal coordonnant tout
├── llm_client.py       # Client Mistral pour IA
├── search_api.py       # API de recherche (DuckDuckGo + Serper)
├── scraper.py          # Scraper web (Newspaper3k + BeautifulSoup)
├── config.py           # Configuration et paramètres
└── __init__.py         # Package Python
```

### Flux de l'agent

1. **Input** : Question utilisateur
2. **Planification** : Mistral génère un plan de recherche structuré
3. **Recherche** : Collecte des URLs via les APIs de recherche
4. **Scraping** : Extraction du contenu des articles les plus pertinents
5. **Synthèse** : Mistral analyse et synthétise toutes les informations
6. **Output** : Synthèse structurée avec sources

## 🔧 Configuration

### Paramètres modifiables dans `config.py`

```python
MAX_SEARCH_RESULTS = 10     # Nombre max de résultats de recherche
MAX_SCRAPED_ARTICLES = 5    # Nombre max d'articles à scraper
MISTRAL_MODEL = "mistral-large-latest"  # Modèle Mistral à utiliser
MAX_TOKENS = 2000           # Tokens max pour les réponses
TEMPERATURE = 0.7           # Créativité du modèle (0-1)
```

### APIs utilisées

- **Mistral AI** : LLM pour planification et synthèse
- **DuckDuckGo API** : Recherche web gratuite
- **Serper.dev** : Recherche Google (fallback, optionnel)
- **Newspaper3k** : Extraction de contenu d'articles
- **BeautifulSoup** : Scraping HTML (fallback)

## 📊 Fonctionnalités avancées

### Interface Streamlit

- **Design moderne** avec CSS personnalisé
- **Loader animé** pendant les recherches
- **Statistiques** détaillées des recherches
- **Historique** des questions précédentes
- **Sources expandables** pour voir les détails
- **Sidebar** avec configuration et status

### Gestion d'erreurs

- **Fallback automatique** entre les méthodes de scraping
- **Retry logic** pour les requêtes réseau
- **Logs détaillés** pour le debugging
- **Plans de fallback** si les APIs échouent

### Performance

- **Limitation des tokens** pour contrôler les coûts
- **Timeout configurables** pour éviter les blocages
- **Déduplication** des résultats
- **Pause entre requêtes** pour respecter les serveurs

## 🆘 Dépannage

### Problèmes courants

1. **Erreur Mistral API**
   - Vérifiez votre clé API dans `.env`
   - Vérifiez votre quota API

2. **Pas de résultats de recherche**
   - Vérifiez votre connexion internet
   - Essayez une question plus simple

3. **Scraping échoue**
   - Normal, certains sites bloquent le scraping
   - L'agent utilise automatiquement d'autres sources

4. **Application lente**
   - Réduisez `MAX_SCRAPED_ARTICLES` dans config.py
   - Vérifiez votre connexion internet

### Logs

Les logs sont affichés dans la console. Pour plus de détails :
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔮 Améliorations futures

- Support de plus d'APIs de recherche
- Cache des résultats pour éviter les re-recherches
- Export des synthèses en PDF/Word
- Support multilingue
- API REST pour intégrations externes
- Recherche d'images et vidéos

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Ouvrir des issues pour les bugs ou suggestions
- Proposer des pull requests pour les améliorations
- Améliorer la documentation

---

**Développé avec ❤️ en Python, Streamlit et Mistral AI** 