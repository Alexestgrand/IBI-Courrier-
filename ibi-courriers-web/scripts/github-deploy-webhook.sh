#!/bin/bash
# Appel webhook deploy depuis GitHub Actions (ou en local)
set -euo pipefail

URL="${DEPLOY_WEBHOOK_URL:?DEPLOY_WEBHOOK_URL requis}"
SECRET="${DEPLOY_WEBHOOK_SECRET:?DEPLOY_WEBHOOK_SECRET requis}"
BODY="${1:-{\"source\":\"github-actions\"}}"
MAX_ATTEMPTS="${DEPLOY_WEBHOOK_ATTEMPTS:-3}"
TIMEOUT_SEC="${DEPLOY_WEBHOOK_TIMEOUT_SEC:-900}"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo "Tentative webhook ${attempt}/${MAX_ATTEMPTS} → ${URL}"
  HTTP_CODE=$(curl -sS -o /tmp/ibi-deploy-response.json -w "%{http_code}" \
    -X POST "${URL}" \
    -H "Authorization: Bearer ${SECRET}" \
    -H "Content-Type: application/json" \
    --max-time "${TIMEOUT_SEC}" \
    -d "${BODY}") || HTTP_CODE="000"

  echo "HTTP ${HTTP_CODE}"
  cat /tmp/ibi-deploy-response.json || true
  echo ""

  if [ "$HTTP_CODE" = "200" ]; then
    exit 0
  fi
  if [ "$attempt" -lt "$MAX_ATTEMPTS" ]; then
    echo "Nouvel essai dans 30s…"
    sleep 30
  fi
done

echo "Échec du déploiement webhook après ${MAX_ATTEMPTS} tentatives."
exit 1
