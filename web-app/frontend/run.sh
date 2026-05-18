#!/bin/bash
# Script de démarrage du frontend

echo "🚀 TactiCore Frontend - Démarrage"
echo "=================================="

# Le frontend est servie en tant que fichiers statiques par le backend
# OU vous pouvez utiliser un serveur HTTP local

cd frontend

# Option 1: Utiliser Python (inclus)
echo "✅ Démarrage du serveur frontend..."
echo "📌 Frontend disponible à http://localhost:3000"

# Option 2: Utiliser Node.js (si disponible)
# npm install
# npm start

# Servir avec Python
python -m http.server 3000
