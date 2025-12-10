# AeroScrap Backend - Quick Start Guide

**Get up and running in 5 minutes!**

---

## 🚀 Super Quick Start (Automated)

```bash
# Run the automated setup script
bash quick_setup.sh

# Create admin user
python manage.py createsuperuser

# Start the server
python manage.py runserver
```

**That's it!** The API is now running at http://127.0.0.1:8000/api/

---

## 📋 Manual Setup (Step by Step)

### 1. Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/Mac
# OR
.venv\Scripts\activate     # Windows
```

### 2. Install Dependencies

```bash
# Install Python packages
pip install -r requirements.txt

# Install Playwright browsers for scrapers
playwright install chromium
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env  # or use any text editor
```

**Minimum required settings in `.env`:**
```bash
SECRET_KEY='your-secret-key-here'
DEBUG=1
ADMIN_API_KEY='your-api-key-here'
DB_USE_POSTGRES=0  # Use SQLite for quick start
```

### 4. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create admin user
python manage.py createsuperuser
```

### 5. Start the Server

```bash
python manage.py runserver
```

**Access points:**
- API: http://127.0.0.1:8000/api/
- Admin: http://127.0.0.1:8000/admin/
- Health Check: http://127.0.0.1:8000/api/jobs/health

---

## 🤖 Setup Automated Scraping

### Option 1: Interactive Setup (Recommended)

```bash
cd scrapers
bash setup_scheduler.sh
```

Follow the prompts to configure daily scraping at your preferred time.

### Option 2: Manual Test Run

```bash
# Test the scraper
python scrapers/test_scraper.py

# Or run manually
python scrapers/daily_scraper_to_db.py
```

---

## 🧪 Test Your Setup

### 1. Test API Health

```bash
curl http://localhost:8000/api/jobs/health
# Should return: {"ok": true, "db": "ok"}
```

### 2. Test Job Listing

```bash
curl http://localhost:8000/api/jobs/
# Should return: [] (empty list initially)
```

### 3. Test Authenticated Endpoint

```bash
curl -H "Authorization: Bearer your-api-key-here" \
     http://localhost:8000/api/jobs/stats
# Should return: {"total": 0, ...}
```

### 4. Run Scrapers

```bash
cd scrapers
python test_scraper.py
```

This will:
- Show current database state
- Run all scrapers
- Display results and statistics

---

## 📊 Quick Data Import

### Import Jobs via API

```bash
# Single job
curl -X POST http://localhost:8000/api/jobs/ingest \
  -H "Authorization: Bearer your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Aircraft Mechanic",
    "company": "Delta Airlines",
    "url": "https://example.com/job/123",
    "description": "Job description here",
    "country_code": "US",
    "operation_type": "Airline"
  }'
```

### Run Scrapers to Collect Real Jobs

```bash
python scrapers/daily_scraper_to_db.py
```

This will collect ~115 jobs from:
- Aviation Job Search (75 jobs)
- Air India Careers (28 jobs)
- Goose Recruitment (12 jobs)

---

## 🎯 Common Tasks

### View Jobs in Database

```bash
python manage.py shell

>>> from jobs.models import Job
>>> Job.objects.count()
>>> Job.objects.all()[:5]
>>> exit()
```

### Export Jobs to CSV

```bash
# Today's jobs
curl http://localhost:8000/api/jobs/export/daily.csv > jobs.csv

# Specific date
curl "http://localhost:8000/api/jobs/export/daily.csv?date=2025-11-20" > jobs.csv
```

### View Logs

```bash
# Django logs
tail -f logs/django.log

# Scraper logs
tail -f scrapers/logs/daily_scraper_*.log
```

### Clear Database (Start Fresh)

```bash
# Delete all jobs
python manage.py shell -c "from jobs.models import Job; Job.objects.all().delete()"

# Or reset entire database
rm db.sqlite3
python manage.py migrate
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use different port
python manage.py runserver 8080
```

### Import Errors

```bash
# Reinstall dependencies
pip install -r requirements.txt
playwright install chromium
```

### Database Locked

```bash
# Stop all Python processes
pkill -f python

# Run migrations again
python manage.py migrate
```

### Scraper Fails

```bash
# Check logs
cat scrapers/logs/daily_scraper_*.log

# Test individual scraper
cd scrapers
python -c "from aviationjobsearchScrap import onCallWorker; print(len(onCallWorker()))"
```

---

## 📚 Next Steps

### Explore Documentation

1. **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - Understand the architecture
2. **[API_DOCUMENTATION.txt](API_DOCUMENTATION.txt)** - Learn all endpoints
3. **[scrapers/README_DAILY_SCRAPER.md](scrapers/README_DAILY_SCRAPER.md)** - Deep dive into scrapers

### Customize Your Setup

- Add more job sources (create new scrapers)
- Configure email notifications
- Set up PostgreSQL for production
- Deploy to cloud (Heroku, AWS, etc.)

### Monitor Your System

```bash
# Check scraper runs
python manage.py shell -c "from jobs.models import CrawlLog; CrawlLog.objects.all()"

# View statistics
curl http://localhost:8000/api/jobs/stats

# Senior role alerts
curl http://localhost:8000/api/jobs/alerts/senior
```

---

## 🎉 You're Ready!

Your AeroScrap Backend is now fully operational. You can:

✅ Accept job data via REST API  
✅ Automatically scrape jobs from multiple sources  
✅ Deduplicate and classify jobs  
✅ Export data in CSV format  
✅ Parse and store resumes  
✅ Access admin panel for manual management  

**Happy scraping!** 🚀

---

**Need Help?**
- Check logs in `logs/` and `scrapers/logs/`
- Review documentation in project root
- Contact development team

**Last Updated**: November 2025
