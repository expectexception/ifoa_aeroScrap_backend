# AeroOps Backend - Project Structure

## 📁 Root Directory Structure

```
backendMain/
├── 📱 Core Django Apps
│   ├── backendMain/          # Main Django project settings
│   ├── jobs/                 # Job listings & applications
│   ├── resumes/              # Resume management & parsing
│   ├── users/                # User authentication & profiles
│   └── scraper_manager/      # Web scraping system
│
├── 📚 Documentation & Scripts
│   ├── documentation/        # Organized docs and scripts
│   │   ├── setup_scripts/    # Setup & deployment scripts
│   │   ├── test_scripts/     # Test files
│   │   └── archived/         # Archived documentation
│   └── docs/                 # API & integration guides
│
├── 🗄️ Data & Output
│   ├── output/               # Scraper output & resume data
│   ├── logs/                 # Application logs
│   └── staticfiles/          # Static files (production)
│
├── 🎨 Frontend Assets
│   ├── static/               # Development static files
│   └── templates/            # Django templates
│
├── 🔧 Configuration Files
│   ├── .env                  # Environment variables (dev)
│   ├── .env.production.template  # Production env template
│   ├── requirements.txt      # Python dependencies
│   ├── manage.py            # Django management script
│   └── db_manage.py         # Database utilities
│
└── 📦 Additional
    ├── tests/               # Integration tests
    ├── scripts/             # Utility scripts
    └── .venv/              # Python virtual environment

```

## 🚀 Core Applications

### 1️⃣ jobs/
**Aviation Job Management System**
- Job listings from multiple sources
- Company mappings & categorization
- Application tracking (JobApplication model)
- Saved jobs (SavedJob model)
- Job views analytics (JobView model)
- Automated scraping & scheduling

**Key Files:**
- `models.py` - Job, CompanyMapping, CrawlLog, ScheduleConfig
- `admin.py` - Enhanced admin interface with analytics
- `application_models.py` - Application tracking models
- `views.py` - API views for job seekers & recruiters

### 2️⃣ resumes/
**Resume Parsing & Management**
- AI-powered resume parsing
- Aviation skills extraction
- Candidate scoring system
- File storage (PDF, DOC, DOCX, TXT)
- Form-based resume submission

**Key Files:**
- `models.py` - Resume model with JSON fields
- `admin.py` - Candidate management interface
- `api_resumes.py` - REST API endpoints (8 endpoints)
- `api.py` - Django Ninja API (legacy)
- `utils.py` - Resume parser & utilities

### 3️⃣ users/
**Authentication & User Management**
- JWT authentication (SimpleJWT)
- User profiles (job seekers & recruiters)
- Role-based permissions (RBAC)
- Staff profiles with departments

**Key Files:**
- `models.py` - UserProfile model
- `admin.py` - User & profile management
- `views.py` - Authentication endpoints

### 4️⃣ scraper_manager/
**Web Scraping System**
- Multiple aviation job board scrapers
- Automated scheduling (Celery)
- URL tracking & deduplication
- Performance monitoring
- Configurable scraper settings

**Key Files:**
- `models.py` - ScraperJob, ScraperConfig, ScrapedURL
- `admin.py` - Scraper control panel
- `scrapers/` - Individual scraper implementations
- `management/commands/` - CLI commands

### 5️⃣ backendMain/
**Django Project Configuration**
- Settings (dev & production)
- URL routing
- Custom admin site
- Celery configuration
- Middleware

**Key Files:**
- `settings.py` - Main settings
- `settings_production.py` - Production config
- `urls.py` - URL routing
- `admin.py` - Custom admin site
- `celery.py` - Celery task queue

## 📚 Documentation Structure

### documentation/setup_scripts/
- `quick_setup.sh` - Development setup
- `setup_postgres.sh` - Database setup
- `setup_celery.sh` - Task queue setup
- `setup_rbac.sh` - Permissions setup
- `*.service` - Systemd service files

### documentation/test_scripts/
- `test_api_endpoints.py` - API testing
- `test_profile_endpoints.py` - Profile tests
- `test_auto_mapping.py` - Auto-mapping tests
- `test_fresh_scrape.py` - Scraper tests

### docs/
- API documentation
- Frontend integration guides
- Implementation checklists
- Feature specifications

## 🗄️ Database Models

### Jobs App
- **Job** - Job listings (title, company, location, etc.)
- **CompanyMapping** - Company normalization & categorization
- **JobApplication** - Application tracking with status
- **SavedJob** - User bookmarks
- **JobView** - Analytics tracking
- **CrawlLog** - Scraping history
- **ScheduleConfig** - Automation settings

### Resumes App
- **Resume** - Parsed resumes with scoring

### Users App
- **UserProfile** - Extended user information
- **User** (Django built-in) - Authentication

## 🔗 API Endpoints

### Authentication (4 endpoints)
- POST `/api/auth/register/`
- POST `/api/auth/login/`
- POST `/api/auth/token/refresh/`
- GET `/api/auth/profile/`

### Job Seeker (10 endpoints)
- Job browsing & search
- Application management
- Saved jobs
- Dashboard

### Recruiter (9 endpoints)
- Candidate management
- Application review
- Bulk operations
- Analytics

### Resumes (8 endpoints)
- Upload (file & form-based)
- List & search
- Download
- Visibility control

## 🚀 Deployment

### Development
```bash
python manage.py runserver
```

### Production
1. Configure `.env.production`
2. Run setup scripts
3. Configure systemd services
4. Start Celery workers

## 📝 Key Features

✅ **Multi-tenant** - Job seekers, recruiters, admins
✅ **Real-time scraping** - Multiple aviation job boards
✅ **Smart parsing** - AI-powered resume analysis
✅ **RBAC** - Role-based access control
✅ **REST API** - Complete backend API
✅ **Admin Dashboard** - Production-ready interface
✅ **Celery Tasks** - Background job processing
✅ **PostgreSQL** - Optimized database schema
✅ **JWT Auth** - Secure token-based authentication

---

## 🔧 Quick Commands

```bash
# Database
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run tests
python manage.py test

# Run scraper
python manage.py run_scraper signature

# Celery worker
celery -A backendMain worker -l info

# Celery beat (scheduler)
celery -A backendMain beat -l info
```

---

Last Updated: November 26, 2025
Project: AeroOps Intel Aviation Recruitment Platform
