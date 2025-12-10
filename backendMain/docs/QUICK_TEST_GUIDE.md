# Quick Start: Test Your Fixed API Endpoints

## 🚀 Start the Server

```bash
cd "/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

## ✅ Test All Endpoints (Quick Version)

Open a new terminal and run these commands:

### 1. Recent Jobs
```bash
curl "http://localhost:8000/api/jobs/recent/?hours=48&limit=5"
```

### 2. Updated Jobs
```bash
curl "http://localhost:8000/api/jobs/updated/?hours=24&limit=5"
```

### 3. Advanced Search
```bash
curl "http://localhost:8000/api/jobs/advanced-search/?q=pilot&limit=5"
```

### 4. List Companies
```bash
curl "http://localhost:8000/api/jobs/companies/?limit=10"
```

### 5. Trending Companies
```bash
curl "http://localhost:8000/api/jobs/companies/trending/?days=30&limit=5"
```

### 6. Analytics - Trends
```bash
curl "http://localhost:8000/api/jobs/analytics/trends/?days=30"
```

### 7. Analytics - Geographic
```bash
curl "http://localhost:8000/api/jobs/analytics/geographic/"
```

### 8. Analytics - Operation Types
```bash
curl "http://localhost:8000/api/jobs/analytics/operation-types/"
```

## 📊 Expected Results

All commands should return JSON data with HTTP status **200 OK**.

If you see JSON output, the endpoint is working! ✅

## 🎯 Automated Testing

Run the comprehensive test script:
```bash
./test_endpoints_comprehensive.sh
```

## ⚠️ Important Note

**Always include the trailing slash (/) in the URL!**

✅ Correct: `/api/jobs/recent/?hours=48`  
❌ Wrong: `/api/jobs/recent?hours=48`

## 📚 Full Documentation

- **API_ENDPOINTS_FIXED.md** - Complete fix documentation
- **FRONTEND_INTEGRATION_GUIDE.md** - Frontend integration guide
- **API_REFERENCE.md** - Quick API reference

## 🎉 You're All Set!

All 8 requested endpoints are now working correctly and ready for your frontend to use!
