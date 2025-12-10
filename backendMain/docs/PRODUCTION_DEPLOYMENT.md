# Production Deployment Guide - AeroOps Backend

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Setup](#database-setup)
3. [Environment Configuration](#environment-configuration)
4. [Application Deployment](#application-deployment)
5. [Performance Optimization](#performance-optimization)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Security Hardening](#security-hardening)
8. [Backup & Recovery](#backup--recovery)

---

## Pre-Deployment Checklist

### System Requirements
- Python 3.10 or higher
- PostgreSQL 14 or higher
- Redis 6 or higher (for caching and rate limiting)
- Nginx (reverse proxy)
- Supervisor or systemd (process management)
- 4GB+ RAM recommended
- 50GB+ disk space

### Pre-Deployment Steps
```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install system dependencies
sudo apt install -y python3-pip python3-dev python3-venv \
    postgresql postgresql-contrib redis-server nginx \
    supervisor git curl wget

# 3. Install Node.js (for playwright)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## Database Setup

### 1. Create PostgreSQL Database and User
```sql
sudo -u postgres psql

CREATE DATABASE aeroops_prod;
CREATE USER aeroops_user WITH PASSWORD 'your-secure-password';

-- Grant privileges
ALTER ROLE aeroops_user SET client_encoding TO 'utf8';
ALTER ROLE aeroops_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE aeroops_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE aeroops_prod TO aeroops_user;

-- Exit
\q
```

### 2. Configure PostgreSQL for Production
Edit `/etc/postgresql/14/main/postgresql.conf`:
```ini
# Performance tuning
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 4MB
min_wal_size = 1GB
max_wal_size = 4GB
max_connections = 100

# Connection pooling
listen_addresses = '*'
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

---

## Environment Configuration

### 1. Create Production Environment File
```bash
cd /opt/aeroops/backend
cp .env.production.template .env

# Edit .env with production values
nano .env
```

### 2. Key Configuration Values
```env
# CRITICAL: Change these!
SECRET_KEY=generate-a-long-random-secret-key-here
DB_PASSWORD=your-secure-database-password

# Production settings
DEBUG=0
ALLOWED_HOSTS=api.yourdomain.com,yourdomain.com

# Database
DB_USE_POSTGRES=1
DB_NAME=aeroops_prod
DB_USER=aeroops_user
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECURE_SSL_REDIRECT=1
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ADMIN_EMAIL=admin@yourdomain.com
```

---

## Application Deployment

### 1. Clone and Setup Application
```bash
# Create application directory
sudo mkdir -p /opt/aeroops
sudo chown $USER:$USER /opt/aeroops
cd /opt/aeroops

# Clone repository
git clone https://github.com/your-repo/aeroScrap_backend.git backend
cd backend/backendMain

# Create virtual environment
python3 -m venv .venv
source .venv/bin/python
```

### 2. Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install Python packages
pip install -r requirements.txt

# Install additional production packages
pip install gunicorn psycopg2-binary python-dotenv redis django-redis

# Install playwright browsers
playwright install chromium
```

### 3. Run Migrations
```bash
# Apply all migrations
python manage.py migrate

# Create company statistics
python manage.py update_company_stats --create-missing

# Create superuser
python manage.py createsuperuser
```

### 4. Collect Static Files
```bash
python manage.py collectstatic --noinput
```

---

## Performance Optimization

### 1. Database Optimization

Run these commands after initial data load:
```bash
# Update company statistics
python manage.py update_company_stats

# Analyze database
sudo -u postgres psql aeroops_prod -c "ANALYZE;"

# Vacuum database
sudo -u postgres psql aeroops_prod -c "VACUUM ANALYZE;"
```

### 2. Create Database Indexes
The migrations include optimized indexes, but verify:
```sql
-- Check indexes
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('jobs', 'company_mapping', 'crawl_log')
ORDER BY tablename, indexname;
```

### 3. Redis Configuration
Edit `/etc/redis/redis.conf`:
```ini
maxmemory 512mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

Restart Redis:
```bash
sudo systemctl restart redis
```

---

## Application Server Setup

### 1. Gunicorn Configuration
Create `/opt/aeroops/backend/gunicorn_config.py`:
```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 120
keepalive = 5
errorlog = "/var/log/aeroops/gunicorn_error.log"
accesslog = "/var/log/aeroops/gunicorn_access.log"
loglevel = "info"
```

### 2. Supervisor Configuration
Create `/etc/supervisor/conf.d/aeroops.conf`:
```ini
[program:aeroops]
command=/opt/aeroops/backend/backendMain/.venv/bin/gunicorn backendMain.wsgi:application -c /opt/aeroops/backend/gunicorn_config.py
directory=/opt/aeroops/backend/backendMain
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/aeroops/supervisor.log
environment=PATH="/opt/aeroops/backend/backendMain/.venv/bin"
```

Enable and start:
```bash
sudo mkdir -p /var/log/aeroops
sudo chown www-data:www-data /var/log/aeroops
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start aeroops
```

### 3. Nginx Configuration
Create `/etc/nginx/sites-available/aeroops`:
```nginx
upstream aeroops_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;
    
    # SSL Configuration (use Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static/ {
        alias /var/www/aeroops/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/aeroops/media/;
        expires 7d;
    }
    
    # Health check
    location /health/ {
        proxy_pass http://aeroops_backend;
        access_log off;
    }
    
    # API endpoints
    location / {
        proxy_pass http://aeroops_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
    }
    
    # Rate limit zone
    limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;
    
    client_max_body_size 10M;
    access_log /var/log/nginx/aeroops_access.log;
    error_log /var/log/nginx/aeroops_error.log;
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/aeroops /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Security Hardening

### 1. SSL/TLS with Let's Encrypt
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.yourdomain.com
sudo systemctl reload nginx
```

### 2. Firewall Configuration
```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 3. Secure File Permissions
```bash
sudo chown -R www-data:www-data /opt/aeroops/backend
sudo chmod -R 750 /opt/aeroops/backend
sudo chmod 640 /opt/aeroops/backend/backendMain/.env
```

### 4. Database Security
```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/14/main/pg_hba.conf

# Change to use md5 authentication
# local   all             all                                     md5
# host    all             all             127.0.0.1/32            md5
```

---

## Monitoring & Maintenance

### 1. Setup Log Rotation
Create `/etc/logrotate.d/aeroops`:
```
/var/log/aeroops/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        supervisorctl restart aeroops > /dev/null
    endscript
}
```

### 2. Scheduled Tasks (Cron)
```bash
sudo crontab -e

# Update company statistics daily at 2 AM
0 2 * * * /opt/aeroops/backend/backendMain/.venv/bin/python /opt/aeroops/backend/backendMain/manage.py update_company_stats

# Run daily scraper at 3 AM
0 3 * * * /opt/aeroops/backend/backendMain/.venv/bin/python /opt/aeroops/backend/scrapers/daily_scraper_to_db.py

# Database maintenance weekly
0 4 * * 0 sudo -u postgres psql aeroops_prod -c "VACUUM ANALYZE;"
```

### 3. Monitoring Script
Create `/opt/aeroops/scripts/monitor.sh`:
```bash
#!/bin/bash

# Check if application is running
if ! supervisorctl status aeroops | grep -q RUNNING; then
    echo "Application is down!"
    supervisorctl restart aeroops
fi

# Check database connections
DB_CONNECTIONS=$(sudo -u postgres psql -t -c "SELECT count(*) FROM pg_stat_activity WHERE datname='aeroops_prod';")
if [ $DB_CONNECTIONS -gt 80 ]; then
    echo "High database connections: $DB_CONNECTIONS"
fi

# Check disk space
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DB_USAGE -gt 80 ]; then
    echo "Disk usage high: ${DISK_USAGE}%"
fi
```

---

## Backup & Recovery

### 1. Database Backup Script
Create `/opt/aeroops/scripts/backup_db.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/opt/aeroops/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aeroops_$DATE.sql.gz"

mkdir -p $BACKUP_DIR

# Backup database
sudo -u postgres pg_dump aeroops_prod | gzip > $BACKUP_FILE

# Keep only last 7 days
find $BACKUP_DIR -name "aeroops_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_FILE"
```

### 2. Automated Backups
```bash
chmod +x /opt/aeroops/scripts/backup_db.sh

# Add to crontab
0 1 * * * /opt/aeroops/scripts/backup_db.sh
```

### 3. Restore Database
```bash
# Stop application
sudo supervisorctl stop aeroops

# Drop and recreate database
sudo -u postgres psql -c "DROP DATABASE aeroops_prod;"
sudo -u postgres psql -c "CREATE DATABASE aeroops_prod OWNER aeroops_user;"

# Restore backup
gunzip < /opt/aeroops/backups/aeroops_20250121_010000.sql.gz | \
    sudo -u postgres psql aeroops_prod

# Restart application
sudo supervisorctl start aeroops
```

---

## Testing Production Setup

### 1. Health Check
```bash
curl https://api.yourdomain.com/health/
```

### 2. Test Authentication
```bash
curl -X POST https://api.yourdomain.com/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"your-password"}'
```

### 3. Load Testing
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test with 100 requests, 10 concurrent
ab -n 100 -c 10 https://api.yourdomain.com/api/jobs/
```

---

## Troubleshooting

### Application Won't Start
```bash
# Check logs
sudo tail -f /var/log/aeroops/supervisor.log
sudo tail -f /var/log/aeroops/gunicorn_error.log

# Check supervisor status
sudo supervisorctl status aeroops

# Restart
sudo supervisorctl restart aeroops
```

### Database Connection Issues
```bash
# Test connection
sudo -u postgres psql aeroops_prod

# Check PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-14-main.log
```

### High Memory Usage
```bash
# Check processes
top -o %MEM
ps aux | grep gunicorn

# Reduce gunicorn workers if needed
# Edit gunicorn_config.py and reduce workers
```

---

## Performance Benchmarks

### Expected Performance
- API response time: <200ms (p95)
- Database query time: <50ms (p95)
- Concurrent users: 100+
- Requests per second: 500+

### Optimization Tips
1. Enable query caching for frequently accessed data
2. Use database connection pooling
3. Implement CDN for static files
4. Enable Nginx caching for cacheable endpoints
5. Monitor slow queries and add indexes as needed

---

## Support & Resources

- Documentation: `/documents/`
- API Reference: `/documents/API_REFERENCE.md`
- Troubleshooting: `/documents/RBAC_TROUBLESHOOTING.md`
- Logs: `/var/log/aeroops/`

---

**Deployment Checklist:**
- [ ] PostgreSQL configured and secured
- [ ] Redis installed and running
- [ ] Environment variables set
- [ ] Migrations applied
- [ ] Static files collected
- [ ] Gunicorn configured
- [ ] Supervisor configured
- [ ] Nginx configured with SSL
- [ ] Firewall configured
- [ ] Backups scheduled
- [ ] Monitoring setup
- [ ] Load tested
- [ ] Health checks passing

---

Last Updated: November 21, 2025
