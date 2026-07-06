#!/bin/bash
# Sauvegarde base de données + pièces jointes — volume Docker /data/backups (même emplacement que l'API admin)
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DATE=$(date +%F_%H%M)
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_PATH="/data/backups"

cd "$DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

if ! docker compose -f "$COMPOSE_FILE" ps --status running backend 2>/dev/null | grep -q backend; then
  echo "ERREUR: le conteneur backend n'est pas démarré."
  exit 1
fi

echo "==> Sauvegarde PostgreSQL → ${BACKUP_PATH}"
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "${POSTGRES_USER:-ibi}" --no-owner --no-acl "${POSTGRES_DB:-ibi_courriers}" \
  | gzip \
  | docker compose -f "$COMPOSE_FILE" exec -T backend \
      sh -c "cat > ${BACKUP_PATH}/db_${DATE}.sql.gz"

echo "==> Sauvegarde fichiers uploads → ${BACKUP_PATH}"
docker compose -f "$COMPOSE_FILE" exec -T backend \
  sh -c "tar czf ${BACKUP_PATH}/uploads_${DATE}.tar.gz -C /data/uploads ."

echo "==> Nettoyage des sauvegardes > ${RETENTION_DAYS} jours"
docker compose -f "$COMPOSE_FILE" exec -T backend \
  sh -c "find ${BACKUP_PATH} -type f \\( -name 'db_*.sql.gz' -o -name 'uploads_*.tar.gz' \\) -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true"

echo "==> Terminé — sauvegardes dans le volume backups (${BACKUP_PATH})"
docker compose -f "$COMPOSE_FILE" exec -T backend ls -lh "${BACKUP_PATH}" | tail -5
