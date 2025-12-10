# 🚀 Enhanced Scraper Manager - Quick Start Guide

## TL;DR

Scrapers now support **parameter control** and **automatic database saving**!

```bash
# Control scraping with parameters
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "scraper": "aviation",
    "max_pages": 2,
    "max_jobs": 30,
    "async": true
  }'
```

## ✨ What's New

| Feature | Description | Benefit |
|---------|-------------|---------|
| `max_pages` | Limit pages to scrape | Faster execution |
| `max_jobs` | Limit total jobs | Predictable results |
| Auto DB save | Jobs saved automatically | No manual work |
| Better errors | Detailed error handling | Easy debugging |
| Statistics | new/updated/duplicate counts | Track changes |

## 🎯 Common Use Cases

### 1. Quick Test (1 Page Only)
```json
{
  "scraper": "aviation",
  "max_pages": 1,
  "async": true
}
```
⏱️ Time: ~30s | Jobs: ~25

### 2. Small Update (20 Jobs)
```json
{
  "scraper": "aviation",
  "max_jobs": 20,
  "async": true
}
```
⏱️ Time: ~40s | Jobs: 20 exactly

### 3. Balanced Scrape
```json
{
  "scraper": "aviation",
  "max_pages": 3,
  "max_jobs": 50,
  "async": true
}
```
⏱️ Time: ~60s | Jobs: ≤50

### 4. Full Scrape (No Limits)
```json
{
  "scraper": "aviation",
  "async": true
}
```
⏱️ Time: ~120s | Jobs: All available

## 📊 Response Fields

### Start Response
```json
{
  "job_id": 1,
  "status": "running",
  "params": {"max_pages": 2, "max_jobs": 30}
}
```

### Status Response
```json
{
  "status": "completed",
  "jobs_found": 30,
  "jobs_new": 15,        // ← New! Added to DB
  "jobs_updated": 10,    // ← New! Updated in DB
  "jobs_duplicates": 5,  // ← New! Already existed
  "execution_time": 45.3
}
```

## 🛠️ All Available Parameters

```json
{
  "scraper": "aviation",      // Required: aviation, airindia, goose, linkedin, all
  "async": true,              // Optional: true=background, false=wait (default: false)
  "max_pages": 3,             // Optional: limit pages (min: 1)
  "max_jobs": 50              // Optional: limit jobs (min: 1)
}
```

## 📝 Scraper-Specific Behavior

| Scraper | Supports max_pages | Supports max_jobs | Default Limit |
|---------|-------------------|-------------------|---------------|
| aviation | ✅ Yes | ✅ Yes | 3 pages |
| airindia | ✅ Yes | ✅ Yes | 4 pages |
| goose | ❌ No | ✅ Yes | 10 jobs |
| linkedin | ❌ No | ✅ Yes | 50 jobs |

## 🐍 Python Quick Example

```python
import requests

# Login
token = requests.post(
    "http://localhost:8000/api/auth/login/",
    json={"username": "admin", "password": "pass"}
).json()["access"]

# Start scraper
job = requests.post(
    "http://localhost:8000/api/scrapers/start/",
    json={"scraper": "aviation", "max_pages": 2, "async": True},
    headers={"Authorization": f"Bearer {token}"}
).json()

print(f"Job ID: {job['job_id']}")

# Check status
status = requests.get(
    f"http://localhost:8000/api/scrapers/status/{job['job_id']}/"
).json()

print(f"Found: {status['jobs_found']}, New: {status['jobs_new']}")
```

## ⚡ Performance Comparison

| Setup | Time | Jobs | Use Case |
|-------|------|------|----------|
| max_pages=1 | ~30s | ~25 | Quick test |
| max_jobs=20 | ~40s | 20 | Small update |
| max_pages=3, max_jobs=50 | ~60s | ≤50 | Balanced |
| No limits | ~120s | All | Full scrape |

## 🎯 Best Practices

### ✅ DO
- Use `async=true` for production
- Start with `max_pages=1` for testing
- Use `max_jobs` for predictable counts
- Monitor `jobs_new` vs `jobs_duplicates`

### ❌ DON'T
- Don't use `max_pages=100` (too many)
- Don't scrape without limits in prod
- Don't ignore error messages
- Don't run sync in production

## 🔍 Check Database

```bash
# Count jobs by source
psql -d aeroops_db -c "
  SELECT source, COUNT(*) 
  FROM jobs 
  GROUP BY source;
"

# View recent jobs
psql -d aeroops_db -c "
  SELECT title, company, source, last_checked 
  FROM jobs 
  ORDER BY last_checked DESC 
  LIMIT 10;
"
```

## 🐛 Troubleshooting

### Issue: Too slow
**Solution:** Use `max_pages=1` or `max_jobs=20`

### Issue: Not enough jobs
**Solution:** Increase limits or remove them

### Issue: All duplicates
**Reason:** Jobs already in database (normal!)  
**Check:** `jobs_updated` for changes

### Issue: Errors
**Check:** 
1. `error_message` in status response
2. `logs/django.log`
3. Parameter validation

## 📚 Full Documentation

- **Enhancement Guide**: `SCRAPER_ENHANCEMENTS.md`
- **API Reference**: `SCRAPER_MANAGER_API.md`
- **Implementation**: `ENHANCEMENTS_SUMMARY.md`

## 🧪 Testing

```bash
# Run enhanced test suite
python test_scraper_parameters.py

# Expected: Tests for parameter validation, execution, and monitoring
```

## ⚙️ Configuration

No configuration needed! Parameters are per-request:

```bash
# Request 1: Quick test
{"max_pages": 1}

# Request 2: Full scrape
{} # No parameters

# Each request independent!
```

## 🎓 Learning Path

### Day 1: Basic Usage
```bash
# Start with one page
{"scraper": "aviation", "max_pages": 1}
```

### Day 2: Job Limits
```bash
# Limit total jobs
{"scraper": "aviation", "max_jobs": 20}
```

### Day 3: Combined
```bash
# Use both parameters
{"scraper": "aviation", "max_pages": 2, "max_jobs": 30}
```

### Day 4: Production
```bash
# Async with monitoring
{"scraper": "aviation", "max_pages": 3, "async": true}
```

## 💡 Pro Tips

1. **Development**: Always use `max_pages=1` for testing
2. **Monitoring**: Check `jobs_new` to see actual impact
3. **Efficiency**: Use `max_jobs` when you need exact count
4. **Production**: Always use `async=true`
5. **Database**: Jobs auto-saved, no manual work needed!

## 📞 Need Help?

- **API Errors**: Check `error_message` in response
- **Scraper Issues**: Review `logs/django.log`
- **Parameters**: See `SCRAPER_ENHANCEMENTS.md`
- **General**: See `SCRAPER_MANAGER_API.md`

---

**Quick Links:**
- Start Server: `python manage.py runserver`
- Test Suite: `python test_scraper_parameters.py`
- API Endpoint: `POST /api/scrapers/start/`
- Status Check: `GET /api/scrapers/status/<id>/`

**Version:** 2.0 | **Status:** ✅ Ready to Use
