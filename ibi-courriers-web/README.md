# IBI Courriers Web (MVP v2)

Application web de gestion des courriers pour le Groupe IBI — accès multi-utilisateurs via navigateur, hébergement cloud.

## Fonctionnalités MVP

- Connexion sécurisée (JWT, sessions persistantes 8 h)
- Courriers entrants : création, liste, fiche détaillée
- **Pièces jointes multiples** à l'enregistrement (PDF, JPG, PNG, DOCX)
- Workflow de validation par rôle (réception → transmis, DG → validé/rejeté)
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
| GET | `/api/pieces-jointes/{id}/download` | Télécharger PJ |

## Prochaines étapes (hors MVP)

- Courriers sortants + génération PDF
- Modification d'un courrier existant
- Gestion des utilisateurs (admin)
- Recherche avancée
- PWA (icône bureau)

## Application desktop (v1)

L'ancienne version desktop reste dans `../ibi-courriers/` pour référence et migration des données.
