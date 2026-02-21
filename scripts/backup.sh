#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Chemistry Bot — Database Backup Script
#
# Creates a compressed MySQL dump and optionally sends it to Telegram.
#
# Usage:
#   ./scripts/backup.sh               — creates backup, no Telegram notification
#   ./scripts/backup.sh --notify      — creates backup + sends via Telegram bot
#
# Scheduled daily backup via host cron (add to crontab -e):
#   0 3 * * * /path/to/chemistry_bot/scripts/backup.sh --notify >> /var/log/chembot_backup.log 2>&1
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

cd "$(dirname "$0")/.."

# Load .env if it exists
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

BACKUP_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$BACKUP_DIR"

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/chemistry_bot_${DATE}.sql.gz"

echo "[$(date '+%F %T')] Starting backup..."

# Dump from the running db container
docker compose exec -T db \
    mysqldump -u"${DB_USER}" -p"${DB_PASSWORD}" "${DB_NAME}" \
    | gzip > "$BACKUP_FILE"

echo "[$(date '+%F %T')] Backup saved: $BACKUP_FILE"

# Remove backups older than 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
echo "[$(date '+%F %T')] Old backups pruned."

# Send backup to Telegram (optional)
if [[ "${1:-}" == "--notify" ]]; then
    docker compose run --rm backup \
        sh -c "cp /dev/stdin /tmp/backup.sql.gz < /dev/null || true && \
               python utils/backup_sender.py" 2>/dev/null || true
fi

echo "[$(date '+%F %T')] Done."
