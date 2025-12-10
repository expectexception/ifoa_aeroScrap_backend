# 📚 AeroOps Backend Documentation Index

**Last Updated**: November 24, 2025  
**Version**: 2.0.0

---

## 🎯 Quick Start Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [QUICKSTART.md](QUICKSTART.md) | Get the backend running in 5 minutes | New developers |
| [AUTO_MAPPING_QUICK_REF.md](AUTO_MAPPING_QUICK_REF.md) | Quick reference for auto-mapping feature | Admins, developers |
| [SCRAPER_QUICK_REFERENCE.md](SCRAPER_QUICK_REFERENCE.md) | Scraper commands and usage | Developers, admins |

---

## 🏗️ Core Documentation

### Backend Architecture
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - System architecture and technology stack
- [BACKEND_IMPLEMENTATION_REQUIREMENTS.md](BACKEND_IMPLEMENTATION_REQUIREMENTS.md) - Implementation requirements
- [BACKEND_OPTIMIZATION_SUMMARY.md](BACKEND_OPTIMIZATION_SUMMARY.md) - Performance optimizations

### API Documentation
- [API_REFERENCE.md](API_REFERENCE.md) - Complete API endpoint reference
- [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md) - Quick API command reference
- [API_ENDPOINTS_FIXED.md](API_ENDPOINTS_FIXED.md) - Fixed endpoint documentation
- [API_V2_SUMMARY.txt](API_V2_SUMMARY.txt) - API version 2 summary

---

## 🤖 Auto-Mapping Feature (NEW)

### Complete Documentation Set

| Document | Purpose | Read Time |
|----------|---------|-----------|
| [AUTO_MAPPING_QUICK_REF.md](AUTO_MAPPING_QUICK_REF.md) | One-page quick reference | 2 min |
| [AUTO_MAPPING_FEATURE.md](AUTO_MAPPING_FEATURE.md) | Comprehensive feature guide | 10 min |
| [AUTO_MAPPING_IMPLEMENTATION_SUMMARY.md](AUTO_MAPPING_IMPLEMENTATION_SUMMARY.md) | Implementation details & testing | 5 min |

**Feature Status**: ✅ Production Ready (v1.0.0)  
**Migration**: `0009_add_company_mapping_review_fields` (applied)

### What It Does
Automatically creates CompanyMapping entries when scrapers discover new companies, flagged for admin review with inherited operation_type and country_code.

### Key Benefits
- 100% automated company discovery
- Smart duplicate detection
- Bulk approval workflow
- Complete audit trail

---

## 🕷️ Scraper Documentation

### Configuration & Usage
- [SCRAPER_QUICK_REFERENCE.md](SCRAPER_QUICK_REFERENCE.md) - Commands and examples
- [SCRAPER_IMPROVEMENTS.md](SCRAPER_IMPROVEMENTS.md) - Recent improvements (threading, limits)
- [SCHEDULING_SETUP.md](SCHEDULING_SETUP.md) - Automated scheduling configuration

### Scraper-Specific
- `scrapers/README_UNIFIED_SCRAPER.md` - Unified scraper architecture
- `scrapers/README_DAILY_SCRAPER.md` - Daily automation setup
- `scrapers/SETUP.md` - Initial setup instructions

---

## 🧪 Testing & Quality Assurance

| Document | Description |
|----------|-------------|
| [TESTING_CHECKLIST_AVIATION_THEME.md](TESTING_CHECKLIST_AVIATION_THEME.md) | Aviation theme testing checklist |
| [TEST_ANALYSIS_REPORT.md](TEST_ANALYSIS_REPORT.md) | Test analysis and results |
| [QUICK_TEST_GUIDE.md](QUICK_TEST_GUIDE.md) | Quick testing procedures |
| `test_all_apis.py` | API test suite |
| `test_auto_mapping.py` | Auto-mapping test suite |

---

## 🎨 UI & Theme

- [AVIATION_THEME_UPDATE.md](AVIATION_THEME_UPDATE.md) - Admin interface theme documentation
- Visual design: Aviation-themed admin with IFOA branding
- Colors: Blue (#003b6f), gold accents, professional aviation aesthetic

---

## 🔄 Migration & Updates

### Recent Features (2025-11-24)
- ✅ Auto-mapping for company discovery
- ✅ ThreadPoolExecutor for concurrent scraping
- ✅ Parameter enforcement (max_pages, max_jobs)
- ✅ Resume parser dependency fixes
- ✅ URL deduplication system

### Migration History
- `0009_add_company_mapping_review_fields` - Auto-mapping feature
- `0002_alter_job_options_remove_job_jobs_normali_0858bc_idx` - Job model optimization
- `0001_initial` - Initial database schema

---

## 📊 Status & Implementation

### Feature Status Matrix

| Feature | Status | Documentation | Tests |
|---------|--------|---------------|-------|
| Auto-Mapping | ✅ Production | Complete | ✅ Passing |
| Threading | ✅ Production | Complete | ✅ Passing |
| Resume Parser | ✅ Production | Complete | ✅ Passing |
| API v2 | ✅ Production | Complete | ✅ Passing |
| Aviation Theme | ✅ Production | Complete | ✅ Passing |
| Scheduling | ✅ Production | Complete | ✅ Passing |

### Component Status

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| Django | 5.1.14 | ✅ Stable | Latest LTS |
| Gunicorn | 23.0.0 | ✅ Running | 3 workers |
| ThreadPool | 4 workers | ✅ Active | Max concurrent scrapers |
| Database | SQLite3 | ✅ Optimized | Indexed queries |
| Resume Parser | pdfplumber 0.11.8 | ✅ Working | All deps installed |

---

## 🔧 Configuration Files

### Backend Configuration
- `backendMain/settings.py` - Django settings
- `settings.json` - Custom application settings
- `.env` - Environment variables (see `.env.example`)

### Scraper Configuration
- `resumes/resumeParcerconfig.json` - Resume parser config
- `scrapers/schedule_runner.py` - Scheduling configuration

---

## 👥 Frontend Integration

- [FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md) - API integration guide
- [FRONTEND_MIGRATION_GUIDE.md](FRONTEND_MIGRATION_GUIDE.md) - Migration from old API

---

## 📝 Release Notes & Summaries

- [PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md) - Project milestones
- [IMPLEMENTED_ENDPOINTS_STATUS.md](IMPLEMENTED_ENDPOINTS_STATUS.md) - Endpoint implementation status
- [NEW_FEATURES.md](NEW_FEATURES.md) - Recent feature additions
- [VISUAL_SUMMARY.txt](VISUAL_SUMMARY.txt) - Visual overview

---

## 🐛 Troubleshooting & Debugging

### Common Issues

#### Auto-Mapping Not Working?
See: [AUTO_MAPPING_FEATURE.md](AUTO_MAPPING_FEATURE.md) - Support & Troubleshooting section

#### Scraper Issues?
See: [SCRAPER_IMPROVEMENTS.md](SCRAPER_IMPROVEMENTS.md) - Troubleshooting section

#### API Errors?
See: [API_REFERENCE.md](API_REFERENCE.md) - Error handling section

### Debug Commands
```bash
# Check server status
pgrep -f gunicorn

# View logs
tail -f logs/gunicorn.log
tail -f logs/scraper.log

# Check database
python manage.py dbshell

# Run tests
python test_auto_mapping.py
python test_all_apis.py
```

---

## 🔗 External Resources

- Django Documentation: https://docs.djangoproject.com/
- REST Framework: https://www.django-rest-framework.org/
- Gunicorn: https://docs.gunicorn.org/
- pdfplumber: https://github.com/jsvine/pdfplumber

---

## 📞 Support & Contact

### For Issues:
1. Check relevant documentation section
2. Review logs in `logs/` directory
3. Run test suite to verify functionality
4. Check migration status: `python manage.py showmigrations`

### For Feature Requests:
1. Check [GAP_ANALYSIS.md](GAP_ANALYSIS.md) for planned features
2. Review [NEW_FEATURES.md](NEW_FEATURES.md) for recent additions

---

## 🎓 Learning Path

### New to the Project?
1. Start: [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md)
2. Setup: [QUICKSTART.md](QUICKSTART.md)
3. API: [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md)
4. Admin: [AUTO_MAPPING_QUICK_REF.md](AUTO_MAPPING_QUICK_REF.md)

### Backend Developer?
1. Architecture: [BACKEND_IMPLEMENTATION_REQUIREMENTS.md](BACKEND_IMPLEMENTATION_REQUIREMENTS.md)
2. API Design: [API_REFERENCE.md](API_REFERENCE.md)
3. Optimizations: [BACKEND_OPTIMIZATION_SUMMARY.md](BACKEND_OPTIMIZATION_SUMMARY.md)
4. Recent Changes: [SCRAPER_IMPROVEMENTS.md](SCRAPER_IMPROVEMENTS.md)

### Admin User?
1. Quick Ref: [AUTO_MAPPING_QUICK_REF.md](AUTO_MAPPING_QUICK_REF.md)
2. Full Guide: [AUTO_MAPPING_FEATURE.md](AUTO_MAPPING_FEATURE.md)
3. Scheduling: [SCHEDULING_SETUP.md](SCHEDULING_SETUP.md)
4. Theme: [AVIATION_THEME_UPDATE.md](AVIATION_THEME_UPDATE.md)

### Frontend Developer?
1. Integration: [FRONTEND_INTEGRATION_GUIDE.md](FRONTEND_INTEGRATION_GUIDE.md)
2. API Reference: [API_REFERENCE.md](API_REFERENCE.md)
3. Migration: [FRONTEND_MIGRATION_GUIDE.md](FRONTEND_MIGRATION_GUIDE.md)

---

## 📈 Statistics

**Total Documentation Files**: 25+  
**Code Files**: 50+  
**API Endpoints**: 20+  
**Scrapers**: 4 (Aviation, Air India, LinkedIn, Goose)  
**Database Models**: 6 (Job, CompanyMapping, CrawlLog, ScraperJob, ScheduleConfig, User)  
**Migrations**: 9 (all applied)  
**Test Suites**: 3 (API, Auto-mapping, Comprehensive)  

**Last Major Update**: Auto-Mapping Feature (2025-11-24)  
**System Status**: ✅ Production Ready  
**Server Uptime**: Active since 2025-11-24 11:06

---

## 🎯 Quick Links

### Most Used Documents (Top 5)
1. [AUTO_MAPPING_QUICK_REF.md](AUTO_MAPPING_QUICK_REF.md) - Daily admin tasks
2. [API_QUICK_REFERENCE.md](API_QUICK_REFERENCE.md) - API commands
3. [SCRAPER_QUICK_REFERENCE.md](SCRAPER_QUICK_REFERENCE.md) - Scraper usage
4. [QUICKSTART.md](QUICKSTART.md) - Setup guide
5. [AUTO_MAPPING_FEATURE.md](AUTO_MAPPING_FEATURE.md) - Feature documentation

### Admin URLs
- Admin Panel: http://localhost:8000/admin/
- Company Mappings: http://localhost:8000/admin/jobs/companymapping/
- Jobs: http://localhost:8000/admin/jobs/job/
- Scraper Jobs: http://localhost:8000/admin/scraper_manager/scraperjob/
- Schedule Config: http://localhost:8000/admin/jobs/scheduleconfig/

### API URLs
- Base URL: http://localhost:8000/api/
- Jobs: http://localhost:8000/api/jobs/
- Mappings: http://localhost:8000/api/company-mappings/
- Scraper: http://localhost:8000/api/scraper/run/

---

**Navigation**: Use Ctrl+F to search | Click document names to open | All paths relative to `/documents/`

**Maintained By**: AeroOps Development Team  
**License**: Private/Proprietary
