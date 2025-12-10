# Logging Guide

Complete guide to the logging system in AeroOps Backend.

## Overview

The application uses a comprehensive, separated logging system with different log files for different components:

```
logs/
├── django.log                    # Main Django application logs
├── django_errors.log             # Django errors only
├── jobs.log                      # Jobs app logs
├── resumes.log                   # Resumes app logs
├── scraper_manager.log           # Scraper orchestration logs
└── scrapers/                     # Individual scraper logs
    ├── aviation.log              # Aviation Job Search scraper
    ├── airindia.log              # Air India scraper
    ├── goose.log                 # Goose Recruitment scraper
    ├── linkedin.log              # LinkedIn scraper
    └── errors.log                # All scraper errors consolidated
```

## Log Levels

- **DEBUG**: Detailed information for diagnosing problems (only in scraper logs)
- **INFO**: General informational messages
- **WARNING**: Warning messages for potentially harmful situations
- **ERROR**: Error messages for serious problems
- **CRITICAL**: Critical errors that may cause the application to fail

## Log Formats

### Standard Format (Django & Apps)
```
[LEVEL] YYYY-MM-DD HH:MM:SS [logger_name] module.function:line - message
```

Example:
```
[INFO] 2025-11-24 12:30:45 [jobs] api.list_jobs:89 - Listing jobs with filters
```

### Scraper Format
```
[LEVEL] YYYY-MM-DD HH:MM:SS [SCRAPER:scraper_name] message
```

Example:
```
[INFO] 2025-11-24 12:30:45 [SCRAPER:aviation] === SCRAPER EXECUTION START === Job ID: 123
```

## Log Configuration

### Django Main Application
- **File**: `logs/django.log`
- **Max Size**: 10 MB
- **Backups**: 5
- **Level**: INFO
- **Contains**: All Django core logs (requests, middleware, etc.)

### Django Errors
- **File**: `logs/django_errors.log`
- **Max Size**: 10 MB
- **Backups**: 5
- **Level**: ERROR
- **Contains**: Only Django errors and exceptions

### Jobs App
- **File**: `logs/jobs.log`
- **Max Size**: 10 MB
- **Backups**: 5
- **Level**: INFO
- **Contains**: Job listing, ingestion, search operations

### Resumes App
- **File**: `logs/resumes.log`
- **Max Size**: 10 MB
- **Backups**: 5
- **Level**: INFO
- **Contains**: Resume parsing, upload, matching operations

### Scraper Manager
- **File**: `logs/scraper_manager.log`
- **Max Size**: 20 MB
- **Backups**: 10
- **Level**: INFO
- **Contains**: Scraper orchestration, job management, API operations

### Individual Scrapers
Each scraper has its own dedicated log file:

- **Files**: `logs/scrapers/{scraper_name}.log`
- **Max Size**: 15 MB per file
- **Backups**: 7
- **Level**: DEBUG
- **Contains**: Detailed scraper execution logs

### Scraper Errors (Consolidated)
- **File**: `logs/scrapers/errors.log`
- **Max Size**: 10 MB
- **Backups**: 10
- **Level**: ERROR
- **Contains**: All scraper errors from all scrapers

## Using Logging in Code

### In Django Apps

```python
import logging

# Get logger for your app
logger = logging.getLogger('jobs')  # or 'resumes', 'scraper_manager'

# Log messages
logger.debug('Debugging information')
logger.info('Informational message')
logger.warning('Warning message')
logger.error('Error message')
logger.critical('Critical error')

# Log with exception traceback
try:
    # some code
    pass
except Exception as e:
    logger.error(f'Operation failed: {e}', exc_info=True)
```

### In Scrapers

Scraper logs go to both the scraper-specific log and the consolidated error log:

```python
import logging

# Get scraper-specific logger
logger = logging.getLogger('scraper_manager.aviation')  # or airindia, goose, linkedin

# Log scraper execution
logger.info('Starting to scrape page 1')
logger.debug(f'Found {len(jobs)} jobs on page')
logger.warning('Rate limit approaching')
logger.error('Failed to parse job listing', exc_info=True)
```

### In Scraper Service

The scraper service automatically logs execution details:

```python
from scraper_manager.services import ScraperService

# Logs are automatically generated for:
# - Scraper start (with parameters)
# - Scraper completion (with statistics)
# - Scraper failures (with errors)
```

## Viewing Logs

### Tail Recent Logs
```bash
# Django main log
tail -f logs/django.log

# Scraper manager
tail -f logs/scraper_manager.log

# Specific scraper
tail -f logs/scrapers/aviation.log

# All scraper errors
tail -f logs/scrapers/errors.log
```

### Search Logs
```bash
# Search for errors in django logs
grep ERROR logs/django.log

# Search for specific scraper job
grep "Job ID: 123" logs/scrapers/*.log

# Search for specific error
grep -r "ConnectionError" logs/
```

### View Last N Lines
```bash
# Last 100 lines of scraper manager log
tail -n 100 logs/scraper_manager.log

# Last 50 errors
tail -n 50 logs/scrapers/errors.log
```

## Log Rotation

Logs automatically rotate when they reach their maximum size:

- Old logs are renamed with a number suffix (`.log.1`, `.log.2`, etc.)
- Oldest logs are deleted when backup count is exceeded
- No manual intervention required

Example:
```
aviation.log          # Current log
aviation.log.1        # Previous rotation
aviation.log.2        # 2 rotations ago
...
aviation.log.7        # Oldest (will be deleted on next rotation)
```

## Monitoring Logs

### Check Log Sizes
```bash
# All log sizes
du -h logs/*.log logs/scrapers/*.log

# Total logs size
du -sh logs/
```

### Count Log Entries
```bash
# Count lines in django log
wc -l logs/django.log

# Count errors
grep -c ERROR logs/django_errors.log
```

### Watch for Errors
```bash
# Monitor all scraper errors in real-time
tail -f logs/scrapers/errors.log

# Monitor specific scraper
tail -f logs/scrapers/aviation.log | grep ERROR
```

## Production Best Practices

### 1. Log Level Management
- **Development**: DEBUG level for scrapers, INFO for apps
- **Production**: INFO level for all (DEBUG only for troubleshooting)

### 2. Log Retention
- Keep logs for at least 30 days
- Archive old logs monthly
- Consider external log aggregation (ELK, Splunk, etc.)

### 3. Monitoring
Set up alerts for:
- High error rates in `django_errors.log`
- Scraper failures in `scrapers/errors.log`
- Disk space (logs directory)

### 4. Performance
- Logs don't block application execution
- Async handlers can be used for high-volume logs
- Consider log sampling for very verbose operations

## Troubleshooting

### Logs Not Being Created
```bash
# Check directory permissions
ls -la logs/
ls -la logs/scrapers/

# Create directories if missing
mkdir -p logs/scrapers

# Check settings.py LOGGING configuration
python manage.py check
```

### Logs Too Large
```bash
# Manually rotate logs
for log in logs/*.log; do
    mv "$log" "$log.1"
done

# Or reduce max size in settings.py:
# 'maxBytes': 1024 * 1024 * 5,  # 5MB instead of 10MB
```

### Missing Log Entries
- Check log level configuration
- Verify logger name matches settings
- Ensure logger propagate is set correctly

## Configuration Reference

Location: `backendMain/settings.py`

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': { ... },
    'handlers': { ... },
    'loggers': { ... },
}
```

To modify logging configuration:
1. Edit `settings.py`
2. Restart Django application
3. Check logs appear correctly

## Examples

### Example: Scraper Execution Log

**File**: `logs/scrapers/aviation.log`
```
[INFO] 2025-11-24 12:30:45 [SCRAPER:aviation] === SCRAPER EXECUTION START === Job ID: 123
[INFO] 2025-11-24 12:30:45 [SCRAPER:aviation] Parameters: max_pages=5, max_jobs=100
[DEBUG] 2025-11-24 12:30:46 [SCRAPER:aviation] Fetching page 1
[DEBUG] 2025-11-24 12:30:47 [SCRAPER:aviation] Found 20 jobs on page 1
[DEBUG] 2025-11-24 12:30:48 [SCRAPER:aviation] Fetching page 2
[INFO] 2025-11-24 12:31:15 [SCRAPER:aviation] === SCRAPER EXECUTION END === Job ID: 123
[INFO] 2025-11-24 12:31:15 [SCRAPER:aviation] Results: 85 jobs found, 12 new, 5 updated, 68 duplicates
[INFO] 2025-11-24 12:31:15 [SCRAPER:aviation] Execution time: 30.45s
```

### Example: Error Log

**File**: `logs/scrapers/errors.log`
```
[ERROR] 2025-11-24 12:45:30 [scraper_manager.linkedin] === SCRAPER EXECUTION FAILED === Job ID: 124
[ERROR] 2025-11-24 12:45:30 [scraper_manager.linkedin] Error: Connection timeout
Traceback (most recent call last):
  File "linkedin_scraper.py", line 45, in scrape
    response = requests.get(url, timeout=10)
  ...
requests.exceptions.Timeout: Connection timeout
```

## Quick Reference

| What | Where | Command |
|------|-------|---------|
| Django logs | `logs/django.log` | `tail -f logs/django.log` |
| Django errors | `logs/django_errors.log` | `tail -f logs/django_errors.log` |
| Scraper manager | `logs/scraper_manager.log` | `tail -f logs/scraper_manager.log` |
| Aviation scraper | `logs/scrapers/aviation.log` | `tail -f logs/scrapers/aviation.log` |
| All scraper errors | `logs/scrapers/errors.log` | `tail -f logs/scrapers/errors.log` |
| Search errors | All files | `grep -r ERROR logs/` |
| Watch specific job | Scraper logs | `grep "Job ID: 123" logs/scrapers/*.log` |

---

For more information, see Django's [logging documentation](https://docs.djangoproject.com/en/stable/topics/logging/).
