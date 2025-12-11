import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test Scraper Manager APIs
Tests all scraper management endpoints
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
    "password": "Test@123456",
    "password2": "Test@123456"
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


def register_user() -> bool:
    """Register a test user"""
    print_test("User Registration")
    try:
        response = requests.post(
            f"{AUTH_URL}/register/",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [200, 201]:
            print_success("User registered successfully")
            return True
        elif response.status_code == 400 and "already exists" in response.text.lower():
            print_info("User already exists, continuing...")
            return True
        else:
            print_error(f"Registration failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Registration error: {e}")
        return False


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
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Login error: {e}")
        return False


def test_list_scrapers():
    """Test GET /api/scrapers/list/"""
    print_test("List Available Scrapers")
    
    try:
        response = requests.get(f"{SCRAPER_URL}/list/")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Found {data['count']} scrapers")
            print_json(data, indent=2)
            return "success"  # Return string instead of True to avoid confusion
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_scraper_stats():
    """Test GET /api/scrapers/stats/"""
    print_test("Get Scraper Statistics")
    
    try:
        response = requests.get(f"{SCRAPER_URL}/stats/")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Statistics retrieved")
            print_json(data, indent=2)
            return "success"  # Return string instead of True
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_start_scraper_sync(scraper_name: str = "aviation"):
    """Test POST /api/scrapers/start/ (synchronous)"""
    print_test(f"Start Scraper Synchronously: {scraper_name}")
    
    if not auth_token:
        print_error("No auth token available")
        return False
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={"scraper": scraper_name, "async": False},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Scraper completed: {data['status']}")
            print_json(data, indent=2)
            return data.get('job_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_start_scraper_async(scraper_name: str = "aviation"):
    """Test POST /api/scrapers/start/ (asynchronous)"""
    print_test(f"Start Scraper Asynchronously: {scraper_name}")
    
    if not auth_token:
        print_error("No auth token available")
        return False
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={"scraper": scraper_name, "async": True},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        if response.status_code == 202:
            data = response.json()
            print_success(f"Scraper started in background")
            print_json(data, indent=2)
            return data.get('job_id')
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_scraper_status(job_id: int):
    """Test GET /api/scrapers/status/<job_id>/"""
    print_test(f"Get Scraper Job Status: {job_id}")
    
    try:
        response = requests.get(f"{SCRAPER_URL}/status/{job_id}/")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Job status: {data['status']}")
            print_json(data, indent=2)
            return True
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False


def test_scraper_history():
    """Test GET /api/scrapers/history/"""
    print_test("Get Scraper History")
    
    try:
        response = requests.get(f"{SCRAPER_URL}/history/?limit=10")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Retrieved {data['count']} history records")
            print_json(data, indent=2)
            return "success"  # Return string instead of True
        else:
            print_error(f"Failed: {response.status_code}")
            print_json(response.json())
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def test_unauthorized_access():
    """Test that start scraper requires authentication"""
    print_test("Unauthorized Access (should fail)")
    
    try:
        response = requests.post(
            f"{SCRAPER_URL}/start/",
            json={"scraper": "aviation"},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code in [401, 403]:
            print_success("Correctly blocked unauthorized access")
            return "success"  # Return string instead of True
        else:
            print_error(f"Unexpected response: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"Error: {e}")
        return None


def main():
    print_header("SCRAPER MANAGER API TEST SUITE")
    
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
    
    # Test authentication setup
    print_header("AUTHENTICATION SETUP")
    if not register_user():
        print_error("Cannot proceed without user registration")
        sys.exit(1)
    
    if not login_user():
        print_error("Cannot proceed without authentication")
        sys.exit(1)
    
    # Test scraper endpoints
    print_header("SCRAPER MANAGEMENT TESTS")
    
    tests = [
        ("List Scrapers", test_list_scrapers, []),
        ("Scraper Statistics", test_scraper_stats, []),
        ("Unauthorized Access", test_unauthorized_access, []),
        ("Scraper History", test_scraper_history, []),
    ]
    
    job_ids = []
    
    for test_name, test_func, args in tests:
        results["total"] += 1
        try:
            result = test_func(*args)
            if result:
                results["passed"] += 1
                if isinstance(result, int):
                    job_ids.append(result)
            else:
                results["failed"] += 1
        except Exception as e:
            print_error(f"Test crashed: {e}")
            results["failed"] += 1
        print()
    
    # Test starting a scraper (async)
    print_header("ASYNC SCRAPER TEST")
    results["total"] += 1
    job_id = test_start_scraper_async("aviation")
    if job_id:
        results["passed"] += 1
        job_ids.append(job_id)
        
        # Wait a bit and check status
        print_info("Waiting 3 seconds before checking status...")
        time.sleep(3)
        
        results["total"] += 1
        if test_scraper_status(job_id):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        results["failed"] += 1
    
    # Test status check for all jobs
    if job_ids:
        print_header("JOB STATUS CHECKS")
        for job_id in job_ids:
            results["total"] += 1
            if test_scraper_status(job_id):
                results["passed"] += 1
            else:
                results["failed"] += 1
            print()
    
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
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ SOME TESTS FAILED{Colors.ENDC}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
