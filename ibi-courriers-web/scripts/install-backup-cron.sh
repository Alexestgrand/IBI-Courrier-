#!/bin/bash
# Installe une tâche cron de sauvegarde quotidienne (3h du matin)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"
CRON_LINE="0 3 * * * $BACKUP_SCRIPT >> $HOME/backups/ibi-courriers/backup.log 2>&1"

chmod +x "$BACKUP_SCRIPT"
mkdir -p "$HOME/backups/ibi-courriers"

if crontab -l 2>/dev/null | grep -Fq "$BACKUP_SCRIPT"; then
  echo "La sauvegarde cron est déjà configurée."
else
  (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
  echo "Cron installé : sauvegarde quotidienne à 3h00"
  echo "$CRON_LINE"
fi

echo ""
echo "Test manuel : $BACKUP_SCRIPT"
