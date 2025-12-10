# AeroOps Scraper Scheduling System

This document explains how to set up and manage the automated scraper scheduling system for AeroOps.

## Overview

The system runs all enabled scrapers **every 3 hours** with comprehensive logging. It uses both Celery Beat (primary) and cron jobs (backup) for redundancy.

## Features

- **Frequency**: Every 3 hours (8 times per day)
- **Comprehensive Logging**: All output logged to rotating files
- **Redundancy**: Both Celery Beat and cron job scheduling
- **Monitoring**: Detailed statistics and error reporting
- **Configurable**: Per-scraper settings via Django admin

## Quick Start

### 1. Set up Celery Schedules (Primary Method)

```bash
cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain
python manage.py setup_schedules
```

This creates Celery Beat tasks that run every 3 hours.

### 2. Start Celery Services

```bash
# Terminal 1: Celery Beat (scheduler)
celery -A backendMain beat -l info

# Terminal 2: Celery Worker (executor)
celery -A backendMain worker -l info
```

### 3. Set up Cron Backup (Optional)

```bash
./setup_scraper_cron.sh
```

This adds a cron job as backup to Celery.

## Manual Testing

### Run All Scrapers with Logging

```bash
python manage.py run_all_scrapers_with_logging --log-level INFO
```

### Run Specific Scrapers

```bash
python manage.py run_all_scrapers_with_logging --scrapers aviationjobsearch linkedin
```

### Run with Debug Logging

```bash
python manage.py run_all_scrapers_with_logging --log-level DEBUG
```

### Run Single Scraper

```bash
python manage.py run_scraper aviationjobsearch --max-jobs 10
```

## Logging

All logs are stored in `scraper_manager/logs/`:

- `scrapers.log` - Main scraper activity
- `scraper_all.log` - All logging activity
- `scraper_errors.log` - Errors only
- `database.log` - Database operations
- `scraper_run_YYYYMMDD_HHMMSS.log` - Individual run logs

### View Recent Logs

```bash
# Latest scraper run
tail -f scraper_manager/logs/scraper_run_$(ls -t scraper_manager/logs/scraper_run_*.log | head -1)

# All scraper activity
tail -f scraper_manager/logs/scrapers.log

# Errors only
tail -f scraper_manager/logs/scraper_errors.log
```

## Schedule Details

- **Runs at**: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00 UTC
- **Duration**: Typically 5-15 minutes depending on scraper load
- **Timezone**: UTC (coordinated universal time)

## Monitoring

### Check Active Schedules

```bash
# Celery Beat schedules
python manage.py shell -c "from django_celery_beat.models import PeriodicTask; [print(f'{t.name}: {t.enabled}') for t in PeriodicTask.objects.filter(name__startswith='scraper_')]"

# Cron jobs
crontab -l | grep scraper
```

### Check Recent Runs

```bash
# Last 10 scraper jobs
python manage.py shell -c "from scraper_manager.models import ScraperJob; [print(f'{j.scraper_name}: {j.status} at {j.started_at}') for j in ScraperJob.objects.order_by('-started_at')[:10]]"
```

## Troubleshooting

### Celery Not Running

```bash
# Check if Celery processes are running
ps aux | grep celery

# Restart Celery Beat
celery -A backendMain beat -l info --pidfile=/tmp/celerybeat.pid

# Restart Celery Worker
celery -A backendMain worker -l info --pidfile=/tmp/celeryworker.pid
```

### Cron Job Issues

```bash
# Check cron logs
grep CRON /var/log/syslog

# Test manual run
./run_scrapers.sh

# Edit cron jobs
crontab -e
```

### Database Issues

```bash
# Check database connectivity
python manage.py dbshell

# Clear stuck jobs
python manage.py shell -c "from scraper_manager.models import ScraperJob; ScraperJob.objects.filter(status='running').update(status='failed')"
```

## Configuration

### Enable/Disable Scrapers

Via Django Admin (`/admin/`):
1. Go to "Scraper Manager" > "Scraper configs"
2. Check/uncheck "Is enabled" for each scraper
3. Run `python manage.py setup_schedules` to update

### Adjust Schedule Frequency

Edit `backendMain/celery.py`:
```python
app.conf.beat_schedule = {
    'run-all-scrapers-every-3-hours': {
        'task': 'scraper_manager.run_all_scrapers',
        'schedule': crontab(minute=0, hour='*/3'),  # Change */3 to */6 for 6-hour intervals
    },
}
```

## File Structure

```
backendMain/
├── run_scrapers.sh              # Manual/cron runner script
├── setup_scraper_cron.sh        # Cron job setup script
├── scraper_manager/
│   ├── logs/                    # All log files
│   │   ├── scrapers.log
│   │   ├── scraper_all.log
│   │   ├── scraper_errors.log
│   │   ├── database.log
│   │   └── scraper_run_*.log
│   ├── management/commands/
│   │   ├── run_all_scrapers_with_logging.py
│   │   └── setup_schedules.py
│   └── logging_config.py
└── backendMain/
    └── celery.py                # Celery Beat schedules
```

## Performance Notes

- **Memory**: Each scraper run uses ~200-500MB RAM
- **Network**: Heavy use of proxies and stealth techniques
- **Database**: ~100-500 new jobs per run typically
- **Duration**: 5-15 minutes for full scraper suite

## Support

For issues:
1. Check logs in `scraper_manager/logs/`
2. Verify Celery services are running
3. Test individual scrapers manually
4. Check database connectivity