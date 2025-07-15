#!/usr/bin/env python3
"""
Script de démarrage rapide pour l'Agent de Recherche
"""

import os
import sys
import subprocess

def main():
    """Lance l'application Streamlit"""
    
    print("🔍 Agent de Recherche Intelligent")
    print("=" * 40)
    
    # Vérifier si nous sommes dans le bon répertoire
    if not os.path.exists("agent"):
        print("❌ Erreur: Le dossier 'agent' n'existe pas.")
        print("Assurez-vous d'être à la racine du projet.")
        sys.exit(1)
    
    # Vérifier si Streamlit est installé
    try:
        import streamlit
    except ImportError:
        print("❌ Streamlit n'est pas installé.")
        print("Installez les dépendances avec: pip install -r requirements.txt")
        sys.exit(1)
    
    # Lancer l'application
    print("🚀 Lancement de l'application...")
    print("L'application sera accessible sur: http://localhost:8501")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("-" * 40)
    
    try:
        # Changer vers le dossier agent et lancer streamlit
        os.chdir("agent")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Application arrêtée.")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 