#!/bin/bash
# Installe une tâche cron de sauvegarde quotidienne (3h du matin)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/backup.log"
CRON_LINE="0 3 * * * $BACKUP_SCRIPT >> $LOG_FILE 2>&1"

chmod +x "$BACKUP_SCRIPT"
mkdir -p "$LOG_DIR"

if crontab -l 2>/dev/null | grep -Fq "$BACKUP_SCRIPT"; then
  echo "La sauvegarde cron est déjà configurée."
else
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "Cron installé : sauvegarde quotidienne à 3h00"
  echo "$CRON_LINE"
fi

echo ""
echo "Les sauvegardes sont stockées dans le volume Docker « backups » (/data/backups),"
echo "visible aussi depuis l'interface admin → Sauvegardes."
echo ""
echo "Test manuel : $BACKUP_SCRIPT"
echo "Logs cron   : $LOG_FILE"
