# Role-Based Access Control (RBAC) System

## Overview

The AeroScrap backend now implements a comprehensive Role-Based Access Control (RBAC) system that allows administrators to assign different access levels to users. This replaces the previous API key authentication system with a more flexible and secure JWT-based authentication with role-based permissions.

## Features

- ✅ **4 User Roles**: Admin, Manager, User, Viewer
- ✅ **JWT Authentication**: Secure token-based authentication
- ✅ **Permission Classes**: Fine-grained access control
- ✅ **Admin Interface**: Easy role management through Django admin
- ✅ **Auto Profile Creation**: UserProfile automatically created for each user
- ✅ **Role Management APIs**: RESTful endpoints for user and role management

## User Roles

### 1. Admin
- **Description**: Full system access
- **Permissions**: Read, Write, Delete, Manage Users, Manage Roles
- **Use Case**: System administrators, super users
- **Access**: All endpoints without restrictions

### 2. Manager
- **Description**: Can manage jobs and scrapers
- **Permissions**: Read, Write, Delete, View Users
- **Use Case**: Team leads, scraper operators
- **Access**: Can start scrapers, manage jobs, view user list

### 3. User
- **Description**: Can create and edit own resources
- **Permissions**: Read, Write
- **Use Case**: Regular users, job seekers
- **Access**: Can view data, upload resumes, search jobs

### 4. Viewer
- **Description**: Read-only access
- **Permissions**: Read
- **Use Case**: Guests, auditors, read-only accounts
- **Access**: Can only view data, cannot create or modify

## Architecture

### Models

#### UserProfile Model
```python
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**Key Features:**
- Auto-created via post-save signals when User is created
- Role field with 4 choices: admin, manager, user, viewer
- Additional profile information (department, phone, bio)
- Helper properties: `is_admin`, `is_manager`, `can_write`

### Permission Classes

#### IsAdmin
```python
class IsAdmin(BasePermission):
    """Allow access only to admin users"""
```
- Checks: `request.user.is_superuser` OR `request.user.role == 'admin'`
- Use: Endpoints that require full admin privileges

#### IsManagerOrAbove
```python
class IsManagerOrAbove(BasePermission):
    """Allow access to manager and admin users"""
```
- Checks: `request.user.is_superuser` OR `request.user.role in ['admin', 'manager']`
- Use: Scraper management, job management

#### IsUserOrAbove
```python
class IsUserOrAbove(BasePermission):
    """Allow access to all authenticated users except viewers"""
```
- Checks: Any authenticated user with role not 'viewer'
- Use: Write operations for regular users

#### IsAdminOrReadOnly
```python
class IsAdminOrReadOnly(BasePermission):
    """Allow read-only for all, write only for admins"""
```
- Read: Any authenticated user
- Write: Admin only
- Use: Role definitions, system configurations

#### IsOwnerOrAdmin
```python
class IsOwnerOrAdmin(BasePermission):
    """Allow access to object owner or admin"""
```
- Object-level permissions
- Checks: `obj.user == request.user` OR `request.user.role == 'admin'`
- Use: User profile updates, own resource management

## API Endpoints

### Authentication Endpoints (Public)

#### Register
```bash
POST /api/auth/register/
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
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
    "last_name": "Doe",
    "date_joined": "2024-01-01T10:00:00Z",
    "role": "user",
    "department": "",
    "is_admin": false,
    "is_manager": false,
    "can_write": true
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "User registered successfully"
}
```

#### Login
```bash
POST /api/auth/login/
Content-Type: application/json

{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "user",
    "is_admin": false,
    "is_manager": false,
    "can_write": true
  },
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "message": "Login successful"
}
```

#### Logout
```bash
POST /api/auth/logout/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Profile Endpoints (Authenticated)

#### Get Profile
```bash
GET /api/auth/profile/
Authorization: Bearer <access_token>
```

#### Update Profile
```bash
PUT /api/auth/profile/update/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe Updated",
  "email": "john.updated@example.com"
}
```

#### Change Password
```bash
POST /api/auth/change-password/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!",
  "new_password2": "NewPass123!"
}
```

### Role Management Endpoints (Admin Only)

#### List All Users
```bash
GET /api/auth/users/
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "count": 10,
  "users": [
    {
      "id": 1,
      "username": "john_doe",
      "email": "john@example.com",
      "role": "user",
      "is_admin": false,
      "is_manager": false,
      "can_write": true
    },
    ...
  ]
}
```

#### Get User Details
```bash
GET /api/auth/users/5/
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "user": {
    "id": 5,
    "username": "jane_doe",
    "email": "jane@example.com",
    "role": "manager",
    "department": "Operations"
  },
  "profile": {
    "id": 5,
    "user": 5,
    "username": "jane_doe",
    "email": "jane@example.com",
    "role": "manager",
    "department": "Operations",
    "phone": "+1234567890",
    "bio": "Operations Manager",
    "is_admin": false,
    "is_manager": true,
    "can_write": true,
    "created_at": "2024-01-01T10:00:00Z",
    "updated_at": "2024-01-15T15:30:00Z"
  }
}
```

#### Update User Role
```bash
POST /api/auth/users/update-role/
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "user_id": 5,
  "role": "manager"
}
```

**Response:**
```json
{
  "message": "User role updated successfully from user to manager",
  "user": {
    "id": 5,
    "username": "jane_doe",
    "role": "manager",
    "is_admin": false,
    "is_manager": true,
    "can_write": true
  }
}
```

**Protection:** Admins cannot remove their own admin role to prevent lockout.

#### List Available Roles
```bash
GET /api/auth/roles/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "roles": [
    {
      "value": "admin",
      "label": "Admin",
      "description": "Full system access - can manage users, roles, and all resources",
      "permissions": ["read", "write", "delete", "manage_users", "manage_roles"]
    },
    {
      "value": "manager",
      "label": "Manager",
      "description": "Can manage jobs and scrapers, view users",
      "permissions": ["read", "write", "delete", "view_users"]
    },
    {
      "value": "user",
      "label": "User",
      "description": "Can create and edit own resources",
      "permissions": ["read", "write"]
    },
    {
      "value": "viewer",
      "label": "Viewer",
      "description": "Read-only access to resources",
      "permissions": ["read"]
    }
  ]
}
```

### Scraper Endpoints (Role-Based)

#### List Scrapers (Public)
```bash
GET /api/scrapers/list/
```
Anyone can view available scrapers.

#### Start Scraper (Manager or Admin Only)
```bash
POST /api/scrapers/start/
Authorization: Bearer <manager_or_admin_token>
Content-Type: application/json

{
  "scraper": "aviation",
  "max_pages": 5,
  "max_jobs": 100
}
```
Only managers and admins can start scrapers.

#### Scraper Status (Authenticated)
```bash
GET /api/scrapers/status/123/
Authorization: Bearer <access_token>
```
Any authenticated user can check scraper status.

#### Scraper History (Authenticated)
```bash
GET /api/scrapers/history/?scraper=aviation&limit=20
Authorization: Bearer <access_token>
```
Any authenticated user can view scraper history.

#### Scraper Stats (Authenticated)
```bash
GET /api/scrapers/stats/
Authorization: Bearer <access_token>
```
Any authenticated user can view scraper statistics.

## Admin Interface

### Managing User Roles via Django Admin

1. **Access Admin Panel**
   ```
   http://localhost:8000/admin/
   ```

2. **Navigate to Users**
   - Click on "Users" under "AUTHENTICATION AND AUTHORIZATION"
   - View list of all users with their roles (color-coded)

3. **Edit User Role**
   - Click on a user
   - Scroll to "Profile & Role" section
   - Select desired role from dropdown
   - Save changes

4. **Direct Profile Management**
   - Navigate to "User profiles" under "JOBS"
   - Edit role, department, phone, bio directly
   - Role can be changed inline in the list view

### Role Color Coding in Admin

- 🔴 **Admin**: Red - Full access
- 🟠 **Manager**: Orange - Management access
- 🟢 **User**: Green - Standard access
- ⚪ **Viewer**: Gray - Read-only

## Security Considerations

### JWT Token Configuration

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

### Best Practices

1. **Token Storage**
   - Store access tokens in memory (not localStorage)
   - Store refresh tokens in httpOnly cookies (recommended)

2. **Token Refresh**
   - Refresh access tokens before expiration
   - Use refresh tokens to get new access tokens

3. **Logout**
   - Always blacklist refresh tokens on logout
   - Clear tokens from client storage

4. **Role Assignment**
   - Only admins can assign roles
   - Admins cannot remove their own admin role
   - Default role for new users: "user"

5. **API Security**
   - Always use HTTPS in production
   - Validate permissions on every request
   - Log all role changes for audit trail

## Migration from API Key

The system has been migrated from API key authentication to JWT + RBAC:

### What Changed

1. **Removed:**
   - ❌ `ADMIN_API_KEY` environment variable
   - ❌ `APIKeyAuth` class
   - ❌ `FlexibleAuth` class (API key + JWT)

2. **Added:**
   - ✅ UserProfile model with roles
   - ✅ Permission classes for role-based access
   - ✅ Role management APIs
   - ✅ Admin interface for role management

3. **Updated:**
   - ✅ All endpoints now use JWT authentication
   - ✅ Scraper endpoints use role-based permissions
   - ✅ User serializers include role information

### Migration Steps for Existing Systems

1. **Run Migrations**
   ```bash
   python manage.py migrate
   ```

2. **Create Admin User** (if not exists)
   ```bash
   python manage.py createsuperuser
   ```

3. **Assign Roles to Existing Users**
   - Via Django admin: `/admin/`
   - Or via API (using superuser token)

4. **Update Client Applications**
   - Remove API key headers
   - Implement JWT token flow
   - Handle role-based UI rendering

5. **Test Permissions**
   - Verify each role has appropriate access
   - Test role management endpoints
   - Ensure admins cannot lock themselves out

## Testing

### Create Test Users

```bash
# Admin user (superuser)
python manage.py createsuperuser

# Regular users via API
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "manager_user",
    "email": "manager@example.com",
    "password": "ManagerPass123!",
    "password2": "ManagerPass123!"
  }'
```

### Assign Roles

```bash
# Get admin token
ADMIN_TOKEN=$(curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin_password"}' \
  | jq -r '.access')

# Update user role
curl -X POST http://localhost:8000/api/auth/users/update-role/ \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "role": "manager"}'
```

### Test Permissions

```bash
# Try to start scraper as viewer (should fail)
VIEWER_TOKEN="<viewer_access_token>"
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation"}'
# Expected: 403 Forbidden

# Try to start scraper as manager (should succeed)
MANAGER_TOKEN="<manager_access_token>"
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer $MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation"}'
# Expected: 202 Accepted
```

## Troubleshooting

### Issue: User has no role after registration

**Solution:** UserProfile is auto-created with default role "user". If missing:
```python
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
```

### Issue: Permission denied for valid user

**Check:**
1. User has correct role: `user.role`
2. Endpoint requires correct permission class
3. Token is valid and not expired

### Issue: Cannot access admin panel

**Solution:** Create superuser:
```bash
python manage.py createsuperuser
```
Superusers bypass all role checks.

### Issue: Admin accidentally removed their role

**Prevention:** System prevents admins from removing their own admin role.

**Recovery:** Use another admin or access via Django shell:
```python
from django.contrib.auth.models import User
user = User.objects.get(username='locked_admin')
user.userprofile.role = 'admin'
user.userprofile.save()
```

## Summary

The RBAC system provides:

- ✅ **Flexible Access Control**: 4 distinct roles with clear permissions
- ✅ **Easy Management**: Django admin interface + REST APIs
- ✅ **Secure Authentication**: JWT-based with token blacklist
- ✅ **Audit Trail**: All role changes logged
- ✅ **Developer Friendly**: Clear permission classes and helpers
- ✅ **Production Ready**: Secure defaults, protection against lockout

For more information, see:
- `jobs/permissions.py` - Permission class implementations
- `jobs/user_profile.py` - UserProfile model and signals
- `jobs/auth_views.py` - Authentication and role management APIs
- `jobs/admin.py` - Django admin interface customizations
