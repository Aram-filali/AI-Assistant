#!/bin/bash

# 🔄 Backup script pour AIAssistant
# Usage: ./backup.sh (dans le dossier projet)

set -e

BACKUP_DIR="/backups/aiassistant"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
DB_BACKUP="$BACKUP_DIR/db_backup_$DATE.sql"
PROJECT_DIR=$(pwd)

echo "🔄 Démarrage du backup..."

# Créer dossier de backup s'il n'existe pas
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "💾 Backup de la base de données..."
docker exec ai-sales-postgres pg_dump \
  -U ai_sales_user \
  ai_sales_db > "$DB_BACKUP"

# Compresser
gzip "$DB_BACKUP"
echo "✅ DB backup: ${DB_BACKUP}.gz"

# Backup Redis
echo "💾 Backup de Redis..."
REDIS_BACKUP="$BACKUP_DIR/redis_backup_$DATE.rdb"
docker exec ai-sales-redis redis-cli --rdb "$REDIS_BACKUP" > /dev/null 2>&1 || true
gzip "$REDIS_BACKUP" 2>/dev/null || true
echo "✅ Redis backup: ${REDIS_BACKUP}.gz (optionnel)"

# Backup fichiers upload
echo "💾 Backup des fichiers..."
if [ -d "$PROJECT_DIR/backend/data/uploads" ]; then
  tar -czf "$BACKUP_DIR/uploads_backup_$DATE.tar.gz" \
    -C "$PROJECT_DIR/backend/data" uploads
  echo "✅ Uploads backup: $BACKUP_DIR/uploads_backup_$DATE.tar.gz"
fi

# Cleanup (garder seulement 7 derniers backups)
echo "🧹 Nettoyage des anciens backups..."
ls -t "$BACKUP_DIR"/db_backup_*.sql.gz 2>/dev/null | tail -n +8 | xargs -r rm

echo ""
echo "✅ ============================================="
echo "✅ Backup complété!"
echo "✅ Location: $BACKUP_DIR"
echo "✅ Date: $DATE"
echo "✅ ============================================="
