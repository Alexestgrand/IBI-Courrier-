#!/bin/bash
# Déploiement production IBI Courriers Web
set -euo pipefail

REPO_DIR="${DEPLOY_REPO_DIR:-$HOME/IBI-Courrier-}"
APP_DIR="${REPO_DIR}/ibi-courriers-web"
BRANCH="${DEPLOY_BRANCH:-main}"
COMPOSE_FILE="${DEPLOY_COMPOSE_FILE:-docker-compose.prod.yml}"
HEALTH_URL="${DEPLOY_HEALTH_URL:-http://127.0.0.1:8080/api/health}"

echo "==> Mise à jour du dépôt (${BRANCH})"
cd "$REPO_DIR"
git fetch origin "$BRANCH"
git reset --hard "origin/${BRANCH}"

echo "==> Rebuild Docker (${COMPOSE_FILE})"
cd "$APP_DIR"
docker compose -f "$COMPOSE_FILE" up -d --build

echo "==> État des conteneurs"
docker compose -f "$COMPOSE_FILE" ps

echo "==> Santé API"
chmod +x scripts/wait-health.sh
./scripts/wait-health.sh "$HEALTH_URL"
echo "Déploiement terminé."
