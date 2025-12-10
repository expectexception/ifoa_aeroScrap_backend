# Scraper Manager API Documentation

## Overview

The Scraper Manager is a Django app that provides REST API endpoints for managing and controlling web scrapers. It allows you to:
- List all available scrapers with their status
- Start individual scrapers or run all scrapers
- Monitor scraper execution status in real-time
- View scraper history and statistics
- Control scraper execution (sync or async)

## Architecture

### Components

1. **Models** (`scraper_manager/models.py`)
   - `ScraperJob`: Tracks individual scraper executions
   - `ScraperConfig`: Stores scraper configuration and statistics

2. **Services** (`scraper_manager/services.py`)
   - `ScraperService`: Business logic for scraper execution
   - Handles scraper discovery, execution, and error handling

3. **API Views** (`scraper_manager/api.py`)
   - REST API endpoints using Django REST Framework
   - JWT authentication for protected endpoints

4. **Admin Interface** (`scraper_manager/admin.py`)
   - Django admin integration for managing scrapers

## Available Scrapers

| Scraper ID | Name | Description |
|-----------|------|-------------|
| `aviation` | Aviation Job Search | Scrapes jobs from aviationjobsearch.com |
| `airindia` | Air India | Scrapes jobs from Air India careers page |
| `goose` | Goose Recruitment | Scrapes jobs from Goose Recruitment |
| `linkedin` | LinkedIn | Scrapes aviation jobs from LinkedIn |

## API Endpoints

### 1. List Scrapers
**Endpoint:** `GET /api/scrapers/list/`  
**Authentication:** Not required  
**Description:** List all available scrapers with their current status

**Response:**
```json
{
  "count": 4,
  "scrapers": [
    {
      "id": "aviation",
      "name": "Aviation Job Search",
      "description": "Scrapes aviation jobs from aviationjobsearch.com",
      "available": true,
      "enabled": true,
      "last_run": "2025-11-21T06:30:00Z",
      "total_runs": 10,
      "successful_runs": 9,
      "failed_runs": 1,
      "recent_jobs_count": 5,
      "recent_success_rate": 90.0
    }
  ]
}
```

### 2. Start Scraper
**Endpoint:** `POST /api/scrapers/start/`  
**Authentication:** Required (JWT)  
**Description:** Start a scraper job

**Request Body:**
```json
{
  "scraper": "aviation",  // or "airindia", "goose", "linkedin", "all"
  "async": false  // optional, default false
}
```

**Response (Synchronous):**
```json
{
  "message": "Scraper completed successfully",
  "job_id": 1,
  "status": "completed",
  "jobs_found": 25,
  "execution_time": 45.2,
  "success": true
}
```

**Response (Asynchronous - 202 Accepted):**
```json
{
  "message": "Scraper aviation started in background",
  "job_id": 1,
  "status": "running"
}
```

### 3. Scraper Status
**Endpoint:** `GET /api/scrapers/status/<job_id>/`  
**Authentication:** Not required  
**Description:** Get the status of a specific scraper job

**Response:**
```json
{
  "job_id": 1,
  "scraper": "aviation",
  "status": "completed",
  "started_at": "2025-11-21T06:30:00Z",
  "completed_at": "2025-11-21T06:30:45Z",
  "execution_time": 45.2,
  "jobs_found": 25,
  "jobs_new": 15,
  "jobs_updated": 8,
  "jobs_duplicates": 2,
  "error_message": null,
  "triggered_by": "admin"
}
```

**Job Statuses:**
- `pending`: Job created but not started
- `running`: Currently executing
- `completed`: Successfully finished
- `failed`: Encountered an error

### 4. Scraper History
**Endpoint:** `GET /api/scrapers/history/`  
**Authentication:** Not required  
**Description:** Get scraper execution history

**Query Parameters:**
- `scraper` (optional): Filter by scraper name
- `status` (optional): Filter by job status
- `limit` (optional): Maximum number of records (default: 20)

**Example:**
```
GET /api/scrapers/history/?scraper=aviation&status=completed&limit=10
```

**Response:**
```json
{
  "count": 10,
  "jobs": [
    {
      "id": 1,
      "scraper": "aviation",
      "status": "completed",
      "started_at": "2025-11-21T06:30:00Z",
      "completed_at": "2025-11-21T06:30:45Z",
      "execution_time": 45.2,
      "jobs_found": 25,
      "jobs_new": 15,
      "error_message": null,
      "triggered_by": "admin"
    }
  ]
}
```

### 5. Scraper Statistics
**Endpoint:** `GET /api/scrapers/stats/`  
**Authentication:** Not required  
**Description:** Get overall scraper statistics

**Response:**
```json
{
  "overall": {
    "total_executions": 100,
    "completed": 95,
    "failed": 5,
    "running": 0,
    "success_rate": 95.0
  },
  "by_scraper": [
    {
      "scraper_name": "aviation",
      "total": 50,
      "completed": 48,
      "failed": 2
    }
  ],
  "recent_activity": {
    "last_7_days": 15
  },
  "total_jobs_scraped": 1250
}
```

## Authentication

Protected endpoints (like starting scrapers) require JWT authentication:

1. **Get Token:** Login via `/api/auth/login/`
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

2. **Use Token:** Include in Authorization header
```bash
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"scraper": "aviation", "async": true}'
```

## Usage Examples

### 1. List All Scrapers
```bash
curl http://localhost:8000/api/scrapers/list/
```

### 2. Start Scraper (Synchronous)
```bash
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"scraper": "aviation", "async": false}'
```

### 3. Start Scraper (Asynchronous)
```bash
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"scraper": "aviation", "async": true}'
```

### 4. Run All Scrapers
```bash
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{"scraper": "all", "async": true}'
```

### 5. Check Job Status
```bash
curl http://localhost:8000/api/scrapers/status/1/
```

### 6. Get Recent History
```bash
curl "http://localhost:8000/api/scrapers/history/?limit=5"
```

### 7. Get Statistics
```bash
curl http://localhost:8000/api/scrapers/stats/
```

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Login
response = requests.post(
    f"{BASE_URL}/auth/login/",
    json={"username": "admin", "password": "password"}
)
token = response.json()["access"]

# List scrapers
response = requests.get(f"{BASE_URL}/scrapers/list/")
scrapers = response.json()
print(f"Available scrapers: {scrapers['count']}")

# Start scraper
response = requests.post(
    f"{BASE_URL}/scrapers/start/",
    json={"scraper": "aviation", "async": True},
    headers={"Authorization": f"Bearer {token}"}
)
job_id = response.json()["job_id"]
print(f"Job started: {job_id}")

# Check status
import time
time.sleep(5)
response = requests.get(f"{BASE_URL}/scrapers/status/{job_id}/")
status = response.json()
print(f"Job status: {status['status']}")
print(f"Jobs found: {status['jobs_found']}")
```

## Database Schema

### ScraperJob Model
```python
{
    "id": Integer (Auto),
    "scraper_name": String(100),
    "status": String(20),  # pending, running, completed, failed
    "started_at": DateTime,
    "completed_at": DateTime,
    "execution_time": Float (seconds),
    "jobs_found": Integer,
    "jobs_new": Integer,
    "jobs_updated": Integer,
    "jobs_duplicates": Integer,
    "error_message": Text,
    "triggered_by": String(100),
    "created_at": DateTime (Auto),
    "updated_at": DateTime (Auto)
}
```

### ScraperConfig Model
```python
{
    "id": Integer (Auto),
    "scraper_name": String(100, Unique),
    "is_enabled": Boolean (default: True),
    "settings": JSON,
    "last_run": DateTime,
    "total_runs": Integer,
    "successful_runs": Integer,
    "failed_runs": Integer,
    "created_at": DateTime (Auto),
    "updated_at": DateTime (Auto)
}
```

## Testing

Run the comprehensive test suite:

```bash
python test_scraper_apis.py
```

The test suite covers:
- ✓ Server health check
- ✓ User authentication
- ✓ List scrapers
- ✓ Scraper statistics
- ✓ Unauthorized access blocking
- ✓ Scraper history
- ✓ Async scraper execution
- ✓ Job status monitoring

## Error Handling

### Common Errors

**400 Bad Request**
```json
{
  "error": "scraper parameter is required"
}
```

**401 Unauthorized**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

**403 Forbidden**
```json
{
  "error": "Scraper aviation is disabled"
}
```

**404 Not Found**
```json
{
  "error": "Job not found"
}
```

**500 Internal Server Error**
```json
{
  "error": "Error message details"
}
```

## Best Practices

1. **Use Async for Long-Running Jobs**: Set `"async": true` for scrapers that take more than a few seconds

2. **Monitor Job Status**: Use the status endpoint to track progress of async jobs

3. **Handle Rate Limits**: Some websites may rate-limit scraping; use appropriate delays

4. **Check Scraper Availability**: Use the list endpoint to verify scrapers are available before starting

5. **Review Error Messages**: Check `error_message` field in job status for debugging

## Admin Interface

Access the Django admin to:
- View all scraper jobs
- Enable/disable scrapers
- Configure scraper settings
- View detailed statistics

URL: `http://localhost:8000/admin/scraper_manager/`

## Troubleshooting

### Scraper Not Starting
- Check if scraper is enabled in `ScraperConfig`
- Verify authentication token is valid
- Review Django logs for errors

### Job Stuck in "Running" Status
- Check scraper process logs
- Verify scraper dependencies are installed
- May need manual database update if process crashed

### No Jobs Found
- Verify target website is accessible
- Check scraper logic in `scrapers/` directory
- Review error messages in job details

## Future Enhancements

- [ ] Scheduled scraping (cron integration)
- [ ] Email notifications on completion/failure
- [ ] Webhook support for job status updates
- [ ] Scraper rate limiting configuration
- [ ] Job cancellation endpoint
- [ ] Real-time progress updates via WebSocket
- [ ] Scraper performance metrics
- [ ] Data export functionality

## Related Documentation

- [API Quick Reference](API_QUICK_REFERENCE.md)
- [Authentication Guide](JWT_AUTHENTICATION.md)
- [Database Setup](POSTGRESQL_INTEGRATION.md)
- [Scraper Development](scrapers/README_UNIFIED_SCRAPER.md)

## Support

For issues or questions:
1. Check Django server logs: `logs/` directory
2. Review test output: `python test_scraper_apis.py`
3. Check scraper logs: `scrapers/logs/`
4. Verify database connections and migrations
