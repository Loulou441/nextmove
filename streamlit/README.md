# NextMove — Streamlit

L’application est disponible en ligne :
**[Ouvrir NextMove](https://nextmove-app.streamlit.app/)**.
Aucune installation locale n’est nécessaire pour l’utiliser.

Elle propose l’authentification, la bibliothèque de matchs, l’import et
l’analyse de vidéos ainsi que des fonctionnalités de coaching pour le padel,
le pickleball et le tennis.

## Organisation

Les chemins suivants sont relatifs à `streamlit/` :

| Emplacement | Rôle |
|---|---|
| `app.py` | Point d’entrée et navigation |
| `src/streamlit_app/` | Écrans de l’application |
| `src/auth/` | Authentification et sessions |
| `src/db/` | Modèles SQLAlchemy et accès à la base |
| `src/services/` | Vidéos, analyses et services métier |
| `src/agents/` | Agents et connaissances de coaching |
| `alembic/` et `alembic.ini` | Migrations de base de données |
| `requirements.txt` | Dépendances Python |
| `.streamlit/config.toml` | Configuration Streamlit |

## Relation avec le backend et iOS

Streamlit appelle directement ses services Python et accède à la base de
données. Il ne dépend pas du serveur HTTP pour fonctionner.
L’API commune aux clients React et iOS se trouve dans
[`backend/`](../backend/README.md). L’ancien dossier `streamlit/src/api/`
a été supprimé ; le déploiement Streamlit n’héberge pas cette API.

Les services de Streamlit et du backend restent deux implémentations distinctes.
Si les applications doivent partager les comptes, utiliser la même base et la
même `SECRET_KEY`. Les opérations sur une base commune affectent les données
partagées. La bibliothèque vidéo iOS reste locale et n’est pas automatiquement
synchronisée avec Streamlit.

## Configuration du déploiement

Le point d’entrée du dépôt est `streamlit/app.py`. Les dépendances de cette
application se trouvent dans `streamlit/requirements.txt` ; les dépendances
système du dépôt sont indiquées dans `packages.txt` à la racine.

Pour maintenir le déploiement, vérifier la branche configurée dans l’hébergement,
le point d’entrée et les secrets. Un commit sur une autre branche ne met pas
automatiquement à jour l’application en ligne.

| Variable | Utilisation |
|---|---|
| `DATABASE_URL` | Connexion à la base |
| `SECRET_KEY` | Signature des sessions |
| `SUPABASE_URL` | Projet de stockage |
| `SUPABASE_SERVICE_KEY` | Accès serveur au stockage |
| `GROQ_API_KEY` | Appels au fournisseur de coaching |
| `CV_WEIGHTS_DIR` | Dossier alternatif des poids YOLO, optionnel |

Les secrets doivent être disponibles dans l’environnement du serveur.
Pour une configuration locale de maintenance, l’exemple est
[`.env.example`](../.env.example) à la racine, à copier en `.env` et à compléter.
`backend/.env` appartient à l’API et n’est pas la configuration de Streamlit.
Ne jamais versionner les secrets.

Le stockage attend un bucket privé `videos`. Les poids YOLO sont recherchés
par défaut dans `training/models/exported/` à la racine ; utiliser un chemin
absolu si `CV_WEIGHTS_DIR` est défini.

La version Python de référence n’est pas fixée dans le dépôt. Conserver celle
du déploiement fonctionnel et vérifier les dépendances avant de la modifier.

## Base de données et vérifications

Consulter [les instructions Alembic](alembic/README) avant d’appliquer une
migration. Distinguer la base Streamlit de celle du backend si leurs
configurations diffèrent.

Après un déploiement, vérifier la connexion, le choix du sport, l’import vidéo,
l’analyse, la bibliothèque et le coaching. Consulter les journaux pour confirmer
qu’une analyse réelle a terminé et identifier les erreurs de stockage ou d’IA.

Voir aussi [la présentation du projet](../README.md).
