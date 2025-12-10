# RBAC Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: 'User' object has no attribute 'userprofile'

**Error Message:**
```
Error during template rendering
'User' object has no attribute 'userprofile'
```

**Cause:**
Some users were created before the UserProfile model was added, so they don't have associated profiles.

**Solution 1: Use Management Command (Recommended)**
```bash
python manage.py create_user_profiles
```

**Solution 2: Manual Fix via Django Shell**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

for user in User.objects.all():
    UserProfile.objects.get_or_create(user=user)
```

**Solution 3: Run Data Migration**
```bash
python manage.py migrate jobs
```

**Prevention:**
The system now includes:
- Post-save signals that auto-create profiles
- Data migration (0004_create_missing_profiles.py)
- Management command for bulk creation
- Admin interface that creates profiles on-the-fly

---

### Issue 2: Permission Denied for Valid User

**Error Message:**
```
403 Forbidden
{"detail": "You do not have permission to perform this action."}
```

**Cause:**
User doesn't have the required role for the endpoint.

**Check User Role:**
```bash
curl http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response will show:**
```json
{
  "role": "user",  ← Current role
  "is_admin": false,
  "is_manager": false,
  "can_write": true
}
```

**Solution:**
Update user role (requires admin):
```bash
curl -X POST http://localhost:8000/api/auth/users/update-role/ \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 2, "role": "manager"}'
```

---

### Issue 3: Token is Invalid or Expired

**Error Message:**
```
401 Unauthorized
{"detail": "Given token not valid for any token type"}
```

**Cause:**
- Access token expired (60 minutes)
- Token was blacklisted on logout
- Token is malformed

**Solution:**
Refresh the token:
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "YOUR_REFRESH_TOKEN"}'
```

If refresh token also expired, login again:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

---

### Issue 4: Cannot Access Admin Panel

**Error:**
Can't login to http://localhost:8000/admin/

**Cause:**
User is not staff or superuser.

**Solution 1: Create Superuser**
```bash
python manage.py createsuperuser
```

**Solution 2: Make Existing User Staff**
```python
python manage.py shell
```
```python
from django.contrib.auth.models import User
user = User.objects.get(username='your_username')
user.is_staff = True
user.is_superuser = True
user.save()
```

**Solution 3: Via Admin (if you have access)**
- Navigate to Users
- Edit the user
- Check "Staff status" and "Superuser status"
- Save

---

### Issue 5: Admin Locked Out (Removed Own Admin Role)

**Error:**
Admin can no longer perform admin actions.

**Prevention:**
The system prevents admins from removing their own admin role.

**Recovery (if it happens):**
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

# Find the admin user
user = User.objects.get(username='admin_username')

# Restore admin role
profile = user.userprofile
profile.role = 'admin'
profile.save()

# Or make them superuser
user.is_superuser = True
user.save()
```

---

### Issue 6: New Users Get Wrong Default Role

**Current Behavior:**
New users get role "user" by default.

**Change Default Role:**

Edit `jobs/user_profile.py`:
```python
class UserProfile(models.Model):
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer'  # ← Change this
    )
```

Then run:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Issue 7: Migration Errors

**Error:**
```
django.db.utils.IntegrityError: UNIQUE constraint failed
```

**Solution:**
1. Check current migrations:
```bash
python manage.py showmigrations jobs
```

2. If migrations are inconsistent:
```bash
# For development (destroys data)
python manage.py migrate jobs zero
python manage.py migrate jobs

# For production (preserves data)
python manage.py migrate jobs --fake-initial
```

---

### Issue 8: API Endpoint Returns 404

**Error:**
```
404 Not Found
```

**Check Available Endpoints:**
```bash
# View all URLs
python manage.py show_urls
```

**Common Endpoints:**
- `/api/auth/login/` (not `/api/auth/login`)
- `/api/auth/users/` (not `/api/users/`)
- `/api/scrapers/start/` (not `/api/scraper/start/`)

---

### Issue 9: Role Not Updating

**Problem:**
Changed role in admin but API still shows old role.

**Cause:**
JWT token contains old role information.

**Solution:**
User must login again to get new token with updated role:
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

The new access token will contain updated role.

---

### Issue 10: Server Won't Start

**Error:**
```
ModuleNotFoundError: No module named 'dotenv'
```

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

**Error:**
```
django.db.utils.OperationalError: no such table: user_profiles
```

**Solution:**
```bash
python manage.py migrate
```

---

## Diagnostic Commands

### Check User Profiles
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

print('Total Users:', User.objects.count())
print('Total Profiles:', UserProfile.objects.count())
print('')

for user in User.objects.all():
    try:
        role = user.userprofile.role
        print(f'{user.username}: {role}')
    except:
        print(f'{user.username}: NO PROFILE!')
"
```

### Check Permissions
```python
python manage.py shell
```
```python
from django.contrib.auth.models import User
from jobs.permissions import IsAdmin, IsManagerOrAbove

user = User.objects.get(username='test_user')
print(f"Role: {user.userprofile.role}")
print(f"Is Admin: {user.userprofile.is_admin}")
print(f"Is Manager: {user.userprofile.is_manager}")
print(f"Can Write: {user.userprofile.can_write}")
```

### View Token Contents
```bash
# Install jwt tool
pip install pyjwt

# Decode token (don't validate signature for inspection)
python -c "
import jwt
token = 'YOUR_ACCESS_TOKEN'
decoded = jwt.decode(token, options={'verify_signature': False})
print(decoded)
"
```

### Check Migrations Status
```bash
python manage.py showmigrations jobs
```

Expected output:
```
jobs
 [X] 0001_initial
 [X] 0002_alter_job_options_remove_job_jobs_normali_0858bc_idx_and_more
 [X] 0003_userprofile
 [X] 0004_create_missing_profiles
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/api/health/

# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Profile
curl http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer TOKEN"
```

---

## Logging

### Enable Debug Logging

Edit `settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',  # ← Change to DEBUG
        },
    },
    'loggers': {
        'jobs': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← Add this
        },
    },
}
```

### View Logs
```bash
# Real-time logs
tail -f logs/django.log

# Search for errors
grep ERROR logs/django.log

# Search for specific user
grep "username=test" logs/django.log
```

---

## Quick Fixes

### Reset Everything (Development Only)
```bash
# WARNING: This deletes all data!
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
python manage.py create_user_profiles
```

### Create Test Users
```bash
python manage.py shell -c "
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile

# Create admin
admin = User.objects.create_user('admin', 'admin@test.com', 'admin123')
admin.userprofile.role = 'admin'
admin.userprofile.save()

# Create manager
manager = User.objects.create_user('manager', 'manager@test.com', 'manager123')
manager.userprofile.role = 'manager'
manager.userprofile.save()

# Create user
user = User.objects.create_user('user', 'user@test.com', 'user123')
# Already has role 'user' by default

# Create viewer
viewer = User.objects.create_user('viewer', 'viewer@test.com', 'viewer123')
viewer.userprofile.role = 'viewer'
viewer.userprofile.save()

print('✓ Test users created!')
"
```

---

## Getting Help

1. **Check logs first:** `logs/django.log`
2. **Run diagnostics:** Use commands above
3. **Check documentation:** 
   - `RBAC_SYSTEM.md` - Full docs
   - `RBAC_QUICK_START.md` - Quick reference
4. **Run tests:** `python test_rbac.py`
5. **Django shell:** `python manage.py shell`

---

## Prevention Tips

1. **Always Use Virtual Environment**
   ```bash
   source .venv/bin/activate
   ```

2. **Keep Migrations Updated**
   ```bash
   python manage.py migrate
   ```

3. **Create Profiles After User Creation**
   ```bash
   python manage.py create_user_profiles
   ```

4. **Test Changes First**
   ```bash
   python test_rbac.py
   ```

5. **Backup Database**
   ```bash
   cp db.sqlite3 db.sqlite3.backup
   ```

6. **Use Setup Script**
   ```bash
   ./setup_rbac.sh
   ```
