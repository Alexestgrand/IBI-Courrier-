#!/bin/bash
# Déploiement production IBI Courriers Web
set -euo pipefail

REPO_DIR="${DEPLOY_REPO_DIR:-$HOME/IBI-Courrier-}"
APP_DIR="${REPO_DIR}/ibi-courriers-web"
BRANCH="${DEPLOY_BRANCH:-main}"

echo "==> Mise à jour du dépôt (${BRANCH})"
cd "$REPO_DIR"
git fetch origin "$BRANCH"
git reset --hard "origin/${BRANCH}"

echo "==> Rebuild Docker"
cd "$APP_DIR"
docker compose -f docker-compose.prod.yml up -d --build

echo "==> État des conteneurs"
docker compose -f docker-compose.prod.yml ps

echo "==> Santé API"
chmod +x scripts/wait-health.sh
./scripts/wait-health.sh
echo "Déploiement terminé."
