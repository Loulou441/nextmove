#!/bin/bash
# Script de démarrage du backend

echo "🚀 TactiCore Backend - Démarrage"
echo "================================"

# Vérifier si les dépendances sont installées
if [ ! -d "venv" ]; then
    echo "📦 Création de l'environnement virtuel..."
    python3 -m venv venv
fi

# Activer l'environnement virtuel
source venv/bin/activate

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

# Créer le répertoire de données
mkdir -p data

# Démarrer le serveur
echo "✅ Démarrage du serveur..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
