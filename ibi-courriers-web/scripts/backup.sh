#!/bin/bash
# Sauvegarde base de données + pièces jointes — IBI Courriers Web
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups/ibi-courriers}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DATE=$(date +%F_%H%M)
COMPOSE_FILE="docker-compose.prod.yml"

mkdir -p "$BACKUP_DIR"
cd "$DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "==> Sauvegarde PostgreSQL"
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "${POSTGRES_USER:-ibi}" "${POSTGRES_DB:-ibi_courriers}" \
  | gzip > "$BACKUP_DIR/db_${DATE}.sql.gz"

echo "==> Sauvegarde fichiers uploads"
VOLUME=$(docker volume ls -q | grep uploads | head -1)
if [ -n "$VOLUME" ]; then
  docker run --rm \
    -v "${VOLUME}:/data:ro" \
    -v "$BACKUP_DIR:/backup" \
    alpine tar czf "/backup/uploads_${DATE}.tar.gz" -C /data .
else
  echo "Avertissement : volume uploads introuvable."
fi

echo "==> Nettoyage des sauvegardes > ${RETENTION_DAYS} jours"
find "$BACKUP_DIR" -type f \( -name 'db_*.sql.gz' -o -name 'uploads_*.tar.gz' \) \
  -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

echo "==> Terminé — $BACKUP_DIR"
ls -lh "$BACKUP_DIR" | tail -5
