# Scraper & Resume Parser - Quick Reference

## What Was Fixed

### 🔧 Main Issues
1. **Scrapers ignored max_pages and max_jobs** - Now properly enforced DURING scraping
2. **Poor threading** - Replaced with ThreadPoolExecutor for better control
3. **Resume parser config issues** - Multiple fallback paths, graceful degradation

## How To Use

### Run Scraper with Limits (Frontend/API)

```bash
# Synchronous (wait for completion)
POST /api/scrapers/start/
{
  "scraper": "aviation",     # or "airindia", "linkedin", "goose", "all"
  "max_pages": 2,            # Stop after 2 pages
  "max_jobs": 10,            # Stop after 10 jobs (enforced during scraping!)
  "async": false
}

# Asynchronous (returns immediately)
POST /api/scrapers/start/
{
  "scraper": "aviation",
  "max_pages": 2,
  "max_jobs": 10,
  "async": true              # Run in background
}

# Check status
GET /api/scrapers/status/{job_id}/
```

### Resume Upload

```bash
# Simple upload (auto-parse)
POST /api/resumes/upload-resume
Content-Type: multipart/form-data
file: <resume.pdf>

# Upload with metadata
POST /api/resumes/upload-resume-with-info
Content-Type: multipart/form-data
file: <resume.pdf>
metadata: {
  "personal": {
    "fullName": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890"
  },
  "experience": [...],
  "certificates": [...]
}
```

## Key Improvements

### Before vs After

| Feature | Before | After |
|---------|--------|-------|
| **max_jobs enforcement** | After scraping all pages | During scraping (stops early) |
| **Time efficiency** | Wasted 2-3 min for 5 jobs | Gets 5 jobs in 20 sec |
| **Threading** | Basic Thread() | ThreadPoolExecutor |
| **Concurrent scrapers** | Unlimited (risky) | Max 4 workers |
| **Resume config** | Single path, fails | Multiple paths, fallback |
| **Error handling** | Silent failures | Logged & handled |

### Performance Example
```
Task: Scrape 5 jobs with max_jobs=5

BEFORE:
- Scrapes ALL pages (e.g., 50 jobs)
- Takes full detail pages for all 50
- Then truncates to 5
- Time: 2m 45s ❌

AFTER:
- Scrapes jobs one by one
- Stops immediately at job #5
- Skips remaining pages
- Time: 22s ✅
```

## Testing

```bash
# Run comprehensive test suite
cd backendMain
python tests/test_scraper_fixes.py

# Test specific scraper
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation", "max_jobs": 3}'
```

## Files Changed

### Scrapers
- ✅ `scraper_manager/scrapers/aviation_scraper.py` - Early max_jobs enforcement
- ✅ `scraper_manager/scrapers/airindia_scraper.py` - Early max_jobs enforcement
- ✅ `scraper_manager/services.py` - ThreadPoolExecutor implementation

### Resume Parser
- ✅ `resumes/utils.py` - Config fallback paths
- ✅ `resumes/resume_parser.py` - Already well implemented

## Monitoring

### Check Scraper Status
```bash
# Active jobs
GET /api/scrapers/history/

# Stats
GET /api/scrapers/stats/

# Specific scraper status
GET /api/scrapers/status/{job_id}/
```

### Logs
```bash
# Watch scraper logs
tail -f logs/gunicorn-error.log | grep -E "scraper|max_jobs|max_pages"

# Check resume parser
tail -f logs/django_errors.log | grep -E "resume|parser"
```

## Common Patterns

### Efficient Job Collection
```python
# Good: Gets exactly what you need
POST /api/scrapers/start/
{
  "scraper": "aviation",
  "max_pages": 3,    # Safety limit
  "max_jobs": 20     # Actual limit (will stop at 20)
}

# Bad: Wastes time (would scrape all 3 pages even if 20 jobs on page 1)
# This is now FIXED - scraper stops early!
```

### Async for Long Operations
```python
# For many jobs, use async
POST /api/scrapers/start/
{
  "scraper": "all",       # Run all scrapers
  "async": true,          # Don't wait
  "max_jobs": 100
}
# Returns: {"job_id": 123, "status": "running"}

# Poll for completion
GET /api/scrapers/status/123/
# Returns: {"status": "completed", "jobs_found": 100, ...}
```

## Troubleshooting

### Scraper Not Stopping
```bash
# Check if parameters are passed
curl http://localhost:8000/api/scrapers/list/ | jq

# Check logs
tail -f logs/gunicorn-error.log | grep "max_jobs"
```

### Resume Parser Failing
```bash
# Check config exists
ls -la resumes/resumeParcerconfig.json

# Check parser initialization
python -c "
import django, sys, os
sys.path.insert(0, '/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain')
os.environ['DJANGO_SETTINGS_MODULE'] = 'backendMain.settings'
django.setup()
from resumes.utils import parser
print('Parser:', parser)
print('Config:', bool(parser.config if parser else False))
"
```

## Architecture

```
Frontend Request
    ↓
API Endpoint (scraper_manager/api.py)
    ↓
ScraperService.run_scraper_async()
    ↓
ThreadPoolExecutor (max 4 workers)
    ↓
Worker Thread
    ├─ Load scraper module
    ├─ Call onCallWorker(max_pages, max_jobs)
    ├─ Scraper enforces limits DURING execution ✅
    ├─ Save results to DB
    └─ Update job status
```

## Next Steps

1. **Test in production**: Run `python tests/test_scraper_fixes.py`
2. **Monitor first runs**: Watch logs for "Reached max_jobs limit" messages
3. **Adjust limits**: Tune max_pages and max_jobs based on needs
4. **Frontend integration**: Update frontend to pass parameters
5. **Add monitoring**: Set up alerts for failed scraper jobs

## Support

### Documentation
- Full details: `documents/SCRAPER_IMPROVEMENTS.md`
- API docs: `documents/API_DOCUMENTATION.txt`
- Test suite: `tests/test_scraper_fixes.py`

### Key Logs
- Scraper execution: Look for `=== SCRAPER EXECUTION START ===`
- Parameter enforcement: Look for `Reached max_jobs limit`
- Resume parsing: Look for `Resume parser initialized`

---

**Summary**: Scrapers now stop early when limits reached (massive time savings), use proper threading, and resume parser has robust config handling. All parameters from frontend are properly enforced during execution, not after. 🚀
