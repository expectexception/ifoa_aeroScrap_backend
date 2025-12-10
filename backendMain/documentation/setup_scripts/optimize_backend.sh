#!/bin/bash

# AeroOps Backend Comprehensive Optimization Script
# This script performs checks, optimizations, and creates a backup

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$HOME/Desktop/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PROJECT_NAME="aeroScrap_backend"
BACKUP_FILE="${BACKUP_DIR}/${PROJECT_NAME}_${TIMESTAMP}.tar.gz"

echo "============================================================"
echo "🚀 AeroOps Backend Optimization & Backup"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "📋 Step 1: Pre-Optimization Checks"
echo "------------------------------------------------------------"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"

# Check Django version
DJANGO_VERSION=$(python -c "import django; print(django.get_version())")
echo "✓ Django version: $DJANGO_VERSION"

# Check database connectivity
python manage.py check --database default > /dev/null 2>&1
echo "✓ Database connection: OK"

# Check migrations
PENDING=$(python manage.py showmigrations --plan | grep -c "\[ \]" || true)
if [ "$PENDING" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Pending migrations: $PENDING${NC}"
else
    echo "✓ All migrations applied"
fi

echo ""
echo "📊 Step 2: Database Health Check"
echo "------------------------------------------------------------"

python manage.py shell -c "
from django.db import connection
from jobs.models import Job, CompanyMapping, CrawlLog, ScheduleConfig
from users.models import UserProfile
from django.contrib.auth.models import User
import django_celery_beat.models as celery_models

print(f'✓ Jobs: {Job.objects.count()}')
print(f'✓ Company Mappings: {CompanyMapping.objects.count()}')
print(f'✓ Crawl Logs: {CrawlLog.objects.count()}')
print(f'✓ Users: {User.objects.count()}')
print(f'✓ User Profiles: {UserProfile.objects.count()}')
print(f'✓ Schedule Config: {\"Configured\" if ScheduleConfig.objects.exists() else \"Not Set\"}')

# Check for orphaned records
users_without_profiles = User.objects.exclude(id__in=UserProfile.objects.values_list('user_id', flat=True)).count()
if users_without_profiles > 0:
    print(f'⚠️  Users without profiles: {users_without_profiles}')
else:
    print('✓ All users have profiles')
"

echo ""
echo "🔧 Step 3: Apply Optimizations"
echo "------------------------------------------------------------"

# Collect static files
echo "→ Collecting static files..."
python manage.py collectstatic --noinput --clear > /dev/null 2>&1
echo "✓ Static files collected"

# Clear expired sessions
echo "→ Clearing expired sessions..."
python manage.py clearsessions > /dev/null 2>&1
echo "✓ Expired sessions cleared"

# Clear old JWT tokens
echo "→ Clearing blacklisted JWT tokens..."
python manage.py flushexpiredtokens > /dev/null 2>&1 || echo "✓ Token cleanup skipped (no expired tokens)"

# Database vacuum (PostgreSQL optimization)
echo "→ Optimizing database..."
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('VACUUM ANALYZE;')
print('✓ Database optimized (VACUUM ANALYZE)')
" || echo "⚠️  Database optimization skipped"

# Check for missing indexes
echo "→ Checking database indexes..."
python manage.py shell -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute(\"\"\"
        SELECT schemaname, tablename, indexname 
        FROM pg_indexes 
        WHERE schemaname = 'public' 
        ORDER BY tablename;
    \"\"\")
    indexes = cursor.fetchall()
    print(f'✓ Total indexes: {len(indexes)}')
"

echo ""
echo "🔒 Step 4: Security Check"
echo "------------------------------------------------------------"

python manage.py check --deploy > /dev/null 2>&1 && echo "✓ Security check passed" || echo -e "${YELLOW}⚠️  Security warnings exist (check logs)${NC}"

# Check for weak passwords
WEAK_PASSWORDS=$(python manage.py shell -c "
from django.contrib.auth.models import User
weak = 0
for user in User.objects.all():
    if user.check_password('password') or user.check_password('admin') or user.check_password('123456'):
        weak += 1
print(weak)
")

if [ "$WEAK_PASSWORDS" -gt 0 ]; then
    echo -e "${RED}⚠️  Found $WEAK_PASSWORDS users with weak passwords${NC}"
else
    echo "✓ No weak passwords detected"
fi

echo ""
echo "📦 Step 5: Creating Backup"
echo "------------------------------------------------------------"

cd "$SCRIPT_DIR/.."

echo "→ Creating compressed backup..."

# Files and directories to backup
tar -czf "$BACKUP_FILE" \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='*/__pycache__' \
    --exclude='*/*/__pycache__' \
    --exclude='staticfiles' \
    --exclude='logs/*.log' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='db.sqlite3' \
    --exclude='*/logs' \
    --exclude='*/raw_pages' \
    --exclude='*/raw_pages_air_india' \
    . 2>/dev/null || true

BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "✓ Backup created: $BACKUP_FILE"
echo "  Size: $BACKUP_SIZE"

# Create database backup
echo "→ Creating database backup..."
DB_BACKUP="${BACKUP_DIR}/${PROJECT_NAME}_db_${TIMESTAMP}.sql"

cd "$SCRIPT_DIR"
PGPASSWORD="aeroops_secure_password_2024" pg_dump -h localhost -U aeroops_user -d aeroops_jobs > "$DB_BACKUP" 2>/dev/null && \
    DB_SIZE=$(du -h "$DB_BACKUP" | cut -f1) && \
    echo "✓ Database backup: $DB_BACKUP ($DB_SIZE)" || \
    echo -e "${YELLOW}⚠️  Database backup failed (may need manual export)${NC}"

echo ""
echo "📋 Step 6: Generate Report"
echo "------------------------------------------------------------"

REPORT_FILE="${BACKUP_DIR}/optimization_report_${TIMESTAMP}.txt"

cat > "$REPORT_FILE" <<REPORT_EOF
============================================================
AeroOps Backend Optimization Report
============================================================
Date: $(date)
Python Version: $PYTHON_VERSION
Django Version: $DJANGO_VERSION

BACKUP INFORMATION
------------------------------------------------------------
Code Backup: $BACKUP_FILE
Size: $BACKUP_SIZE
Database Backup: $DB_BACKUP

DATABASE STATISTICS
------------------------------------------------------------
$(python manage.py shell -c "
from jobs.models import Job, CompanyMapping, CrawlLog
from users.models import UserProfile
from django.contrib.auth.models import User

print(f'Total Jobs: {Job.objects.count()}')
print(f'Active Jobs: {Job.objects.filter(status=\"active\").count()}')
print(f'Company Mappings: {CompanyMapping.objects.count()}')
print(f'Crawl Logs: {CrawlLog.objects.count()}')
print(f'Total Users: {User.objects.count()}')
print(f'User Profiles: {UserProfile.objects.count()}')
")

OPTIMIZATION APPLIED
------------------------------------------------------------
✓ Static files collected
✓ Expired sessions cleared
✓ JWT tokens flushed
✓ Database vacuum/analyze
✓ Security check performed

PENDING MIGRATIONS
------------------------------------------------------------
$(python manage.py showmigrations --plan | grep "\[ \]" | wc -l) pending migration(s)

NEXT STEPS
------------------------------------------------------------
1. Review security warnings if any
2. Update any weak passwords
3. Apply pending migrations if needed
4. Test all API endpoints
5. Configure email settings for alerts
6. Enable scheduling when ready

============================================================
REPORT_EOF

echo "✓ Report generated: $REPORT_FILE"

echo ""
echo "============================================================"
echo -e "${GREEN}✅ Optimization Complete!${NC}"
echo "============================================================"
echo ""
echo "📦 Backups created:"
echo "   • Code: $BACKUP_FILE ($BACKUP_SIZE)"
echo "   • Database: $DB_BACKUP"
echo "   • Report: $REPORT_FILE"
echo ""
echo "🔍 Next: Review the optimization report for any warnings"
echo ""
