# Frontend Backend Requirements & New Profile Endpoints

## 📋 Overview
This document outlines the new profile management endpoints added to the backend and identifies additional requirements for frontend integration.

---

## 🆕 NEW PROFILE ENDPOINTS

### 1. Job Seeker Profile Management
**Endpoint:** `/api/auth/profile/job-seeker/`  
**Methods:** GET, PUT, PATCH  
**Authentication:** Required (JWT Bearer Token)

#### GET Request
Returns complete job seeker profile with completion percentage.

**Response:**
```json
{
  "username": "john_pilot",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "bio": "Experienced pilot with 10+ years...",
  "desired_job_title": "Senior Pilot",
  "desired_location": "New York, USA",
  "experience_years": 10,
  "skills": ["Boeing 737", "Airbus A320", "IFR", "Night Flying"],
  "certifications": ["ATP License", "Type Rating B737"],
  "availability": "Immediate",
  "profile_completion": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

#### PUT/PATCH Request
Update job seeker profile fields.

**Request Body (all fields optional for PATCH):**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "bio": "Updated bio...",
  "desired_job_title": "Senior Pilot",
  "desired_location": "Los Angeles, USA",
  "experience_years": 12,
  "skills": ["Boeing 737", "Airbus A320", "Airbus A380"],
  "certifications": ["ATP License", "Type Rating B737", "Type Rating A320"],
  "availability": "2 weeks"
}
```

**Response:**
```json
{
  "message": "Profile updated successfully",
  "profile": { ... }  // Full profile data
}
```

**Error Response (403):**
```json
{
  "error": "This endpoint is only for job seekers"
}
```

---

### 2. Recruiter Profile Management
**Endpoint:** `/api/auth/profile/recruiter/`  
**Methods:** GET, PUT, PATCH  
**Authentication:** Required (JWT Bearer Token)

#### GET Request
Returns complete recruiter profile with completion percentage.

**Response:**
```json
{
  "username": "airline_recruiter",
  "email": "recruiter@airline.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1234567890",
  "bio": "HR Manager at Major Airlines...",
  "company_name": "Major Airlines Inc.",
  "company_website": "https://www.majorairlines.com",
  "is_verified_recruiter": true,
  "profile_completion": 100,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

#### PUT/PATCH Request
Update recruiter profile fields.

**Request Body (all fields optional for PATCH):**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+1234567890",
  "bio": "Updated bio...",
  "company_name": "Major Airlines Inc.",
  "company_website": "https://www.majorairlines.com"
}
```

**Note:** `is_verified_recruiter` is read-only and can only be changed by admins.

**Response:**
```json
{
  "message": "Profile updated successfully",
  "profile": { ... }  // Full profile data
}
```

**Error Response (403):**
```json
{
  "error": "This endpoint is only for recruiters"
}
```

---

### 3. Profile Completion Check
**Endpoint:** `/api/auth/profile/completion/`  
**Method:** GET  
**Authentication:** Required (JWT Bearer Token)

Returns profile completion percentage and list of missing fields.

**Response:**
```json
{
  "username": "john_pilot",
  "role": "job_seeker",
  "completion_percentage": 70,
  "missing_fields": [
    "certifications",
    "availability",
    "bio"
  ],
  "is_complete": false
}
```

**Use Cases:**
- Show "Complete your profile" banner
- Display progress bar on profile page
- Suggest missing fields to user
- Gamification (rewards for complete profiles)

---

## 🔄 EXISTING ENDPOINTS (Still Available)

### General Profile Endpoints
These endpoints work for ALL user types (admin, manager, job_seeker, recruiter, etc.)

1. **GET /api/auth/profile/** - Get any user's profile
2. **PUT /api/auth/profile/update/** - Update any user's profile
3. **POST /api/auth/change-password/** - Change password

**Recommendation:** Use role-specific endpoints for job seekers and recruiters for better validation and cleaner data.

---

## ✅ BACKEND FEATURES ALREADY IMPLEMENTED

### 1. Authentication System ✓
- JWT-based authentication
- Token refresh mechanism
- Role-based access control (RBAC)
- Separate registration for job seekers and recruiters

### 2. Job Management ✓
- Full CRUD operations for jobs
- Job search with filters (location, airline, job type)
- Job application system
- Application tracking

### 3. Resume Management ✓
- Resume upload (PDF, DOC, DOCX)
- Resume parsing and field extraction
- Resume download
- Resume linking to applications

### 4. Admin Panel ✓
- Custom Django admin with aviation theme
- User management
- Role assignment
- Job and application moderation

### 5. Scraper System ✓
- Automated job scraping from multiple airlines
- Scheduled scraping with Celery Beat
- Manual scraper triggers
- Scraper status monitoring

---

## 🚀 ADDITIONAL REQUIREMENTS FOR FRONTEND

### 1. Profile Picture Upload (❌ NOT IMPLEMENTED)

**What's Needed:**
- Add `profile_picture` field to UserProfile model
- Create endpoint: `POST /api/auth/profile/upload-picture/`
- Support image formats: JPG, PNG (max 5MB)
- Image resizing and optimization on backend
- Return image URL in profile responses

**Frontend Impact:**
- File upload component
- Image preview before upload
- Crop/resize functionality
- Display profile picture in navbar, profile page, applications

**Implementation Priority:** HIGH (enhances user experience significantly)

---

### 2. Email Verification (❌ NOT IMPLEMENTED)

**What's Needed:**
- Add `email_verified` field to UserProfile
- Send verification email on registration
- Create endpoint: `GET /api/auth/verify-email/<token>/`
- Resend verification email endpoint

**Frontend Impact:**
- Show "Verify your email" banner
- Resend verification button
- Email verification success page

**Implementation Priority:** HIGH (security and trust)

---

### 3. Password Reset (❌ PARTIALLY IMPLEMENTED)

**Current:** Only change password (requires old password)  
**What's Needed:**
- Forgot password flow
- Send reset email with token
- Create endpoints:
  - `POST /api/auth/forgot-password/` (send email)
  - `POST /api/auth/reset-password/<token>/` (reset with token)

**Frontend Impact:**
- "Forgot password?" link on login page
- Reset password form
- Success confirmation

**Implementation Priority:** HIGH (user accessibility)

---

### 4. Notification System (❌ NOT IMPLEMENTED)

**What's Needed:**
- Notification model (in-app notifications)
- Create endpoints:
  - `GET /api/notifications/` (list notifications)
  - `POST /api/notifications/<id>/mark-read/`
  - `POST /api/notifications/mark-all-read/`
- WebSocket support for real-time notifications (optional)

**Notification Types:**
- New job matching your profile
- Application status changed
- New message from recruiter
- Profile completion reminder

**Frontend Impact:**
- Notification bell icon with badge
- Notification dropdown
- Notification page
- Real-time updates (if WebSocket)

**Implementation Priority:** MEDIUM (nice to have)

---

### 5. Saved Jobs / Favorites (❌ NOT IMPLEMENTED)

**What's Needed:**
- SavedJob model (many-to-many with Job)
- Create endpoints:
  - `POST /api/jobs/<id>/save/` (save job)
  - `DELETE /api/jobs/<id>/unsave/` (remove saved job)
  - `GET /api/jobs/saved/` (list saved jobs)

**Frontend Impact:**
- Heart/bookmark icon on job cards
- "Saved Jobs" page
- Filter and manage saved jobs

**Implementation Priority:** MEDIUM (improves user experience)

---

### 6. Job Alerts / Subscriptions (❌ NOT IMPLEMENTED)

**What's Needed:**
- JobAlert model (search criteria + email frequency)
- Create endpoints:
  - `POST /api/job-alerts/` (create alert)
  - `GET /api/job-alerts/` (list alerts)
  - `PUT /api/job-alerts/<id>/` (update alert)
  - `DELETE /api/job-alerts/<id>/` (delete alert)
- Background task to send alert emails

**Frontend Impact:**
- "Create Job Alert" form
- Manage alerts page
- Email preferences

**Implementation Priority:** MEDIUM (user engagement)

---

### 7. Messaging System (❌ NOT IMPLEMENTED)

**What's Needed:**
- Message model (recruiter ↔ job seeker)
- Create endpoints:
  - `GET /api/messages/` (list conversations)
  - `GET /api/messages/<conversation_id>/` (get messages)
  - `POST /api/messages/` (send message)
- Real-time messaging with WebSocket (optional)

**Frontend Impact:**
- Messages page
- Conversation list
- Chat interface
- Unread message badge

**Implementation Priority:** LOW (can use external tools initially)

---

### 8. Analytics & Insights (❌ NOT IMPLEMENTED)

**What's Needed:**
- Endpoints for analytics:
  - `GET /api/analytics/job-seeker/` (profile views, application stats)
  - `GET /api/analytics/recruiter/` (job views, applicant stats)
  - `GET /api/analytics/dashboard/` (overall stats)

**Frontend Impact:**
- Dashboard with charts
- Profile view count
- Application success rate
- Popular jobs/skills

**Implementation Priority:** LOW (nice to have)

---

### 9. Multi-Resume Support (❌ PARTIALLY IMPLEMENTED)

**Current:** One resume per application  
**What's Needed:**
- Multiple resumes per user
- Set default resume
- Name/tag resumes (e.g., "Technical Resume", "Management Resume")

**Frontend Impact:**
- Resume library page
- Select resume for application
- Manage multiple resumes

**Implementation Priority:** LOW (current implementation sufficient for MVP)

---

### 10. Social Login (❌ NOT IMPLEMENTED)

**What's Needed:**
- OAuth integration (Google, LinkedIn)
- Create endpoints:
  - `POST /api/auth/google/`
  - `POST /api/auth/linkedin/`

**Frontend Impact:**
- "Sign in with Google/LinkedIn" buttons
- OAuth callback handling

**Implementation Priority:** MEDIUM (improves signup conversion)

---

## 📊 FEATURE PRIORITY MATRIX

| Feature | Priority | Impact | Effort | Status |
|---------|----------|--------|--------|--------|
| Profile Picture Upload | HIGH | HIGH | LOW | ❌ Not Implemented |
| Email Verification | HIGH | HIGH | MEDIUM | ❌ Not Implemented |
| Password Reset | HIGH | HIGH | LOW | ❌ Not Implemented |
| Notification System | MEDIUM | HIGH | HIGH | ❌ Not Implemented |
| Saved Jobs | MEDIUM | MEDIUM | LOW | ❌ Not Implemented |
| Job Alerts | MEDIUM | MEDIUM | MEDIUM | ❌ Not Implemented |
| Social Login | MEDIUM | MEDIUM | MEDIUM | ❌ Not Implemented |
| Messaging System | LOW | MEDIUM | HIGH | ❌ Not Implemented |
| Analytics Dashboard | LOW | LOW | MEDIUM | ❌ Not Implemented |
| Multi-Resume | LOW | LOW | LOW | ❌ Not Implemented |

---

## 🔧 FRONTEND INTEGRATION CHECKLIST

### Phase 1: Profile Management (Current)
- [x] Understand role-specific profile endpoints
- [ ] Create job seeker profile page
- [ ] Create recruiter profile page
- [ ] Implement profile completion indicator
- [ ] Add profile update forms
- [ ] Handle role-based routing

### Phase 2: Critical Features
- [ ] Implement profile picture upload
- [ ] Add email verification flow
- [ ] Create password reset flow
- [ ] Test all authentication flows

### Phase 3: Enhanced Features
- [ ] Build notification system
- [ ] Add saved jobs functionality
- [ ] Create job alerts
- [ ] Implement social login

### Phase 4: Advanced Features
- [ ] Add messaging system
- [ ] Build analytics dashboard
- [ ] Support multiple resumes

---

## 📝 NOTES FOR FRONTEND DEVELOPERS

### 1. Authentication
Always include JWT token in headers:
```javascript
headers: {
  'Authorization': `Bearer ${accessToken}`,
  'Content-Type': 'application/json'
}
```

### 2. Role-Based Routing
Check user role from login response:
```javascript
if (user.role === 'job_seeker') {
  navigate('/job-seeker/dashboard');
} else if (user.role === 'recruiter') {
  navigate('/recruiter/dashboard');
}
```

### 3. Profile Completion
Show progress indicator on all pages until profile is 100%:
```javascript
const { completion_percentage, missing_fields } = await fetchProfileCompletion();
if (completion_percentage < 100) {
  showProfileCompletionBanner(missing_fields);
}
```

### 4. Error Handling
All endpoints return consistent error format:
```json
{
  "error": "Error message here"
}
// OR
{
  "field_name": ["Error for this field"]
}
```

### 5. File Uploads (for future profile picture)
Use FormData for file uploads:
```javascript
const formData = new FormData();
formData.append('profile_picture', file);
await axios.post('/api/auth/profile/upload-picture/', formData, {
  headers: { 'Content-Type': 'multipart/form-data' }
});
```

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

1. **Week 1-2:** Implement role-specific profile pages
2. **Week 3:** Add profile picture upload (backend + frontend)
3. **Week 4:** Implement email verification & password reset
4. **Week 5-6:** Build notification system
5. **Week 7:** Add saved jobs and job alerts
6. **Week 8+:** Advanced features (messaging, analytics, etc.)

---

## 📞 SUPPORT

For backend API questions or new feature requests:
- Check: `/backendMain/docs/API_DOCUMENTATION.txt`
- Check: `/documents/FRONTEND_INTEGRATION_PROMPT.md`
- Test endpoints using the provided test files

---

**Last Updated:** 2024-01-20  
**Backend Version:** 1.0  
**API Version:** v1
