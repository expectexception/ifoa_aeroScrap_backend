# 🚀 Scraper Manager - Quick Reference Guide

## Quick Commands

### Run Scrapers
```bash
# Single scraper
python manage.py run_scraper signature --max-jobs 50

# All scrapers
python manage.py run_scraper all

# List available
python manage.py run_scraper --list
```

### View Logs
```bash
# All logs
tail -f logs/scraper_all.log

# Errors only
tail -f logs/scraper_errors.log

# Scraper activity
tail -f logs/scrapers.log
```

### Quick Test
```bash
python test_quick_verify.py
```

---

## API Endpoints

### Start Scraper
```bash
POST /api/scrapers/start/
{
  "scraper_name": "signature",
  "max_jobs": 50
}
```

### Check Status
```bash
GET /api/scrapers/status/{job_id}/
```

### Get Statistics
```bash
GET /api/scrapers/stats/
```

### View History
```bash
GET /api/scrapers/history/?scraper=signature&limit=20
```

---

## Key Features

✅ **No JSON Files** - All data in PostgreSQL  
✅ **URL Deduplication** - Never scrape same URL twice  
✅ **Comprehensive Logging** - All activity tracked  
✅ **Threading Support** - Non-blocking execution  
✅ **Admin Panel** - Enhanced with analytics  
✅ **Error Handling** - Robust and detailed  
✅ **Duplicate Prevention** - Can't run same scraper twice  
✅ **Auto Tracking** - Every URL, every run logged  

---

## Database Tables

- **ScraperJob** - Tracks each scraper run
- **ScrapedURL** - Tracks all URLs (deduplication)
- **ScraperConfig** - Scraper settings
- **Job** (jobs app) - Actual job data

---

## File Locations

- **Logs**: `scraper_manager/logs/`
- **Config**: `scraper_manager/config.py`
- **Scrapers**: `scraper_manager/scrapers/`
- **API**: `scraper_manager/api.py`
- **Admin**: `scraper_manager/admin.py`

---

## Common Tasks

### Enable/Disable Scraper
Admin → Scraper Manager → Scraper configs → Edit

### View Job History
Admin → Scraper Manager → Scraper jobs

### Trigger Manual Scrape
Admin → Scraper Manager → "Trigger Scraper" button

### Delete Old Jobs
Admin → Scraper jobs → Select → Actions → "Delete old jobs"

### Check Duplicates
ScrapedURL model shows `scrape_count` for each URL

---

## Troubleshooting

**Scraper not starting?**
→ Check `logs/scraper_errors.log`

**Database errors?**
→ Check `logs/database.log`

**Duplicate jobs?**
→ Not possible! Deduplication prevents this

**High memory?**
→ Reduce `max_jobs` in config

---

## Best Practices

1. Always check logs after running scrapers
2. Monitor duplicate counts in admin panel  
3. Clean old jobs periodically (>30 days)
4. Use `--max-jobs` to limit testing runs
5. Review statistics in analytics dashboard

---

## Monitoring

### Check Scraper Health
```bash
GET /api/scrapers/health/
```

### View Active Jobs
```bash
GET /api/scrapers/active/
```

### Get Recent Jobs
```bash
GET /api/scrapers/recent/?limit=50
```

---

## Documentation

- **Full docs**: `OPTIMIZATION_COMPLETE.md`
- **Summary**: `SCRAPER_OPTIMIZATION_SUMMARY.md`
- **This file**: `QUICK_REFERENCE.md`

---

## Emergency Commands

### Stop All Scrapers
Via admin panel → Cancel jobs action

### Clear Old Data
```python
# Django shell
from scraper_manager.models import ScraperJob
from django.utils import timezone
from datetime import timedelta
old = timezone.now() - timedelta(days=30)
ScraperJob.objects.filter(created_at__lt=old).delete()
```

### Reset Scraper
```python
# Django shell  
from scraper_manager.models import ScraperConfig
config = ScraperConfig.objects.get(scraper_name='signature')
config.total_runs = 0
config.save()
```

---

**Need help? Check the full documentation or logs!**
