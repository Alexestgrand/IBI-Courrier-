#!/bin/bash
# Envoie une alerte e-mail via le conteneur backend (SMTP configuré dans .env)
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
MESSAGE="${1:-Échec de la sauvegarde automatique IBI Courriers}"

cd "$DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if docker compose -f "$COMPOSE_FILE" ps --status running backend 2>/dev/null | grep -q backend; then
  docker compose -f "$COMPOSE_FILE" exec -T backend \
    python scripts/notify_backup_failure.py "$MESSAGE" || true
else
  echo "ALERTE SAUVEGARDE: $MESSAGE" >&2
  echo "Backend indisponible — impossible d'envoyer l'e-mail d'alerte." >&2
fi
