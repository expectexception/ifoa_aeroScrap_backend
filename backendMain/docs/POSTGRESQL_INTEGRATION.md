# PostgreSQL Integration Guide for AeroOps Backend

## Overview

This guide explains how to integrate and use PostgreSQL with the AeroOps backend. The system is designed to work seamlessly with both SQLite (development) and PostgreSQL (production).

## Quick Setup

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
cd backendMain
./setup_postgres.sh
```

This script will:
- ✅ Check PostgreSQL installation
- ✅ Create database and user
- ✅ Configure permissions
- ✅ Update .env file
- ✅ Run migrations
- ✅ Test connection

### Option 2: Manual Setup

#### 1. Install PostgreSQL

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib python3-dev libpq-dev

# macOS
brew install postgresql
brew services start postgresql
```

#### 2. Create Database and User

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# In PostgreSQL shell:
CREATE DATABASE aeroops_db;
CREATE USER aeroops_user WITH PASSWORD 'your_secure_password';
ALTER ROLE aeroops_user SET client_encoding TO 'utf8';
ALTER ROLE aeroops_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE aeroops_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aeroops_db TO aeroops_user;

# Connect to the new database
\c aeroops_db

# Grant schema privileges
GRANT ALL ON SCHEMA public TO aeroops_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO aeroops_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO aeroops_user;

# Exit
\q
```

#### 3. Update .env File

```bash
# Edit .env file
DB_USE_POSTGRES=1
DB_NAME=aeroops_db
DB_USER=aeroops_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

#### 4. Install Python PostgreSQL Adapter

```bash
pip install psycopg2-binary
```

#### 5. Run Migrations

```bash
python manage.py migrate
```

## Configuration Details

### Django Settings (settings.py)

The system automatically detects PostgreSQL configuration from environment variables:

```python
if os.environ.get('DB_USE_POSTGRES') == '1':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'aeroops_db'),
            'USER': os.environ.get('DB_USER', 'aeroops_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'connect_timeout': 10,
                'options': '-c statement_timeout=30000',
            },
            'CONN_MAX_AGE': 600,  # Connection pooling
            'ATOMIC_REQUESTS': True,  # Transaction wrapping
        }
    }
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_USE_POSTGRES` | `0` | Set to `1` to use PostgreSQL |
| `DB_NAME` | `aeroops_db` | Database name |
| `DB_USER` | `aeroops_user` | Database user |
| `DB_PASSWORD` | - | Database password |
| `DB_HOST` | `localhost` | Database host |
| `DB_PORT` | `5432` | Database port |

## Database Management

### Using the Database Management Utility

```bash
python db_manage.py
```

This provides an interactive menu for:
- ✅ Check database connection
- ✅ Show database information
- ✅ Run migrations
- ✅ Backup database
- ✅ Show statistics
- ✅ Open database shell

### Common Commands

#### Check Connection

```bash
python db_manage.py
# Select option 1
```

#### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

#### Create Superuser

```bash
python manage.py createsuperuser
```

#### Database Shell

```bash
# Django shell
python manage.py dbshell

# Or direct PostgreSQL connection
psql -h localhost -U aeroops_user -d aeroops_db
```

#### Backup Database

```bash
# Using db_manage.py (option 4)
python db_manage.py

# Or manually
pg_dump -h localhost -U aeroops_user -d aeroops_db > backup.sql
```

#### Restore Database

```bash
psql -h localhost -U aeroops_user -d aeroops_db < backup.sql
```

## Performance Optimization

### Connection Pooling

The configuration includes connection pooling:

```python
'CONN_MAX_AGE': 600  # Keep connections alive for 10 minutes
```

### Query Optimization

```python
'ATOMIC_REQUESTS': True  # Wrap each request in a transaction
'OPTIONS': {
    'connect_timeout': 10,
    'options': '-c statement_timeout=30000',  # 30 second timeout
}
```

### Indexes

Ensure proper indexes are created for frequently queried fields:

```python
# In your models
class Job(models.Model):
    title = models.CharField(max_length=500, db_index=True)
    company = models.CharField(max_length=500, db_index=True)
    posted_date = models.DateField(null=True, blank=True, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'posted_date']),
            models.Index(fields=['company', 'status']),
        ]
```

## Migration from SQLite to PostgreSQL

### Step 1: Backup SQLite Data

```bash
python manage.py dumpdata > data_backup.json
```

### Step 2: Setup PostgreSQL

```bash
./setup_postgres.sh
```

### Step 3: Load Data

```bash
python manage.py loaddata data_backup.json
```

### Alternative: Using Django's dumpdata/loaddata

```bash
# Export from SQLite
DB_USE_POSTGRES=0 python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > data.json

# Import to PostgreSQL
DB_USE_POSTGRES=1 python manage.py loaddata data.json
```

## Monitoring and Maintenance

### Check Active Connections

```sql
SELECT * FROM pg_stat_activity WHERE datname = 'aeroops_db';
```

### Database Size

```sql
SELECT pg_size_pretty(pg_database_size('aeroops_db'));
```

### Table Sizes

```sql
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Vacuum and Analyze

```bash
# Vacuum to reclaim space
psql -h localhost -U aeroops_user -d aeroops_db -c "VACUUM ANALYZE;"
```

## Security Best Practices

### 1. Strong Passwords

Always use strong, unique passwords for database users.

### 2. Restrict Access

Configure PostgreSQL to only accept connections from trusted sources:

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/16/main/pg_hba.conf

# Add rules like:
host    aeroops_db    aeroops_user    127.0.0.1/32    md5
```

### 3. SSL Connections (Production)

Enable SSL for database connections in production:

```python
'OPTIONS': {
    'sslmode': 'require',
}
```

### 4. Regular Backups

Set up automated backups:

```bash
# Create backup script
cat > /etc/cron.daily/postgres-backup << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/postgres"
mkdir -p $BACKUP_DIR
pg_dump -h localhost -U aeroops_user aeroops_db | gzip > \
  $BACKUP_DIR/aeroops_db_$(date +%Y%m%d_%H%M%S).sql.gz
# Keep only last 7 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
EOF

chmod +x /etc/cron.daily/postgres-backup
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Start if needed
sudo systemctl start postgresql
```

### Authentication Failed

```bash
# Check user exists
sudo -u postgres psql -c "\du"

# Reset password
sudo -u postgres psql
ALTER USER aeroops_user WITH PASSWORD 'new_password';
```

### Permission Denied

```bash
# Grant all permissions
sudo -u postgres psql -d aeroops_db
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aeroops_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aeroops_user;
```

### Too Many Connections

```bash
# Check max connections
sudo -u postgres psql -c "SHOW max_connections;"

# Increase if needed (edit postgresql.conf)
sudo nano /etc/postgresql/16/main/postgresql.conf
# Change: max_connections = 200

# Restart PostgreSQL
sudo systemctl restart postgresql
```

## Testing the Integration

### Test Connection

```bash
python -c "
import os
os.environ['DB_USE_POSTGRES'] = '1'
import django
django.setup()
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT version()')
    print(c.fetchone()[0])
"
```

### Run Test Suite

```bash
python test_auth.py
python test_jwt_integration.py
```

## Production Considerations

### 1. Database Configuration

```python
# Production settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'aeroops_prod',
        'USER': 'aeroops_prod_user',
        'PASSWORD': env('DB_PASSWORD'),  # From environment
        'HOST': 'db.example.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 600,
        'ATOMIC_REQUESTS': True,
    }
}
```

### 2. Connection Pooling (pgBouncer)

Consider using pgBouncer for connection pooling in production:

```bash
sudo apt-get install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
aeroops_db = host=localhost port=5432 dbname=aeroops_db

[pgbouncer]
listen_port = 6432
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

### 3. Monitoring

Set up monitoring with tools like:
- pgAdmin
- pg_stat_statements
- Datadog
- New Relic

## Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Django PostgreSQL Notes](https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes)
- [psycopg2 Documentation](https://www.psycopg.org/docs/)

## Support

For issues:
1. Check PostgreSQL logs: `sudo tail -f /var/log/postgresql/postgresql-16-main.log`
2. Check Django logs: `tail -f logs/django.log`
3. Run database diagnostics: `python db_manage.py`

---

**Status**: PostgreSQL integration complete and production-ready! ✅
