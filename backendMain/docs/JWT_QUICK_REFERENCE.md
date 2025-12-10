# JWT Authentication - Quick Reference

## 🚀 Quick Start

### 1. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","email":"user@example.com","password":"Pass123!","password2":"Pass123!"}'
```

### 2. Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"Pass123!"}'
```

### 3. Use Token
```bash
curl http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 📌 All Endpoints

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/auth/register/` | POST | ❌ | Create account |
| `/api/auth/login/` | POST | ❌ | Get tokens |
| `/api/auth/logout/` | POST | ✅ | Invalidate token |
| `/api/auth/token/refresh/` | POST | ❌ | New access token |
| `/api/auth/profile/` | GET | ✅ | Get user info |
| `/api/auth/profile/update/` | PUT/PATCH | ✅ | Update profile |
| `/api/auth/change-password/` | POST | ✅ | Change password |
| `/api/auth/status/` | GET | ⚡ | Check auth status |

Legend: ✅ Required | ❌ Not Required | ⚡ Optional

## 🔑 Token Info

- **Access Token**: 60 minutes
- **Refresh Token**: 7 days
- **Header Format**: `Authorization: Bearer <token>`

## ✅ Test Commands

```bash
# Start server
cd backendMain
python manage.py runserver

# Run tests (in another terminal)
python test_auth.py
python test_jwt_integration.py
```

## 📝 Register Request

```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "password2": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

## 📝 Login Request

```json
{
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

## 📝 Login Response

```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com"
  },
  "access": "eyJhbGc...",
  "refresh": "eyJhbGc...",
  "message": "Login successful"
}
```

## 🐍 Python Quick Example

```python
import requests

base = "http://localhost:8000/api/auth"

# Login
r = requests.post(f"{base}/login/", json={
    "username": "user", "password": "pass"
})
token = r.json()['access']

# Use token
headers = {"Authorization": f"Bearer {token}"}
profile = requests.get(f"{base}/profile/", headers=headers).json()
print(profile)
```

## 🌐 JavaScript Quick Example

```javascript
const base = "http://localhost:8000/api/auth";

// Login
const response = await fetch(`${base}/login/`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: "user", password: "pass"})
});
const {access} = await response.json();

// Use token
const profile = await fetch(`${base}/profile/`, {
  headers: {'Authorization': `Bearer ${access}`}
}).then(r => r.json());
```

## 🔧 Using with Existing APIs

```python
# FlexibleAuth accepts both API keys and JWT tokens
from jobs.auth import FlexibleAuth

flexible_auth = FlexibleAuth()

@router.get('/my-endpoint', auth=flexible_auth)
def my_endpoint(request):
    # Works with both JWT and API key
    return {"status": "ok"}
```

## ⚠️ Common Issues

**401 Unauthorized**
- Check token format: `Bearer <token>` (space required)
- Verify token hasn't expired (60 min for access)
- Ensure correct endpoint is being called

**Token after logout still works**
- This is normal! Access tokens can't be revoked
- Only refresh tokens are blacklisted
- Access tokens expire after 60 minutes

## 📚 Full Documentation

See `documents/JWT_AUTHENTICATION.md` for complete API documentation.

## 🎯 Status: Production Ready ✅

All tests passing. All endpoints working correctly.
