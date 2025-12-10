# Frontend API Reference: Job Seekers & Recruiters

This document provides a focused integration guide for frontend development teams implementing Job Seeker and Recruiter experiences. It consolidates endpoints, request/response schemas, common query patterns, and usage examples.

---
## 1. Authentication
All protected endpoints require a valid JWT access token.

Send in header:
```
Authorization: Bearer <ACCESS_TOKEN>
Content-Type: application/json
```

Frontend should handle 401 by refreshing the token (if a refresh mechanism exists) or redirecting to login.

---
## 2. Base Paths
| Role | Base Path |
|------|-----------|
| Job Seeker | `/api/job-seeker/` |
| Recruiter  | `/api/recruiter/` |

---
## 3. Common Conventions
### Pagination
Query params:
- `page` (int, default 1)
- `page_size` (int, default 20)
Responses include: `count`, `page`, `page_size`, `total_pages` (when provided).

### Ordering
Param: `order_by` (field name, prefix with `-` for descending). Examples: `-posted_date`, `-total_score`, `-applied_at`.

### Filtering
- Boolean flags use strings: `true` / `false`.
- Multi-value filters (skills) use comma-separated strings: `skills=python,django`.

### Error Structure
Typical error response:
```json
{
  "error": "Only recruiters can access this endpoint"
}
```
Validation errors:
```json
{
  "status": ["This field is required."],
  "rating": ["Must be an integer."]
}
```

---
## 4. Serializers / Field Specs (Frontend Mapping)
### JobListSerializer
Fields: `id,title,company,location,country_code,operation_type,status,senior_flag,posted_date,source,url,user_applied,user_saved,total_applications`

### JobDetailSerializer
Fields include JobList fields plus: `normalized_title,company_id,retrieved_date,last_checked,description,created_at,updated_at,is_senior_position,total_applications,total_views`

### JobApplicationSerializer
Fields: `id,job,job_title,job_company,applicant{ id,username,email,first_name,last_name,role,phone },resume{ id,filename,name,email,total_score,created_at },status,cover_letter,applicant_notes,recruiter_notes,reviewed_by,reviewed_at,rating,interview_date,interview_notes,applied_at,updated_at,days_since_application`

### CandidateSerializer (Recruiter)
Fields: `id,filename,name,email,username,phones,total_score,is_active,created_at,parsed_at,email_verified,total_applications`

### ResumeDetailSerializer (Recruiter)
Fields: `id,filename,name,email,phones,username,user_email,skills,aviation,experience,total_score,raw_text,is_public,is_active,parsed_at,additional_info,created_at,updated_at,profile{ desired_job_title,desired_location,experience_years,skills,certifications,availability }`

### RecruiterJobSerializer
Fields: `id,title,company,location,country_code,operation_type,status,senior_flag,posted_date,source,url,total_applications,pending_applications,total_views,created_at`

---
## 5. Job Seeker Endpoints
### 5.1 List Jobs
`GET /api/job-seeker/jobs/`
Query params:
- `search` (title/company/description substring)
- `location` (matches `location` or exact `country_code`)
- `operation_type`
- `senior_only=true`
- Pagination: `page`, `page_size`
- Ordering: `order_by` (default `-posted_date`)

Response sample:
```json
{
  "count": 142,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "results": [
    {
      "id": 91,
      "title": "Senior A320 Captain",
      "company": "Global Air",
      "location": "Doha, Qatar",
      "country_code": "QA",
      "operation_type": "passenger",
      "status": "active",
      "senior_flag": true,
      "posted_date": "2025-11-20",
      "source": "signature",
      "url": "https://example.com/jobs/91",
      "user_applied": false,
      "user_saved": true,
      "total_applications": 12
    }
  ]
}
```

### 5.2 Job Detail
`GET /api/job-seeker/jobs/{job_id}/`
Response adds full description, view/application counts.

### 5.3 Apply to Job
`POST /api/job-seeker/jobs/{job_id}/apply/`
Body:
```json
{
  "resume_id": 15,
  "cover_letter": "I have 5000+ flight hours...",
  "applicant_notes": "Prefer night rotations"
}
```
Success:
```json
{
  "message": "Application submitted successfully",
  "application": { "id": 301, "status": "pending", "job": 91, "job_title": "Senior A320 Captain" }
}
```
Errors: 400 if already applied.

### 5.4 List My Applications
`GET /api/job-seeker/applications/?status=pending&page=1&page_size=10`
Returns paginated application list.

### 5.5 Application Detail
`GET /api/job-seeker/applications/{application_id}/`

### 5.6 Withdraw Application
`POST /api/job-seeker/applications/{application_id}/withdraw/`
Success:
```json
{"message": "Application withdrawn successfully"}
```

### 5.7 Save a Job
`POST /api/job-seeker/jobs/{job_id}/save/`
Body (optional):
```json
{ "notes": "Follow up after recruiter webinar" }
```

### 5.8 Unsave a Job
`DELETE /api/job-seeker/jobs/{job_id}/save/`

### 5.9 List Saved Jobs
`GET /api/job-seeker/saved-jobs/?page=1`
Each item includes nested `job` (JobListSerializer).

### 5.10 Dashboard Stats
`GET /api/job-seeker/dashboard/`
Response sample:
```json
{
  "stats": {
    "total_applications": 12,
    "pending": 3,
    "reviewing": 2,
    "shortlisted": 1,
    "interviewed": 1,
    "offers": 0,
    "accepted": 0,
    "rejected": 5,
    "saved_jobs": 7,
    "total_resumes": 2,
    "active_resumes": 1
  },
  "recent_applications": [ { "id": 301, "status": "pending", "job_title": "Senior A320 Captain" } ]
}
```

---
## 6. Recruiter Endpoints
(Access requires `profile.is_recruiter == True`.)

### 6.1 List Candidates
`GET /api/recruiter/candidates/`
Query params:
- `search` (name/email/raw_text)
- `min_score`
- `skills=python,ifrs,airbus` (OR matching – applied sequentially)
- `is_active=true`
- `order_by` (default `-total_score`)
- Pagination params

Response sample:
```json
{
  "count": 54,
  "page": 1,
  "page_size": 20,
  "total_pages": 3,
  "results": [
    {
      "id": 15,
      "filename": "jane_doe_resume.pdf",
      "name": "Jane Doe",
      "email": "jane@example.com",
      "username": "jane_doe",
      "phones": ["+44-7700-900123"],
      "total_score": 86,
      "is_active": true,
      "created_at": "2025-11-24T09:33:11Z",
      "parsed_at": "2025-11-24T09:34:02Z",
      "email_verified": true,
      "total_applications": 5
    }
  ]
}
```

### 6.2 Candidate Detail
`GET /api/recruiter/candidates/{resume_id}/`
Includes resume fields + last 10 applications.

### 6.3 List Applications
`GET /api/recruiter/applications/?status=pending&job_id=91&unreviewed=true`
Filters: `job_id`, `status`, `rating`, `unreviewed=true`.

### 6.4 Application Detail
`GET /api/recruiter/applications/{application_id}/`

### 6.5 Update Application Status
`PATCH /api/recruiter/applications/{application_id}/`
Body (any subset):
```json
{
  "status": "shortlisted",
  "recruiter_notes": "Strong Airbus background",
  "rating": 4,
  "interview_date": "2025-12-02T10:00:00Z",
  "interview_notes": "Panel interview scheduled"
}
```
Success:
```json
{
  "message": "Application updated successfully",
  "application": { "id": 301, "status": "shortlisted", "rating": 4 }
}
```

### 6.6 Bulk Update Applications
`POST /api/recruiter/applications/bulk-update/`
Body:
```json
{
  "application_ids": [301, 302, 305],
  "status": "reviewing",
  "recruiter_notes": "Batch status update after initial screening"
}
```
Success:
```json
{
  "message": "3 applications updated successfully",
  "updated_count": 3
}
```

### 6.7 Recruiter Dashboard
`GET /api/recruiter/dashboard/`
Sample:
```json
{
  "application_stats": {
    "total": 120,
    "pending": 34,
    "reviewing": 22,
    "shortlisted": 10,
    "interviewed": 6,
    "offers": 2
  },
  "candidate_stats": {
    "total": 54,
    "active": 40,
    "average_score": 71.3
  },
  "recent_applications": [ { "id": 501, "status": "pending" } ],
  "top_jobs": [ { "id": 91, "title": "Senior A320 Captain", "total_applications": 28 } ]
}
```

### 6.8 List Jobs With Stats
`GET /api/recruiter/jobs/?page=1&page_size=10`
Each job includes `total_applications`, `pending_applications`, `total_views`.

### 6.9 Job Applications
`GET /api/recruiter/jobs/{job_id}/applications/?status=pending`
Response:
```json
{
  "job": { "id": 91, "title": "Senior A320 Captain", "company": "Global Air" },
  "count": 12,
  "applications": [ { "id": 301, "status": "pending", "applicant": { "username": "jane_doe" } } ]
}
```

---
## 7. Field Notes & Frontend Usage Tips
- `senior_flag`: Already computed server-side; use to badge senior roles.
- `user_applied` / `user_saved`: Avoid extra calls for user-specific state.
- `total_views` / `total_applications`: For recruiter analytics UI.
- `total_score` (resume): Driving candidate ranking logic; consider color-banding (>=80 excellent, 60–79 good, 40–59 fair, <40 low).
- `days_since_application`: Useful for aging badges (e.g., >14 days = stale).
- `parsed_at`: Null means resume pending processing; disable certain actions until parsed.

---
## 8. Frontend Workflow Examples
### Job Seeker Apply Flow
1. GET jobs list → display.
2. On job click: GET job detail.
3. Open apply modal → POST apply.
4. Update UI with application state (`user_applied=true`).

### Recruiter Screening Flow
1. GET candidates with `min_score` and `skills` filters.
2. Open candidate detail; show last applications.
3. Bulk update newly screened applications (status=reviewing).
4. Use dashboard for daily metrics.

---
## 9. Error Handling Strategy
| Code | Cause | Frontend Action |
|------|-------|-----------------|
| 400  | Validation / duplicate | Surface field errors or toast message |
| 401  | Missing/expired token | Trigger re-auth / refresh |
| 403  | Role mismatch | Redirect or show permission notice |
| 404  | Resource not found | Show not-found state |
| 500  | Server error | Generic retry banner |

---
## 10. Caching & Performance Recommendations
- Cache last job list response (search + filters) in memory to avoid flicker.
- Debounce `search` input (300–500ms) before calling list endpoints.
- Batch recruiter bulk updates—avoid one PATCH per application.
- Use optimistic UI for save/unsave job actions; revert on failure.

---
## 11. Future Extension Hooks (Optional)
- Add `favorite` flag to candidates list (PATCH resume metadata).
- Real-time status updates via WebSocket channel (application status changes).
- Expand dashboard endpoints to include time-series graph data (daily counts).

---
## 12. Quick Reference (Cheat Sheet)
| Action | Method | Path |
|--------|--------|------|
| List Jobs | GET | /api/job-seeker/jobs/ |
| Job Detail | GET | /api/job-seeker/jobs/{id}/ |
| Apply | POST | /api/job-seeker/jobs/{id}/apply/ |
| My Applications | GET | /api/job-seeker/applications/ |
| Withdraw | POST | /api/job-seeker/applications/{id}/withdraw/ |
| Save Job | POST | /api/job-seeker/jobs/{id}/save/ |
| Unsave Job | DELETE | /api/job-seeker/jobs/{id}/save/ |
| Saved Jobs | GET | /api/job-seeker/saved-jobs/ |
| Seeker Dashboard | GET | /api/job-seeker/dashboard/ |
| Candidates | GET | /api/recruiter/candidates/ |
| Candidate Detail | GET | /api/recruiter/candidates/{id}/ |
| Applications | GET | /api/recruiter/applications/ |
| Application Detail | GET | /api/recruiter/applications/{id}/ |
| Update Application | PATCH | /api/recruiter/applications/{id}/ |
| Bulk Update Apps | POST | /api/recruiter/applications/bulk-update/ |
| Recruiter Jobs | GET | /api/recruiter/jobs/ |
| Job Applications | GET | /api/recruiter/jobs/{id}/applications/ |
| Recruiter Dashboard | GET | /api/recruiter/dashboard/ |

---
## 13. Frontend Integration Checklist
- [ ] Inject JWT in all protected calls.
- [ ] Centralize pagination component (accepts count/page/page_size).
- [ ] Define score band UI mapping (colors + labels).
- [ ] Implement global 401/403 interceptor.
- [ ] Use a serializer-to-TypeScript interface mapping tool (optional).
- [ ] Debounce candidate/job search inputs.
- [ ] Show loading skeletons for detail pages.
- [ ] Provide bulk action confirmation modals.

---
**End of Document**
