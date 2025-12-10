# Frontend Integration Guide - RBAC System

## Overview
The backend now implements a comprehensive Role-Based Access Control (RBAC) system with 4 user roles. API key authentication has been removed - **all endpoints now use JWT authentication only**.

---

## Authentication Changes

### 🔴 CRITICAL: Remove API Key Authentication
- **Delete all API key related code** from your frontend
- Remove any headers like: `X-API-Key`, `Authorization: ApiKey xxx`
- **Use JWT tokens exclusively** for all API calls

### JWT Token Usage
```javascript
// Store tokens after login
localStorage.setItem('access_token', response.data.access);
localStorage.setItem('refresh_token', response.data.refresh);

// Add to all API requests
headers: {
  'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json'
}
```

---

## New Authentication Endpoints

### 1. User Registration
```
POST /api/auth/register/
```
**Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "first_name": "string (optional)",
  "last_name": "string (optional)"
}
```
**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "access": "eyJ0eXAiOiJKV1QiLCJh...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJh..."
}
```

### 2. User Login
```
POST /api/auth/login/
```
**Body:**
```json
{
  "username": "string",
  "password": "string"
}
```
**Response:** Same as registration

### 3. Token Refresh
```
POST /api/auth/token/refresh/
```
**Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

### 4. Logout
```
POST /api/auth/logout/
```
**Headers:** `Authorization: Bearer <access_token>`
**Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

---

## User Roles & Permissions

### Role Hierarchy
1. **👑 Admin** - Full system access
2. **⚡ Manager** - Can manage jobs, scrapers, and users (read-only)
3. **👤 User** - Can view and create jobs/scrapers
4. **👁️ Viewer** - Read-only access

### Permission Matrix

| Action | Admin | Manager | User | Viewer |
|--------|-------|---------|------|--------|
| View Jobs | ✅ | ✅ | ✅ | ✅ |
| Create Jobs | ✅ | ✅ | ✅ | ❌ |
| Edit Jobs | ✅ | ✅ | ✅ | ❌ |
| Delete Jobs | ✅ | ✅ | ❌ | ❌ |
| View Users | ✅ | ✅ | ✅ | ✅ |
| Edit User Roles | ✅ | ❌ | ❌ | ❌ |
| View Scrapers | ✅ | ✅ | ✅ | ✅ |
| Start Scrapers | ✅ | ✅ | ✅ | ❌ |
| Edit Scrapers | ✅ | ✅ | ❌ | ❌ |
| View Resumes | ✅ | ✅ | ✅ | ✅ |
| Upload Resumes | ✅ | ✅ | ✅ | ❌ |

---

## New User Management Endpoints

### 1. Get Current User Profile
```
GET /api/auth/me/
```
**Headers:** `Authorization: Bearer <token>`
**Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "profile": {
    "role": "user",
    "department": "Engineering",
    "phone": "+1234567890",
    "bio": "Software Developer"
  }
}
```

### 2. Update User Profile
```
PUT /api/auth/profile/update/
```
**Body:**
```json
{
  "first_name": "string",
  "last_name": "string",
  "email": "string",
  "department": "string",
  "phone": "string",
  "bio": "string"
}
```

### 3. Change Password
```
POST /api/auth/password/change/
```
**Body:**
```json
{
  "old_password": "string",
  "new_password": "string"
}
```

### 4. List All Users (Admin Only)
```
GET /api/auth/users/
```
**Response:**
```json
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "profile": {
      "role": "user",
      "department": "Engineering"
    }
  }
]
```

### 5. Update User Role (Admin Only)
```
POST /api/auth/users/{user_id}/update-role/
```
**Body:**
```json
{
  "role": "manager"  // Options: "admin", "manager", "user", "viewer"
}
```

### 6. Get User by ID
```
GET /api/auth/users/{user_id}/
```

---

## Scraper Manager Updates

All scraper endpoints now use **role-based permissions**:

### 1. List Scrapers
```
GET /api/scraper-manager/scrapers/
```
**Access:** All authenticated users

### 2. Start Scraping
```
POST /api/scraper-manager/scrape/start/
```
**Body:**
```json
{
  "scraper": "aviation",  // "aviation", "linkedin", "airindia", "goose", "all"
  "max_pages": 5,         // Optional
  "max_jobs": 100         // Optional
}
```
**Access:** User role or above (no viewers)

### 3. Check Scraper Status
```
GET /api/scraper-manager/scrape/status/{job_id}/
```
**Access:** All authenticated users

### 4. List Scraper Jobs
```
GET /api/scraper-manager/jobs/
```
**Access:** All authenticated users

### 5. Get Job Details
```
GET /api/scraper-manager/jobs/{job_id}/
```
**Access:** All authenticated users

---

## Frontend Implementation Checklist

### Phase 1: Authentication (Priority: HIGH)
- [ ] Remove all API key authentication code
- [ ] Implement JWT token storage (localStorage/cookies)
- [ ] Create login page with username/password
- [ ] Create registration page
- [ ] Add token refresh logic (before 60min expiry)
- [ ] Add logout functionality (blacklist token)
- [ ] Handle 401 errors (redirect to login)
- [ ] Show authentication errors to user

### Phase 2: User Profile (Priority: MEDIUM)
- [ ] Create user profile page showing:
  - Username, email, name
  - Role badge with icon (👑⚡👤👁️)
  - Department, phone, bio
- [ ] Add profile edit form
- [ ] Add change password form
- [ ] Display current user info in navbar/header

### Phase 3: Role-Based UI (Priority: MEDIUM)
- [ ] Store user role from `/api/auth/me/` response
- [ ] Hide/disable buttons based on role:
  - Hide "Create Job" for viewers
  - Hide "Start Scraper" for viewers
  - Hide "Upload Resume" for viewers
  - Hide "Manage Users" for non-admins
- [ ] Show role badge in UI (use icons and colors)
- [ ] Add permission warnings when needed

### Phase 4: Admin Panel (Priority: LOW)
- [ ] Create user management page (admin only)
- [ ] List all users with roles
- [ ] Add "Change Role" dropdown/modal
- [ ] Show role change confirmation
- [ ] Handle permission errors gracefully

### Phase 5: Error Handling (Priority: HIGH)
- [ ] Handle 403 Forbidden (insufficient permissions)
- [ ] Handle 401 Unauthorized (token expired)
- [ ] Handle 400 Bad Request (validation errors)
- [ ] Show user-friendly error messages
- [ ] Add retry logic for failed requests

---

## Role Badge Styling

Use these colors and icons for consistent UI:

```css
.role-admin {
  background: #dc3545;
  color: white;
  icon: '👑';
}

.role-manager {
  background: #fd7e14;
  color: white;
  icon: '⚡';
}

.role-user {
  background: #28a745;
  color: white;
  icon: '👤';
}

.role-viewer {
  background: #6c757d;
  color: white;
  icon: '👁️';
}
```

---

## Example: Protected API Call

```javascript
async function fetchJobs() {
  try {
    const token = localStorage.getItem('access_token');
    
    const response = await fetch('http://localhost:8000/api/jobs/', {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 401) {
      // Token expired, try to refresh
      await refreshToken();
      return fetchJobs(); // Retry
    }
    
    if (response.status === 403) {
      // Insufficient permissions
      alert('You do not have permission to perform this action');
      return;
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('Error fetching jobs:', error);
  }
}

async function refreshToken() {
  const refresh = localStorage.getItem('refresh_token');
  const response = await fetch('http://localhost:8000/api/auth/token/refresh/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh })
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access);
  } else {
    // Refresh failed, redirect to login
    localStorage.clear();
    window.location.href = '/login';
  }
}
```

---

## Example: Role-Based UI Components

```jsx
// React example
function JobActions({ userRole }) {
  const canCreate = ['admin', 'manager', 'user'].includes(userRole);
  const canDelete = ['admin', 'manager'].includes(userRole);
  
  return (
    <div>
      {canCreate && (
        <button onClick={createJob}>Create Job</button>
      )}
      {canDelete && (
        <button onClick={deleteJob}>Delete Job</button>
      )}
    </div>
  );
}

// Vue example
<template>
  <div>
    <button v-if="canCreate" @click="createJob">Create Job</button>
    <button v-if="canDelete" @click="deleteJob">Delete Job</button>
  </div>
</template>

<script>
computed: {
  canCreate() {
    return ['admin', 'manager', 'user'].includes(this.userRole);
  },
  canDelete() {
    return ['admin', 'manager'].includes(this.userRole);
  }
}
</script>
```

---

## Testing Credentials

Test with these user roles (if created in your backend):

| Username | Password | Role | Use Case |
|----------|----------|------|----------|
| admin | admin123 | Admin | Full access testing |
| manager1 | manager123 | Manager | Manager permissions testing |
| user1 | user123 | User | Regular user testing |
| viewer1 | viewer123 | Viewer | Read-only testing |

**Note:** Create these users through Django admin or registration API.

---

## Common Issues & Solutions

### Issue 1: "Authentication credentials were not provided"
**Solution:** Add `Authorization: Bearer <token>` header to all requests

### Issue 2: "Token has expired"
**Solution:** Call `/api/auth/token/refresh/` to get new access token

### Issue 3: "You do not have permission"
**Solution:** Check user role and hide/disable the action in UI

### Issue 4: "Invalid token"
**Solution:** Clear tokens and redirect to login page

---

## Migration Steps

1. **Remove API Key Code**
   - Search for "API-Key" or "X-API-Key" in your codebase
   - Remove all references
   - Update API service/axios instances

2. **Implement JWT Auth**
   - Add token storage
   - Add token to all requests
   - Implement refresh logic

3. **Update UI**
   - Add login/register pages
   - Add role badges
   - Hide/show features based on role

4. **Test Each Role**
   - Create test users for each role
   - Verify permissions work correctly
   - Test edge cases (expired tokens, no permissions)

---

## API Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

---

## Need Help?

- Check `/documents/API_REFERENCE.md` for detailed API docs
- Check `/documents/RBAC_TROUBLESHOOTING.md` for backend issues
- Test endpoints using the provided test scripts in `/backendMain/`

---

**Last Updated:** November 21, 2025
**Backend Version:** Django 5.2.8 + DRF 3.16.1 + JWT
