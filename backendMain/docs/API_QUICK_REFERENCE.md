# Quick API Reference Guide

## Base URL
```
http://localhost:8000/api
```

## Authentication
Most endpoints are public. Admin endpoints require Bearer token via `ADMIN_API_KEY` environment variable.

---

## Most Used Endpoints

### 1. Advanced Job Search
**Endpoint**: `GET /jobs/advanced-search/`

**All Parameters** (all optional):
```
q             - Search text (searches title, company, description)
countries     - Comma-separated country codes (e.g., "US,UK,UAE")
operation_types - Comma-separated types (e.g., "Passenger,Cargo")
senior_only   - "true" or "false" as string
date_from     - Date in YYYY-MM-DD format
date_to       - Date in YYYY-MM-DD format
status        - "active" or "closed" (default: "active")
sort_by       - "posted_date", "title", "company", "created_at"
order         - "asc" or "desc" (default: "desc")
skip          - Pagination offset (default: 0)
limit         - Results per page (default: 50, max: 100)
```

**Example**:
```bash
curl "http://localhost:8000/api/jobs/advanced-search/?q=pilot&countries=US,UK&senior_only=true&limit=20"
```

**Response**:
```json
{
  "count": 45,
  "results": [
    {
      "id": 1,
      "title": "Senior Pilot",
      "company": "Delta Airlines",
      "country": "US",
      "location": "Atlanta, GA",
      "operation_type": "Passenger",
      "is_senior_position": true,
      "posted_date": "2025-11-15T10:30:00Z",
      "status": "active"
    }
  ]
}
```

---

### 2. List All Companies
**Endpoint**: `GET /jobs/companies/`

**Parameters**:
- `limit` - Max companies to return (default: 100)

**Example**:
```bash
curl "http://localhost:8000/api/jobs/companies/?limit=10"
```

**Response**:
```json
{
  "companies": [
    {
      "company": "Delta Airlines",
      "total_jobs": 25,
      "active_jobs": 18,
      "countries": ["US", "UK"],
      "operation_types": ["Passenger", "Cargo"]
    }
  ]
}
```

---

### 3. Company Profile
**Endpoint**: `GET /jobs/companies/{company_name}/`

**Example**:
```bash
curl "http://localhost:8000/api/jobs/companies/Delta%20Airlines/"
```

**Response**:
```json
{
  "name": "Delta Airlines",
  "total_jobs": 25,
  "active_jobs": 18,
  "closed_jobs": 7,
  "countries": ["US", "UK", "UAE"],
  "locations": ["Atlanta, GA", "New York, NY"],
  "operation_types": ["Passenger", "Cargo"],
  "hiring_trends": {
    "last_7_days": 3,
    "last_30_days": 12
  }
}
```

---

### 4. Trending Companies
**Endpoint**: `GET /jobs/companies/trending/`

**Parameters**:
- `days` - Analysis period in days (default: 30)
- `limit` - Max companies (default: 10)

**Example**:
```bash
curl "http://localhost:8000/api/jobs/companies/trending/?days=7&limit=5"
```

**Response**:
```json
{
  "companies": [
    {
      "company": "Delta Airlines",
      "new_jobs": 12,
      "growth_percentage": 15.5
    }
  ]
}
```

---

### 5. Recent Jobs
**Endpoint**: `GET /jobs/recent/`

**Parameters**:
- `hours` - Lookback period in hours (default: 48)
- `limit` - Max jobs (default: 10)

**Example**:
```bash
curl "http://localhost:8000/api/jobs/recent/?hours=24&limit=5"
```

**Response**:
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Senior Pilot",
      "company": "Delta Airlines",
      "country": "US",
      "location": "Atlanta, GA",
      "operation_type": "Passenger",
      "is_senior_position": true,
      "posted_date": "2025-11-20T08:30:00Z",
      "status": "active"
    }
  ]
}
```

---

### 6. Job Analytics - Trends
**Endpoint**: `GET /jobs/analytics/trends/`

**Parameters**:
- `days` - Period to analyze (default: 30)

**Example**:
```bash
curl "http://localhost:8000/api/jobs/analytics/trends/?days=30"
```

**Response**:
```json
{
  "total_jobs": 150,
  "average_per_day": 5.0,
  "daily_trends": [
    {
      "date": "2025-11-15",
      "count": 8
    }
  ]
}
```

---

### 7. Geographic Distribution
**Endpoint**: `GET /jobs/analytics/geographic/`

**Example**:
```bash
curl "http://localhost:8000/api/jobs/analytics/geographic/"
```

**Response**:
```json
{
  "total_countries": 15,
  "distribution": [
    {
      "country": "US",
      "count": 75
    },
    {
      "country": "UK",
      "count": 45
    }
  ]
}
```

---

### 8. Operation Type Stats
**Endpoint**: `GET /jobs/analytics/operation-types/`

**Example**:
```bash
curl "http://localhost:8000/api/jobs/analytics/operation-types/"
```

**Response**:
```json
{
  "total_types": 5,
  "distribution": [
    {
      "operation_type": "Passenger",
      "count": 120
    },
    {
      "operation_type": "Cargo",
      "count": 80
    }
  ]
}
```

---

### 9. Compare Jobs
**Endpoint**: `POST /jobs/compare/`

**Example**:
```bash
curl -X POST "http://localhost:8000/api/jobs/compare/" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1, 2, 3]}'
```

**Response**:
```json
{
  "jobs": [
    {
      "id": 1,
      "title": "Senior Pilot",
      "company": "Delta Airlines",
      "country": "US",
      "location": "Atlanta, GA",
      "operation_type": "Passenger",
      "is_senior_position": true,
      "posted_date": "2025-11-15T10:30:00Z",
      "status": "active"
    }
  ],
  "summary": {
    "common_fields": {
      "country": "US",
      "operation_type": "Passenger"
    },
    "differences": [
      "Company names differ",
      "Experience requirements differ"
    ]
  }
}
```

---

### 10. Similar Jobs
**Endpoint**: `GET /jobs/similar/{job_id}/`

**Parameters**:
- `limit` - Max similar jobs (default: 5)

**Example**:
```bash
curl "http://localhost:8000/api/jobs/similar/123/?limit=5"
```

**Response**:
```json
{
  "jobs": [
    {
      "id": 2,
      "title": "Pilot",
      "company": "United Airlines",
      "country": "US",
      "location": "Chicago, IL",
      "operation_type": "Passenger",
      "is_senior_position": false,
      "posted_date": "2025-11-18T10:30:00Z",
      "status": "active"
    }
  ]
}
```

---

## Admin Endpoints (Require API Key)

### Ingest Single Job
**Endpoint**: `POST /jobs/ingest`

**Headers**:
```
Authorization: Bearer YOUR_API_KEY
```

**Body**:
```json
{
  "title": "Senior Pilot",
  "company": "Delta Airlines",
  "country_code": "US",
  "operation_type": "Passenger",
  "posted_date": "2025-11-20",
  "url": "https://example.com/job/123",
  "description": "...",
  "senior_flag": true
}
```

---

### Bulk Ingest Jobs
**Endpoint**: `POST /jobs/bulk_ingest`

**Headers**:
```
Authorization: Bearer YOUR_API_KEY
```

**Body**:
```json
[
  {
    "title": "Pilot",
    "company": "American Airlines",
    "url": "https://example.com/job/1"
  },
  {
    "title": "Co-Pilot",
    "company": "United Airlines",
    "url": "https://example.com/job/2"
  }
]
```

**Response**:
```json
{
  "results": [
    {"status": "created", "id": 1},
    {"status": "updated", "id": 2}
  ],
  "found": 2,
  "inserted": 1,
  "updated": 1,
  "errors": []
}
```

---

## Resume Endpoints

### Upload Resume
**Endpoint**: `POST /upload-resume`

**Body**: multipart/form-data with `file` field

**Example**:
```bash
curl -X POST "http://localhost:8000/api/upload-resume" \
  -F "file=@resume.pdf"
```

---

### List Resumes
**Endpoint**: `GET /resumes`

**Parameters**:
- `skip` - Offset (default: 0)
- `limit` - Per page (default: 20)
- `search` - Search in name/email

**Example**:
```bash
curl "http://localhost:8000/api/resumes?limit=10"
```

**Response**:
```json
{
  "count": 50,
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "skills": ["Python", "Django"],
      "total_score": 85
    }
  ]
}
```

---

## Error Responses

### 404 Not Found
```json
{
  "detail": "Company not found"
}
```

### 400 Bad Request
```json
{
  "detail": "Invalid parameters"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid API key"
}
```

---

## Common Query Patterns

### Get all senior positions in US
```bash
curl "http://localhost:8000/api/jobs/advanced-search/?countries=US&senior_only=true"
```

### Get recent jobs from last 24 hours
```bash
curl "http://localhost:8000/api/jobs/recent/?hours=24"
```

### Get all Passenger operations in Europe
```bash
curl "http://localhost:8000/api/jobs/advanced-search/?operation_types=Passenger&countries=UK,FR,DE"
```

### Get top 5 trending companies this week
```bash
curl "http://localhost:8000/api/jobs/companies/trending/?days=7&limit=5"
```

### Search for "dispatcher" jobs sorted by date
```bash
curl "http://localhost:8000/api/jobs/advanced-search/?q=dispatcher&sort_by=posted_date&order=desc"
```

---

## Testing Tips

1. **Use trailing slashes**: Most endpoints require trailing `/`
2. **URL encode parameters**: Spaces and special characters must be encoded
3. **Check response keys**: All list endpoints return `{count, results}` format
4. **Date format**: Use ISO 8601 format (YYYY-MM-DD)
5. **Boolean strings**: Use "true" or "false" as strings, not booleans

---

## Frontend Integration Example (JavaScript)

```javascript
// Advanced search
const searchJobs = async (query, countries, seniorOnly) => {
  const params = new URLSearchParams({
    q: query,
    countries: countries.join(','),
    senior_only: seniorOnly ? 'true' : 'false',
    limit: 20
  });
  
  const response = await fetch(
    `http://localhost:8000/api/jobs/advanced-search/?${params}`
  );
  const data = await response.json();
  
  console.log(`Found ${data.count} jobs`);
  return data.results;
};

// Get company profile
const getCompanyProfile = async (companyName) => {
  const encoded = encodeURIComponent(companyName);
  const response = await fetch(
    `http://localhost:8000/api/jobs/companies/${encoded}/`
  );
  return await response.json();
};

// Compare jobs
const compareJobs = async (jobIds) => {
  const response = await fetch(
    'http://localhost:8000/api/jobs/compare/',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_ids: jobIds })
    }
  );
  return await response.json();
};
```

---

## Performance Notes

- All endpoints support pagination via `skip` and `limit`
- Maximum limit is typically 100 for performance
- Database indexes enable fast filtering by country, type, company, date
- Use specific filters to reduce result set size
- Consider caching frequently accessed data on frontend

---

**Last Updated**: November 20, 2025  
**API Version**: 1.0  
**Base URL**: `http://localhost:8000/api`
