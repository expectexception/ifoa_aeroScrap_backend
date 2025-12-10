# Frontend Migration Guide

## Overview
This guide helps frontend developers migrate to the updated backend API. Most endpoints remain compatible, but some response formats have changed for consistency.

---

## ⚠️ Breaking Changes

### Response Format Changes
Three endpoints changed from returning arrays to returning objects with `count` and `results`:

#### 1. List Jobs Endpoint

**Old Response** (Array):
```javascript
// GET /api/jobs/
[
  { id: 1, title: "Pilot", ... },
  { id: 2, title: "Co-Pilot", ... }
]
```

**New Response** (Object):
```javascript
// GET /api/jobs/
{
  count: 100,
  results: [
    { id: 1, title: "Pilot", ... },
    { id: 2, title: "Co-Pilot", ... }
  ]
}
```

**Migration Code**:
```javascript
// OLD CODE ❌
const jobs = await api.getJobs();
jobs.forEach(job => displayJob(job));

// NEW CODE ✅
const response = await api.getJobs();
response.results.forEach(job => displayJob(job));
console.log(`Total jobs: ${response.count}`);

// Or with destructuring
const { count, results: jobs } = await api.getJobs();
jobs.forEach(job => displayJob(job));
```

---

#### 2. Search Jobs Endpoint

**Old Response** (Array):
```javascript
// GET /api/jobs/search?q=pilot
[
  { id: 1, title: "Pilot", ... }
]
```

**New Response** (Object):
```javascript
// GET /api/jobs/search/?q=pilot
{
  count: 25,
  results: [
    { id: 1, title: "Pilot", ... }
  ]
}
```

**Migration Code**:
```javascript
// OLD CODE ❌
const searchResults = await api.searchJobs(query);
setJobList(searchResults);

// NEW CODE ✅
const { count, results } = await api.searchJobs(query);
setJobList(results);
setTotalCount(count);
```

---

#### 3. List Resumes Endpoint

**Old Response** (Array):
```javascript
// GET /api/resumes
[
  { id: 1, name: "John Doe", ... }
]
```

**New Response** (Object):
```javascript
// GET /api/resumes
{
  count: 50,
  results: [
    { id: 1, name: "John Doe", ... }
  ]
}
```

**Migration Code**:
```javascript
// OLD CODE ❌
const resumes = await api.getResumes();
displayResumes(resumes);

// NEW CODE ✅
const { count, results: resumes } = await api.getResumes();
displayResumes(resumes);
setResumeCount(count);
```

---

## ✅ New Features (Backward Compatible)

### 1. Additional Job Fields
New optional fields added to job objects:

```javascript
{
  id: 1,
  title: "Senior Pilot",
  company: "Delta Airlines",
  
  // NEW FIELDS
  location: "Atlanta, GA",              // Full location string
  is_senior_position: true,             // Alias for senior_flag
  last_updated: "2025-11-20T14:30:00Z", // Auto-updated timestamp
  
  // EXISTING FIELDS
  country: "US",
  operation_type: "Passenger",
  posted_date: "2025-11-20T08:30:00Z",
  status: "active"
}
```

**Using New Fields**:
```javascript
// Display location (falls back to country)
const displayLocation = (job) => {
  return job.location || job.country || "Unknown";
};

// Use either field name for senior position
const isSenior = job.is_senior_position || job.senior_flag;

// Show when job was last updated
const lastUpdate = new Date(job.last_updated);
console.log(`Updated: ${lastUpdate.toLocaleDateString()}`);
```

---

### 2. Improved Advanced Search

**New/Enhanced Parameters**:
- `senior_only`: Now accepts string "true"/"false" (more reliable)
- `countries`: Better handling of comma-separated values
- `operation_types`: Multiple types supported
- All empty/whitespace parameters are properly ignored

**Example Usage**:
```javascript
const searchParams = {
  q: searchText,
  countries: selectedCountries.join(','),  // ["US", "UK"] → "US,UK"
  operation_types: selectedTypes.join(','), // ["Passenger", "Cargo"]
  senior_only: seniorCheckbox ? 'true' : 'false',  // String, not boolean!
  date_from: startDate?.toISOString().split('T')[0],  // YYYY-MM-DD
  date_to: endDate?.toISOString().split('T')[0],
  sort_by: 'posted_date',
  order: 'desc',
  skip: (page - 1) * pageSize,
  limit: pageSize
};

// Build query string (skip undefined/null values)
const params = new URLSearchParams(
  Object.entries(searchParams)
    .filter(([_, v]) => v != null && v !== '')
);

const response = await fetch(
  `/api/jobs/advanced-search/?${params}`
);
const { count, results } = await response.json();
```

---

### 3. Company Endpoints - Enhanced Data

**List Companies** now includes more metadata:

```javascript
// GET /api/jobs/companies/
{
  companies: [
    {
      company: "Delta Airlines",
      total_jobs: 25,
      active_jobs: 18,           // NEW: Active job count
      countries: ["US", "UK"],    // NEW: Countries list
      operation_types: ["Passenger", "Cargo"]  // NEW: Types list
    }
  ]
}
```

**Company Profile** includes hiring trends:

```javascript
// GET /api/jobs/companies/Delta%20Airlines/
{
  name: "Delta Airlines",
  total_jobs: 25,
  active_jobs: 18,
  closed_jobs: 7,              // NEW: Closed count
  countries: ["US", "UK"],
  locations: ["Atlanta, GA"],  // NEW: Specific locations
  operation_types: ["Passenger"],
  hiring_trends: {             // NEW: Trending data
    last_7_days: 3,
    last_30_days: 12
  }
}
```

**Display Hiring Trends**:
```javascript
const CompanyProfile = ({ companyData }) => {
  const { hiring_trends } = companyData;
  
  return (
    <div>
      <h2>{companyData.name}</h2>
      <p>Active Jobs: {companyData.active_jobs}</p>
      <p>New This Week: {hiring_trends.last_7_days}</p>
      <p>New This Month: {hiring_trends.last_30_days}</p>
    </div>
  );
};
```

---

### 4. Trending Companies

**New endpoint for trending companies**:

```javascript
// GET /api/jobs/companies/trending/?days=7&limit=5
{
  companies: [
    {
      company: "Delta Airlines",
      new_jobs: 12,
      growth_percentage: 15.5
    }
  ]
}
```

**Display Trending Companies**:
```javascript
const TrendingCompanies = () => {
  const [trending, setTrending] = useState([]);
  
  useEffect(() => {
    fetch('/api/jobs/companies/trending/?days=7&limit=5')
      .then(res => res.json())
      .then(data => setTrending(data.companies));
  }, []);
  
  return (
    <div className="trending-companies">
      <h3>Hot Companies This Week</h3>
      {trending.map(company => (
        <div key={company.company} className="trending-item">
          <span>{company.company}</span>
          <span className="badge">+{company.new_jobs} jobs</span>
          <span className="growth">↑ {company.growth_percentage}%</span>
        </div>
      ))}
    </div>
  );
};
```

---

### 5. Recent & Updated Jobs

**Two new activity feed endpoints**:

```javascript
// Recent jobs (newly posted)
// GET /api/jobs/recent/?hours=48&limit=5
{
  jobs: [
    {
      id: 1,
      title: "Senior Pilot",
      company: "Delta Airlines",
      country: "US",
      location: "Atlanta, GA",
      operation_type: "Passenger",
      is_senior_position: true,
      posted_date: "2025-11-20T08:30:00Z",
      status: "active"
    }
  ]
}

// Recently updated jobs
// GET /api/jobs/updated/?hours=24&limit=10
{
  jobs: [
    {
      ...
      last_updated: "2025-11-20T14:30:00Z"
    }
  ]
}
```

**Activity Feed Component**:
```javascript
const ActivityFeed = () => {
  const [recentJobs, setRecentJobs] = useState([]);
  const [updatedJobs, setUpdatedJobs] = useState([]);
  
  useEffect(() => {
    // Get jobs from last 24 hours
    fetch('/api/jobs/recent/?hours=24&limit=5')
      .then(res => res.json())
      .then(data => setRecentJobs(data.jobs));
    
    // Get recently updated
    fetch('/api/jobs/updated/?hours=24&limit=5')
      .then(res => res.json())
      .then(data => setUpdatedJobs(data.jobs));
  }, []);
  
  return (
    <div className="activity-feed">
      <section>
        <h4>🆕 New Jobs</h4>
        {recentJobs.map(job => <JobCard key={job.id} job={job} />)}
      </section>
      <section>
        <h4>🔄 Recently Updated</h4>
        {updatedJobs.map(job => <JobCard key={job.id} job={job} />)}
      </section>
    </div>
  );
};
```

---

### 6. Job Comparison

**New endpoint to compare multiple jobs**:

```javascript
// POST /api/jobs/compare/
// Body: { job_ids: [1, 2, 3] }

const compareJobs = async (selectedIds) => {
  const response = await fetch('/api/jobs/compare/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ job_ids: selectedIds })
  });
  
  const data = await response.json();
  // {
  //   jobs: [...],
  //   summary: {
  //     common_fields: { country: "US", operation_type: "Passenger" },
  //     differences: ["Company names differ", ...]
  //   }
  // }
  
  return data;
};
```

**Comparison Table Component**:
```javascript
const JobComparisonTable = ({ comparisonData }) => {
  const { jobs, summary } = comparisonData;
  
  return (
    <div className="comparison-table">
      <div className="common-fields">
        <h4>Common Attributes</h4>
        {Object.entries(summary.common_fields).map(([key, value]) => (
          <p key={key}><strong>{key}:</strong> {value}</p>
        ))}
      </div>
      
      <div className="differences">
        <h4>Differences</h4>
        <ul>
          {summary.differences.map((diff, i) => (
            <li key={i}>{diff}</li>
          ))}
        </ul>
      </div>
      
      <table>
        <thead>
          <tr>
            <th>Title</th>
            <th>Company</th>
            <th>Location</th>
            <th>Type</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map(job => (
            <tr key={job.id}>
              <td>{job.title}</td>
              <td>{job.company}</td>
              <td>{job.location}</td>
              <td>{job.operation_type}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
```

---

### 7. Similar Jobs

**Find similar jobs by job ID**:

```javascript
// GET /api/jobs/similar/123/?limit=5
const getSimilarJobs = async (jobId, limit = 5) => {
  const response = await fetch(
    `/api/jobs/similar/${jobId}/?limit=${limit}`
  );
  const data = await response.json();
  return data.jobs;
};
```

**Similar Jobs Widget**:
```javascript
const SimilarJobsWidget = ({ currentJobId }) => {
  const [similarJobs, setSimilarJobs] = useState([]);
  
  useEffect(() => {
    if (currentJobId) {
      getSimilarJobs(currentJobId, 5)
        .then(jobs => setSimilarJobs(jobs));
    }
  }, [currentJobId]);
  
  return (
    <div className="similar-jobs">
      <h4>Similar Opportunities</h4>
      {similarJobs.map(job => (
        <JobCard key={job.id} job={job} compact />
      ))}
    </div>
  );
};
```

---

### 8. Analytics Endpoints

**Three new analytics endpoints with consistent format**:

```javascript
// Job trends over time
// GET /api/jobs/analytics/trends/?days=30
{
  total_jobs: 150,
  average_per_day: 5.0,
  daily_trends: [
    { date: "2025-11-15", count: 8 },
    { date: "2025-11-16", count: 12 }
  ]
}

// Geographic distribution
// GET /api/jobs/analytics/geographic/
{
  total_countries: 15,
  distribution: [
    { country: "US", count: 75 },
    { country: "UK", count: 45 }
  ]
}

// Operation type stats
// GET /api/jobs/analytics/operation-types/
{
  total_types: 5,
  distribution: [
    { operation_type: "Passenger", count: 120 },
    { operation_type: "Cargo", count: 80 }
  ]
}
```

**Analytics Dashboard Component**:
```javascript
const AnalyticsDashboard = () => {
  const [trends, setTrends] = useState(null);
  const [geographic, setGeographic] = useState(null);
  const [opTypes, setOpTypes] = useState(null);
  
  useEffect(() => {
    // Fetch all analytics in parallel
    Promise.all([
      fetch('/api/jobs/analytics/trends/?days=30').then(r => r.json()),
      fetch('/api/jobs/analytics/geographic/').then(r => r.json()),
      fetch('/api/jobs/analytics/operation-types/').then(r => r.json())
    ]).then(([trendsData, geoData, typesData]) => {
      setTrends(trendsData);
      setGeographic(geoData);
      setOpTypes(typesData);
    });
  }, []);
  
  if (!trends || !geographic || !opTypes) return <Loading />;
  
  return (
    <div className="analytics-dashboard">
      <div className="stat-card">
        <h3>Job Trends</h3>
        <p className="big-number">{trends.total_jobs}</p>
        <p className="subtitle">{trends.average_per_day} per day average</p>
        <LineChart data={trends.daily_trends} />
      </div>
      
      <div className="stat-card">
        <h3>Geographic Distribution</h3>
        <p className="big-number">{geographic.total_countries}</p>
        <p className="subtitle">countries</p>
        <BarChart data={geographic.distribution} />
      </div>
      
      <div className="stat-card">
        <h3>Operation Types</h3>
        <PieChart data={opTypes.distribution} />
      </div>
    </div>
  );
};
```

---

## 🔧 Helper Functions & Utilities

### API Client Wrapper

```javascript
// api-client.js
class JobsAPI {
  constructor(baseURL = 'http://localhost:8000/api') {
    this.baseURL = baseURL;
  }
  
  async advancedSearch(params) {
    // Convert filters to query params
    const queryParams = new URLSearchParams();
    
    if (params.query) queryParams.append('q', params.query);
    if (params.countries?.length) {
      queryParams.append('countries', params.countries.join(','));
    }
    if (params.operationTypes?.length) {
      queryParams.append('operation_types', params.operationTypes.join(','));
    }
    if (params.seniorOnly != null) {
      queryParams.append('senior_only', params.seniorOnly ? 'true' : 'false');
    }
    if (params.dateFrom) queryParams.append('date_from', params.dateFrom);
    if (params.dateTo) queryParams.append('date_to', params.dateTo);
    
    queryParams.append('skip', params.skip || 0);
    queryParams.append('limit', params.limit || 20);
    
    const response = await fetch(
      `${this.baseURL}/jobs/advanced-search/?${queryParams}`
    );
    return await response.json();
  }
  
  async getCompanyProfile(companyName) {
    const encoded = encodeURIComponent(companyName);
    const response = await fetch(
      `${this.baseURL}/jobs/companies/${encoded}/`
    );
    if (!response.ok) throw new Error('Company not found');
    return await response.json();
  }
  
  async getTrendingCompanies(days = 30, limit = 10) {
    const response = await fetch(
      `${this.baseURL}/jobs/companies/trending/?days=${days}&limit=${limit}`
    );
    const data = await response.json();
    return data.companies;
  }
  
  async getRecentJobs(hours = 48, limit = 10) {
    const response = await fetch(
      `${this.baseURL}/jobs/recent/?hours=${hours}&limit=${limit}`
    );
    const data = await response.json();
    return data.jobs;
  }
  
  async compareJobs(jobIds) {
    const response = await fetch(`${this.baseURL}/jobs/compare/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_ids: jobIds })
    });
    return await response.json();
  }
  
  async getSimilarJobs(jobId, limit = 5) {
    const response = await fetch(
      `${this.baseURL}/jobs/similar/${jobId}/?limit=${limit}`
    );
    const data = await response.json();
    return data.jobs;
  }
}

export const api = new JobsAPI();
```

---

### Date Formatting Helper

```javascript
// Format ISO dates from API
export const formatJobDate = (isoDate) => {
  if (!isoDate) return 'N/A';
  const date = new Date(isoDate);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  });
};

// Calculate time ago
export const timeAgo = (isoDate) => {
  if (!isoDate) return 'Unknown';
  const date = new Date(isoDate);
  const seconds = Math.floor((new Date() - date) / 1000);
  
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
      return `${interval} ${unit}${interval > 1 ? 's' : ''} ago`;
    }
  }
  
  return 'Just now';
};
```

---

## 📝 Testing Checklist

Before deploying frontend changes:

- [ ] Updated all `/api/jobs/` calls to handle `{count, results}` format
- [ ] Updated all `/api/jobs/search/` calls to handle new format
- [ ] Updated all `/api/resumes` calls to handle new format
- [ ] Updated advanced search to use string booleans ("true"/"false")
- [ ] Tested pagination with new `count` field
- [ ] Integrated new `location` field display
- [ ] Added trending companies widget
- [ ] Added recent/updated jobs feed
- [ ] Added job comparison feature
- [ ] Added similar jobs widget
- [ ] Added analytics dashboard
- [ ] Tested error handling (404, 400, etc.)
- [ ] Verified date formatting is correct
- [ ] URL-encoded company names in profile links

---

## 🚀 Deployment Steps

1. **Update API client code** with new response formats
2. **Test locally** against updated backend
3. **Update type definitions** (TypeScript) if applicable
4. **Run E2E tests** to verify integration
5. **Deploy backend first** to production
6. **Deploy frontend** after backend is stable
7. **Monitor** for any errors in production logs

---

## 📞 Support

If you encounter issues:

1. Check browser console for error messages
2. Verify API responses in Network tab
3. Ensure proper URL encoding for parameters
4. Check that trailing slashes are included where required
5. Review this migration guide for examples

---

**Migration Difficulty**: 🟢 Low (mostly response format updates)  
**Estimated Time**: 1-2 hours for small frontend, 4-6 hours for large frontend  
**Backward Compatibility**: ⚠️ Breaking changes in 3 endpoints only
