#!/bin/bash
# Comprehensive API Test Script
# Tests all endpoints with proper trailing slashes

BASE_URL="http://localhost:8000/api/jobs"

echo "======================================"
echo "  API Endpoints Test - Fixed Version"
echo "======================================"
echo ""
echo "Testing with trailing slashes (/)..."
echo ""

test_endpoint() {
    local name="$1"
    local url="$2"
    local response=$(curl -s -w "\n%{http_code}" "$url")
    local body=$(echo "$response" | head -n -1)
    local status=$(echo "$response" | tail -n 1)
    
    if [ "$status" = "200" ]; then
        echo "✅ $name"
        echo "   Status: $status"
    else
        echo "❌ $name"
        echo "   Status: $status"
        echo "   Response: $body"
    fi
    echo ""
}

# Core endpoints
test_endpoint "1. Recent Jobs" "$BASE_URL/recent/?hours=48&limit=3"
test_endpoint "2. Updated Jobs" "$BASE_URL/updated/?hours=24&limit=3"
test_endpoint "3. Advanced Search" "$BASE_URL/advanced-search/?q=pilot&limit=3"
test_endpoint "4. List Companies" "$BASE_URL/companies/?limit=5"
test_endpoint "5. Trending Companies" "$BASE_URL/companies/trending/?days=30&limit=5"
test_endpoint "6. Analytics - Trends" "$BASE_URL/analytics/trends/?days=30"
test_endpoint "7. Analytics - Geographic" "$BASE_URL/analytics/geographic/"
test_endpoint "8. Analytics - Operation Types" "$BASE_URL/analytics/operation-types/"

echo "======================================"
echo "  Additional Endpoint Tests"
echo "======================================"
echo ""

# Test with actual data
echo "📊 Sample Responses:"
echo ""
echo "Recent Jobs (first 2):"
curl -s "$BASE_URL/recent/?hours=48&limit=2" | python3 -m json.tool | head -20
echo ""

echo "Advanced Search Results:"
curl -s "$BASE_URL/advanced-search/?q=pilot&limit=1" | python3 -m json.tool | head -30
echo ""

echo "Analytics Trends:"
curl -s "$BASE_URL/analytics/trends/?days=30" | python3 -m json.tool
echo ""

echo "======================================"
echo "  Test Complete"
echo "======================================"
