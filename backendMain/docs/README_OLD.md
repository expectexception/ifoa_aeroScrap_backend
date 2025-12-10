# AeroScrap Backend

**Complete Django-based backend for aviation job scraping, resume analysis, and data management.**

## 🚀 Overview

AeroScrap Backend is a comprehensive Django application that combines:
- **Job Scraping**: Automated collection of aviation jobs from multiple sources
- **Resume Analysis**: Parse and analyze resumes with structured data extraction
- **REST API**: Django Ninja-powered API for all operations
- **Automated Scheduling**: Daily scraper runs with deduplication

## 📁 Project Structure

```
backendMain/
├── backendMain/         # Django project settings and URLs
├── jobs/                # Job scraping and management app
├── resumes/             # Resume parsing and analysis app
├── scrapers/            # Web scrapers and automation scripts
│   ├── daily_scraper_to_db.py      # Main scheduler script
│   ├── aviationjobsearchScrap.py   # Aviation job search scraper
│   ├── airIndiaScrap.py            # Air India careers scraper
│   ├── gooseScrap.py               # Goose Recruitment scraper
│   └── linkdinScraperRT.py         # LinkedIn scraper
├── scripts/             # Utility scripts
├── manage.py            # Django management
├── requirements.txt     # Python dependencies
└── .env                 # Environment configuration (create from .env.example)
```

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- PostgreSQL (optional, SQLite by default)
- Git

### Quick Start

1. **Clone and setup virtual environment:**
```bash
cd backendMain
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers (for scrapers):**
```bash
playwright install chromium
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings (API keys, database, etc.)
```

5. **Run database migrations:**
```bash
python manage.py migrate
```

6. **Create admin user:**
```bash
python manage.py createsuperuser
```

7. **Start the server:**
```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/api/`

## 📊 Database Configuration

### SQLite (Default - No setup required)
```bash
# In .env
DB_USE_POSTGRES=0
```

### PostgreSQL (Production recommended)
```bash
# In .env
DB_USE_POSTGRES=1
DB_NAME=aero_db
DB_USER=aero_user
DB_PASSWORD=your_secure_password
DB_HOST=127.0.0.1
DB_PORT=5432
```

## 🤖 Automated Job Scraping

### Setup Daily Scraper

The system can automatically scrape jobs daily from multiple sources:

1. **Interactive setup (recommended):**
```bash
cd scrapers
bash setup_scheduler.sh
```

2. **Manual cron setup:**
```bash
crontab -e
# Add: 0 2 * * * cd /path/to/backendMain && /path/to/.venv/bin/python scrapers/daily_scraper_to_db.py
```

3. **Or run manually:**
```bash
python scrapers/daily_scraper_to_db.py
```

### Scraper Sources
- **Aviation Job Search**: ~75 jobs from aviationjobsearch.com
- **Air India Careers**: ~28 jobs from careers.airindia.com
- **Goose Recruitment**: ~12 jobs from goose-recruitment.com
- **LinkedIn**: Manual configuration required

### Features
- ✅ Automatic deduplication (URL + fuzzy title matching)
- ✅ Direct database integration
- ✅ Transaction safety (individual job isolation)
- ✅ Comprehensive logging in `scrapers/logs/`
- ✅ Edge case handling (empty fields, timeouts)

## 📡 API Endpoints

### Jobs API (`/api/jobs/`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | List jobs with filters | No |
| GET | `/id/{job_id}` | Get single job | No |
| POST | `/ingest` | Ingest single job | Yes |
| POST | `/bulk_ingest` | Bulk ingest jobs | Yes |
| PATCH | `/{job_id}` | Update job | Yes |
| DELETE | `/{job_id}` | Delete job | Yes |
| GET | `/search?q=query` | Search jobs | No |
| GET | `/stats` | Job statistics | No |
| GET | `/alerts/senior` | Senior role alerts | No |
| GET | `/export/daily.csv` | Export CSV | No |
| GET | `/health` | Health check | No |

### Resumes API (`/api/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload resume for parsing |
| GET | `/resumes` | List all resumes |
| GET | `/resume/{id}` | Get specific resume |

### Authentication

Protected endpoints require Bearer token:
```bash
curl -H "Authorization: Bearer your-api-key-here" \
  http://localhost:8000/api/jobs/ingest
```

Set `ADMIN_API_KEY` in `.env` file.

## 🧪 Testing

### Test scrapers:
```bash
cd scrapers
python test_scraper.py  # Interactive testing with DB stats
python quick_test.py    # Validate edge cases
```

### Run Django tests:
```bash
python manage.py test
```

## 📝 Key Features

### Jobs App
- **Models**: Job, CompanyMapping, CrawlLog
- **Auto-classification**: Operation type detection (Airline, MRO, Airport, etc.)
- **Deduplication**: Smart matching to prevent duplicates
- **CSV Export**: Daily job reports
- **Analytics**: Statistics and senior role alerts

### Resumes App
- **Resume parsing**: Extract structured data from resumes
- **JSON storage**: Backup to ResumeDataStore.json
- **Format support**: PDF, DOCX, TXT

### Scrapers
- **Multi-source**: 4+ aviation job sources
- **Robust**: Handles timeouts, retries, and edge cases
- **Logging**: Detailed logs with rotation
- **Scheduling**: Multiple options (cron, systemd, Python)

## 🔧 Configuration

### Environment Variables

Key settings in `.env`:
```bash
SECRET_KEY=your-django-secret-key
DEBUG=1
ADMIN_API_KEY=your-api-key
DB_USE_POSTGRES=0
TIME_ZONE=UTC
```

See `.env.example` for all options.

## 📚 Documentation

- **[PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)** - High-level architecture and data flow
- **[API_DOCUMENTATION.txt](API_DOCUMENTATION.txt)** - Detailed API reference
- **[scrapers/README_DAILY_SCRAPER.md](scrapers/README_DAILY_SCRAPER.md)** - Scraper documentation
- **[scrapers/TESTING_SUMMARY.md](scrapers/TESTING_SUMMARY.md)** - Testing results and fixes

## 🐛 Troubleshooting

### Common Issues

**Import errors:**
```bash
pip install -r requirements.txt
playwright install chromium
```

**Database locked:**
```bash
# Stop all Python processes, then:
python manage.py migrate --run-syncdb
```

**Scraper timeouts:**
- Check network connection
- Review logs in `scrapers/logs/`
- Jobs will be collected on next run

**API authentication fails:**
- Verify `ADMIN_API_KEY` in `.env`
- Check Authorization header format

## 🚀 Production Deployment

1. **Security:**
   - Generate new `SECRET_KEY`
   - Set `DEBUG=0`
   - Configure `ALLOWED_HOSTS`
   - Use PostgreSQL database

2. **Server:**
   - Use gunicorn/uWSGI
   - Set up nginx reverse proxy
   - Enable HTTPS

3. **Automation:**
   - Set up systemd service for scrapers
   - Configure log rotation
   - Set up monitoring (Sentry)

## 📄 License

This project is proprietary software for AeroOps Intel.

## 🤝 Contributing

For questions or issues, contact the development team.

---

**Last Updated**: November 2025  
**Version**: 1.0.0
