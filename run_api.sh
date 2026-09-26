#!/usr/bin/env bash
#
# Lance l'API NextMove (FastAPI) nécessaire à l'app mobile et à l'app web.
# Usage :  ./run_api.sh          (port 8000 par défaut)
#           PORT=9000 ./run_api.sh
#
# L'app mobile se connecte à :
#   - Simulateur     : http://localhost:8000
#   - iPhone physique : http://<IP-LAN-du-Mac>:8000  (même réseau Wi-Fi)
#     → mettre à jour NEXTMOVE_API_URL dans ios/nextmove/Info.plist si l'IP change.
#
# Ce script :
#   - se place toujours à la racine du projet (indépendant du cwd d'appel) ;
#   - utilise le venv .venv_api s'il existe, sinon le Python du système ;
#   - charge backend/.env (symlink vers .env.api.local) via backend/config.py.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# Choisit l'environnement Python : .venv_api en priorité, puis python3 du système.
if [ -x "$ROOT/.venv_api/bin/uvicorn" ]; then
  UVICORN="$ROOT/.venv_api/bin/uvicorn"
elif command -v uvicorn &>/dev/null; then
  UVICORN="uvicorn"
else
  echo "ERREUR : uvicorn introuvable." >&2
  echo "Installe les dépendances : pip install -r backend/requirements.txt" >&2
  exit 1
fi

PORT="${PORT:-8000}"

echo "→ API NextMove sur http://0.0.0.0:$PORT (Ctrl+C pour arrêter)"
echo "  Docs interactives : http://localhost:$PORT/docs"
echo "  iPhone physique   : http://$(ipconfig getifaddr en0 2>/dev/null || echo '<IP-LAN>'):$PORT"

# PYTHONPATH=. pour que 'backend.api.main' soit importable depuis la racine.
# --host 0.0.0.0 permet aussi la connexion depuis un iPhone physique sur le même Wi-Fi.
exec env PYTHONPATH="$ROOT" \
  "$UVICORN" backend.api.main:app --host 0.0.0.0 --port "$PORT" --reload
