# API HTTP NextMove

Cette API est utilisée par les clients React et iOS.
Voir [le README du backend](../README.md) pour la configuration, les routes,
la migration et les tests. Depuis la racine du dépôt :

```bash
python -m uvicorn backend.api.main:app --reload --port 8000
```

Documentation interactive : http://localhost:8000/docs.

En production, l’API est servie par un conteneur Docker sur AWS EC2 : voir
[le guide de déploiement](../DEPLOY.md).
