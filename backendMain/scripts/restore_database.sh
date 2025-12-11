#!/bin/bash
# PostgreSQL Database Restore Script for AeroOps
# Restores database from a backup file

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
DB_NAME="${DB_NAME:-aeroops_db}"
DB_USER="${DB_USER:-aeroops_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="$(dirname "$0")/backups/database"

echo "============================================"
echo "AeroOps Database Restore"
echo "============================================"

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Available backups:"
    echo "----------------------------------------"
    ls -lht "$BACKUP_DIR"/*.gz 2>/dev/null | awk '{print NR". "$9, "-", $5, "-", $6, $7, $8}'
    echo ""
    echo "Usage: $0 <backup_file>"
    echo "Example: $0 ./backups/database/aeroops_db_backup_20251203_180133.sql.gz"
    exit 1
fi

BACKUP_FILE="$1"

# Check if file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo "Backup file: $BACKUP_FILE"
echo ""

# Warning
read -p "⚠️  WARNING: This will replace all data in $DB_NAME. Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Decompress if needed
TEMP_FILE=""
if [[ "$BACKUP_FILE" == *.gz ]]; then
    echo "Decompressing backup..."
    TEMP_FILE="${BACKUP_FILE%.gz}"
    gunzip -c "$BACKUP_FILE" > "$TEMP_FILE"
    RESTORE_FILE="$TEMP_FILE"
else
    RESTORE_FILE="$BACKUP_FILE"
fi

# Drop existing connections
echo "Terminating existing connections..."
PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "
SELECT pg_terminate_backend(pg_stat_activity.pid)
FROM pg_stat_activity
WHERE pg_stat_activity.datname = '$DB_NAME'
  AND pid <> pg_backend_pid();" > /dev/null 2>&1

# Restore database
echo "Restoring database..."
if PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$RESTORE_FILE"; then
    echo "✅ Database restored successfully"
    
    # Count restored jobs
    TOTAL_JOBS=$(PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM jobs;" 2>/dev/null | xargs)
    echo "📊 Total jobs restored: $TOTAL_JOBS"
    
    echo ""
    echo "============================================"
    echo "✅ Restore completed successfully!"
    echo "============================================"
else
    echo "❌ Error: Database restore failed"
    exit 1
fi

# Clean up temp file
if [ -n "$TEMP_FILE" ] && [ -f "$TEMP_FILE" ]; then
    rm "$TEMP_FILE"
fi
