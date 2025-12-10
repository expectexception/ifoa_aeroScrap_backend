# Backend API Implementation Request

I need you to implement the following new API endpoints for my Django backend. The frontend is already built and waiting for these endpoints.

## Requirements:
- Base URL: `/api/jobs/`
- All endpoints should return JSON
- Use existing Job model
- Response format must match the examples below
- All dates in ISO 8601 format (e.g., `2025-11-20T10:30:00Z`)

---

## 1. Advanced Search Endpoint
**Endpoint:** `GET /api/jobs/advanced-search`

**Query Parameters:**
- `q` (optional): Search text for title, company, description
- `countries` (optional): Comma-separated country codes (e.g., "US,UK,UAE")
- `operation_types` (optional): Comma-separated types (e.g., "Passenger,Cargo")
- `senior_only` (optional): Boolean string "true" or "false"
- `date_from` (optional): Date string YYYY-MM-DD
- `date_to` (optional): Date string YYYY-MM-DD
- `status` (optional): "active" or "closed"
- `sort_by` (optional): Field name like "posted_date", "title", "company"
- `order` (optional): "asc" or "desc"
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Items per page (default: 20)

**Response Format:**
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

## 2. Company Endpoints

### 2.1 List Companies
**Endpoint:** `GET /api/jobs/companies`

**Query Parameters:**
- `limit` (optional): Max companies to return (default: 100)

**Response:**
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

### 2.2 Company Profile
**Endpoint:** `GET /api/jobs/companies/{company_name}`

**Response:**
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

### 2.3 Company Jobs
**Endpoint:** `GET /api/jobs/companies/{company_name}/jobs`

**Query Parameters:**
- `skip` (optional): Pagination offset (default: 0)
- `limit` (optional): Items per page (default: 20)

**Response:**
```json
{
  "count": 25,
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
  ]
}
```

### 2.4 Trending Companies
**Endpoint:** `GET /api/jobs/companies/trending`

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)
- `limit` (optional): Max companies to return (default: 10)

**Response:**
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

## 3. Analytics Endpoints

### 3.1 Job Trends
**Endpoint:** `GET /api/jobs/analytics/trends`

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 30)

**Response:**
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

### 3.2 Geographic Distribution
**Endpoint:** `GET /api/jobs/analytics/geographic`

**Response:**
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

### 3.3 Operation Type Stats
**Endpoint:** `GET /api/jobs/analytics/operation-types`

**Response:**
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

## 4. Activity Feed Endpoints

### 4.1 Recent Jobs
**Endpoint:** `GET /api/jobs/recent`

**Query Parameters:**
- `hours` (optional): Number of hours to look back (default: 48)
- `limit` (optional): Max jobs to return (default: 10)

**Response:**
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

### 4.2 Updated Jobs
**Endpoint:** `GET /api/jobs/updated`

**Query Parameters:**
- `hours` (optional): Number of hours to look back (default: 24)
- `limit` (optional): Max jobs to return (default: 10)

**Response:**
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
      "last_updated": "2025-11-20T14:20:00Z",
      "status": "active"
    }
  ]
}
```

**Note:** You may need to add `last_updated` field to Job model:
```python
last_updated = models.DateTimeField(auto_now=True)
```

---

## 5. Comparison Endpoints

### 5.1 Compare Jobs
**Endpoint:** `POST /api/jobs/compare`

**Request Body:**
```json
{
  "job_ids": [1, 2, 3]
}
```

**Response:**
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

### 5.2 Similar Jobs
**Endpoint:** `GET /api/jobs/similar/{job_id}`

**Query Parameters:**
- `limit` (optional): Max similar jobs to return (default: 5)

**Response:**
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

## Important Notes:
1. **ALL ENDPOINTS MUST HAVE TRAILING SLASHES** (Django default: `/api/jobs/recent/` not `/api/jobs/recent`)
2. All GET endpoints should support CORS for `http://localhost:3000` and `http://192.168.205.117:3000`
3. Comma-separated parameters should be split and treated as arrays
4. Boolean parameters come as strings ("true"/"false") and need conversion
5. Empty comma-separated values should be ignored (e.g., `countries=` or `countries=,`)
6. Date filters should use Django's `__gte` and `__lte` lookups
7. Text search should use `__icontains` across title, company, and description fields
8. All endpoints should handle missing/invalid parameters gracefully
9. Return 404 if company name not found in company-specific endpoints

## Priority Order:
1. Advanced search (most important for frontend)
2. Company endpoints
3. Analytics endpoints
4. Activity feeds
5. Comparison endpoints

---

## Django Implementation Example

### URL Configuration (urls.py)
```python
from django.urls import path
from . import views

urlpatterns = [
    # Advanced search
    path('jobs/advanced-search', views.advanced_search, name='advanced_search'),
    
    # Companies
    path('jobs/companies', views.list_companies, name='list_companies'),
    path('jobs/companies/trending', views.trending_companies, name='trending_companies'),
    path('jobs/companies/<str:name>', views.company_profile, name='company_profile'),
    path('jobs/companies/<str:name>/jobs', views.company_jobs, name='company_jobs'),
    
    # Analytics
    path('jobs/analytics/trends', views.job_trends, name='job_trends'),
    path('jobs/analytics/geographic', views.geographic_distribution, name='geographic_distribution'),
    path('jobs/analytics/operation-types', views.operation_type_stats, name='operation_type_stats'),
    
    # Activity feeds
    path('jobs/recent', views.recent_jobs, name='recent_jobs'),
    path('jobs/updated', views.updated_jobs, name='updated_jobs'),
    
    # Comparison
    path('jobs/compare', views.compare_jobs, name='compare_jobs'),
    path('jobs/similar/<int:id>', views.similar_jobs, name='similar_jobs'),
]
```

### Model Update (models.py)
```python
from django.db import models

class Job(models.Model):
    # ... existing fields ...
    
    # Add this field if not present:
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_date']
```

### Migration Commands
```bash
python manage.py makemigrations
python manage.py migrate
```

---

## Testing Endpoints

After implementation, test each endpoint:

```bash
# Advanced search
curl "http://localhost:8000/api/jobs/advanced-search?q=pilot&countries=US&senior_only=true"

# List companies
curl "http://localhost:8000/api/jobs/companies?limit=10"

# Company profile
curl "http://localhost:8000/api/jobs/companies/Delta%20Airlines"

# Job trends
curl "http://localhost:8000/api/jobs/analytics/trends?days=30"

# Recent jobs
curl "http://localhost:8000/api/jobs/recent?hours=48&limit=10"
```

---

## Expected Frontend Integration

Once these endpoints are implemented, the frontend will:
- Use Advanced Search page with multiple filters
- Display company directory with profiles
- Show analytics dashboard with charts
- Display recent and updated job feeds
- Enable job comparison features

All frontend code is already built and waiting for these backend endpoints to return data in the specified format.
