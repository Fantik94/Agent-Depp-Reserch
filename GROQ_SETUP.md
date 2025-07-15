# 🚀 Configuration Groq (Gratuit et Rapide)

## Pourquoi Groq ?

- **100% GRATUIT** (pas de rate limits stricts)
- **ULTRA RAPIDE** (inférence en millisecondes)
- **Modèles puissants** (Llama 3.1 70B)
- **Pas de quota mensuel** restrictif

## Obtenir votre clé API Groq (2 minutes)

1. **Allez sur** : https://console.groq.com/
2. **Créez un compte** (avec email ou Google)
3. **Allez dans "API Keys"** dans le menu de gauche
4. **Cliquez "Create API Key"**
5. **Copiez votre clé** (format: `gsk_...`)

## Configuration dans l'agent

### Option 1 : Variable d'environnement (recommandé)
```bash
# Windows PowerShell
$env:GROQ_API_KEY="votre_clé_ici"

# Windows CMD
set GROQ_API_KEY=votre_clé_ici

# Linux/Mac
export GROQ_API_KEY="votre_clé_ici"
```

### Option 2 : Directement dans config.py
```python
GROQ_API_KEY = "votre_clé_ici"
```

## Lancement avec Groq

1. **Sélectionnez "groq"** dans l'interface
2. **Profitez** de la vitesse et gratuité !

## Modèles disponibles (Gratuits 2024)

- **llama-3.3-70b-versatile** : Dernier modèle Meta (par défaut)
- **llama-3.1-8b-instant** : Ultra rapide pour tests
- **mixtral-8x7b-32768** : Excellent pour longs contextes
- **gemma2-9b-it** : Alternative Google
- **llama3-groq-70b-8192-tool-use-preview** : Spécialisé pour tools/functions

💡 **L'agent teste automatiquement ces modèles dans l'ordre jusqu'à trouver un qui fonctionne !**

## Avantages vs Mistral

| Critère | Groq | Mistral |
|---------|------|---------|
| Prix | 🟢 Gratuit | 🔴 Payant |
| Vitesse | 🟢 Ultra rapide | 🟡 Moyen |
| Rate limits | 🟢 Généreux | 🔴 Stricts |
| Qualité | 🟢 Excellent | 🟢 Excellent |

---

**🎯 Recommandation** : Utilisez Groq par défaut, Mistral seulement si nécessaire. 