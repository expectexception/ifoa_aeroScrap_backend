# Scraper Manager Quick Reference

## Quick Start

```bash
# 1. Start server
python manage.py runserver

# 2. Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'
# Save the "access" token

# 3. List scrapers
curl http://localhost:8000/api/scrapers/list/

# 4. Start scraper
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"scraper": "aviation", "async": true}'
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/scrapers/list/` | No | List all scrapers |
| POST | `/api/scrapers/start/` | Yes | Start scraper |
| GET | `/api/scrapers/status/<id>/` | No | Job status |
| GET | `/api/scrapers/history/` | No | Job history |
| GET | `/api/scrapers/stats/` | No | Statistics |

## Available Scrapers

| ID | Name | Description |
|----|------|-------------|
| `aviation` | Aviation Job Search | aviationjobsearch.com |
| `airindia` | Air India | Air India careers |
| `goose` | Goose Recruitment | Goose jobs |
| `linkedin` | LinkedIn | LinkedIn aviation jobs |
| `all` | All Scrapers | Run all sequentially |

## Start Scraper Options

```json
{
  "scraper": "aviation",  // Required: scraper ID or "all"
  "async": false          // Optional: true=background, false=wait
}
```

## Job Statuses

- `pending`: Created, not started
- `running`: Currently executing
- `completed`: Successfully finished
- `failed`: Error occurred

## Testing

```bash
# Run all tests
python test_scraper_apis.py

# Expected: 7/7 tests pass, 100% success rate
```

## Common Commands

```bash
# List scrapers
curl http://localhost:8000/api/scrapers/list/

# Start sync (waits for completion)
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation", "async": false}'

# Start async (returns immediately)
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation", "async": true}'

# Check status
curl http://localhost:8000/api/scrapers/status/1/

# Get history (last 10)
curl http://localhost:8000/api/scrapers/history/?limit=10

# Get stats
curl http://localhost:8000/api/scrapers/stats/
```

## Python Example

```python
import requests

BASE = "http://localhost:8000/api"

# Login
r = requests.post(f"{BASE}/auth/login/", 
                  json={"username": "user", "password": "pass"})
token = r.json()["access"]

# Start scraper
r = requests.post(
    f"{BASE}/scrapers/start/",
    json={"scraper": "aviation", "async": True},
    headers={"Authorization": f"Bearer {token}"}
)
job_id = r.json()["job_id"]

# Check status
r = requests.get(f"{BASE}/scrapers/status/{job_id}/")
print(r.json())
```

## Response Examples

### List Scrapers
```json
{
  "count": 4,
  "scrapers": [{
    "id": "aviation",
    "name": "Aviation Job Search",
    "available": true,
    "enabled": true,
    "recent_success_rate": 95.0
  }]
}
```

### Start Scraper (Async)
```json
{
  "message": "Scraper aviation started in background",
  "job_id": 1,
  "status": "running"
}
```

### Job Status
```json
{
  "job_id": 1,
  "scraper": "aviation",
  "status": "completed",
  "execution_time": 45.2,
  "jobs_found": 25,
  "jobs_new": 15
}
```

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 202 | Accepted (async started) |
| 400 | Bad request (missing params) |
| 401 | Not authenticated |
| 403 | Forbidden (scraper disabled) |
| 404 | Job not found |
| 500 | Server error |

## Files

```
backendMain/
├── scraper_manager/
│   ├── models.py         # ScraperJob, ScraperConfig
│   ├── services.py       # ScraperService
│   ├── api.py            # REST API views
│   ├── urls.py           # URL routing
│   └── admin.py          # Django admin
├── scrapers/
│   ├── aviationjobsearchScrap.py
│   ├── airIndiaScrap.py
│   ├── gooseScrap.py
│   └── linkdinScraperRT.py
└── test_scraper_apis.py  # Test suite
```

## Admin Access

URL: `http://localhost:8000/admin/scraper_manager/`

- View all jobs
- Enable/disable scrapers
- Configure settings

## Troubleshooting

**Can't start scraper?**
- Check authentication token
- Verify scraper is enabled
- Check Django logs

**Job stuck in "running"?**
- Check scraper process
- Review error logs
- May need manual DB update

**No jobs found?**
- Verify website accessible
- Check scraper logic
- Review error message

## See Also

- Full docs: `documents/SCRAPER_MANAGER_API.md`
- Auth guide: `documents/JWT_AUTHENTICATION.md`
- Scraper dev: `scrapers/README_UNIFIED_SCRAPER.md`
