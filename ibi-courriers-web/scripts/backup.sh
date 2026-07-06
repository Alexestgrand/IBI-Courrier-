#!/bin/bash
# Sauvegarde base de données + pièces jointes — IBI Courriers Web
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP_DIR="${HOME}/backups/ibi-courriers"
DATE=$(date +%F_%H%M)

mkdir -p "$BACKUP_DIR"

cd "$DIR"

echo "Sauvegarde PostgreSQL…"
docker compose -f docker-compose.prod.yml exec -T db \
  pg_dump -U "${POSTGRES_USER:-ibi}" "${POSTGRES_DB:-ibi_courriers}" \
  > "$BACKUP_DIR/db_${DATE}.sql"

echo "Sauvegarde fichiers uploads…"
VOLUME=$(docker volume ls -q | grep uploads | head -1)
if [ -n "$VOLUME" ]; then
  docker run --rm \
    -v "${VOLUME}:/data" \
    -v "$BACKUP_DIR:/backup" \
    alpine tar czf "/backup/uploads_${DATE}.tar.gz" -C /data .
fi

echo "Sauvegardes dans $BACKUP_DIR"
ls -lh "$BACKUP_DIR" | tail -5
