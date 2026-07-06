#!/bin/bash
# Installe une tâche cron de sauvegarde quotidienne (3h du matin) avec alerte en cas d'échec
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup-cron.sh"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/backup.log"
CRON_LINE="0 3 * * * $BACKUP_SCRIPT"

chmod +x "$SCRIPT_DIR/backup.sh" "$SCRIPT_DIR/backup-cron.sh" "$SCRIPT_DIR/notify-backup-failure.sh"
mkdir -p "$LOG_DIR"

if crontab -l 2>/dev/null | grep -Fq "$BACKUP_SCRIPT"; then
  echo "La sauvegarde cron est déjà configurée."
else
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "Cron installé : sauvegarde quotidienne à 3h00 (avec alerte e-mail si échec)"
  echo "$CRON_LINE"
fi

echo ""
echo "Les sauvegardes sont stockées dans le volume Docker « backups » (/data/backups),"
echo "visible aussi depuis l'interface admin → Sauvegardes."
echo ""
echo "Alertes : configurez SMTP_ENABLED=true et NOTIFY_EMAILS dans .env"
echo "Test manuel : $SCRIPT_DIR/backup.sh"
echo "Logs cron   : $LOG_FILE"
