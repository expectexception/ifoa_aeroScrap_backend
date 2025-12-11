import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test Enhanced Scraper Manager APIs with Parameters
Tests scraper management endpoints with max_pages and max_jobs parameters
"""
import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000/api"
AUTH_URL = f"{BASE_URL}/auth"
SCRAPER_URL = f"{BASE_URL}/scrapers"

# Test user credentials
TEST_USER = {
    "username": "scraper_test_user",
    "email": "scraper@test.com",
    "password": "Test@123456"
}

# Global token storage
auth_token = None


class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_test(test_name: str):
    print(f"{Colors.OKCYAN}{Colors.BOLD}Testing:{Colors.ENDC} {test_name}")


def print_success(message: str):
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message: str):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_info(message: str):
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")


def print_json(data: Dict[Any, Any], indent: int = 2):
    print(json.dumps(data, indent=indent))


def login_user() -> bool:
    """Login and get JWT token"""
    global auth_token
    print_test("User Login")
    
    try:
        response = requests.post(
            f"{AUTH_URL}/login/",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get("access")
            print_success(f"Login successful, token: {auth_token[:20]}...")
            return True
        else:
            print_error(f"Login failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Login error: {e}")
        return False


def test_scraper_with_limits():
    """Test POST /api/scrapers/start/ with max_pages and max_jobs"""
    print_test("Start Scraper with Limits (max_pages=2, max_jobs=10)")
    
    if not auth_token:
        print_error("No auth token available")
        return False
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={
                "scraper": "aviation",
                "async": True,
                "max_pages": 2,
                "max_jobs": 10
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if response.status_code == 202:
            data = response.json()
            print_success(f"Scraper started with limits")
            print_json(data, indent=2)
            return data.get('job_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_scraper_max_pages_only():
    """Test with only max_pages parameter"""
    print_test("Start Scraper with max_pages=1")
    
    if not auth_token:
        print_error("No auth token available")
        return False
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={
                "scraper": "aviation",
                "async": True,
                "max_pages": 1
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if response.status_code == 202:
            data = response.json()
            print_success(f"Scraper started with max_pages=1")
            print_json(data, indent=2)
            return data.get('job_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_invalid_parameters():
    """Test with invalid parameters"""
    print_test("Test Invalid Parameters (negative max_pages)")
    
    if not auth_token:
        print_error("No auth token available")
        return False
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={
                "scraper": "aviation",
                "max_pages": -1
            },
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if response.status_code == 400:
            print_success("Correctly rejected invalid parameter")
            print_json(response.json())
            return True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_scraper_status_detailed(job_id: int):
    """Test GET /api/scrapers/status/<job_id>/ with enhanced details"""
    print_test(f"Get Enhanced Scraper Job Status: {job_id}")
    
    try:
        response = requests.get(f"{SCRAPER_URL}/status/{job_id}/")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Job status: {data['status']}")
            print_json(data, indent=2)
            
            # Print key metrics
            if data['status'] == 'completed':
                print_info(f"Jobs found: {data['jobs_found']}")
                print_info(f"New jobs: {data['jobs_new']}")
                print_info(f"Updated: {data['jobs_updated']}")
                print_info(f"Duplicates: {data['jobs_duplicates']}")
                print_info(f"Execution time: {data['execution_time']}s")
            
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def wait_for_completion(job_id: int, max_wait: int = 60):
    """Wait for job to complete"""
    print_info(f"Waiting for job {job_id} to complete (max {max_wait}s)...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{SCRAPER_URL}/status/{job_id}/")
            if response.status_code == 200:
                data = response.json()
                status = data['status']
                
                if status in ['completed', 'failed']:
                    print_success(f"Job {status}")
                    return data
                
                print_info(f"Status: {status}...")
                time.sleep(5)
            else:
                print_error(f"Error checking status: {response.status_code}")
                return None
        except Exception as e:
            print_error(f"Error: {e}")
            return None
    
    print_error(f"Timeout waiting for job completion")
    return None


def main():
    print_header("ENHANCED SCRAPER MANAGER API TESTS")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Check if server is running
    print_test("Server Health Check")
    try:
        response = requests.get(f"{BASE_URL}/health/", timeout=5)
        if response.status_code == 200:
            print_success("Server is running")
        else:
            print_error("Server is not responding correctly")
            sys.exit(1)
    except Exception as e:
        print_error(f"Cannot connect to server: {e}")
        print_info("Please start the server with: python manage.py runserver")
        sys.exit(1)
    
    # Login
    print_header("AUTHENTICATION")
    if not login_user():
        print_error("Cannot proceed without authentication")
        sys.exit(1)
    
    # Test parameter validation
    print_header("PARAMETER VALIDATION TESTS")
    
    results["total"] += 1
    if test_invalid_parameters():
        results["passed"] += 1
    else:
        results["failed"] += 1
    print()
    
    # Test scraper with limits
    print_header("SCRAPER WITH PARAMETERS")
    
    results["total"] += 1
    job_id1 = test_scraper_with_limits()
    if job_id1:
        results["passed"] += 1
    else:
        results["failed"] += 1
    print()
    
    results["total"] += 1
    job_id2 = test_scraper_max_pages_only()
    if job_id2:
        results["passed"] += 1
    else:
        results["failed"] += 1
    print()
    
    # Wait for one job to complete and check detailed status
    if job_id1:
        print_header("MONITORING JOB EXECUTION")
        completed_job = wait_for_completion(job_id1, max_wait=120)
        
        if completed_job:
            results["total"] += 1
            if test_scraper_status_detailed(job_id1):
                results["passed"] += 1
            else:
                results["failed"] += 1
    
    # Print summary
    print_header("TEST SUMMARY")
    print(f"Total Tests: {results['total']}")
    print(f"{Colors.OKGREEN}Passed: {results['passed']}{Colors.ENDC}")
    print(f"{Colors.FAIL}Failed: {results['failed']}{Colors.ENDC}")
    
    success_rate = (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0
    print(f"\nSuccess Rate: {success_rate:.1f}%")
    
    if results['failed'] == 0:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.ENDC}\n")
        return 0
    else:
        print(f"\n{Colors.WARNING}{Colors.BOLD}⚠ SOME TESTS FAILED{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
