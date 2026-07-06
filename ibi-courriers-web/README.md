# IBI Courriers Web (v2)

Application web de gestion des courriers pour le Groupe IBI — accès multi-utilisateurs via navigateur, hébergement cloud.

## Fonctionnalités

- Connexion sécurisée (JWT, sessions persistantes 8 h)
- **Courriers entrants** : création, liste, fiche, modification, pièces jointes
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

Chaque `push` sur `main` qui modifie `ibi-courriers-web/` déclenche un déploiement automatique sur le VPS.

### 1. Créer une clé SSH pour GitHub Actions (sur le VPS)

```bash
ssh deploy@VOTRE_IP
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""
cat ~/.ssh/github_actions.pub >> ~/.ssh/authorized_keys
cat ~/.ssh/github_actions   # copier la clé PRIVÉE
```

### 2. Ajouter les secrets GitHub

Dans le dépôt GitHub → **Settings → Secrets and variables → Actions** :

| Secret | Valeur |
|--------|--------|
| `VPS_HOST` | `187.124.49.6` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | clé privée complète (voir format ci-dessous) |

**Format du secret `VPS_SSH_KEY`** — copier-coller **tout** le fichier, y compris :

```
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

Vérifier qu'il n'y a **pas d'espace** avant/après, et qu'une **ligne vide** existe à la fin.

Test manuel depuis votre Mac :

```bash
ssh -i ~/.ssh/github_actions deploy@187.124.49.6 "echo SSH OK"
```

Si ça fonctionne, la même clé dans GitHub Actions fonctionnera.

### 3. Déploiement manuel (si besoin)

```bash
cd ~/IBI-Courrier-/ibi-courriers-web
./scripts/deploy.sh
```

En cas de conflit git sur le serveur : le script fait `git reset --hard origin/main`.

## Sauvegardes automatiques

```bash
chmod +x scripts/backup.sh
./scripts/backup.sh
```

Planifier avec cron (ex. chaque nuit à 2h) :

```bash
0 2 * * * /home/deploy/IBI-Courrier-/ibi-courriers-web/scripts/backup.sh >> /home/deploy/backups/backup.log 2>&1
```

## Migration desktop → web

```bash
docker compose -f docker-compose.prod.yml exec backend \
  python /app/scripts/migrate_desktop.py \
  --sqlite /chemin/vers/courriers.db \
  --uploads /chemin/vers/uploads
```

## Application desktop (v1)

L'ancienne version desktop reste dans `../ibi-courriers/` pour référence et migration des données.
