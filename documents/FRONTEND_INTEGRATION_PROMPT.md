# 🎯 AeroOps Backend API Documentation for Frontend Integration

**Version:** 2.0  
**Date:** November 24, 2025  
**Backend Base URL:** `http://localhost:8000`

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Authentication](#authentication)
3. [Core API Endpoints](#core-api-endpoints)
4. [Data Models](#data-models)
5. [Auto-Mapping Feature](#auto-mapping-feature)
6. [Scraper Integration](#scraper-integration)
7. [Admin Interface](#admin-interface)
8. [Frontend Implementation Guide](#frontend-implementation-guide)
9. [Error Handling](#error-handling)
10. [Real-time Updates](#real-time-updates)

---

## 1. System Overview

### Technology Stack
- **Framework:** Django 5.1.14 + Django REST Framework
- **Database:** PostgreSQL
- **Server:** Gunicorn (3 workers)
- **Concurrent Processing:** ThreadPoolExecutor (4 workers)
- **Resume Parser:** pdfplumber 0.11.8

### Key Features
- ✅ Job scraping from 4 aviation job sites
- ✅ Automatic company mapping with review workflow
- ✅ Resume parsing and matching
- ✅ Real-time scraper status tracking
- ✅ Advanced filtering and search
- ✅ Company classification system

---

## 2. Authentication

### Admin Login
```http
POST /admin/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

### API Token (if using token auth)
```http
GET /api/jobs/
Authorization: Token <your-token>
```

**Note:** Current setup uses Django session auth. For frontend, use:
- Cookie-based authentication
- CSRF token handling required

---

## 3. Core API Endpoints

### 3.1 Jobs API

#### Get All Jobs
```http
GET /api/jobs/
```

**Query Parameters:**
- `status` - Filter by status: `new`, `active`, `reviewed`, `expired`, `archived`, `closed`
- `operation_type` - Filter by type: `passenger`, `cargo`, `business`, `scheduled`, `low_cost`, `ad_hoc_charter`, `helicopter`, `mro`, `ground_ops`, `atc`
- `country_code` - Filter by country (2-letter ISO): `IN`, `US`, `GB`, `AE`, etc.
- `source` - Filter by source: `Air India`, `Aviation Job Search`, `LinkedIn`, `Goose Recruitment`
- `company` - Filter by company name (case-insensitive)
- `company_id` - Filter by company mapping ID
- `senior_flag` - Filter senior positions: `true`/`false`
- `search` - Search in title, company, location, description
- `ordering` - Sort results: `-posted_date`, `company`, `title`, `-created_at`
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

**Response:**
```json
{
  "count": 75,
  "next": "http://localhost:8000/api/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Senior Pilot - Boeing 777",
      "company": "Air India",
      "company_id": 5,
      "location": "Delhi, India",
      "country_code": "IN",
      "operation_type": "scheduled",
      "status": "active",
      "source": "Air India",
      "senior_flag": true,
      "is_senior_position": true,
      "posted_date": "2025-11-24",
      "retrieved_date": "2025-11-24T11:25:00Z",
      "url": "https://careers.airindia.com/job/...",
      "description": "Full job description...",
      "created_at": "2025-11-24T11:26:08Z",
      "updated_at": "2025-11-24T11:26:08Z"
    }
  ]
}
```

#### Get Single Job
```http
GET /api/jobs/{id}/
```

#### Filter Examples
```http
# Active jobs from India
GET /api/jobs/?status=active&country_code=IN

# Senior pilot positions
GET /api/jobs/?search=pilot&senior_flag=true

# Jobs from specific company mapping
GET /api/jobs/?company_id=5

# Recent jobs, sorted by date
GET /api/jobs/?ordering=-posted_date&page_size=50
```

---

### 3.2 Company Mappings API

#### Get All Company Mappings
```http
GET /api/company-mappings/
```

**Query Parameters:**
- `needs_review` - Filter by review status: `true`/`false`
- `auto_created` - Filter auto-created: `true`/`false`
- `operation_type` - Filter by aviation type
- `country_code` - Filter by country
- `search` - Search in company name, notes
- `ordering` - Sort: `company_name`, `-total_jobs`, `-created_at`

**Response:**
```json
{
  "count": 17,
  "results": [
    {
      "id": 5,
      "company_name": "Air India",
      "normalized_name": "air india",
      "operation_type": "scheduled",
      "country_code": "IN",
      "total_jobs": 25,
      "active_jobs": 25,
      "last_job_date": "2025-11-24",
      "auto_created": true,
      "needs_review": true,
      "reviewed_by": null,
      "reviewed_at": null,
      "notes": "Auto-created from job: Senior Pilot...",
      "created_at": "2025-11-24T11:26:08Z",
      "updated_at": "2025-11-24T11:26:08Z"
    }
  ]
}
```

#### Get Single Company Mapping
```http
GET /api/company-mappings/{id}/
```

#### Get Jobs for a Company
```http
GET /api/company-mappings/{id}/jobs/
```

**Response:**
```json
{
  "company_mapping": {
    "id": 5,
    "company_name": "Air India",
    "total_jobs": 25
  },
  "jobs": [
    { /* job object */ }
  ]
}
```

#### Mark Company as Reviewed
```http
POST /api/company-mappings/{id}/mark-reviewed/
Content-Type: application/json

{
  "username": "admin"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Company mapping marked as reviewed",
  "reviewed_by": "admin",
  "reviewed_at": "2025-11-24T11:30:00Z"
}
```

---

### 3.3 Scraper API

#### Run Scraper
```http
POST /api/scraper/run/
Content-Type: application/json

{
  "scraper_name": "aviation",
  "max_pages": 2,
  "max_jobs": 50
}
```

**Scraper Names:**
- `aviation` - Aviation Job Search
- `airindia` - Air India Careers
- `linkedin` - LinkedIn Jobs
- `goose` - Goose Recruitment

**Response:**
```json
{
  "status": "started",
  "job_id": 123,
  "scraper_name": "aviation",
  "message": "Scraper started successfully"
}
```

#### Get Scraper Status
```http
GET /api/scraper/status/{job_id}/
```

**Response (Running):**
```json
{
  "job_id": 123,
  "scraper_name": "aviation",
  "status": "running",
  "started_at": "2025-11-24T11:26:00Z",
  "progress": "Scraping page 1/2..."
}
```

**Response (Completed):**
```json
{
  "job_id": 123,
  "scraper_name": "aviation",
  "status": "completed",
  "started_at": "2025-11-24T11:26:00Z",
  "completed_at": "2025-11-24T11:30:00Z",
  "execution_time": 248.92,
  "jobs_found": 50,
  "jobs_new": 50,
  "jobs_updated": 0,
  "jobs_duplicates": 0
}
```

#### Get All Scraper Jobs
```http
GET /api/scraper/jobs/
```

**Query Parameters:**
- `status` - `pending`, `running`, `completed`, `failed`, `cancelled`
- `scraper_name` - Filter by scraper
- `ordering` - Sort: `-started_at`, `-completed_at`

---

### 3.4 Resume API

#### Upload Resume
```http
POST /api/resume/upload/
Content-Type: multipart/form-data

resume_file: <file>
```

**Response:**
```json
{
  "status": "success",
  "resume_id": 456,
  "parsed_data": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "+1234567890",
    "skills": ["Python", "Django", "React"],
    "experience_years": 5
  }
}
```

#### Match Resume with Jobs
```http
POST /api/resume/match/
Content-Type: application/json

{
  "resume_id": 456,
  "filters": {
    "country_code": "IN",
    "operation_type": "scheduled"
  }
}
```

**Response:**
```json
{
  "matches": [
    {
      "job_id": 1,
      "job_title": "Senior Pilot - Boeing 777",
      "company": "Air India",
      "match_score": 0.85,
      "matched_skills": ["Boeing 777", "Commercial Aviation"],
      "location": "Delhi, India"
    }
  ]
}
```

---

## 4. Data Models

### Job Model
```typescript
interface Job {
  id: number;
  title: string;
  normalized_title?: string;
  company: string;
  company_id?: number;  // FK to CompanyMapping
  location?: string;
  country_code?: string;  // 2-letter ISO (IN, US, GB, etc.)
  operation_type?: OperationType;
  status: JobStatus;
  source?: string;
  senior_flag: boolean;
  is_senior_position: boolean;
  posted_date?: string;  // ISO date
  retrieved_date: string;  // ISO datetime
  last_checked?: string;  // ISO datetime
  url: string;  // Unique
  description?: string;
  raw_json?: any;
  created_at: string;  // ISO datetime
  updated_at: string;  // ISO datetime
}

type JobStatus = 'new' | 'active' | 'reviewed' | 'expired' | 'archived' | 'closed';

type OperationType = 
  | 'passenger'       // ✈️ Passenger Airlines
  | 'cargo'           // 📦 Cargo & Freight
  | 'business'        // 🎩 Business & Private Aviation
  | 'scheduled'       // 🗓️ Scheduled Operations
  | 'low_cost'        // 💺 Low-Cost Carrier
  | 'ad_hoc_charter'  // 🛩️ Charter & On-Demand
  | 'helicopter'      // 🚁 Helicopter Operations
  | 'mro'             // 🔧 Maintenance & Repair
  | 'ground_ops'      // 🏢 Ground Operations
  | 'atc';            // 🎯 Air Traffic Control
```

### CompanyMapping Model
```typescript
interface CompanyMapping {
  id: number;
  company_name: string;
  normalized_name: string;  // Lowercase, for matching
  operation_type?: OperationType;
  country_code?: string;
  total_jobs: number;  // Auto-calculated
  active_jobs: number;  // Auto-calculated
  last_job_date?: string;  // ISO date
  auto_created: boolean;  // Created by scraper?
  needs_review: boolean;  // Needs admin review?
  reviewed_by?: string;  // Username who reviewed
  reviewed_at?: string;  // ISO datetime
  notes?: string;
  created_at: string;  // ISO datetime
  updated_at: string;  // ISO datetime
}
```

### ScraperJob Model
```typescript
interface ScraperJob {
  id: number;
  scraper_name: string;
  status: ScraperStatus;
  started_at?: string;  // ISO datetime
  completed_at?: string;  // ISO datetime
  execution_time?: number;  // Seconds
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  jobs_duplicates: number;
  error_message?: string;
  parameters?: {
    max_pages?: number;
    max_jobs?: number;
  };
}

type ScraperStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
```

---

## 5. Auto-Mapping Feature

### Overview
The backend **automatically creates CompanyMapping entries** when scrapers discover new companies. This eliminates manual mapping creation while maintaining quality through a review workflow.

### How It Works
```
1. Scraper finds job from "Emirates Cargo"
2. System checks if mapping exists → Not found
3. Auto-creates CompanyMapping:
   - company_name: "Emirates Cargo"
   - auto_created: true
   - needs_review: true
   - operation_type: inherited from job
   - country_code: inherited from job
4. Links ALL jobs from "Emirates Cargo" to this mapping
5. Admin reviews and approves in frontend
```

### Frontend Integration

#### Display Auto-Created Mappings
```typescript
// Get mappings needing review
const response = await fetch('/api/company-mappings/?needs_review=true&auto_created=true');
const data = await response.json();

// Show with warning badge
data.results.forEach(mapping => {
  if (mapping.needs_review) {
    showWarningBadge(); // ⚠️ NEEDS REVIEW
  }
  if (mapping.auto_created) {
    showAutoCreatedLabel(); // 🤖 Auto-created
  }
});
```

#### Review Workflow UI
```typescript
// 1. Show mapping details
const mapping = await fetch(`/api/company-mappings/${id}/`).then(r => r.json());

// 2. Show similar companies (for duplicate detection)
// Frontend can implement fuzzy matching or use backend stats

// 3. Allow admin to:
//    - Edit company name, operation_type, country_code
//    - Mark as reviewed
//    - Delete if duplicate

// 4. Mark as reviewed
await fetch(`/api/company-mappings/${id}/mark-reviewed/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: currentUser })
});
```

#### Visual Indicators
```jsx
// React example
function CompanyBadge({ mapping }) {
  return (
    <div className="company-mapping">
      <h3>{mapping.company_name}</h3>
      {mapping.needs_review && (
        <span className="badge badge-warning">⚠️ Needs Review</span>
      )}
      {mapping.auto_created && (
        <span className="badge badge-info">🤖 Auto-created</span>
      )}
      {mapping.reviewed_by && (
        <span className="badge badge-success">
          ✓ Reviewed by {mapping.reviewed_by}
        </span>
      )}
      <p>{mapping.total_jobs} jobs</p>
    </div>
  );
}
```

---

## 6. Scraper Integration

### Available Scrapers

| Scraper | Source | Features |
|---------|--------|----------|
| `aviation` | aviationjobsearch.com | Global aviation jobs, detailed descriptions |
| `airindia` | careers.airindia.com | Air India official careers, India-focused |
| `linkedin` | linkedin.com | LinkedIn jobs (requires auth), diverse roles |
| `goose` | goose-recruitment.com | Goose recruitment agency jobs |

### Frontend Scraper UI

#### Scraper Control Panel
```jsx
function ScraperPanel() {
  const [selectedScrapers, setSelectedScrapers] = useState(['aviation']);
  const [maxPages, setMaxPages] = useState(2);
  const [maxJobs, setMaxJobs] = useState(50);
  
  const runScraper = async () => {
    for (const scraper of selectedScrapers) {
      const response = await fetch('/api/scraper/run/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scraper_name: scraper,
          max_pages: maxPages,
          max_jobs: maxJobs
        })
      });
      
      const data = await response.json();
      startMonitoring(data.job_id); // Poll for status
    }
  };
  
  return (
    <div className="scraper-control">
      <h2>Run Scrapers</h2>
      <ScraperSelector onChange={setSelectedScrapers} />
      <input 
        type="number" 
        value={maxPages} 
        onChange={e => setMaxPages(e.target.value)}
        placeholder="Max Pages"
      />
      <input 
        type="number" 
        value={maxJobs} 
        onChange={e => setMaxJobs(e.target.value)}
        placeholder="Max Jobs"
      />
      <button onClick={runScraper}>Start Scraping</button>
    </div>
  );
}
```

#### Real-time Status Monitoring
```typescript
function monitorScraperStatus(jobId: number) {
  const interval = setInterval(async () => {
    const response = await fetch(`/api/scraper/status/${jobId}/`);
    const status = await response.json();
    
    updateUI(status);
    
    if (['completed', 'failed', 'cancelled'].includes(status.status)) {
      clearInterval(interval);
      showResults(status);
    }
  }, 2000); // Poll every 2 seconds
}
```

#### Progress Display
```jsx
function ScraperStatus({ jobId }) {
  const [status, setStatus] = useState(null);
  
  useEffect(() => {
    const monitor = setInterval(async () => {
      const response = await fetch(`/api/scraper/status/${jobId}/`);
      const data = await response.json();
      setStatus(data);
      
      if (data.status === 'completed') {
        clearInterval(monitor);
      }
    }, 2000);
    
    return () => clearInterval(monitor);
  }, [jobId]);
  
  if (!status) return <div>Loading...</div>;
  
  return (
    <div className="scraper-status">
      <h3>{status.scraper_name}</h3>
      <div className={`status-${status.status}`}>
        {status.status === 'running' && '⏳ Running...'}
        {status.status === 'completed' && '✅ Completed'}
        {status.status === 'failed' && '❌ Failed'}
      </div>
      {status.status === 'completed' && (
        <div className="results">
          <p>Jobs Found: {status.jobs_found}</p>
          <p>New: {status.jobs_new}</p>
          <p>Updated: {status.jobs_updated}</p>
          <p>Duplicates: {status.jobs_duplicates}</p>
          <p>Time: {status.execution_time}s</p>
        </div>
      )}
    </div>
  );
}
```

---

## 7. Admin Interface

### Admin URLs
- **Main Admin:** `http://localhost:8000/admin/`
- **Jobs:** `http://localhost:8000/admin/jobs/job/`
- **Company Mappings:** `http://localhost:8000/admin/jobs/companymapping/`
- **Scraper Jobs:** `http://localhost:8000/admin/scraper_manager/scraperjob/`

### Theme
- **Aviation-themed** with IFOA branding
- **Colors:** Navy blue (#003b6f) primary, gold accents
- **Icons:** Aviation emojis (✈️ 📦 🛩️ etc.)

### Custom Features
- Bulk actions for approval
- Company mapping review workflow
- Job statistics dashboard
- Scraper execution tracking

---

## 8. Frontend Implementation Guide

### 8.1 Jobs Dashboard

#### Features to Implement
```typescript
interface JobsDashboard {
  // Filters
  filters: {
    status: JobStatus[];
    operationType: OperationType[];
    countryCode: string[];
    source: string[];
    seniorOnly: boolean;
    search: string;
  };
  
  // Display
  view: 'grid' | 'list' | 'table';
  sortBy: '-posted_date' | 'company' | 'title';
  pageSize: 20 | 50 | 100;
  
  // Actions
  actions: {
    viewDetails: (jobId: number) => void;
    applyFilter: () => void;
    exportCSV: () => void;
  };
}
```

#### Sample Implementation
```jsx
function JobsDashboard() {
  const [jobs, setJobs] = useState([]);
  const [filters, setFilters] = useState({});
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20 });
  
  useEffect(() => {
    fetchJobs();
  }, [filters, pagination]);
  
  const fetchJobs = async () => {
    const params = new URLSearchParams({
      ...filters,
      page: pagination.page,
      page_size: pagination.pageSize
    });
    
    const response = await fetch(`/api/jobs/?${params}`);
    const data = await response.json();
    setJobs(data.results);
  };
  
  return (
    <div className="jobs-dashboard">
      <JobFilters filters={filters} onChange={setFilters} />
      <JobList jobs={jobs} />
      <Pagination 
        total={data.count} 
        current={pagination.page}
        onChange={page => setPagination({...pagination, page})}
      />
    </div>
  );
}
```

---

### 8.2 Company Management

#### Features to Implement
```typescript
interface CompanyManagement {
  // Display
  mappings: CompanyMapping[];
  filterBy: 'all' | 'needs_review' | 'auto_created';
  
  // Review Workflow
  reviewQueue: CompanyMapping[];
  currentReview: CompanyMapping | null;
  
  // Actions
  actions: {
    markAsReviewed: (id: number) => Promise<void>;
    editMapping: (id: number, data: Partial<CompanyMapping>) => Promise<void>;
    deleteMapping: (id: number) => Promise<void>;
    viewJobs: (id: number) => void;
  };
}
```

#### Review Interface
```jsx
function CompanyReviewPanel({ mappingId }) {
  const [mapping, setMapping] = useState(null);
  const [jobs, setJobs] = useState([]);
  
  useEffect(() => {
    loadMapping();
    loadJobs();
  }, [mappingId]);
  
  const loadMapping = async () => {
    const response = await fetch(`/api/company-mappings/${mappingId}/`);
    setMapping(await response.json());
  };
  
  const loadJobs = async () => {
    const response = await fetch(`/api/company-mappings/${mappingId}/jobs/`);
    const data = await response.json();
    setJobs(data.jobs);
  };
  
  const handleApprove = async () => {
    await fetch(`/api/company-mappings/${mappingId}/mark-reviewed/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: currentUser })
    });
    
    // Refresh or navigate to next review
  };
  
  return (
    <div className="company-review">
      <CompanyDetails mapping={mapping} />
      <OperationTypeSelector 
        value={mapping.operation_type}
        onChange={updateOperationType}
      />
      <CountryCodeSelector 
        value={mapping.country_code}
        onChange={updateCountryCode}
      />
      <JobsList jobs={jobs} />
      <button onClick={handleApprove}>✓ Approve</button>
    </div>
  );
}
```

---

### 8.3 Scraper Dashboard

#### Features to Implement
```jsx
function ScraperDashboard() {
  const [activeJobs, setActiveJobs] = useState([]);
  const [history, setHistory] = useState([]);
  
  return (
    <div className="scraper-dashboard">
      {/* Control Panel */}
      <ScraperControlPanel onStart={handleScraperStart} />
      
      {/* Active Jobs */}
      <section>
        <h2>Running Scrapers</h2>
        {activeJobs.map(job => (
          <ScraperStatusCard key={job.id} job={job} />
        ))}
      </section>
      
      {/* History */}
      <section>
        <h2>Recent Scraper Runs</h2>
        <ScraperHistory jobs={history} />
      </section>
      
      {/* Statistics */}
      <section>
        <h2>Statistics</h2>
        <ScraperStats />
      </section>
    </div>
  );
}
```

---

## 9. Error Handling

### API Error Responses
```typescript
interface APIError {
  error: string;
  message: string;
  details?: any;
  status_code: number;
}
```

### Common Error Codes
```typescript
const errorHandlers = {
  400: (error) => showMessage('Invalid request: ' + error.message),
  401: () => redirectToLogin(),
  403: () => showMessage('Access denied'),
  404: () => showMessage('Resource not found'),
  500: () => showMessage('Server error. Please try again later'),
  504: () => showMessage('Request timeout. The server might be busy')
};
```

### Frontend Error Handling
```typescript
async function apiRequest(url: string, options?: RequestInit) {
  try {
    const response = await fetch(url, options);
    
    if (!response.ok) {
      const error = await response.json();
      throw new APIError(error);
    }
    
    return await response.json();
  } catch (error) {
    handleAPIError(error);
    throw error;
  }
}
```

---

## 10. Real-time Updates

### Polling Strategy
```typescript
// Poll for new jobs
function useJobPolling(interval = 30000) {
  const [jobs, setJobs] = useState([]);
  
  useEffect(() => {
    const fetchLatest = async () => {
      const response = await fetch('/api/jobs/?ordering=-created_at&page_size=10');
      const data = await response.json();
      setJobs(data.results);
    };
    
    fetchLatest();
    const timer = setInterval(fetchLatest, interval);
    
    return () => clearInterval(timer);
  }, [interval]);
  
  return jobs;
}
```

### Notification System
```typescript
// Monitor for new auto-created mappings
function useCompanyMappingNotifications() {
  const [notifications, setNotifications] = useState([]);
  
  useEffect(() => {
    const check = async () => {
      const response = await fetch('/api/company-mappings/?needs_review=true&auto_created=true');
      const data = await response.json();
      
      if (data.count > 0) {
        notify(`${data.count} companies need review`);
      }
    };
    
    const timer = setInterval(check, 60000); // Check every minute
    return () => clearInterval(timer);
  }, []);
  
  return notifications;
}
```

---

## 11. Best Practices

### 11.1 Performance Optimization

```typescript
// Use pagination
const params = new URLSearchParams({
  page: 1,
  page_size: 50, // Don't load all at once
  ordering: '-posted_date'
});

// Cache static data
const cachedCompanyMappings = useMemo(() => {
  return companyMappings; // Recompute only when data changes
}, [companyMappings]);

// Debounce search
const debouncedSearch = useMemo(
  () => debounce((query) => fetchJobs(query), 500),
  []
);
```

### 11.2 Data Freshness

```typescript
// Invalidate cache after actions
const invalidateJobsCache = () => {
  queryClient.invalidateQueries('jobs');
};

// Refetch after scraper completes
useEffect(() => {
  if (scraperStatus === 'completed') {
    refetchJobs();
    refetchCompanyMappings();
  }
}, [scraperStatus]);
```

### 11.3 User Experience

```jsx
// Loading states
{isLoading && <Spinner />}
{!isLoading && jobs.length === 0 && <EmptyState />}
{!isLoading && jobs.length > 0 && <JobList jobs={jobs} />}

// Error boundaries
<ErrorBoundary fallback={<ErrorScreen />}>
  <JobsDashboard />
</ErrorBoundary>

// Optimistic updates
const handleApprove = async (id) => {
  // Update UI immediately
  updateMappingInState(id, { needs_review: false });
  
  try {
    await api.markAsReviewed(id);
  } catch (error) {
    // Revert on error
    revertMappingInState(id);
    showError(error);
  }
};
```

---

## 12. Quick Reference

### Essential Endpoints
```
GET  /api/jobs/                    - List all jobs
GET  /api/jobs/{id}/               - Get single job
GET  /api/company-mappings/        - List mappings
POST /api/company-mappings/{id}/mark-reviewed/ - Approve mapping
POST /api/scraper/run/             - Start scraper
GET  /api/scraper/status/{id}/     - Check scraper status
```

### Key Features for Frontend
- ✅ Job listing with advanced filters
- ✅ Company mapping review workflow  
- ✅ Scraper control panel with real-time status
- ✅ Auto-created mapping alerts
- ✅ Resume upload and matching
- ✅ Export functionality

### Priority Implementation Order
1. **Jobs Dashboard** - Core functionality
2. **Company Review Panel** - Handle auto-created mappings
3. **Scraper Control** - Allow admins to run scrapers
4. **Resume Matching** - Job recommendations
5. **Analytics Dashboard** - Statistics and insights

---

## 13. Support

**Backend Documentation Location:**
- `/documents/AUTO_MAPPING_FEATURE.md` - Auto-mapping details
- `/documents/API_REFERENCE.md` - Complete API reference
- `/documents/JOB_LINKING_FIX.md` - Job linking implementation

**Test Data:**
Current database has **75 jobs** and **17 company mappings** (all auto-created, all need review).

**Admin Credentials:**
- Username: `admin`
- Password: `admin123`

---

**Last Updated:** November 24, 2025  
**Backend Version:** 2.0.0  
**Author:** AeroOps Development Team
