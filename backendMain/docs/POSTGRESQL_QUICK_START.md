# PostgreSQL Integration - Quick Reference

## 🚀 Quick Setup

### Automated Setup (Recommended)
```bash
cd backendMain
./setup_postgres.sh
```

### Manual Setup
```bash
# 1. Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE aeroops_db;
CREATE USER aeroops_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE aeroops_db TO aeroops_user;
\c aeroops_db
GRANT ALL ON SCHEMA public TO aeroops_user;
EOF

# 2. Update .env
DB_USE_POSTGRES=1
DB_NAME=aeroops_db
DB_USER=aeroops_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# 3. Run migrations
python manage.py migrate

# 4. Test connection
python test_postgres.py
```

## 📊 Database Management

### Quick Commands
```bash
# Interactive management tool
python db_manage.py

# Test connection
python test_postgres.py

# Database shell
python manage.py dbshell

# Backup database
pg_dump -h localhost -U aeroops_user aeroops_db > backup.sql

# Restore database
psql -h localhost -U aeroops_user aeroops_db < backup.sql
```

## 🔄 Switch Between SQLite and PostgreSQL

### Use SQLite (Development)
```bash
# In .env file
DB_USE_POSTGRES=0
```

### Use PostgreSQL (Production)
```bash
# In .env file
DB_USE_POSTGRES=1
```

## 📝 Configuration

### Environment Variables (.env)
```bash
DB_USE_POSTGRES=1              # Enable PostgreSQL
DB_NAME=aeroops_db             # Database name
DB_USER=aeroops_user           # Database user
DB_PASSWORD=secure_password    # User password
DB_HOST=localhost              # Database host
DB_PORT=5432                   # Database port
```

### Django Settings Features
- ✅ Connection pooling (10 minutes)
- ✅ Transaction wrapping
- ✅ Connection timeout (10 seconds)
- ✅ Statement timeout (30 seconds)
- ✅ Automatic UTF-8 encoding

## 🧪 Testing

### Run PostgreSQL Tests
```bash
python test_postgres.py
```

### Test Authentication with PostgreSQL
```bash
python test_auth.py
python test_jwt_integration.py
```

## 🔍 Common Operations

### Check PostgreSQL Status
```bash
sudo systemctl status postgresql
```

### Start PostgreSQL
```bash
sudo systemctl start postgresql
```

### Connect to Database
```bash
psql -h localhost -U aeroops_user -d aeroops_db
```

### List All Databases
```bash
psql -U postgres -l
```

### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('aeroops_db'));
```

## 📦 Migration from SQLite

```bash
# 1. Backup SQLite data
DB_USE_POSTGRES=0 python manage.py dumpdata > data.json

# 2. Setup PostgreSQL
./setup_postgres.sh

# 3. Load data into PostgreSQL
DB_USE_POSTGRES=1 python manage.py loaddata data.json

# 4. Verify
python test_postgres.py
```

## 🛠️ Troubleshooting

### Connection Refused
```bash
sudo systemctl start postgresql
```

### Authentication Failed
```bash
sudo -u postgres psql
ALTER USER aeroops_user WITH PASSWORD 'new_password';
```

### Permission Denied
```bash
sudo -u postgres psql aeroops_db
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO aeroops_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO aeroops_user;
```

### Check Logs
```bash
# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*-main.log

# Django logs
tail -f logs/django.log
```

## 📊 Performance Tips

### Enable Query Logging (Development)
```python
# In settings.py
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}
```

### Index Important Fields
```python
class Job(models.Model):
    title = models.CharField(max_length=500, db_index=True)
    posted_date = models.DateField(db_index=True)
```

### Use select_related and prefetch_related
```python
# Optimize queries
jobs = Job.objects.select_related('company').all()
```

## 🔒 Security Checklist

- ✅ Use strong passwords
- ✅ Enable SSL in production
- ✅ Restrict pg_hba.conf
- ✅ Regular backups
- ✅ Keep PostgreSQL updated
- ✅ Use environment variables for credentials

## 📚 Resources

- Setup Script: `./setup_postgres.sh`
- Management Tool: `python db_manage.py`
- Test Suite: `python test_postgres.py`
- Full Guide: `documents/POSTGRESQL_INTEGRATION.md`

## ✅ Verification Checklist

```bash
# 1. PostgreSQL installed?
which psql

# 2. Service running?
sudo systemctl status postgresql

# 3. Database exists?
psql -U postgres -l | grep aeroops_db

# 4. Django can connect?
python test_postgres.py

# 5. All tests pass?
python test_auth.py
```

---

**Quick Help**: Run `./setup_postgres.sh` for automated setup or `python db_manage.py` for database management.
