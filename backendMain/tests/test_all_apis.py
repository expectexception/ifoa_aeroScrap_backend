#!/usr/bin/env python3
"""
Comprehensive API testing script for all backend endpoints
Tests all endpoints with various parameters and validates response formats
"""

import requests
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000/api"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_test(name, status, details=""):
    """Log test results with colors"""
    color = GREEN if status == "PASS" else RED if status == "FAIL" else YELLOW
    print(f"{color}[{status}]{RESET} {name}")
    if details:
        print(f"      {details}")

def test_endpoint(name, url, method="GET", data=None, expected_keys=None):
    """Test a single endpoint"""
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            log_test(name, "SKIP", f"Method {method} not implemented")
            return False
        
        if response.status_code != 200:
            log_test(name, "FAIL", f"Status: {response.status_code}, Response: {response.text[:200]}")
            return False
        
        result = response.json()
        
        # Validate expected keys
        if expected_keys:
            missing_keys = [key for key in expected_keys if key not in result]
            if missing_keys:
                log_test(name, "FAIL", f"Missing keys: {missing_keys}")
                return False
        
        log_test(name, "PASS", f"Response keys: {list(result.keys())}")
        return True
    except requests.exceptions.Timeout:
        log_test(name, "FAIL", "Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        log_test(name, "FAIL", "Connection error - is server running?")
        return False
    except Exception as e:
        log_test(name, "FAIL", f"Error: {str(e)}")
        return False

def main():
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Backend API Comprehensive Test Suite{RESET}")
    print(f"{BLUE}{'='*80}{RESET}\n")
    
    passed = 0
    failed = 0
    
    # Test 1: Health Check
    print(f"\n{BLUE}=== Health Checks ==={RESET}")
    if test_endpoint("Health Check", f"{BASE_URL}/health/", expected_keys=["ok"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Jobs Health Check", f"{BASE_URL}/jobs/health", expected_keys=["ok"]):
        passed += 1
    else:
        failed += 1
    
    # Test 2: Advanced Search
    print(f"\n{BLUE}=== Advanced Search ==={RESET}")
    if test_endpoint("Advanced Search - Basic", f"{BASE_URL}/jobs/advanced-search/", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Advanced Search - With Query", f"{BASE_URL}/jobs/advanced-search/?q=pilot", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Advanced Search - With Countries", f"{BASE_URL}/jobs/advanced-search/?countries=US,UK", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Advanced Search - Senior Only", f"{BASE_URL}/jobs/advanced-search/?senior_only=true", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    date_from = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    if test_endpoint("Advanced Search - Date Range", f"{BASE_URL}/jobs/advanced-search/?date_from={date_from}", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Advanced Search - With Sorting", f"{BASE_URL}/jobs/advanced-search/?sort_by=title&order=asc", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    # Test 3: Company Endpoints
    print(f"\n{BLUE}=== Company Endpoints ==={RESET}")
    if test_endpoint("List Companies", f"{BASE_URL}/jobs/companies/", expected_keys=["companies"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("List Companies - Limited", f"{BASE_URL}/jobs/companies/?limit=5", expected_keys=["companies"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Trending Companies", f"{BASE_URL}/jobs/companies/trending/", expected_keys=["companies"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Trending Companies - Custom", f"{BASE_URL}/jobs/companies/trending/?days=7&limit=5", expected_keys=["companies"]):
        passed += 1
    else:
        failed += 1
    
    # Test a specific company (if exists)
    # Note: This will fail if no companies exist in DB
    print(f"{YELLOW}Note: Company-specific tests may fail if no data exists{RESET}")
    
    # Test 4: Analytics Endpoints
    print(f"\n{BLUE}=== Analytics Endpoints ==={RESET}")
    if test_endpoint("Job Trends", f"{BASE_URL}/jobs/analytics/trends/", expected_keys=["total_jobs", "average_per_day", "daily_trends"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Job Trends - 7 Days", f"{BASE_URL}/jobs/analytics/trends/?days=7", expected_keys=["total_jobs", "average_per_day", "daily_trends"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Geographic Distribution", f"{BASE_URL}/jobs/analytics/geographic/", expected_keys=["total_countries", "distribution"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Operation Type Stats", f"{BASE_URL}/jobs/analytics/operation-types/", expected_keys=["total_types", "distribution"]):
        passed += 1
    else:
        failed += 1
    
    # Test 5: Activity Feed
    print(f"\n{BLUE}=== Activity Feed ==={RESET}")
    if test_endpoint("Recent Jobs", f"{BASE_URL}/jobs/recent/", expected_keys=["jobs"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Recent Jobs - Custom", f"{BASE_URL}/jobs/recent/?hours=24&limit=5", expected_keys=["jobs"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Updated Jobs", f"{BASE_URL}/jobs/updated/", expected_keys=["jobs"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Updated Jobs - Custom", f"{BASE_URL}/jobs/updated/?hours=48&limit=10", expected_keys=["jobs"]):
        passed += 1
    else:
        failed += 1
    
    # Test 6: Job Listing & Details
    print(f"\n{BLUE}=== Job Listing & Details ==={RESET}")
    if test_endpoint("List Jobs", f"{BASE_URL}/jobs/", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Search Jobs", f"{BASE_URL}/jobs/search/?q=pilot", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Job Stats", f"{BASE_URL}/jobs/stats/", expected_keys=["total"]):
        passed += 1
    else:
        failed += 1
    
    # Test 7: Comparison (will fail without job IDs)
    print(f"\n{BLUE}=== Comparison Endpoints ==={RESET}")
    print(f"{YELLOW}Note: Comparison tests require existing job IDs{RESET}")
    
    # Test 8: Resume Endpoints
    print(f"\n{BLUE}=== Resume Endpoints ==={RESET}")
    if test_endpoint("List Resumes", f"{BASE_URL}/resumes", expected_keys=["count", "results"]):
        passed += 1
    else:
        failed += 1
    
    if test_endpoint("Resume Stats", f"{BASE_URL}/stats", expected_keys=["total", "avg_score"]):
        passed += 1
    else:
        failed += 1
    
    # Summary
    print(f"\n{BLUE}{'='*80}{RESET}")
    print(f"{BLUE}Test Summary{RESET}")
    print(f"{BLUE}{'='*80}{RESET}")
    total = passed + failed
    percentage = (passed / total * 100) if total > 0 else 0
    print(f"\n{GREEN}Passed: {passed}{RESET}")
    print(f"{RED}Failed: {failed}{RESET}")
    print(f"Total: {total}")
    print(f"Success Rate: {percentage:.1f}%\n")
    
    if failed == 0:
        print(f"{GREEN}✓ All tests passed!{RESET}")
        return 0
    else:
        print(f"{RED}✗ Some tests failed{RESET}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
