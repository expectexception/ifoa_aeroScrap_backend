#!/bin/bash
# PostgreSQL Database Backup Script for AeroOps
# Creates timestamped backups of the database

# Load environment variables from .env if it exists
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
DB_NAME="${DB_NAME:-aeroops_db}"
DB_USER="${DB_USER:-aeroops_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Backup directory
BACKUP_DIR="$(dirname "$0")/backups/database"
mkdir -p "$BACKUP_DIR"

# Timestamp for backup file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/aeroops_db_backup_$TIMESTAMP.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

echo "============================================"
echo "AeroOps Database Backup"
echo "============================================"
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo "User: $DB_USER"
echo "Backup file: $BACKUP_FILE"
echo ""

# Create SQL dump
echo "Creating database dump..."
if PGPASSWORD="${DB_PASSWORD}" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F p -f "$BACKUP_FILE"; then
    echo "✅ Database dump created successfully"
    
    # Compress the backup
    echo "Compressing backup..."
    gzip "$BACKUP_FILE"
    
    if [ -f "$COMPRESSED_FILE" ]; then
        BACKUP_SIZE=$(du -h "$COMPRESSED_FILE" | cut -f1)
        echo "✅ Backup compressed successfully"
        echo "📦 Backup size: $BACKUP_SIZE"
        echo "📁 Location: $COMPRESSED_FILE"
        
        # Count total jobs in backup
        TOTAL_JOBS=$(PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM jobs;" 2>/dev/null | xargs)
        echo "📊 Total jobs backed up: $TOTAL_JOBS"
    else
        echo "⚠️  Warning: Compression may have failed"
    fi
    
    # List recent backups
    echo ""
    echo "Recent backups:"
    echo "----------------------------------------"
    ls -lht "$BACKUP_DIR"/*.gz 2>/dev/null | head -5 | awk '{print $9, "-", $5}'
    
    # Cleanup old backups (keep last 10)
    echo ""
    echo "Cleaning up old backups (keeping last 10)..."
    cd "$BACKUP_DIR" && ls -t *.gz 2>/dev/null | tail -n +11 | xargs -r rm
    echo "✅ Cleanup complete"
    
    echo ""
    echo "============================================"
    echo "✅ Backup completed successfully!"
    echo "============================================"
else
    echo "❌ Error: Database dump failed"
    echo "Please check your database credentials and connection"
    exit 1
fi
