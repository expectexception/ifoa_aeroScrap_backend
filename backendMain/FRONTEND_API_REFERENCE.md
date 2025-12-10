# Job Portal API Reference

## Overview
This document provides a quick reference for the Job Portal APIs, separated by user roles. All endpoints require JWT authentication.

**Base URL:** `/api/`

## Authentication
- Use JWT tokens in Authorization header: `Bearer <token>`
- Job seekers and recruiters have role-based access

## Job Seeker APIs

### Job Browsing
- **GET** `/job-seeker/jobs/` - List available jobs (with filters: search, location, company, etc.)
- **GET** `/job-seeker/jobs/{job_id}/` - Get detailed job information
- **GET** `/job-seeker/jobs/{job_id}/similar/` - Get similar jobs

### Applications
- **POST** `/job-seeker/jobs/{job_id}/apply/` - Apply to a job
- **GET** `/job-seeker/applications/` - List user's applications
- **GET** `/job-seeker/applications/{application_id}/` - Get application details
- **DELETE** `/job-seeker/applications/{application_id}/` - Withdraw application

### Saved Jobs
- **POST** `/job-seeker/saved-jobs/` - Save a job
- **GET** `/job-seeker/saved-jobs/` - List saved jobs
- **DELETE** `/job-seeker/saved-jobs/{saved_job_id}/` - Remove saved job

### Profile & Dashboard
- **GET** `/job-seeker/profile/` - Get user profile
- **PATCH** `/job-seeker/profile/` - Update profile
- **GET** `/job-seeker/dashboard/` - Get dashboard stats (applications, saved jobs, etc.)

## Recruiter APIs

### Candidate Management
- **GET** `/recruiter/candidates/` - List all candidates (with filters: search, skills, location, score)
- **GET** `/recruiter/candidates/{resume_id}/` - Get detailed candidate info

### Application Management
- **GET** `/recruiter/applications/` - List applications (with filters: job_id, status, rating)
- **GET** `/recruiter/applications/{application_id}/` - Get application details
- **PATCH** `/recruiter/applications/{application_id}/update/` - Update application status/notes
- **POST** `/recruiter/applications/bulk-update/` - Bulk update multiple applications

### Job Management
- **GET** `/recruiter/my-jobs/` - List jobs posted by the recruiter (with application stats)
- **POST** `/recruiter/jobs/create/` - Create a new job posting
- **PUT** `/recruiter/jobs/{job_id}/update/` - Update an existing job posting
- **DELETE** `/recruiter/jobs/{job_id}/delete/` - Archive/delete a job posting

### Shortlisting (New Features)
- **GET** `/recruiter/advanced-search/` - Advanced candidate search with multiple filters
- **POST** `/recruiter/shortlist/{resume_id}/` - Add candidate to shortlist
- **GET** `/recruiter/shortlist/` - List shortlisted candidates
- **DELETE** `/recruiter/shortlist/{shortlist_id}/` - Remove from shortlist

### Dashboard
- **GET** `/recruiter/dashboard/` - Get recruiter dashboard stats (applications, candidates, jobs)

## Common Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Optional message"
}
```

## Error Responses
```json
{
  "error": "Error description",
  "details": "Optional details"
}
```

## Notes
- Pagination: Use `page` and `page_size` query parameters
- Filtering: Most list endpoints support various filters
- All endpoints return JSON responses
- Recruiter endpoints require `is_recruiter: true` in user profile
- **Notifications**: Recruiters receive email notifications when job seekers apply to their posted jobs
- **Job Creation**: Only recruiters can create jobs, which are automatically marked with `posted_by` field

For detailed request/response schemas, refer to the full API documentation.