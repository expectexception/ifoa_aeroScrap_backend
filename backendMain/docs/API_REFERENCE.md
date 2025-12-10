# 🚀 API Quick Reference Guide

**AeroScrap Backend - Complete API Endpoints**

---

## 📊 Summary

- **Total Endpoints**: 31+ REST API endpoints
- **Base URL**: `http://localhost:8000/api/`
- **Authentication**: Bearer token for protected endpoints
- **Response Format**: JSON

---

## 🎯 Quick Examples

### Search for Jobs
```bash
# Simple search
curl "http://localhost:8000/api/jobs/search?q=pilot"

# Advanced search with filters
curl "http://localhost:8000/api/jobs/advanced-search?q=captain&countries=US,UK&senior_only=true&sort_by=posted_date"
```

### Get Company Information
```bash
# Company profile
curl "http://localhost:8000/api/jobs/companies/Delta%20Airlines"

# Trending companies
curl "http://localhost:8000/api/jobs/companies/trending?days=7"
```

### Analytics
```bash
# Job trends
curl "http://localhost:8000/api/jobs/analytics/trends?days=30"

# Geographic distribution
curl "http://localhost:8000/api/jobs/analytics/geographic"
```

### Recent Activity
```bash
# Jobs added in last 24 hours
curl "http://localhost:8000/api/jobs/recent?hours=24&limit=20"

# Recently updated jobs
curl "http://localhost:8000/api/jobs/updated?hours=48"
```

### Export Data
```bash
# Export as JSON
curl "http://localhost:8000/api/jobs/export/json?country=US&limit=500" -o jobs.json

# Export as CSV
curl "http://localhost:8000/api/jobs/export/daily.csv?date=2025-11-20" -o jobs.csv
```

### Compare Jobs
```bash
# Find similar jobs
curl "http://localhost:8000/api/jobs/similar/123?limit=10"

# Compare specific jobs
curl -X POST "http://localhost:8000/api/jobs/compare" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1, 2, 3, 4]}'
```

---

## 📡 All Endpoints by Category

### 🔍 SEARCH & FILTERING

#### Basic Search
- **GET** `/api/jobs/search`
  - Query: `q`, `limit`
  - Search across title, company, description

#### Advanced Search
- **GET** `/api/jobs/advanced-search`
  - Query: `q`, `countries`, `operation_types`, `senior_only`, `date_from`, `date_to`, `status`, `sort_by`, `order`, `skip`, `limit`
  - Multi-filter search with sorting and pagination

#### List Jobs
- **GET** `/api/jobs/`
  - Query: `skip`, `limit`, `country`, `type`, `senior`, `company`, `title`
  - Basic job listing with simple filters

---

### 🏢 COMPANY APIs

#### List Companies
- **GET** `/api/jobs/companies`
  - Query: `skip`, `limit`
  - Returns all companies with job counts

#### Company Profile
- **GET** `/api/jobs/companies/{company_name}`
  - Returns detailed statistics, locations, operation types

#### Company Jobs
- **GET** `/api/jobs/companies/{company_name}/jobs`
  - Query: `skip`, `limit`
  - All jobs from specific company

#### Trending Companies
- **GET** `/api/jobs/companies/trending`
  - Query: `days`, `limit`
  - Companies with most recent postings

---

### 📈 ANALYTICS & INSIGHTS

#### Job Trends
- **GET** `/api/jobs/analytics/trends`
  - Query: `days`
  - Daily job posting trends and growth rate

#### Geographic Distribution
- **GET** `/api/jobs/analytics/geographic`
  - Jobs by country/location

#### Operation Type Stats
- **GET** `/api/jobs/analytics/operation-types`
  - Jobs by type (Airline, MRO, Airport, etc.)

#### Quick Stats
- **GET** `/api/jobs/stats`
  - Total jobs, top companies, country breakdown

---

### ⏰ RECENT ACTIVITY

#### Recently Added
- **GET** `/api/jobs/recent`
  - Query: `hours`, `limit`
  - Jobs added in last N hours

#### Recently Updated
- **GET** `/api/jobs/updated`
  - Query: `hours`, `limit`
  - Jobs modified in last N hours

#### Senior Alerts
- **GET** `/api/jobs/alerts/senior`
  - Query: `hours`
  - Recent senior positions

---

### 🔄 JOB COMPARISON

#### Compare Jobs
- **POST** `/api/jobs/compare`
  - Body: `{"job_ids": [1, 2, 3]}`
  - Compare multiple jobs side-by-side (max 10)

#### Similar Jobs
- **GET** `/api/jobs/similar/{job_id}`
  - Query: `limit`
  - Find jobs similar to given job

---

### 📥 EXPORT & REPORTS

#### JSON Export
- **GET** `/api/jobs/export/json`
  - Query: `country`, `operation_type`, `status`, `limit`
  - Download jobs as JSON file

#### CSV Export (Daily)
- **GET** `/api/jobs/export/daily.csv`
  - Query: `date` (YYYY-MM-DD)
  - Download daily report as CSV

---

### 📝 JOB MANAGEMENT

#### Get Single Job
- **GET** `/api/jobs/id/{job_id}`
  - Full job details

#### Ingest Single Job
- **POST** `/api/jobs/ingest` 🔒
  - Body: Job object
  - Auth required

#### Bulk Ingest
- **POST** `/api/jobs/bulk_ingest` 🔒
  - Body: Array of job objects
  - Auth required

#### Update Job
- **PATCH** `/api/jobs/{job_id}` 🔒
  - Body: Fields to update
  - Auth required

#### Delete Job
- **DELETE** `/api/jobs/{job_id}` 🔒
  - Auth required

---

### 🤖 SCRAPER MANAGEMENT

#### Scraper Status
- **GET** `/api/jobs/admin/scrapers/status` 🔒
  - Recent runs by scraper
  - Auth required

#### Scraper Logs
- **GET** `/api/jobs/admin/scrapers/logs` 🔒
  - Query: `source`, `limit`
  - Detailed execution logs
  - Auth required

---

### 🏭 COMPANY MAPPINGS

#### List Mappings
- **GET** `/api/jobs/admin/company-mappings` 🔒
  - Query: `skip`, `limit`
  - Auth required

#### Create Mapping
- **POST** `/api/jobs/admin/company-mappings` 🔒
  - Body: Company mapping object
  - Auth required

#### Update Mapping
- **PUT** `/api/jobs/admin/company-mappings/{id}` 🔒
  - Body: Updated fields
  - Auth required

#### Delete Mapping
- **DELETE** `/api/jobs/admin/company-mappings/{id}` 🔒
  - Auth required

#### Unknown Companies
- **GET** `/api/jobs/admin/unknown-companies` 🔒
  - Query: `limit`
  - Companies without mappings
  - Auth required

---

### 🏥 HEALTH & STATUS

#### Health Check
- **GET** `/api/jobs/health`
  - Returns `{"ok": true, "db": "ok"}`

---

### 📄 RESUME APIs

#### Upload Resume
- **POST** `/api/upload-resume`
  - Form-data: `file`
  - Parse and store resume

#### Upload with Metadata
- **POST** `/api/upload-resume-with-info`
  - Form-data: `file`, `metadata`
  - Upload with structured data

#### List Resumes
- **GET** `/api/resumes`
  - Query: `skip`, `limit`, `search`

#### Get Resume
- **GET** `/api/resumes/{id}`
  - Full resume details

#### Download Resume
- **GET** `/api/resumes/{id}/download`
  - Download original file

#### Delete Resume
- **DELETE** `/api/resumes/{id}`
  - Remove resume

#### Resume Stats
- **GET** `/api/stats`
  - Aggregate resume statistics

---

## 🔐 Authentication

### For Protected Endpoints (marked with 🔒)

```bash
# Set API key in environment
export API_KEY="your-api-key-here"

# Use in request
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/jobs/ingest"
```

### Configure API Key
Set `ADMIN_API_KEY` in `.env` file:
```bash
ADMIN_API_KEY='your-secure-api-key-here'
```

---

## 📊 Response Formats

### Success Response
```json
{
  "id": 123,
  "title": "Senior Captain",
  "company": "Delta Airlines",
  "status": "active"
}
```

### List Response
```json
{
  "total": 150,
  "skip": 0,
  "limit": 50,
  "results": [...]
}
```

### Error Response
```json
{
  "error": "Job not found"
}
```

---

## 🎨 Query Parameter Formats

### Dates
```
YYYY-MM-DD
Example: 2025-11-20
```

### Multiple Values
```
Comma-separated
Example: countries=US,UK,CA
```

### Boolean
```
true or false
Example: senior_only=true
```

### Sorting
```
Field: created_at, posted_date, title, company
Order: asc, desc
Example: sort_by=posted_date&order=desc
```

---

## 🚀 Common Use Cases

### 1. Build a Job Board
```bash
# Get recent jobs
GET /api/jobs/recent?hours=48&limit=20

# Search with filters
GET /api/jobs/advanced-search?q=pilot&countries=US&senior_only=false

# Get company details
GET /api/jobs/companies/Delta%20Airlines
```

### 2. Market Analysis
```bash
# View trends
GET /api/jobs/analytics/trends?days=90

# Geographic distribution
GET /api/jobs/analytics/geographic

# Top companies
GET /api/jobs/companies?limit=50
```

### 3. Automated Reporting
```bash
# Daily export
GET /api/jobs/export/daily.csv?date=2025-11-20

# Bulk JSON export
GET /api/jobs/export/json?status=active&limit=5000
```

### 4. Job Recommendations
```bash
# Find similar jobs
GET /api/jobs/similar/123

# Compare opportunities
POST /api/jobs/compare (body: {"job_ids": [1,2,3,4]})
```

### 5. Monitor Scrapers
```bash
# Check scraper status
GET /api/jobs/admin/scrapers/status

# View logs
GET /api/jobs/admin/scrapers/logs?source=aviation_jobs
```

---

## 📞 Support

### Testing Endpoints
Use the interactive API docs:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc` (if enabled)

### Health Checks
```bash
# API health
curl http://localhost:8000/api/jobs/health

# Database check
python manage.py check --database default
```

### Logs
- API logs: `logs/django.log`
- Errors: `logs/django_errors.log`

---

**Last Updated**: November 20, 2025  
**API Version**: 2.0  
**Total Endpoints**: 31+
