#!/bin/bash
# Wrapper cron : sauvegarde + alerte en cas d'échec
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/logs"
LOG_FILE="${LOG_DIR}/backup.log"

mkdir -p "$LOG_DIR"

if "$SCRIPT_DIR/backup.sh" >> "$LOG_FILE" 2>&1; then
  echo "[$(date -Iseconds)] Sauvegarde OK" >> "$LOG_FILE"
  exit 0
fi

CODE=$?
echo "[$(date -Iseconds)] Sauvegarde ÉCHEC (code $CODE)" >> "$LOG_FILE"
"$SCRIPT_DIR/notify-backup-failure.sh" "Échec sauvegarde IBI Courriers le $(date '+%d/%m/%Y à %H:%M') — voir logs/backup.log"
exit "$CODE"
