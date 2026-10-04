FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 libxext6 libsm6 libxrender1 libglib2.0-0 libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# PyTorch CPU d'abord : évite les roues CUDA (plusieurs Go) inutiles sur EC2 sans GPU.
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Modèle d'embeddings téléchargé dans l'image (évite un échec réseau au démarrage).
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')"

# Chromium pour l'export PDF.
RUN playwright install --with-deps chromium

# Code backend et poids YOLO, aux mêmes emplacements que dans le dépôt
# (backend/config.py calcule REPO_ROOT = /app).
COPY backend/ backend/
COPY training/models/exported/ training/models/exported/

RUN chmod +x backend/start.sh
EXPOSE 8000
CMD ["backend/start.sh"]