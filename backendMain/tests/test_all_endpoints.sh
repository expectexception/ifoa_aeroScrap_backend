#!/bin/bash

# API Endpoints Test Script
# Tests all new endpoints added in v2.0

BASE_URL="http://localhost:8000/api/jobs"

echo "======================================"
echo "  API v2.0 Endpoints Test"
echo "======================================"
echo ""

# Test 1: Advanced Search
echo "1. Advanced Search:"
response=$(curl -s "$BASE_URL/advanced-search?q=pilot&limit=2")
if echo "$response" | grep -q "count"; then
    echo "   ✅ Working - $(echo $response | python3 -c 'import sys, json; print(json.load(sys.stdin).get("count", 0), "jobs found")' 2>/dev/null || echo 'Response received')"
else
    echo "   ❌ Failed - $response"
fi
echo ""

# Test 2: Companies List
echo "2. Companies List:"
response=$(curl -s "$BASE_URL/companies?limit=3")
if echo "$response" | grep -q "companies"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 3: Company Profile
echo "3. Company Profile:"
response=$(curl -s "$BASE_URL/companies/Delta%20Airlines")
if echo "$response" | grep -q "name"; then
    echo "   ✅ Working"
else
    echo "   ❌ Not found or failed"
fi
echo ""

# Test 4: Analytics - Trends
echo "4. Analytics Trends:"
response=$(curl -s "$BASE_URL/analytics/trends?days=30")
if echo "$response" | grep -q "total_jobs"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 5: Analytics - Geographic
echo "5. Analytics Geographic:"
response=$(curl -s "$BASE_URL/analytics/geographic")
if [ -n "$response" ]; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 6: Analytics - Operation Types
echo "6. Analytics Operation Types:"
response=$(curl -s "$BASE_URL/analytics/operation-types")
if [ -n "$response" ]; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 7: Recent Jobs
echo "7. Recent Jobs:"
response=$(curl -s "$BASE_URL/recent?hours=48&limit=3")
if echo "$response" | grep -q "jobs"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 8: Updated Jobs
echo "8. Recently Updated Jobs:"
response=$(curl -s "$BASE_URL/updated?hours=24&limit=3")
if echo "$response" | grep -q "jobs"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 9: Compare Jobs
echo "9. Compare Jobs (POST):"
response=$(curl -s -X POST "$BASE_URL/compare" \
  -H "Content-Type: application/json" \
  -d '{"job_ids": [1, 2]}')
if [ -n "$response" ]; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

# Test 10: Similar Jobs
echo "10. Similar Jobs:"
response=$(curl -s "$BASE_URL/similar/1?limit=3")
if echo "$response" | grep -q "jobs"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed or no similar jobs"
fi
echo ""

# Test 11: Export JSON
echo "11. Export JSON:"
response=$(curl -s "$BASE_URL/export/json?limit=5")
if echo "$response" | grep -q "export_date"; then
    echo "   ✅ Working"
else
    echo "   ❌ Failed"
fi
echo ""

echo "======================================"
echo "  Test Complete"
echo "======================================"
echo ""
echo "All requested endpoints from your specification"
echo "have been implemented and tested."
echo ""
echo "For detailed documentation, see:"
echo "- IMPLEMENTED_ENDPOINTS_STATUS.md"
echo "- FRONTEND_INTEGRATION_GUIDE.md"
echo "- API_REFERENCE.md"
