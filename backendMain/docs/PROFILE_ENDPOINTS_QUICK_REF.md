# 🎯 Profile Endpoints - Quick Reference

## New Endpoints (3 total)

### 1. Job Seeker Profile
```
GET/PUT/PATCH /api/auth/profile/job-seeker/
```
**Auth:** Required (JWT)  
**Role:** job_seeker only  
**Returns:** Full profile + completion %

**Response Fields:**
```json
{
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "bio": "string",
  "desired_job_title": "string",
  "desired_location": "string",
  "experience_years": "integer",
  "skills": ["array"],
  "certifications": ["array"],
  "availability": "string",
  "profile_completion": "integer (0-100)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### 2. Recruiter Profile
```
GET/PUT/PATCH /api/auth/profile/recruiter/
```
**Auth:** Required (JWT)  
**Role:** recruiter only  
**Returns:** Full profile + completion %

**Response Fields:**
```json
{
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "phone": "string",
  "bio": "string",
  "company_name": "string",
  "company_website": "url",
  "is_verified_recruiter": "boolean (read-only)",
  "profile_completion": "integer (0-100)",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### 3. Profile Completion
```
GET /api/auth/profile/completion/
```
**Auth:** Required (JWT)  
**Role:** job_seeker or recruiter  
**Returns:** Completion % + missing fields

**Response:**
```json
{
  "username": "string",
  "role": "job_seeker | recruiter",
  "completion_percentage": "integer (0-100)",
  "missing_fields": ["array of field names"],
  "is_complete": "boolean"
}
```

---

## Usage Examples

### Get Profile
```bash
curl -X GET http://localhost:8000/api/auth/profile/job-seeker/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Profile (Partial)
```bash
curl -X PATCH http://localhost:8000/api/auth/profile/job-seeker/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "bio": "Updated bio",
    "skills": ["Skill1", "Skill2"],
    "availability": "Immediate"
  }'
```

### Check Completion
```bash
curl -X GET http://localhost:8000/api/auth/profile/completion/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Error Codes

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | - |
| 400 | Validation Error | Check request body |
| 401 | Unauthorized | Include valid JWT token |
| 403 | Wrong Role | Use correct endpoint for your role |
| 404 | Not Found | Check URL |
| 500 | Server Error | Contact backend team |

---

## Profile Completion Calculation

### Job Seeker (10 fields):
✓ first_name  
✓ last_name  
✓ phone  
✓ bio  
✓ desired_job_title  
✓ desired_location  
✓ experience_years  
✓ skills (at least 1)  
✓ certifications (at least 1)  
✓ availability  

### Recruiter (6 fields):
✓ first_name  
✓ last_name  
✓ phone  
✓ bio  
✓ company_name  
✓ company_website  

---

## Frontend Integration Checklist

- [ ] Create job seeker profile page
- [ ] Create recruiter profile page
- [ ] Add profile completion indicator (progress bar)
- [ ] Show missing fields to user
- [ ] Implement profile update forms
- [ ] Add skills/certifications multi-input
- [ ] Handle role-based routing
- [ ] Show "Complete your profile" banner if < 100%

---

## Testing

Run test suite:
```bash
cd /path/to/backendMain
python test_profile_endpoints.py
```

Expected: **ALL TESTS PASSED: 8/8** ✓

---

## Documents

📄 Full Docs: `/backendMain/docs/FRONTEND_BACKEND_REQUIREMENTS.md`  
📊 Summary: `/backendMain/docs/PROFILE_UPDATE_SUMMARY.md`  
🧪 Tests: `/backendMain/test_profile_endpoints.py`

---

**Version:** 1.0  
**Last Updated:** November 26, 2024  
**Status:** ✅ Production Ready
