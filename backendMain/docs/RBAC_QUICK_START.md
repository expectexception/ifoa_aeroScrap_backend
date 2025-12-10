# RBAC Quick Start Guide

## 🚀 Quick Setup (3 Steps)

### 1. Apply Migrations
```bash
cd backendMain
python manage.py migrate
```

### 2. Create Superuser
```bash
# Option A: Using setup script
./setup_rbac.sh

# Option B: Manual
python manage.py createsuperuser
```

### 3. Start Server
```bash
python manage.py runserver
```

## 🎯 Quick API Examples

### Login as Superuser
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {...}
}
```

Save the `access` token!

### Register New User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123!",
    "password2": "TestPass123!"
  }'
```

### List All Users (Admin Only)
```bash
curl http://localhost:8000/api/auth/users/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Update User Role (Admin Only)
```bash
curl -X POST http://localhost:8000/api/auth/users/update-role/ \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "role": "manager"}'
```

### Start Scraper (Manager/Admin Only)
```bash
curl -X POST http://localhost:8000/api/scrapers/start/ \
  -H "Authorization: Bearer YOUR_MANAGER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"scraper": "aviation", "max_pages": 5}'
```

## 🧪 Test RBAC System

Run the comprehensive test suite:

```bash
# Make sure server is running first!
python test_rbac.py
```

This will:
- ✓ Create 4 test users (admin, manager, user, viewer)
- ✓ Test role assignment
- ✓ Test permission enforcement
- ✓ Verify security restrictions

## 👥 User Roles

| Role | Permissions | Can Start Scrapers? | Can Manage Users? |
|------|-------------|---------------------|-------------------|
| **Admin** | Full access | ✓ Yes | ✓ Yes |
| **Manager** | Manage resources | ✓ Yes | ✗ No (view only) |
| **User** | Read + Write | ✗ No | ✗ No |
| **Viewer** | Read only | ✗ No | ✗ No |

## 🔑 Token Management

### Get New Access Token (Refresh)
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

### Logout (Blacklist Token)
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

## 🎨 Admin Interface

Access Django admin panel:
```
http://localhost:8000/admin/
```

Login with superuser credentials.

### Managing Roles:
1. Navigate to **Users** under "AUTHENTICATION AND AUTHORIZATION"
2. Click on a user
3. Scroll to **Profile & Role** section
4. Select desired role
5. Click **Save**

## 🔒 Security Notes

- Access tokens expire in **60 minutes**
- Refresh tokens expire in **7 days**
- Tokens are blacklisted on logout
- Admins cannot remove their own admin role
- All role changes are logged

## 📚 Full Documentation

For detailed information, see:
- `documents/RBAC_SYSTEM.md` - Complete documentation
- `test_rbac.py` - Test suite and examples
- `jobs/permissions.py` - Permission class definitions
- `jobs/user_profile.py` - UserProfile model

## 🆘 Troubleshooting

### Server won't start
```bash
# Check for errors
python manage.py check

# Reapply migrations
python manage.py migrate
```

### Missing UserProfile
```python
# In Django shell
python manage.py shell

from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

# Create profiles for all users
for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
```

### Permission Denied
- Check your token is valid: `GET /api/auth/profile/`
- Verify your role: response will include `role` field
- Ensure endpoint allows your role (see RBAC_SYSTEM.md)

## 📞 API Endpoints Summary

### Public Endpoints
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login
- `GET /api/scrapers/list/` - List scrapers

### Authenticated Endpoints
- `GET /api/auth/profile/` - Get own profile
- `PUT /api/auth/profile/update/` - Update profile
- `POST /api/auth/change-password/` - Change password
- `GET /api/scrapers/status/<id>/` - Check scraper status
- `GET /api/scrapers/history/` - View scraper history
- `GET /api/scrapers/stats/` - View statistics

### Manager/Admin Endpoints
- `POST /api/scrapers/start/` - Start scraper

### Admin Only Endpoints
- `GET /api/auth/users/` - List all users
- `GET /api/auth/users/<id>/` - Get user details
- `POST /api/auth/users/update-role/` - Update user role

## 🎉 You're Ready!

Your RBAC system is now configured. Happy coding! 🚀
