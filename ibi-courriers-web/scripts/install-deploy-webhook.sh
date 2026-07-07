#!/bin/bash
# Installation unique sur le VPS — webhook HTTPS pour GitHub Actions (sans SSH port 22)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="${DEPLOY_WEBHOOK_ENV:-$HOME/.config/ibi-deploy-webhook.env}"
SERVICE_NAME="ibi-deploy-webhook"

mkdir -p "$(dirname "$ENV_FILE")"

if [ ! -f "$ENV_FILE" ]; then
  SECRET="$(openssl rand -hex 32)"
  cat >"$ENV_FILE" <<EOF
DEPLOY_WEBHOOK_SECRET=${SECRET}
DEPLOY_REPO_DIR=${HOME}/IBI-Courrier-
DEPLOY_WEBHOOK_HOST=127.0.0.1
DEPLOY_WEBHOOK_PORT=9089
EOF
  chmod 600 "$ENV_FILE"
  echo "==> Fichier créé : $ENV_FILE"
else
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  SECRET="${DEPLOY_WEBHOOK_SECRET:-}"
fi

if [ -z "${SECRET:-}" ]; then
  echo "ERREUR: DEPLOY_WEBHOOK_SECRET manquant dans $ENV_FILE"
  exit 1
fi

echo "==> Service systemd ${SERVICE_NAME}"
sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=IBI Courriers — webhook de déploiement GitHub Actions
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${USER}
Group=${USER}
WorkingDirectory=${HOME}
EnvironmentFile=${ENV_FILE}
ExecStart=/usr/bin/python3 ${SCRIPT_DIR}/deploy-webhook.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now "${SERVICE_NAME}.service"
sudo systemctl status "${SERVICE_NAME}.service" --no-pager -l || true

echo ""
echo "==> Mettre à jour Caddy (une fois)"
echo "    sudo cp ${APP_DIR}/deploy/Caddyfile /etc/caddy/Caddyfile"
echo "    sudo caddy validate --config /etc/caddy/Caddyfile"
echo "    sudo systemctl reload caddy"
echo ""
echo "==> Secrets GitHub (Settings → Secrets → Actions)"
echo "    DEPLOY_WEBHOOK_URL=https://courriersibi.com/hooks/deploy"
echo "    DEPLOY_WEBHOOK_SECRET=${SECRET}"
echo ""
echo "Test local :"
echo "  curl -sS -X POST http://127.0.0.1:9089/hooks/deploy -H 'Authorization: Bearer ${SECRET}'"
