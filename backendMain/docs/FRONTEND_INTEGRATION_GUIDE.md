# Frontend Integration Guide
## AeroScrap Backend API v2.0

**Document Version:** 1.0  
**API Version:** 2.0  
**Last Updated:** November 20, 2025  
**Base URL:** `http://localhost:8000` (Development) | `https://your-domain.com` (Production)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [API Changes Summary](#api-changes-summary)
4. [Core Job Endpoints](#core-job-endpoints)
5. [New Advanced Search](#new-advanced-search)
6. [Company Intelligence APIs](#company-intelligence-apis)
7. [Analytics & Insights](#analytics--insights)
8. [Recent Activity & Feeds](#recent-activity--feeds)
9. [Job Comparison Features](#job-comparison-features)
10. [Data Export](#data-export)
11. [Error Handling](#error-handling)
12. [Response Formats](#response-formats)
13. [Integration Examples](#integration-examples)
14. [Performance Tips](#performance-tips)

---

## 🎯 Overview

### What Changed in v2.0?

The backend has been significantly enhanced with **15+ new endpoints** that provide:
- **Advanced multi-filter search** for better job discovery
- **Company intelligence** to research employers
- **Analytics dashboards** for market insights
- **Job comparison tools** for better decision making
- **Real-time activity feeds** for new job alerts
- **Enhanced data exports** in multiple formats

### API Growth
- **Before:** 16 endpoints
- **After:** 31+ endpoints
- **Growth:** 94% increase in functionality

### Key Benefits for Frontend
✅ More powerful search capabilities  
✅ Better user experience with company profiles  
✅ Data visualization ready (trends, charts, maps)  
✅ Job recommendation features  
✅ Real-time job alerts capability  

---

## 🔐 Authentication

### API Key Authentication
All requests require Bearer token authentication (except public endpoints).

**Header Format:**
```javascript
headers: {
  'Authorization': 'Bearer YOUR_API_KEY',
  'Content-Type': 'application/json'
}
```

**Getting API Key:**
Contact backend admin or generate via Django admin panel at `/admin/`.

**Public Endpoints (No Auth Required):**
- `GET /api/jobs/` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `GET /api/jobs/search` - Basic search
- `GET /api/jobs/companies` - List companies
- `GET /api/jobs/analytics/*` - All analytics endpoints

---

## 📊 API Changes Summary

### ✅ Existing Endpoints (Unchanged - Backward Compatible)

All your existing frontend code will continue to work without changes:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/jobs/` | List all jobs (paginated) |
| GET | `/api/jobs/{id}` | Get single job details |
| GET | `/api/jobs/search` | Basic text search |
| POST | `/api/jobs/` | Create new job (admin) |
| PUT | `/api/jobs/{id}` | Update job (admin) |
| DELETE | `/api/jobs/{id}` | Delete job (admin) |
| GET | `/api/jobs/countries` | List all countries |
| GET | `/api/jobs/stats` | Job statistics |
| GET | `/api/jobs/export/csv` | Export as CSV |

### 🆕 New Endpoints (Available Now)

| Category | Endpoint | Purpose |
|----------|----------|---------|
| **Advanced Search** | `GET /api/jobs/advanced-search` | Multi-filter search |
| **Companies** | `GET /api/jobs/companies` | List companies |
| **Companies** | `GET /api/jobs/companies/{name}` | Company profile |
| **Companies** | `GET /api/jobs/companies/{name}/jobs` | Jobs by company |
| **Companies** | `GET /api/jobs/companies/trending` | Trending companies |
| **Analytics** | `GET /api/jobs/analytics/trends` | Job posting trends |
| **Analytics** | `GET /api/jobs/analytics/geographic` | Jobs by location |
| **Analytics** | `GET /api/jobs/analytics/operation-types` | Jobs by type |
| **Activity** | `GET /api/jobs/recent` | Recently added jobs |
| **Activity** | `GET /api/jobs/updated` | Recently updated jobs |
| **Comparison** | `POST /api/jobs/compare` | Compare multiple jobs |
| **Comparison** | `GET /api/jobs/similar/{id}` | Find similar jobs |
| **Export** | `GET /api/jobs/export/json` | Export as JSON |
| **Admin** | `GET /api/jobs/admin/scrapers/status` | Scraper status 🔒 |
| **Admin** | `GET /api/jobs/admin/scrapers/logs` | Scraper logs 🔒 |

🔒 = Requires admin authentication

---

## 📦 Core Job Endpoints

### 1. List All Jobs
```javascript
GET /api/jobs/?skip=0&limit=20

// Response
{
  "count": 150,
  "results": [
    {
      "id": 1,
      "title": "Senior Pilot",
      "company": "Delta Airlines",
      "country": "US",
      "location": "Atlanta, GA",
      "operation_type": "Passenger",
      "experience_required": "5+ years",
      "is_senior_position": true,
      "posted_date": "2025-11-15T10:30:00Z",
      "job_url": "https://...",
      "status": "active",
      "description": "..."
    }
  ]
}
```

**Query Parameters:**
- `skip` (default: 0) - Pagination offset
- `limit` (default: 20) - Items per page

**Frontend Usage:**
- Job listings page
- Homepage job feed
- Infinite scroll implementation

---

### 2. Get Job Details
```javascript
GET /api/jobs/123

// Response
{
  "id": 123,
  "title": "Senior Pilot",
  "company": "Delta Airlines",
  "country": "US",
  "location": "Atlanta, GA",
  "operation_type": "Passenger",
  "experience_required": "5+ years",
  "is_senior_position": true,
  "posted_date": "2025-11-15T10:30:00Z",
  "updated_at": "2025-11-16T14:20:00Z",
  "job_url": "https://...",
  "status": "active",
  "description": "Full job description...",
  "requirements": "Requirements...",
  "benefits": "Benefits..."
}
```

**Frontend Usage:**
- Job detail page
- Job modal/popup
- Application flow

---

### 3. Basic Search (Existing)
```javascript
GET /api/jobs/search?q=pilot&skip=0&limit=20

// Response - Same as List All Jobs
```

**Query Parameters:**
- `q` (required) - Search query
- `skip`, `limit` - Pagination

**Frontend Usage:**
- Simple search bar
- Quick search results

---

## 🔍 New Advanced Search

### **Most Important New Feature for Frontend**

The advanced search endpoint provides powerful multi-filter capabilities.

```javascript
GET /api/jobs/advanced-search?
  q=pilot&
  countries=US,UK,UAE&
  operation_types=Passenger,Cargo&
  senior_only=true&
  date_from=2025-11-01&
  date_to=2025-11-20&
  status=active&
  sort_by=posted_date&
  order=desc&
  skip=0&
  limit=20
```

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `q` | string | No | Search text (title, company, description) | `pilot` |
| `countries` | string | No | Comma-separated country codes | `US,UK,UAE` |
| `operation_types` | string | No | Comma-separated types | `Passenger,Cargo` |
| `senior_only` | boolean | No | Filter senior positions only | `true` |
| `date_from` | string | No | Posted after date (YYYY-MM-DD) | `2025-11-01` |
| `date_to` | string | No | Posted before date (YYYY-MM-DD) | `2025-11-20` |
| `status` | string | No | Job status | `active` / `closed` |
| `sort_by` | string | No | Sort field | `posted_date`, `title`, `company` |
| `order` | string | No | Sort order | `asc` / `desc` |
| `skip` | integer | No | Pagination offset | `0` |
| `limit` | integer | No | Results per page | `20` |

### Response Format
```javascript
{
  "count": 45,
  "filters_applied": {
    "q": "pilot",
    "countries": ["US", "UK"],
    "operation_types": ["Passenger"],
    "senior_only": true,
    "date_range": "2025-11-01 to 2025-11-20"
  },
  "results": [ /* array of jobs */ ]
}
```

### Frontend Implementation Example

**React Component:**
```jsx
import { useState, useEffect } from 'react';

function AdvancedJobSearch() {
  const [filters, setFilters] = useState({
    q: '',
    countries: [],
    operation_types: [],
    senior_only: false,
    date_from: '',
    date_to: '',
    sort_by: 'posted_date',
    order: 'desc'
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const searchJobs = async () => {
    setLoading(true);
    
    // Build query string
    const params = new URLSearchParams();
    if (filters.q) params.append('q', filters.q);
    if (filters.countries.length) params.append('countries', filters.countries.join(','));
    if (filters.operation_types.length) params.append('operation_types', filters.operation_types.join(','));
    if (filters.senior_only) params.append('senior_only', 'true');
    if (filters.date_from) params.append('date_from', filters.date_from);
    if (filters.date_to) params.append('date_to', filters.date_to);
    params.append('sort_by', filters.sort_by);
    params.append('order', filters.order);
    
    try {
      const response = await fetch(`/api/jobs/advanced-search?${params}`);
      const data = await response.json();
      setResults(data.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="advanced-search">
      <input 
        type="text" 
        placeholder="Search jobs..."
        value={filters.q}
        onChange={(e) => setFilters({...filters, q: e.target.value})}
      />
      
      <select 
        multiple 
        onChange={(e) => setFilters({
          ...filters, 
          countries: Array.from(e.target.selectedOptions, option => option.value)
        })}
      >
        <option value="US">United States</option>
        <option value="UK">United Kingdom</option>
        <option value="UAE">United Arab Emirates</option>
      </select>
      
      <label>
        <input 
          type="checkbox"
          checked={filters.senior_only}
          onChange={(e) => setFilters({...filters, senior_only: e.target.checked})}
        />
        Senior Positions Only
      </label>
      
      <button onClick={searchJobs}>Search</button>
      
      {loading ? <p>Loading...</p> : (
        <div className="results">
          {results.map(job => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**Frontend Usage:**
- Advanced search page
- Filter sidebar
- Search refinement UI
- Saved searches feature

---

## 🏢 Company Intelligence APIs

### 1. List All Companies
```javascript
GET /api/jobs/companies?limit=50

// Response
{
  "count": 25,
  "companies": [
    {
      "name": "Delta Airlines",
      "total_jobs": 15,
      "active_jobs": 12,
      "countries": ["US", "UK"],
      "operation_types": ["Passenger", "Cargo"]
    },
    {
      "name": "Emirates Airlines",
      "total_jobs": 8,
      "active_jobs": 8,
      "countries": ["UAE"],
      "operation_types": ["Passenger"]
    }
  ]
}
```

**Query Parameters:**
- `limit` (default: 100) - Max companies to return

**Frontend Usage:**
- Company directory page
- Employer list
- Company autocomplete

---

### 2. Company Profile
```javascript
GET /api/jobs/companies/Delta%20Airlines

// Response
{
  "name": "Delta Airlines",
  "total_jobs": 15,
  "active_jobs": 12,
  "closed_jobs": 3,
  "countries": ["US", "UK", "FR"],
  "locations": ["Atlanta, GA", "London, UK", "Paris, FR"],
  "operation_types": ["Passenger", "Cargo"],
  "hiring_trends": {
    "last_7_days": 2,
    "last_30_days": 8
  },
  "recent_jobs": [
    { /* job object */ }
  ]
}
```

**Frontend Usage:**
- Company profile page
- Employer details modal
- Company comparison

**UI Suggestions:**
- Display company stats in cards
- Show hiring activity chart
- List all locations
- Show recent job postings

---

### 3. Jobs by Company
```javascript
GET /api/jobs/companies/Delta%20Airlines/jobs?skip=0&limit=20

// Response
{
  "company": "Delta Airlines",
  "total_jobs": 15,
  "jobs": [ /* array of job objects */ ]
}
```

**Frontend Usage:**
- "All jobs from this company" section
- Company page job listings

---

### 4. Trending Companies
```javascript
GET /api/jobs/companies/trending?days=30&limit=10

// Response
{
  "period": "Last 30 days",
  "trending_companies": [
    {
      "name": "Delta Airlines",
      "total_jobs": 15,
      "recent_jobs": 8,
      "growth_rate": 114.3,
      "active_jobs": 12
    }
  ]
}
```

**Query Parameters:**
- `days` (default: 30) - Period for trends
- `limit` (default: 10) - Top N companies

**Frontend Usage:**
- "Trending Employers" widget
- Homepage featured companies
- Market activity dashboard

**UI Suggestions:**
```html
<div class="trending-companies">
  <h3>🔥 Trending Employers</h3>
  <div class="company-card">
    <h4>Delta Airlines</h4>
    <span class="badge">+114% hiring</span>
    <p>8 new jobs this month</p>
  </div>
</div>
```

---

## 📈 Analytics & Insights

### 1. Job Posting Trends
```javascript
GET /api/jobs/analytics/trends?days=30

// Response
{
  "period": "Last 30 days",
  "total_jobs": 150,
  "daily_trends": [
    {
      "date": "2025-11-01",
      "count": 5,
      "new_jobs": 3,
      "updated_jobs": 2
    },
    {
      "date": "2025-11-02",
      "count": 8,
      "new_jobs": 6,
      "updated_jobs": 2
    }
    // ... more days
  ],
  "growth_rate": 15.5,
  "peak_day": {
    "date": "2025-11-15",
    "count": 12
  }
}
```

**Query Parameters:**
- `days` (default: 30) - Time period

**Frontend Usage:**
- Dashboard line chart
- Market activity visualization
- Homepage statistics

**Chart Implementation (Chart.js):**
```javascript
const chartData = {
  labels: data.daily_trends.map(d => d.date),
  datasets: [{
    label: 'Job Postings',
    data: data.daily_trends.map(d => d.count),
    borderColor: 'rgb(75, 192, 192)',
    tension: 0.1
  }]
};
```

---

### 2. Geographic Distribution
```javascript
GET /api/jobs/analytics/geographic

// Response
{
  "total_jobs": 150,
  "by_country": [
    {
      "country": "US",
      "count": 65,
      "percentage": 43.3,
      "active_jobs": 60
    },
    {
      "country": "UK",
      "count": 35,
      "percentage": 23.3,
      "active_jobs": 30
    }
  ],
  "top_locations": [
    {
      "location": "Atlanta, GA",
      "count": 25
    },
    {
      "location": "London, UK",
      "count": 18
    }
  ]
}
```

**Frontend Usage:**
- Interactive map visualization
- Country filter suggestions
- Geographic insights dashboard

**Map Implementation Suggestion:**
```javascript
// Using Leaflet or Google Maps
locations.forEach(loc => {
  addMarker({
    position: getCoordinates(loc.location),
    title: `${loc.count} jobs`,
    size: loc.count // Bubble size
  });
});
```

---

### 3. Operation Type Statistics
```javascript
GET /api/jobs/analytics/operation-types

// Response
{
  "total_jobs": 150,
  "by_operation_type": [
    {
      "operation_type": "Passenger",
      "count": 85,
      "percentage": 56.7,
      "avg_senior_positions": 45.2
    },
    {
      "operation_type": "Cargo",
      "count": 40,
      "percentage": 26.7,
      "avg_senior_positions": 32.5
    }
  ]
}
```

**Frontend Usage:**
- Pie/donut chart
- Job type distribution
- Filter suggestions

**Chart Example:**
```javascript
const pieData = {
  labels: data.by_operation_type.map(t => t.operation_type),
  datasets: [{
    data: data.by_operation_type.map(t => t.count),
    backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
  }]
};
```

---

## ⏰ Recent Activity & Feeds

### 1. Recently Added Jobs
```javascript
GET /api/jobs/recent?hours=24&limit=20

// Response
{
  "period": "Last 24 hours",
  "count": 12,
  "jobs": [
    {
      "id": 156,
      "title": "Senior Pilot",
      "company": "Delta Airlines",
      "posted_date": "2025-11-20T08:30:00Z",
      "hours_ago": 2,
      "is_new": true,
      // ... other job fields
    }
  ]
}
```

**Query Parameters:**
- `hours` (default: 24) - Time window
- `limit` (default: 20) - Max results

**Frontend Usage:**
- "New Jobs" feed
- Real-time notifications
- Homepage "Latest Opportunities"

**UI Example:**
```html
<div class="new-jobs-feed">
  <h3>🆕 New Opportunities</h3>
  {jobs.map(job => (
    <div class="job-item">
      <span class="badge">New - {job.hours_ago}h ago</span>
      <h4>{job.title}</h4>
      <p>{job.company}</p>
    </div>
  ))}
</div>
```

---

### 2. Recently Updated Jobs
```javascript
GET /api/jobs/updated?hours=48&limit=20

// Response
{
  "period": "Last 48 hours",
  "count": 8,
  "jobs": [
    {
      "id": 123,
      "title": "Captain Position",
      "company": "Emirates",
      "updated_at": "2025-11-19T15:20:00Z",
      "hours_ago": 18,
      "changes": "Description updated"
      // ... other fields
    }
  ]
}
```

**Frontend Usage:**
- "Recently Updated" section
- Job change notifications
- Saved job alerts

---

## 🔄 Job Comparison Features

### 1. Compare Multiple Jobs
```javascript
POST /api/jobs/compare
Content-Type: application/json

{
  "job_ids": [123, 456, 789]
}

// Response
{
  "comparison": {
    "jobs": [
      {
        "id": 123,
        "title": "Senior Pilot",
        "company": "Delta Airlines",
        "country": "US",
        "operation_type": "Passenger",
        "is_senior_position": true,
        "posted_date": "2025-11-15T10:30:00Z"
      },
      {
        "id": 456,
        "title": "Captain",
        "company": "Emirates",
        "country": "UAE",
        "operation_type": "Passenger",
        "is_senior_position": true,
        "posted_date": "2025-11-16T09:00:00Z"
      }
    ],
    "comparison_matrix": {
      "countries": ["US", "UAE"],
      "operation_types": ["Passenger"],
      "all_senior": true,
      "companies": ["Delta Airlines", "Emirates"]
    }
  }
}
```

**Frontend Usage:**
- Job comparison table
- Side-by-side view
- "Compare" feature

**UI Implementation:**
```html
<table class="job-comparison">
  <thead>
    <tr>
      <th>Attribute</th>
      <th>Job 1</th>
      <th>Job 2</th>
      <th>Job 3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Company</td>
      <td>Delta Airlines</td>
      <td>Emirates</td>
      <td>United</td>
    </tr>
    <tr>
      <td>Location</td>
      <td>US</td>
      <td>UAE</td>
      <td>US</td>
    </tr>
  </tbody>
</table>
```

---

### 2. Find Similar Jobs
```javascript
GET /api/jobs/similar/123?limit=5

// Response
{
  "original_job": {
    "id": 123,
    "title": "Senior Pilot",
    "company": "Delta Airlines"
  },
  "similar_jobs": [
    {
      "id": 456,
      "title": "Senior Captain",
      "company": "United Airlines",
      "similarity_score": 95,
      "matching_criteria": ["country", "operation_type", "senior_position"]
    },
    {
      "id": 789,
      "title": "Pilot",
      "company": "American Airlines",
      "similarity_score": 85,
      "matching_criteria": ["country", "operation_type"]
    }
  ]
}
```

**Query Parameters:**
- `limit` (default: 5) - Max similar jobs

**Frontend Usage:**
- "Similar Jobs" section
- Job recommendations
- "You might also like" feature

**UI Example:**
```html
<div class="similar-jobs">
  <h3>Similar Opportunities</h3>
  {similarJobs.map(job => (
    <div class="job-card">
      <span class="similarity">{job.similarity_score}% match</span>
      <h4>{job.title}</h4>
      <p>{job.company}</p>
    </div>
  ))}
</div>
```

---

## 📥 Data Export

### Export as JSON
```javascript
GET /api/jobs/export/json?
  country=US&
  operation_type=Passenger&
  status=active

// Response (downloadable JSON file)
{
  "export_date": "2025-11-20T10:30:00Z",
  "filters": {
    "country": "US",
    "operation_type": "Passenger",
    "status": "active"
  },
  "total_jobs": 45,
  "jobs": [ /* array of job objects */ ]
}
```

**Query Parameters:**
- `country` - Filter by country
- `operation_type` - Filter by type
- `status` - Filter by status

**Frontend Implementation:**
```javascript
function exportJobs(filters) {
  const params = new URLSearchParams(filters);
  const url = `/api/jobs/export/json?${params}`;
  
  // Trigger download
  window.location.href = url;
  // OR
  fetch(url)
    .then(res => res.blob())
    .then(blob => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `jobs_export_${Date.now()}.json`;
      a.click();
    });
}
```

**Existing CSV Export:**
```javascript
GET /api/jobs/export/csv
// Downloads CSV file
```

---

## ⚠️ Error Handling

### Standard Error Response Format
```javascript
{
  "detail": "Error message",
  "status": 404 // or other HTTP status
}
```

### Common HTTP Status Codes

| Code | Meaning | Frontend Action |
|------|---------|-----------------|
| 200 | Success | Display data |
| 400 | Bad Request | Show validation error |
| 401 | Unauthorized | Redirect to login |
| 403 | Forbidden | Show access denied message |
| 404 | Not Found | Show "not found" message |
| 500 | Server Error | Show generic error + retry |

### Frontend Error Handling Example
```javascript
async function fetchJobs() {
  try {
    const response = await fetch('/api/jobs/');
    
    if (!response.ok) {
      if (response.status === 401) {
        // Redirect to login
        window.location.href = '/login';
        return;
      }
      
      if (response.status === 404) {
        throw new Error('Jobs not found');
      }
      
      if (response.status >= 500) {
        throw new Error('Server error. Please try again later.');
      }
      
      const error = await response.json();
      throw new Error(error.detail || 'Unknown error');
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('Failed to fetch jobs:', error);
    // Show user-friendly error message
    showNotification('error', error.message);
  }
}
```

---

## 📋 Response Formats

### Job Object Schema
```typescript
interface Job {
  id: number;
  title: string;
  company: string;
  country: string;
  location: string;
  operation_type: string;
  experience_required: string;
  is_senior_position: boolean;
  posted_date: string; // ISO 8601 format
  updated_at: string;  // ISO 8601 format
  job_url: string;
  status: 'active' | 'closed';
  description?: string;
  requirements?: string;
  benefits?: string;
}
```

### Paginated Response Schema
```typescript
interface PaginatedResponse<T> {
  count: number;
  results: T[];
}
```

### Date Format
All dates are in **ISO 8601 format**: `2025-11-20T10:30:00Z`

**Frontend Parsing:**
```javascript
// Parse and format dates
const date = new Date(job.posted_date);
const formatted = date.toLocaleDateString('en-US', {
  year: 'numeric',
  month: 'long',
  day: 'numeric'
});
// "November 20, 2025"

// Relative time (for recent jobs)
function timeAgo(dateString) {
  const seconds = Math.floor((new Date() - new Date(dateString)) / 1000);
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60
  };
  
  for (const [unit, secondsInUnit] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secondsInUnit);
    if (interval >= 1) {
      return `${interval} ${unit}${interval === 1 ? '' : 's'} ago`;
    }
  }
  return 'just now';
}
```

---

## 💡 Integration Examples

### Complete Job Search Component (React)
```jsx
import React, { useState, useEffect } from 'react';

function JobSearchApp() {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    q: '',
    countries: [],
    senior_only: false
  });

  useEffect(() => {
    searchJobs();
  }, [filters]);

  const searchJobs = async () => {
    setLoading(true);
    const params = new URLSearchParams();
    
    if (filters.q) params.append('q', filters.q);
    if (filters.countries.length) {
      params.append('countries', filters.countries.join(','));
    }
    if (filters.senior_only) params.append('senior_only', 'true');

    try {
      const response = await fetch(
        `/api/jobs/advanced-search?${params}`
      );
      const data = await response.json();
      setJobs(data.results);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="job-search-app">
      <SearchFilters filters={filters} onChange={setFilters} />
      <JobResults jobs={jobs} loading={loading} />
    </div>
  );
}
```

### Dashboard with Analytics (Vue.js)
```vue
<template>
  <div class="dashboard">
    <div class="stats-grid">
      <StatCard 
        title="Total Jobs" 
        :value="stats.total_jobs" 
      />
      <StatCard 
        title="Active Jobs" 
        :value="stats.active_jobs" 
      />
      <StatCard 
        title="New This Week" 
        :value="recentJobs.length" 
      />
    </div>
    
    <TrendChart :data="trends" />
    <GeographicMap :data="geographic" />
    <RecentJobsFeed :jobs="recentJobs" />
  </div>
</template>

<script>
export default {
  data() {
    return {
      stats: {},
      trends: [],
      geographic: [],
      recentJobs: []
    };
  },
  async mounted() {
    await this.loadDashboardData();
  },
  methods: {
    async loadDashboardData() {
      // Parallel API calls for better performance
      const [stats, trends, geographic, recent] = await Promise.all([
        fetch('/api/jobs/stats').then(r => r.json()),
        fetch('/api/jobs/analytics/trends?days=30').then(r => r.json()),
        fetch('/api/jobs/analytics/geographic').then(r => r.json()),
        fetch('/api/jobs/recent?hours=168').then(r => r.json())
      ]);
      
      this.stats = stats;
      this.trends = trends;
      this.geographic = geographic;
      this.recentJobs = recent.jobs;
    }
  }
};
</script>
```

### Job Comparison Feature (Angular)
```typescript
import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-job-comparison',
  template: `
    <div class="comparison-tool">
      <button (click)="addJobToCompare(job.id)">
        Add to Compare
      </button>
      
      <div class="comparison-table" *ngIf="comparisonData">
        <table>
          <thead>
            <tr>
              <th>Attribute</th>
              <th *ngFor="let job of comparisonData.jobs">
                {{job.title}}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Company</td>
              <td *ngFor="let job of comparisonData.jobs">
                {{job.company}}
              </td>
            </tr>
            <tr>
              <td>Location</td>
              <td *ngFor="let job of comparisonData.jobs">
                {{job.location}}
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  `
})
export class JobComparisonComponent {
  selectedJobs: number[] = [];
  comparisonData: any = null;

  constructor(private http: HttpClient) {}

  addJobToCompare(jobId: number) {
    if (this.selectedJobs.length < 3) {
      this.selectedJobs.push(jobId);
    }
    
    if (this.selectedJobs.length >= 2) {
      this.compareJobs();
    }
  }

  compareJobs() {
    this.http.post('/api/jobs/compare', {
      job_ids: this.selectedJobs
    }).subscribe(data => {
      this.comparisonData = data;
    });
  }
}
```

---

## ⚡ Performance Tips

### 1. Use Pagination
Always implement pagination to avoid loading too many jobs at once.

```javascript
// Good - Paginated loading
const loadMore = async (page) => {
  const skip = page * 20;
  const response = await fetch(`/api/jobs/?skip=${skip}&limit=20`);
  return response.json();
};

// Bad - Loading everything
const loadAll = async () => {
  const response = await fetch('/api/jobs/?limit=10000');
  return response.json();
};
```

### 2. Implement Debouncing for Search
Prevent excessive API calls during user typing.

```javascript
function debounce(func, wait) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

const searchJobs = debounce(async (query) => {
  const response = await fetch(`/api/jobs/search?q=${query}`);
  return response.json();
}, 300); // Wait 300ms after user stops typing
```

### 3. Cache Analytics Data
Analytics data doesn't change frequently, so cache it.

```javascript
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

async function getAnalytics() {
  const cached = localStorage.getItem('analytics_cache');
  const timestamp = localStorage.getItem('analytics_timestamp');
  
  if (cached && timestamp && (Date.now() - timestamp < CACHE_DURATION)) {
    return JSON.parse(cached);
  }
  
  const response = await fetch('/api/jobs/analytics/trends');
  const data = await response.json();
  
  localStorage.setItem('analytics_cache', JSON.stringify(data));
  localStorage.setItem('analytics_timestamp', Date.now().toString());
  
  return data;
}
```

### 4. Parallel API Calls
When loading multiple data sources, use Promise.all().

```javascript
// Good - Parallel loading
async function loadDashboard() {
  const [jobs, companies, trends] = await Promise.all([
    fetch('/api/jobs/').then(r => r.json()),
    fetch('/api/jobs/companies').then(r => r.json()),
    fetch('/api/jobs/analytics/trends').then(r => r.json())
  ]);
  
  return { jobs, companies, trends };
}

// Bad - Sequential loading (slower)
async function loadDashboard() {
  const jobs = await fetch('/api/jobs/').then(r => r.json());
  const companies = await fetch('/api/jobs/companies').then(r => r.json());
  const trends = await fetch('/api/jobs/analytics/trends').then(r => r.json());
  
  return { jobs, companies, trends };
}
```

### 5. Optimize Images & Assets
- Use lazy loading for job images
- Implement virtual scrolling for long lists
- Compress API responses (enable gzip)

---

## 🎨 UI/UX Recommendations

### Dashboard Layout Suggestion
```
┌─────────────────────────────────────────────────┐
│  📊 Analytics Dashboard                         │
├──────────────┬──────────────┬───────────────────┤
│ Total Jobs   │ Active Jobs  │ New This Week     │
│    150       │     135      │      12           │
├──────────────┴──────────────┴───────────────────┤
│                                                  │
│  📈 Job Posting Trends (30 days)                │
│  [Line Chart showing daily trends]              │
│                                                  │
├─────────────────────┬────────────────────────────┤
│  🌍 Geographic      │  🔥 Trending Companies    │
│  Distribution       │                           │
│  [Map or Chart]     │  1. Delta Airlines (+114%)│
│                     │  2. Emirates (+85%)       │
│                     │  3. United (+60%)         │
└─────────────────────┴────────────────────────────┘
```

### Job Search Page Layout
```
┌─────────────────────────────────────────────────┐
│  🔍 Advanced Job Search                         │
├──────────────┬──────────────────────────────────┤
│              │                                  │
│  Filters     │  Search Results (45 jobs)       │
│              │                                  │
│  [Country]   │  ┌────────────────────────────┐ │
│  [Type]      │  │ Senior Pilot               │ │
│  [Senior]    │  │ Delta Airlines | US        │ │
│  [Date]      │  │ Posted 2 hours ago         │ │
│              │  └────────────────────────────┘ │
│  [Search]    │                                  │
│              │  ┌────────────────────────────┐ │
│              │  │ Captain                    │ │
│              │  │ Emirates | UAE             │ │
│              │  │ Posted 5 hours ago         │ │
│              │  └────────────────────────────┘ │
│              │                                  │
└──────────────┴──────────────────────────────────┘
```

### Company Profile Page
```
┌─────────────────────────────────────────────────┐
│  🏢 Delta Airlines                              │
├─────────────────────────────────────────────────┤
│  📊 Overview                                    │
│  • 15 total jobs                                │
│  • 12 active positions                          │
│  • Hiring in: US, UK, FR                        │
│  • Types: Passenger, Cargo                      │
├─────────────────────────────────────────────────┤
│  📈 Hiring Activity                             │
│  • 8 jobs posted in last 30 days                │
│  • +114% growth rate                            │
├─────────────────────────────────────────────────┤
│  💼 Current Openings                            │
│  [List of all jobs from this company]           │
└─────────────────────────────────────────────────┘
```

---

## 🚀 Getting Started Checklist

### Phase 1: Basic Integration (Week 1)
- [ ] Set up API base URL and authentication
- [ ] Implement job listing page with pagination
- [ ] Add job detail page
- [ ] Implement basic search
- [ ] Test all existing endpoints

### Phase 2: Advanced Features (Week 2)
- [ ] Integrate advanced search with filters
- [ ] Add company directory and profiles
- [ ] Implement job comparison feature
- [ ] Add "similar jobs" recommendations
- [ ] Build recent jobs feed

### Phase 3: Analytics & Dashboard (Week 3)
- [ ] Create analytics dashboard
- [ ] Add trend charts (Chart.js/D3.js)
- [ ] Implement geographic visualization
- [ ] Add trending companies widget
- [ ] Build operation type statistics

### Phase 4: Polish & Optimization (Week 4)
- [ ] Implement caching strategy
- [ ] Add loading states and error handling
- [ ] Optimize API calls (debouncing, parallel loading)
- [ ] Add export functionality
- [ ] Conduct performance testing

---

## 📞 Support & Questions

### For Backend Issues:
- Check API_DOCUMENTATION.txt for complete API reference
- Review error responses and HTTP status codes
- Test endpoints using curl or Postman

### For Integration Help:
- Review API_REFERENCE.md for quick examples
- Check NEW_FEATURES.md for feature explanations
- Refer to this document for frontend patterns

### Testing Endpoints:
```bash
# Test server is running
curl http://localhost:8000/api/jobs/stats

# Test advanced search
curl "http://localhost:8000/api/jobs/advanced-search?q=pilot&limit=5"

# Test company API
curl "http://localhost:8000/api/jobs/companies?limit=10"

# Test analytics
curl "http://localhost:8000/api/jobs/analytics/trends?days=7"
```

---

## 📝 Change Log

### Version 2.0 (November 20, 2025)
- ✅ Added 15+ new API endpoints
- ✅ Introduced advanced multi-filter search
- ✅ Added company intelligence APIs (4 endpoints)
- ✅ Added analytics and insights (3 endpoints)
- ✅ Added job comparison features (2 endpoints)
- ✅ Added recent activity feeds (2 endpoints)
- ✅ Enhanced data export capabilities
- ✅ Added scraper management endpoints (admin)
- ✅ All endpoints backward compatible

### Version 1.0 (Original)
- Basic CRUD operations
- Simple search
- CSV export
- Job statistics

---

## 🎯 Quick Reference Card

**Print this section for your desk:**

```
╔══════════════════════════════════════════════════╗
║  AEROOPS BACKEND API v2.0 - QUICK REFERENCE     ║
╚══════════════════════════════════════════════════╝

BASE URL: http://localhost:8000

🔍 SEARCH
  GET /api/jobs/advanced-search
      ?q=pilot&countries=US,UK&senior_only=true

🏢 COMPANIES
  GET /api/jobs/companies
  GET /api/jobs/companies/{name}
  GET /api/jobs/companies/trending

📈 ANALYTICS
  GET /api/jobs/analytics/trends?days=30
  GET /api/jobs/analytics/geographic
  GET /api/jobs/analytics/operation-types

⏰ RECENT ACTIVITY
  GET /api/jobs/recent?hours=24
  GET /api/jobs/updated?hours=48

🔄 COMPARISON
  POST /api/jobs/compare (body: {job_ids: [1,2,3]})
  GET /api/jobs/similar/{id}

📥 EXPORT
  GET /api/jobs/export/json?country=US
  GET /api/jobs/export/csv

💾 CORE ENDPOINTS
  GET /api/jobs/?skip=0&limit=20
  GET /api/jobs/{id}
  GET /api/jobs/search?q=pilot

Auth: Bearer {API_KEY}
Format: JSON
Dates: ISO 8601 (2025-11-20T10:30:00Z)
```

---

**Document End**

*For complete API documentation, see API_DOCUMENTATION.txt*  
*For quick examples, see API_REFERENCE.md*  
*For new features details, see NEW_FEATURES.md*
