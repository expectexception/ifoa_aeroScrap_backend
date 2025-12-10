# AeroScrap Backend - Project Overview

**High-Level Architecture and System Documentation**

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Core Components](#core-components)
3. [Data Flow](#data-flow)
4. [Database Schema](#database-schema)
5. [API Architecture](#api-architecture)
6. [Scraper System](#scraper-system)
7. [Integration Points](#integration-points)
8. [Security Model](#security-model)
9. [Deployment Strategy](#deployment-strategy)
10. [Future Enhancements](#future-enhancements)

---

## 🏗️ System Architecture

### Overview
AeroScrap Backend is a Django-based monolithic application with modular components for job scraping, resume analysis, and data management. The system follows a traditional Django app structure with clear separation of concerns.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Layer                            │
│  (Web Browser, Mobile App, External APIs, Cron Jobs)        │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                         │
│           Django Ninja REST API (/api/)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Jobs API    │  │ Resumes API  │  │  Admin API   │      │
│  │  /api/jobs/  │  │   /api/      │  │  /admin/     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
│  │   Jobs App     │  │  Resumes App   │  │  Auth System  │ │
│  │                │  │                │  │               │ │
│  │ • Models       │  │ • Models       │  │ • API Keys    │ │
│  │ • Dedup Logic  │  │ • Parser       │  │ • Bearer Auth │ │
│  │ • Classification│ │ • Extraction   │  │               │ │
│  └────────────────┘  └────────────────┘  └───────────────┘ │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Layer                                │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Django ORM (Object-Relational Mapping)               │ │
│  └────────────────┬───────────────────────────────────────┘ │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────────┐ │
│  │  Database (SQLite / PostgreSQL)                       │ │
│  │  • jobs_job             • resumes_resume              │ │
│  │  • jobs_companymapping  • jobs_crawllog               │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 External Scraper Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Scraper Orchestrator (daily_scraper_to_db.py)      │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │                                                │
│  ┌──────────▼────────┬─────────────┬──────────────────┐    │
│  │ Aviation Scraper  │ Air India   │ Goose Scraper    │    │
│  │ (BeautifulSoup)   │ (Requests)  │ (Playwright)     │    │
│  └──────────┬────────┴─────────────┴────────┬─────────┘    │
│             │                                │               │
│             └────────► Direct DB Insert ◄────┘               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Automation Layer                           │
│  • Cron Jobs (Linux)                                         │
│  • Systemd Timers (Linux)                                    │
│  • Python Schedule (Cross-platform)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Core Components

### 1. **Jobs App** (`jobs/`)
**Purpose**: Manage aviation job listings from multiple sources

**Key Files**:
- `models.py` - Job, CompanyMapping, CrawlLog models
- `api.py` - REST endpoints for job operations
- `utils.py` - Deduplication and classification logic
- `auth.py` - API authentication

**Responsibilities**:
- Store and manage job listings
- Handle deduplication (URL-based + fuzzy matching)
- Classify companies by operation type
- Track scraping history via CrawlLog
- Export data (CSV, JSON)

### 2. **Resumes App** (`resumes/`)
**Purpose**: Parse and analyze aviation resumes

**Key Files**:
- `models.py` - Resume model
- `api.py` - Resume upload and retrieval endpoints
- `resume_parser.py` - Text extraction and parsing
- `utils.py` - JSON backup helpers

**Responsibilities**:
- Accept resume uploads (PDF, DOCX, TXT)
- Extract structured data (name, email, experience, skills)
- Store parsed data in database
- Maintain JSON backup (ResumeDataStore.json)

### 3. **Scrapers** (`scrapers/`)
**Purpose**: Automated data collection from external sources

**Key Files**:
- `daily_scraper_to_db.py` - Main orchestrator
- `aviationjobsearchScrap.py` - Aviation job board scraper
- `airIndiaScrap.py` - Air India careers scraper
- `gooseScrap.py` - Goose Recruitment scraper
- `linkdinScraperRT.py` - LinkedIn job scraper

**Responsibilities**:
- Scrape job listings from target websites
- Normalize data into standard format
- Direct database insertion
- Handle errors and retries
- Log all activities

### 4. **Backend Main** (`backendMain/`)
**Purpose**: Django project configuration

**Key Files**:
- `settings.py` - Django configuration, database, middleware
- `urls.py` - URL routing and API mounting
- `wsgi.py` / `asgi.py` - Server gateways

---

## 🔄 Data Flow

### 1. **Job Scraping Flow**

```
┌──────────────┐
│   Scheduler  │ (Cron/Systemd/Schedule)
│  Triggers    │
└──────┬───────┘
       │
       ▼
┌─────────────────────────────────┐
│  daily_scraper_to_db.py         │
│  • Initialize Django            │
│  • Setup logging                │
│  • Run all scrapers in sequence │
└──────┬──────────────────────────┘
       │
       ├────► Aviation Scraper ────► Returns 75 jobs (dict format)
       │
       ├────► Air India Scraper ──► Returns 28 jobs (dict format)
       │
       ├────► Goose Scraper ───────► Returns 12 jobs (dict format)
       │
       └────► LinkedIn Scraper ────► Returns N jobs (dict format)
       │
       ▼
┌─────────────────────────────────┐
│  Normalize Job Data             │
│  • Convert to standard format   │
│  • Fill missing fields          │
│  • Validate data types          │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  insert_or_update_job()         │
│  • Check URL duplication        │
│  • Check fuzzy title match      │
│  • Insert new or update existing│
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Django ORM                     │
│  • Transaction per job          │
│  • Save to database             │
│  • Log result                   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│  Database (jobs_job table)      │
│  • Job record created/updated   │
└─────────────────────────────────┘
```

### 2. **API Request Flow**

```
Client Request
     │
     ▼
Django Middleware Stack
     │
     ├──► CORS Check
     ├──► CSRF Validation (if applicable)
     ├──► Authentication (Bearer token)
     │
     ▼
Django Ninja Router
     │
     ├──► Route matching (/api/jobs/...)
     ├──► Parameter validation
     │
     ▼
API Endpoint Handler (jobs/api.py)
     │
     ├──► Business logic execution
     ├──► Database queries (ORM)
     ├──► Data transformation
     │
     ▼
Response Serialization
     │
     ▼
JSON Response to Client
```

### 3. **Resume Processing Flow**

```
Resume Upload (POST /api/upload)
     │
     ▼
File Validation
     │
     ├──► Check file type (PDF, DOCX, TXT)
     ├──► Check file size
     │
     ▼
resume_parser.py
     │
     ├──► Extract text content
     ├──► Parse sections (education, experience, skills)
     ├──► Extract contact info
     │
     ▼
Create Resume Object
     │
     ├──► Save to database (resumes_resume)
     ├──► Backup to ResumeDataStore.json
     │
     ▼
Return Parsed Data
```

---

## 🗄️ Database Schema

### **jobs_job** (Main Job Listings Table)

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| title | CharField(500) | Job title |
| normalized_title | CharField(500) | Normalized job title |
| company | CharField(300) | Company name |
| company_id | CharField(100) | External company ID |
| country_code | CharField(2) | ISO country code |
| operation_type | CharField(50) | Airline/MRO/Airport/etc. |
| posted_date | DateField | When job was posted |
| url | URLField(1000) | Job listing URL (unique) |
| description | TextField | Full job description |
| status | CharField(20) | active/expired/filled |
| senior_flag | BooleanField | Is senior position |
| source | CharField(100) | Scraper source |
| last_checked | DateTimeField | Last verification |
| raw_json | JSONField | Original scraped data |
| created_at | DateTimeField | Record creation |
| updated_at | DateTimeField | Last update |

**Indexes**: url (unique), company, country_code, operation_type, posted_date

### **jobs_companymapping** (Company Classification)

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| company_name | CharField(300) | Display name |
| normalized_name | CharField(300) | Lowercase normalized (unique) |
| operation_type | CharField(50) | Company type |
| country_code | CharField(2) | Primary country |
| notes | TextField | Additional info |
| created_at | DateTimeField | Record creation |
| updated_at | DateTimeField | Last update |

### **jobs_crawllog** (Scraping History)

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| source | CharField(100) | Scraper name |
| run_time | DateTimeField | Execution timestamp |
| items_found | IntegerField | Total items scraped |
| items_inserted | IntegerField | New records |
| items_updated | IntegerField | Updated records |
| error | TextField | Error messages |

### **resumes_resume** (Resume Data)

| Column | Type | Description |
|--------|------|-------------|
| id | BigAutoField | Primary key |
| name | CharField(200) | Candidate name |
| email | EmailField | Contact email |
| phone | CharField(20) | Phone number |
| raw_text | TextField | Full resume text |
| parsed_data | JSONField | Structured data |
| file_path | CharField(500) | Original file path |
| created_at | DateTimeField | Upload time |
| updated_at | DateTimeField | Last update |

---

## 🔌 API Architecture

### **Django Ninja Framework**
- Schema-based validation
- Auto-generated OpenAPI docs
- Type hints for endpoints
- Built-in authentication

### **API Statistics**

- **Total Endpoints**: 31+ REST API endpoints
- **Public Endpoints**: 24 (no authentication required)
- **Protected Endpoints**: 7 (require API key)
- **Categories**: 9 major categories
  - Core Job Operations (7 endpoints)
  - Advanced Search (1 endpoint)
  - Company APIs (4 endpoints)
  - Analytics (4 endpoints)
  - Recent Activity (3 endpoints)
  - Job Comparison (2 endpoints)
  - Export & Reports (2 endpoints)
  - Scraper Management (2 endpoints)
  - Admin Operations (6 endpoints)

### **Endpoint Organization**

```
/api/
├── jobs/                           # Job management (31+ endpoints)
│   ├── /                          # List jobs (GET)
│   ├── /id/{id}                   # Single job (GET)
│   ├── /ingest                    # Single ingest (POST, auth)
│   ├── /bulk_ingest               # Bulk ingest (POST, auth)
│   ├── /search                    # Simple search (GET)
│   ├── /advanced-search           # ✨ Advanced multi-filter search (GET)
│   ├── /stats                     # Statistics (GET)
│   ├── /health                    # Health check (GET)
│   │
│   ├── /companies/                # ✨ Company APIs
│   │   ├── /                     # List all companies (GET)
│   │   ├── /{name}               # Company profile (GET)
│   │   ├── /{name}/jobs          # Company's jobs (GET)
│   │   └── /trending             # Trending companies (GET)
│   │
│   ├── /analytics/                # ✨ Analytics & Insights
│   │   ├── /trends               # Job posting trends (GET)
│   │   ├── /geographic           # Geographic distribution (GET)
│   │   └── /operation-types      # Stats by type (GET)
│   │
│   ├── /recent                    # ✨ Recently added jobs (GET)
│   ├── /updated                   # ✨ Recently updated jobs (GET)
│   ├── /alerts/senior             # Senior role alerts (GET)
│   │
│   ├── /compare                   # ✨ Compare multiple jobs (POST)
│   ├── /similar/{id}              # ✨ Find similar jobs (GET)
│   │
│   ├── /export/
│   │   ├── /daily.csv            # Daily CSV export (GET)
│   │   └── /json                 # ✨ JSON export with filters (GET)
│   │
│   └── /admin/                    # Admin operations (auth)
│       ├── /company-mappings     # Manage mappings (CRUD)
│       ├── /unknown-companies    # Companies without mapping (GET)
│       ├── /scrapers/status      # ✨ Scraper status (GET, auth)
│       └── /scrapers/logs        # ✨ Scraper logs (GET, auth)
│
├── upload-resume                   # Resume upload (POST)
├── upload-resume-with-info         # Resume with metadata (POST)
├── resumes                         # List resumes (GET)
├── resumes/{id}                    # Single resume (GET)
├── resumes/{id}/download           # Download resume file (GET)
└── stats                           # Resume statistics (GET)
```

✨ **New in v2.0** - 15+ new endpoints added

### **Authentication**
- **Type**: Bearer Token (HTTP Authorization header)
- **Implementation**: `jobs/auth.py` - APIKeyAuth class
- **Configuration**: `ADMIN_API_KEY` environment variable
- **Scope**: Protected endpoints (ingest, bulk_ingest, PATCH, DELETE)

---

## 🕷️ Scraper System

### **Scraper Technologies**

| Scraper | Technology | Method | Output |
|---------|------------|--------|--------|
| Aviation Jobs | BeautifulSoup4 + Requests | HTML parsing | 75 jobs/run |
| Air India | Requests + JSON | API endpoint | 28 jobs/run |
| Goose | Playwright | Headless browser | 12 jobs/run |
| LinkedIn | Playwright (manual) | Browser automation | Variable |

### **Normalization Pipeline**

Each scraper returns different formats, normalized to:

```python
{
    'title': str,
    'company': str,
    'url': str,
    'description': str,
    'posted_date': date or None,
    'country_code': str,
    'operation_type': str or None,
    'source': str
}
```

### **Deduplication Strategy**

**Primary**: URL matching
- If URL exists → update existing record

**Secondary**: Fuzzy title + company matching
- Levenshtein distance < 85% similarity
- Same company name
- Same posted date
- → Treat as duplicate, update existing

### **Error Handling**

- Individual transaction per job (prevents cascade failure)
- NULL field fallbacks (company → 'Unknown Company')
- Network timeout handling (job skipped, logged)
- Comprehensive logging to `scrapers/logs/`

---

## 🔗 Integration Points

### **External Services**
Currently self-contained, ready for:
- Email notifications (SMTP)
- Sentry error tracking
- Redis caching
- Elasticsearch for search

### **Internal Integration**
- Scrapers → Direct database insert (bypasses API for performance)
- API → Can be consumed by frontend, mobile, external systems
- Admin panel → Django built-in admin for manual management

---

## 🔒 Security Model

### **Authentication**
- API key-based authentication
- Environment variable configuration
- Optional (disabled if `ADMIN_API_KEY` not set)

### **CORS**
- Currently allows all origins (development)
- Should be restricted in production

### **Database**
- ORM prevents SQL injection
- Prepared statements
- Input validation via Django forms/serializers

### **Secret Management**
- `.env` file for sensitive data
- `.env.example` template
- `.gitignore` prevents commits

### **Production Recommendations**
- Use PostgreSQL (not SQLite)
- Enable HTTPS only
- Restrict `ALLOWED_HOSTS`
- Rotate `SECRET_KEY`
- Set `DEBUG=0`
- Use secrets manager (AWS Secrets Manager, Vault)

---

## 🚀 Deployment Strategy

### **Development**
```bash
python manage.py runserver  # SQLite, DEBUG=1
```

### **Staging/Production**

**Option 1: Traditional Server**
```bash
# Install dependencies
pip install gunicorn
pip install -r requirements.txt

# Run with Gunicorn
gunicorn backendMain.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --timeout 120

# Nginx reverse proxy
# PostgreSQL database
# Systemd service for scrapers
```

**Option 2: Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "backendMain.wsgi:application"]
```

**Option 3: Platform-as-a-Service**
- Heroku
- Railway
- Render
- AWS Elastic Beanstalk

### **Scraper Scheduling**

**Development**: Manual runs
**Production**: 
- Cron job (Linux servers)
- Systemd timer (Linux servers)
- AWS EventBridge + Lambda
- Kubernetes CronJob

---

## 🔮 Future Enhancements

### **Short-term**
- [ ] Email notifications for scraper failures
- [ ] Prometheus metrics endpoint
- [ ] API rate limiting
- [ ] Frontend dashboard (React/Vue)

### **Medium-term**
- [ ] Elasticsearch integration for full-text search
- [ ] Redis caching for frequently accessed data
- [ ] WebSocket support for real-time job alerts
- [ ] ML-based job recommendation engine

### **Long-term**
- [ ] Microservices architecture (scraper service separate)
- [ ] GraphQL API alongside REST
- [ ] Mobile app (React Native)
- [ ] AI-powered resume matching
- [ ] Multi-tenant support for different aviation sectors

---

## 📊 Performance Metrics

### **Current Benchmarks**
- Job scraping: ~115 jobs in 10 minutes
- API response time: < 100ms (average)
- Database size: ~1MB per 1000 jobs
- Deduplication accuracy: 84% insert rate

### **Scalability**
- SQLite: Up to 10K jobs (development)
- PostgreSQL: Millions of jobs (production)
- API throughput: 100+ req/sec (with Gunicorn)

---

## 📞 Support & Maintenance

### **Logs Location**
- Django: Console output
- Scrapers: `scrapers/logs/daily_scraper_YYYYMMDD.log`
- Django errors: `backendMain/django_errors.log` (if configured)

### **Health Checks**
- API: `GET /api/jobs/health`
- Database: `python manage.py check --database default`

### **Backup Strategy**
- Database: Daily PostgreSQL dumps
- Resumes: File system backup + JSON backup
- Code: Git repository

---

**Document Version**: 1.0  
**Last Updated**: November 2025  
**Maintainer**: AeroOps Intel Development Team
