--- a/backend/DEPLOY.md
+++ b/backend/DEPLOY.md
@@ -1,7 +1,7 @@
 # Déploiement de NextMove (Vercel + AWS EC2)
 
-Ce guide déploie l'API FastAPI dans un conteneur Docker sur une instance AWS EC2,
-et l'interface web sur Vercel. L'app mobile et le web partagent les mêmes comptes
+Ce guide déploie l'API FastAPI dans un conteneur Docker sur une instance AWS EC2
+(`m7i-flex.large`), et l'interface web sur Vercel. L'app mobile et le web partagent les mêmes comptes
 et les mêmes données grâce à une base Supabase unique.
 
 ## Architecture
@@ -24,9 +24,11 @@
 
 ## 1. Prérequis
 
-- Une instance AWS EC2 avec Docker installé : au moins 4 Go de
-  RAM et 20 à 30 Go de disque (l'image contient PyTorch, Chromium et le modèle
-  d'embeddings ; vérifier sa taille réelle après le build).
+- Une instance AWS EC2 `m7i-flex.large` (2 vCPU, 8 Go de RAM), sous Ubuntu Server LTS,
+  avec un volume EBS d'au moins 30 Go (l'image contient PyTorch, Chromium et le modèle
+  d'embeddings ; vérifier sa taille réelle après le build) et une adresse IP élastique.
+  Compter 8 Go de RAM au minimum : l'analyse vidéo (YOLO) et l'export PDF (Chromium)
+  sont gourmands, et 4 Go risquent de ne pas suffire en cas d'usages simultanés.
 - Un nom de domaine pour l'API, par exemple `api.nextmoveapp.lol`,
   dont l'enregistrement DNS pointe vers l'adresse IP de l'instance.
 - Le projet Supabase existant (base et Storage, bucket privé `videos`).
@@ -62,7 +64,22 @@
 
 ## 3. Configurer l'instance EC2
 
-Groupe de sécurité :
+**Création.** Console AWS → EC2 → *Launch instance* :
+
+| Paramètre | Valeur |
+|---|---|
+| Type | `m7i-flex.large` (2 vCPU, 8 Go de RAM) |
+| Système | Ubuntu Server LTS (les commandes ci-dessous supposent Ubuntu ou Debian) |
+| Stockage | Volume EBS gp3 de 30 Go minimum |
+| Clé SSH | Une paire de clés propre au projet, conservée hors du dépôt |
+| Région | **[à compléter]**, la même que celle utilisée pour les estimations de coûts |
+
+**Adresse IP élastique.** Associer une *Elastic IP* à l'instance (EC2 → *Elastic IPs*) :
+sans elle, l'IP publique change à chaque arrêt de l'instance et l'enregistrement DNS
+devient faux. Créer ensuite l'enregistrement DNS `A` de `api.nextmoveapp.lol` vers
+cette adresse.
+
+**Groupe de sécurité :**
 
 | Port | Ouverture |
 |---|---|
@@ -70,6 +87,32 @@
 | 80 et 443 | Public (HTTP pour le certificat, HTTPS pour l'API) |
 | 8000 | **Fermé** à l'extérieur : seul le reverse proxy y accède |
 
+**Installation de Docker et de Git** (connexion SSH à l'instance) :
+
+```bash
+sudo apt-get update
+sudo apt-get install -y docker.io git
+sudo systemctl enable --now docker
+sudo usermod -aG docker $USER   # puis se déconnecter et se reconnecter
+```
+
+Le dépôt peut alors être cloné sur l'instance (`git clone https://github.com/Loulou441/nextmove.git`)
+pour construire l'image (étape 2). Sur Amazon Linux, les commandes d'installation
+diffèrent (`dnf` au lieu d'`apt-get`).
+
+## Coûts indicatifs
+
+| Poste | Coût |
+|---|---|
+| EC2 `m7i-flex.large`, tarif à la demande | 0,1017 $ de l'heure, soit environ 74 $ par mois en usage continu (730 h) |
+| Volume EBS gp3 (30 Go) | À ajouter ; voir la grille de tarifs de la région |
+| Adresse IPv4 publique | À ajouter ; AWS facture désormais les IPv4 publiques |
+| Transfert de données sortant | À ajouter ; au-delà du quota gratuit d'AWS |
+
+Le tarif horaire est celui d'une instance Linux à la demande ; il varie selon la région.
+Arrêter l'instance (et non la résilier) interrompt la facturation de l'instance, mais
+pas celle du volume EBS ni de l'IP élastique.
+
 ## 4. Variables d'environnement
 
 Créer un fichier `.env` **sur le serveur** (jamais commité), à partir de
@@ -94,12 +137,24 @@
 > cookies tiers) le bloquent même avec `SameSite=None`. Pour une connexion fiable,
 > servir le frontend et l'API comme sous-domaines du même site (par exemple
 > `app.nextmoveapp.lol` pour Vercel et `api.nextmoveapp.lol` pour EC2) et utiliser
-> `AUTH_COOKIE_SAMESITE=lax`.
+> `AUTH_COOKIE_SAMESITE=lax`. Tant que le frontend reste sur son adresse
+> `*.vercel.app`, utiliser `AUTH_COOKIE_SAMESITE=none` et tester la connexion sous Safari.
 
 ## 5. HTTPS
 
 Placer un reverse proxy devant l'API. Avec Caddy (certificat Let's Encrypt automatique),
-le fichier `/etc/caddy/Caddyfile` suffit :
+installer Caddy sur l'instance :
+
+```bash
+sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
+curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
+  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
+curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
+  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
+sudo apt-get update && sudo apt-get install -y caddy
+```
+
+puis écrire le fichier `/etc/caddy/Caddyfile` :
 
 ```
 api.nextmoveapp.lol {
@@ -107,6 +162,10 @@
 }
 ```
 
+et recharger la configuration avec `sudo systemctl reload caddy`. Le DNS de
+`api.nextmoveapp.lol` doit déjà pointer vers l'IP élastique, et les ports 80 et 443
+doivent être ouverts, sans quoi Let's Encrypt ne peut pas délivrer le certificat.
+
 Avec nginx, prévoir `client_max_body_size 60m;` : l'API accepte des vidéos jusqu'à
 50 Mo (`MAX_UPLOAD_SIZE_MB` dans `backend/services/video_storage.py`).
 
@@ -161,8 +220,10 @@
    compilation** : après toute modification, redéployer.
 4. Branche de production : `main` (les autres branches produisent des déploiements
    de prévisualisation).
-5. Domaine personnalisé : ajouter `app.nextmoveapp.lol` **[à confirmer]** et reporter
-   cette URL dans `CORS_ORIGINS` côté API.
+5. Domaine du frontend : ajouter `app.nextmoveapp.lol` **[à confirmer]** pour que le
+   frontend et l'API soient sur le même site (voir la section Cookies) et reporter cette
+   URL dans `CORS_ORIGINS` côté API. Si le frontend reste sur son adresse `*.vercel.app`
+   (par exemple `https://nextmove-gold.vercel.app`), reporter cette adresse à la place.
 
 ## 9. Pointer l'app mobile vers l'API
 
@@ -200,6 +261,8 @@
 | Connexion qui ne persiste pas | `AUTH_COOKIE_SECURE=true`, `AUTH_COOKIE_SAMESITE` adapté, frontend et API sur le même site si possible |
 | Inscription en erreur 502 | `RESEND_API_KEY` présente et domaine vérifié dans Resend |
 | Import de vidéo refusé | Taille de la vidéo (limite de 50 Mo), `client_max_body_size` du proxy, bucket `videos` |
-| Analyse en échec | Poids dans `training/models/exported/` ou `CV_WEIGHTS_DIR`, mémoire de l'instance, `docker logs` |
+| Analyse en échec | Poids dans `training/models/exported/` ou `CV_WEIGHTS_DIR`, mémoire de l'instance (`free -h`, `docker stats`), `docker logs` |
+| Le certificat HTTPS n'est pas délivré | DNS de l'API vers l'IP élastique, ports 80 et 443 ouverts dans le groupe de sécurité, `sudo journalctl -u caddy` |
+| L'API est injoignable après un redémarrage | Adresse IP élastique associée, conteneur lancé avec `--restart unless-stopped`, `sudo systemctl status docker caddy` |
 | Export PDF indisponible (503) | Chromium installé dans l'image, mémoire disponible |
 | Erreur SQL ou de révision | Étape 6, sauvegarde et état de `alembic current` |