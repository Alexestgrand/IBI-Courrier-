#!/bin/bash
# Sauvegarde base de données + pièces jointes — volume Docker /data/backups (même emplacement que l'API admin)
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
DATE=$(date +%F_%H%M)
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
BACKUP_PATH="/data/backups"
DB_FILE="db_${DATE}.sql.gz"
UPLOADS_FILE="uploads_${DATE}.tar.gz"

cd "$DIR"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

# Nom de projet explicite pour éviter de cibler un mauvais stack Docker (staging vs prod)
export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-ibi-courriers-prod}"

if ! docker compose -f "$COMPOSE_FILE" ps --status running backend 2>/dev/null | grep -q backend; then
  echo "ERREUR: le conteneur backend (${COMPOSE_PROJECT_NAME}) n'est pas démarré."
  exit 1
fi

if ! docker compose -f "$COMPOSE_FILE" ps --status running db 2>/dev/null | grep -q db; then
  echo "ERREUR: le conteneur PostgreSQL (${COMPOSE_PROJECT_NAME}) n'est pas démarré."
  exit 1
fi

_verifier_fichier_backup() {
  local nom="$1"
  docker compose -f "$COMPOSE_FILE" exec -T backend \
    sh -c "test -s ${BACKUP_PATH}/${nom}" || {
    echo "ERREUR: sauvegarde invalide ou vide — ${BACKUP_PATH}/${nom}"
    exit 1
  }
}

echo "==> Sauvegarde PostgreSQL → ${BACKUP_PATH}/${DB_FILE}"
docker compose -f "$COMPOSE_FILE" exec -T db \
  pg_dump -U "${POSTGRES_USER:-ibi}" --no-owner --no-acl "${POSTGRES_DB:-ibi_courriers}" \
  | gzip \
  | docker compose -f "$COMPOSE_FILE" exec -T backend \
      sh -c "cat > ${BACKUP_PATH}/${DB_FILE}"
_verifier_fichier_backup "$DB_FILE"

echo "==> Sauvegarde fichiers uploads → ${BACKUP_PATH}/${UPLOADS_FILE}"
docker compose -f "$COMPOSE_FILE" exec -T backend \
  sh -c "tar czf ${BACKUP_PATH}/${UPLOADS_FILE} -C /data/uploads ."
_verifier_fichier_backup "$UPLOADS_FILE"

echo "==> Nettoyage des sauvegardes > ${RETENTION_DAYS} jours"
docker compose -f "$COMPOSE_FILE" exec -T backend \
  sh -c "find ${BACKUP_PATH} -type f \\( -name 'db_*.sql.gz' -o -name 'uploads_*.tar.gz' \\) -mtime +${RETENTION_DAYS} -delete 2>/dev/null || true"

echo "==> Terminé — sauvegardes dans le volume backups (${BACKUP_PATH})"
docker compose -f "$COMPOSE_FILE" exec -T backend ls -lh "${BACKUP_PATH}" | tail -5
