#!/bin/bash
# Script de démarrage complet de l'application

echo "
╔════════════════════════════════════════════╗
║         🚀 TactiCore Web Application 🚀    ║
║                                            ║
║  Architecture: Backend API + Frontend Web  ║
║  Synchronisation: WebSocket + Polling      ║
╚════════════════════════════════════════════╝
"

# Vérifier si les scripts sont exécutables
chmod +x backend/run.sh
chmod +x frontend/run.sh

# Démarrer le backend en arrière-plan
echo "📌 Démarrage du Backend (port 8000)..."
cd backend
bash run.sh &
BACKEND_PID=$!

# Attendre que le backend soit prêt
sleep 5

# Démarrer le frontend
echo "📌 Démarrage du Frontend (port 3000)..."
cd ../frontend
bash run.sh &
FRONTEND_PID=$!

echo ""
echo "✅ Applications démarrées !"
echo ""
echo "📍 Backend:  http://localhost:8000"
echo "📍 Frontend: http://localhost:3000"
echo "📚 Docs API: http://localhost:8000/docs"
echo ""
echo "🛑 Pour arrêter: Pressez Ctrl+C"

# Garder les processus actifs
wait
