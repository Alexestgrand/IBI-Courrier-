# IBI Courriers Web (v2)

Application web de gestion des courriers pour le Groupe IBI — accès multi-utilisateurs via navigateur, hébergement cloud.

## Fonctionnalités

- Connexion sécurisée (JWT, sessions persistantes 8 h)
- **Courriers entrants** : création (wizard 3 étapes + OCR), liste, fiche, modification, suppression, pièces jointes
- **Courriers sortants** : création (saisie + PDF auto ou import PDF scanné), liste, téléchargement PDF
- Workflow de validation par rôle (réception → transmis, DG → validé/rejeté)
- **Recherche avancée** multi-critères (type, statut, service, urgence, dates, filiale)
- **Gestion utilisateurs** (admin) : CRUD, activation, réinitialisation mot de passe, journal d'audit
- **Profil** : changement de mot de passe
- **8 filiales** visibles par tous : IBI, Thabor, Mamel, N'kafu, Lemetier, BAYI, comm'eve, Calao
- **7 services** : Direction, Comptabilité, Service Marché, Facturation, DAF, Service Audit, Service Informatique
- Tableau de bord avec statistiques par filiale

## Architecture

```
Navigateur  →  Nginx (frontend)  →  React
                    ↓ /api
              FastAPI (backend)  →  PostgreSQL
                                 →  Volume fichiers (/data/uploads)
```

## Démarrage local (développement)

Prérequis : Docker et Docker Compose.

```bash
cd ibi-courriers-web
docker compose up --build
```

- Frontend : http://localhost:5173
- API : http://localhost:8000/api/health
- Documentation API : http://localhost:8000/docs

**Compte par défaut** (première installation) :
- E-mail : `admin@ibi.ci`
- Mot de passe : `admin123`

## Déploiement cloud (production)

### 1. Serveur VPS (OVH, Scaleway, etc.)

- Ubuntu 22.04+, 2 Go RAM minimum
- Docker + Docker Compose installés
- Nom de domaine pointant vers l'IP du serveur (ex. `courriers.ibi.ci`)

### 2. Variables d'environnement

Créer un fichier `.env` à la racine :

```env
POSTGRES_USER=ibi
POSTGRES_PASSWORD=<mot-de-passe-fort>
POSTGRES_DB=ibi_courriers
SECRET_KEY=<cle-secrete-longue-aleatoire>
CORS_ORIGINS=https://courriers.ibi.ci
```

Générer une clé secrète :
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Lancer en production

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

L'application est accessible sur le port 80.

### 4. HTTPS (recommandé)

Installer Certbot avec Nginx ou placer un reverse proxy (Traefik, Caddy) devant le conteneur frontend pour obtenir un certificat Let's Encrypt.

Exemple avec Caddy devant le port 80 :
```
courriers.ibi.ci {
    reverse_proxy localhost:80
}
```

### 5. Sauvegardes

Sauvegarder régulièrement :
- Volume PostgreSQL (`pgdata`)
- Volume fichiers (`uploads`)

```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U ibi ibi_courriers > backup.sql
```

## Structure du projet

```
ibi-courriers-web/
├── backend/          # API FastAPI + PostgreSQL
│   └── app/
├── frontend/         # Interface React (Vite)
├── docker-compose.yml        # Développement
└── docker-compose.prod.yml   # Production
```

## API principale

| Méthode | Route | Description |
|---------|-------|-------------|
| POST | `/api/auth/login` | Connexion |
| GET | `/api/auth/me` | Utilisateur courant |
| GET | `/api/courriers/entrants` | Liste courriers |
| POST | `/api/courriers/entrants` | Créer (multipart + fichiers) |
| GET | `/api/courriers/{id}` | Détail |
| PATCH | `/api/courriers/{id}/statut` | Changer statut |
| PATCH | `/api/courriers/{id}` | Modifier courrier |
| GET | `/api/courriers/sortants` | Liste sortants |
| POST | `/api/courriers/sortants` | Créer sortant |
| GET | `/api/courriers/{id}/pdf` | Télécharger PDF sortant |
| GET | `/api/recherche` | Recherche avancée |
| GET/POST/PATCH | `/api/users` | Gestion utilisateurs (admin) |
| POST | `/api/auth/change-password` | Changer son mot de passe |
| GET | `/api/audit` | Journal d'audit (admin) |

## Déploiement automatique (GitHub Actions)

Chaque `push` sur `main` qui modifie `ibi-courriers-web/` déclenche tests, build puis déploiement.

**Méthode recommandée : webhook HTTPS** (contourne les blocages SSH depuis GitHub). Guide complet : [`deploy/DEPLOY.md`](deploy/DEPLOY.md).

### 1. Installer le webhook sur le VPS (une fois)

```bash
ssh deploy@VOTRE_IP
cd ~/IBI-Courrier-/ibi-courriers-web
./scripts/install-deploy-webhook.sh
sudo cp deploy/Caddyfile /etc/caddy/Caddyfile && sudo systemctl reload caddy
```

### 2. Secrets GitHub

| Secret | Valeur |
|--------|--------|
| `DEPLOY_WEBHOOK_URL` | `https://courriersibi.com/hooks/deploy` |
| `DEPLOY_WEBHOOK_SECRET` | affiché par le script d'installation |

### 3. Secours SSH (optionnel)

Si le webhook n'est pas configuré, les secrets `VPS_HOST`, `VPS_USER` et `VPS_SSH_KEY` sont utilisés (souvent bloqués par le pare-feu OVH depuis GitHub).

### 4. Déploiement manuel

```bash
cd ~/IBI-Courrier-/ibi-courriers-web
./scripts/deploy.sh
```

En cas de conflit git sur le serveur : le script fait `git reset --hard origin/main`.

## Sauvegardes automatiques

Les sauvegardes (cron et interface admin) sont stockées dans le **même volume Docker** `backups` (`/data/backups`).

```bash
chmod +x scripts/backup.sh scripts/install-backup-cron.sh
./scripts/backup.sh              # test manuel
./scripts/install-backup-cron.sh # cron quotidien à 3h00
```

Logs cron : `logs/backup.log`

## Sécurité serveur (recommandé)

- Pare-feu : n'exposer que SSH (22), HTTP (80) et HTTPS (443)
  ```bash
  sudo ufw allow OpenSSH
  sudo ufw allow 80/tcp
  sudo ufw allow 443/tcp
  sudo ufw enable
  ```
- L'application Docker écoute uniquement sur `127.0.0.1:8080` ; Caddy termine le TLS en frontal
- `SECRET_KEY` et `POSTGRES_PASSWORD` : valeurs uniques, jamais les défauts du dépôt
- Rotation périodique des clés SSH de déploiement

## Migration desktop → web

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python /app/scripts/migrate_desktop.py \
  --sqlite /chemin/vers/courriers.db \
  --uploads /chemin/vers/uploads
```

## Application desktop (v1)

L'ancienne version desktop reste dans `../ibi-courriers/` pour référence et migration des données.
