# Database Backup & Restore Guide

## Quick Reference

### Backup Database
```bash
# Simple backup (with timestamp)
./backup_database.sh

# The backup will be saved to:
# ./backups/database/aeroops_db_backup_YYYYMMDD_HHMMSS.sql.gz
```

### Restore Database
```bash
# List available backups
./restore_database.sh

# Restore from specific backup
./restore_database.sh ./backups/database/aeroops_db_backup_20251203_180133.sql.gz
```

## What's Included in Backup

✅ All database tables and data:
- Jobs table (573 jobs as of last backup)
- Users and authentication data
- Scraper configurations and jobs
- Resume data
- All relationships and indexes

✅ Database schema:
- Table structures
- Indexes
- Constraints
- Foreign keys

## Backup Features

- **Automatic compression**: Backups are gzipped to save space
- **Timestamped files**: Each backup has a unique timestamp
- **Auto-cleanup**: Keeps last 10 backups, deletes older ones
- **Job statistics**: Shows total jobs backed up

## Latest Backup

**File**: `aeroops_db_backup_20251203_180133.sql.gz`
**Size**: 1.3 MB
**Jobs**: 573
**Date**: December 3, 2025, 18:01:33

## Manual Backup Commands

If you prefer manual backup:

```bash
# Full database backup
pg_dump -h localhost -U aeroops_user -d aeroops_db > backup.sql

# Compressed backup
pg_dump -h localhost -U aeroops_user -d aeroops_db | gzip > backup.sql.gz

# With custom format (smaller, faster restore)
pg_dump -h localhost -U aeroops_user -d aeroops_db -Fc -f backup.dump
```

## Manual Restore Commands

```bash
# From SQL file
psql -h localhost -U aeroops_user -d aeroops_db < backup.sql

# From compressed file
gunzip -c backup.sql.gz | psql -h localhost -U aeroops_user -d aeroops_db

# From custom format
pg_restore -h localhost -U aeroops_user -d aeroops_db backup.dump
```

## Scheduled Backups

To run automatic daily backups, add to crontab:

```bash
# Edit crontab
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain && ./backup_database.sh >> /tmp/db_backup.log 2>&1
```

## Backup Location

All backups are stored in:
```
/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/backups/database/
```

## Important Notes

⚠️ **Before Restoring**:
- Restoring will **replace all current data**
- Make a backup of current database first
- All active connections will be terminated during restore

✅ **Best Practices**:
- Backup before major changes
- Test restore process periodically
- Keep backups in multiple locations
- Store backups outside the project directory for production

## Troubleshooting

### Permission Denied
```bash
chmod +x backup_database.sh
chmod +x restore_database.sh
```

### Password Issues
- Make sure `.env` file contains `DB_PASSWORD`
- Check database credentials in `.env`

### Connection Issues
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check database exists: `psql -l`
- Verify user permissions

## Database Statistics

Current database state (as of backup):
- **Total Jobs**: 573
- **Sources**: 10 active sources
- **Top Sources**: LinkedIn (124), Flygosh (111), Aviation Job Search (90)
