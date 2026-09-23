# NextMove — frontend React / Next.js

Les instructions de lancement, configuration et test sont dans
[web/README.md](../README.md).

Le client `lib/api.ts` utilise `NEXT_PUBLIC_API_URL` pour joindre l’API commune
du dossier [backend/](../../backend/README.md). Valeur locale : http://localhost:8000.
Configurer `.env.local` à partir de `.env.local.example`, puis exécuter `npm ci`
et `npm run dev` depuis ce dossier.
