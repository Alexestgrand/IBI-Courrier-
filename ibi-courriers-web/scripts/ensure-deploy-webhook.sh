#!/bin/bash
# Réparer / redémarrer le webhook deploy sur le VPS
set -euo pipefail

REPO_DIR="${DEPLOY_REPO_DIR:-$HOME/IBI-Courrier-}"
APP_DIR="${REPO_DIR}/ibi-courriers-web"
ENV_FILE="${DEPLOY_WEBHOOK_ENV:-$HOME/.config/ibi-deploy-webhook.env}"

echo "==> Mise à jour du code"
cd "$REPO_DIR"
git fetch origin main
git reset --hard origin/main

echo "==> Réinstallation du service"
chmod +x "${APP_DIR}/scripts/install-deploy-webhook.sh" "${APP_DIR}/scripts/deploy-webhook.py"
"${APP_DIR}/scripts/install-deploy-webhook.sh"

echo ""
echo "==> Diagnostic"
sudo systemctl is-active ibi-deploy-webhook || true
ss -tlnp | grep 9089 || echo "Port 9089 : rien n'écoute"
curl -sf "http://127.0.0.1:9089/hooks/deploy/health" && echo "" || {
  echo "Échec health — logs :"
  journalctl -u ibi-deploy-webhook -n 20 --no-pager || true
  exit 1
}
echo "Webhook OK"
