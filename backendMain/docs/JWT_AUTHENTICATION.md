# JWT Authentication API Documentation

## Overview

This document describes the JWT (JSON Web Token) authentication system implemented in the AeroScrap backend. The system provides secure user authentication with access and refresh tokens.

## Base URL

```
http://localhost:8000/api/auth/
```

## Authentication Flow

1. **Register** a new user account
2. **Login** to receive access and refresh tokens
3. **Use access token** in Authorization header for protected endpoints
4. **Refresh** tokens when access token expires
5. **Logout** to blacklist refresh token

## Token Types

### Access Token
- **Lifetime**: 60 minutes
- **Purpose**: Authenticate API requests
- **Usage**: Include in Authorization header as `Bearer <token>`
- **Note**: Cannot be invalidated before expiry (stateless design)

### Refresh Token
- **Lifetime**: 7 days
- **Purpose**: Obtain new access tokens
- **Rotation**: New refresh token issued on each refresh
- **Blacklist**: Old refresh tokens are blacklisted after rotation

## Endpoints

### 1. Register User

Create a new user account and receive JWT tokens.

**Endpoint**: `POST /api/auth/register/`

**Authentication**: None required

**Request Body**:
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "password2": "SecurePassword123!",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Required Fields**:
- `username`: Unique username
- `email`: Valid email address (must be unique)
- `password`: Strong password (validated by Django)
- `password2`: Password confirmation (must match password)

**Optional Fields**:
- `first_name`: User's first name
- `last_name`: User's last name

**Success Response** (201 Created):
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-11-21T12:00:00Z"
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "User registered successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid input data
  - Password mismatch
  - Weak password
  - Email already exists
  - Username already taken

---

### 2. Login

Authenticate with username and password to receive JWT tokens.

**Endpoint**: `POST /api/auth/login/`

**Authentication**: None required

**Request Body**:
```json
{
  "username": "johndoe",
  "password": "SecurePassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-11-21T12:00:00Z"
  },
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "message": "Login successful"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "error": "Invalid credentials"
}
```

---

### 3. Refresh Token

Obtain a new access token using a valid refresh token.

**Endpoint**: `POST /api/auth/token/refresh/`

**Authentication**: None required (refresh token in body)

**Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Note**: A new refresh token is also issued due to rotation policy.

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Token is blacklisted",
  "code": "token_not_valid"
}
```

---

### 4. Logout

Blacklist the refresh token to prevent further use.

**Endpoint**: `POST /api/auth/logout/`

**Authentication**: Required (Bearer token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "message": "Logout successful"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid or missing refresh token
- `401 Unauthorized`: Invalid access token

**Note**: Access tokens remain valid until expiry (this is standard JWT behavior).

---

### 5. Get Profile

Retrieve the authenticated user's profile information.

**Endpoint**: `GET /api/auth/profile/`

**Authentication**: Required (Bearer token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Success Response** (200 OK):
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "date_joined": "2025-11-21T12:00:00Z"
}
```

**Error Response** (401 Unauthorized):
```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 6. Update Profile

Update the authenticated user's profile information.

**Endpoint**: `PUT /api/auth/profile/update/` or `PATCH /api/auth/profile/update/`

**Authentication**: Required (Bearer token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body** (all fields optional):
```json
{
  "first_name": "Johnny",
  "last_name": "Doe",
  "email": "johnny@example.com"
}
```

**Success Response** (200 OK):
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "johnny@example.com",
    "first_name": "Johnny",
    "last_name": "Doe",
    "date_joined": "2025-11-21T12:00:00Z"
  },
  "message": "Profile updated successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Invalid data
- `401 Unauthorized`: Invalid access token

---

### 7. Change Password

Change the authenticated user's password.

**Endpoint**: `POST /api/auth/change-password/`

**Authentication**: Required (Bearer token)

**Headers**:
```
Authorization: Bearer <access_token>
```

**Request Body**:
```json
{
  "old_password": "OldPassword123!",
  "new_password": "NewPassword123!",
  "new_password2": "NewPassword123!"
}
```

**Success Response** (200 OK):
```json
{
  "message": "Password changed successfully"
}
```

**Error Responses**:
- `400 Bad Request`: Wrong old password or password mismatch
```json
{
  "error": "Wrong password"
}
```

---

### 8. Check Authentication Status

Check if the current request is authenticated.

**Endpoint**: `GET /api/auth/status/`

**Authentication**: Optional

**Headers** (optional):
```
Authorization: Bearer <access_token>
```

**Success Response - Authenticated** (200 OK):
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-11-21T12:00:00Z"
  }
}
```

**Success Response - Not Authenticated** (200 OK):
```json
{
  "authenticated": false
}
```

---

## Usage Examples

### cURL Examples

#### Register
```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "password2": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePassword123!"
  }'
```

#### Get Profile
```bash
curl -X GET http://localhost:8000/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

#### Refresh Token
```bash
curl -X POST http://localhost:8000/api/auth/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'
```

#### Logout
```bash
curl -X POST http://localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<refresh_token>"
  }'
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000/api/auth"

# Register
response = requests.post(f"{BASE_URL}/register/", json={
    "username": "johndoe",
    "email": "john@example.com",
    "password": "SecurePassword123!",
    "password2": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe"
})
data = response.json()
access_token = data['access']
refresh_token = data['refresh']

# Use access token for protected endpoints
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/profile/", headers=headers)
profile = response.json()

# Refresh token when needed
response = requests.post(f"{BASE_URL}/token/refresh/", json={
    "refresh": refresh_token
})
new_tokens = response.json()
access_token = new_tokens['access']
refresh_token = new_tokens['refresh']

# Logout
response = requests.post(f"{BASE_URL}/logout/", 
    headers={"Authorization": f"Bearer {access_token}"},
    json={"refresh": refresh_token}
)
```

### JavaScript/Fetch Example

```javascript
const BASE_URL = "http://localhost:8000/api/auth";

// Register
const response = await fetch(`${BASE_URL}/register/`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    username: "johndoe",
    email: "john@example.com",
    password: "SecurePassword123!",
    password2: "SecurePassword123!",
    first_name: "John",
    last_name: "Doe"
  })
});
const data = await response.json();
const accessToken = data.access;
const refreshToken = data.refresh;

// Use access token
const profileResponse = await fetch(`${BASE_URL}/profile/`, {
  headers: {'Authorization': `Bearer ${accessToken}`}
});
const profile = await profileResponse.json();

// Refresh token
const refreshResponse = await fetch(`${BASE_URL}/token/refresh/`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({refresh: refreshToken})
});
const newTokens = await refreshResponse.json();
```

---

## Protecting Existing APIs

### Django-Ninja Endpoints

The system includes a `FlexibleAuth` class that supports both API keys and JWT tokens for django-ninja endpoints:

```python
from jobs.auth import FlexibleAuth

flexible_auth = FlexibleAuth()

@router.post('/some-endpoint', auth=flexible_auth)
def protected_endpoint(request):
    user = request.user  # Available if JWT authenticated
    # Your logic here
```

This allows endpoints to accept:
- API Key (via `ADMIN_API_KEY` environment variable)
- JWT token (from user login)

### Example Usage

```bash
# Using JWT token
curl -X GET http://localhost:8000/api/jobs/ \
  -H "Authorization: Bearer <access_token>"

# Using API key
curl -X GET http://localhost:8000/api/jobs/ \
  -H "Authorization: Bearer <admin_api_key>"
```

---

## Security Considerations

1. **Token Storage**: Store tokens securely (e.g., httpOnly cookies, secure storage)
2. **HTTPS**: Always use HTTPS in production
3. **Token Expiry**: Access tokens expire after 60 minutes
4. **Refresh Rotation**: New refresh tokens are issued on each refresh
5. **Blacklist**: Logout blacklists refresh tokens
6. **Password Policy**: Django's password validation is enforced

---

## Configuration

JWT settings are configured in `settings.py`:

```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}
```

---

## Testing

Run the comprehensive test suite:

```bash
python test_auth.py
```

This tests:
- User registration
- Login
- Token refresh
- Profile management
- Password change
- Logout
- Protected endpoints
- Authentication status

---

## Error Codes

| Status Code | Meaning |
|------------|---------|
| 200 | Success |
| 201 | Created (registration successful) |
| 400 | Bad Request (invalid data) |
| 401 | Unauthorized (invalid credentials or token) |
| 403 | Forbidden (insufficient permissions) |

---

## Support

For issues or questions, please refer to:
- Django REST Framework: https://www.django-rest-framework.org/
- Simple JWT: https://django-rest-framework-simplejwt.readthedocs.io/
