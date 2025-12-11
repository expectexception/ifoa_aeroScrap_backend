"""
Test script for Job Seeker and Recruiter endpoints
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_test(name, passed, details=""):
    status = f"{GREEN}✓ PASS{RESET}" if passed else f"{RED}✗ FAIL{RESET}"
    print(f"{status} - {name}")
    if details:
        print(f"  {details}")

def test_registration():
    """Test user registration for job seeker and recruiter"""
    print(f"\n{YELLOW}=== Testing User Registration ==={RESET}")
    
    # Register job seeker
    job_seeker_data = {
        "username": "testjobseeker",
        "email": "jobseeker@test.com",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "Test",
        "last_name": "JobSeeker",
        "user_type": "job_seeker",
        "desired_job_title": "Pilot",
        "desired_location": "New York",
        "experience_years": 5,
        "phone": "+1234567890"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register/", json=job_seeker_data)
    print_test("Job Seeker Registration", response.status_code == 201, 
               f"Status: {response.status_code}, Response: {response.json() if response.status_code == 201 else response.text[:100]}")
    
    if response.status_code == 201:
        global job_seeker_token
        job_seeker_token = response.json()['access']
    
    # Register recruiter
    recruiter_data = {
        "username": "testrecruiter",
        "email": "recruiter@test.com",
        "password": "TestPass123!",
        "password2": "TestPass123!",
        "first_name": "Test",
        "last_name": "Recruiter",
        "user_type": "recruiter",
        "company_name": "Test Airlines",
        "company_website": "https://testairlines.com",
        "phone": "+1234567891"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register/", json=recruiter_data)
    print_test("Recruiter Registration", response.status_code == 201,
               f"Status: {response.status_code}, Response: {response.json() if response.status_code == 201 else response.text[:100]}")
    
    if response.status_code == 201:
        global recruiter_token
        recruiter_token = response.json()['access']


def test_job_seeker_endpoints():
    """Test job seeker endpoints"""
    print(f"\n{YELLOW}=== Testing Job Seeker Endpoints ==={RESET}")
    
    headers = {"Authorization": f"Bearer {job_seeker_token}"}
    
    # List jobs
    response = requests.get(f"{BASE_URL}/job-seeker/jobs/", headers=headers)
    print_test("List Jobs", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # Get job detail (if jobs exist)
    if response.status_code == 200 and response.json().get('count', 0) > 0:
        job_id = response.json()['results'][0]['id']
        response = requests.get(f"{BASE_URL}/job-seeker/jobs/{job_id}/", headers=headers)
        print_test("Get Job Detail", response.status_code == 200,
                   f"Status: {response.status_code}, Job: {response.json().get('title', 'N/A')[:50] if response.status_code == 200 else 'N/A'}")
        
        # Save job
        response = requests.post(f"{BASE_URL}/job-seeker/jobs/{job_id}/save/", headers=headers)
        print_test("Save Job", response.status_code in [200, 201],
                   f"Status: {response.status_code}")
    
    # List saved jobs
    response = requests.get(f"{BASE_URL}/job-seeker/saved-jobs/", headers=headers)
    print_test("List Saved Jobs", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # My applications
    response = requests.get(f"{BASE_URL}/job-seeker/applications/", headers=headers)
    print_test("My Applications", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # Dashboard
    response = requests.get(f"{BASE_URL}/job-seeker/dashboard/", headers=headers)
    print_test("Job Seeker Dashboard", response.status_code == 200,
               f"Status: {response.status_code}")


def test_recruiter_endpoints():
    """Test recruiter endpoints"""
    print(f"\n{YELLOW}=== Testing Recruiter Endpoints ==={RESET}")
    
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    
    # List candidates
    response = requests.get(f"{BASE_URL}/recruiter/candidates/", headers=headers)
    print_test("List Candidates", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # List applications
    response = requests.get(f"{BASE_URL}/recruiter/applications/", headers=headers)
    print_test("List Applications", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # List jobs with stats
    response = requests.get(f"{BASE_URL}/recruiter/jobs/", headers=headers)
    print_test("List Jobs with Stats", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # Dashboard
    response = requests.get(f"{BASE_URL}/recruiter/dashboard/", headers=headers)
    print_test("Recruiter Dashboard", response.status_code == 200,
               f"Status: {response.status_code}")


def test_resume_endpoints():
    """Test resume endpoints"""
    print(f"\n{YELLOW}=== Testing Resume Endpoints ==={RESET}")
    
    job_seeker_headers = {"Authorization": f"Bearer {job_seeker_token}"}
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    
    # Job seeker: List own resumes
    response = requests.get(f"{BASE_URL}/resumes/", headers=job_seeker_headers)
    print_test("Job Seeker: List Own Resumes", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # Recruiter: List all public resumes
    response = requests.get(f"{BASE_URL}/resumes/", headers=recruiter_headers)
    print_test("Recruiter: List Public Resumes", response.status_code == 200,
               f"Status: {response.status_code}, Count: {response.json().get('count', 0) if response.status_code == 200 else 'N/A'}")
    
    # Resume stats
    response = requests.get(f"{BASE_URL}/resumes/stats/", headers=job_seeker_headers)
    print_test("Job Seeker: Resume Stats", response.status_code == 200,
               f"Status: {response.status_code}")
    
    response = requests.get(f"{BASE_URL}/resumes/stats/", headers=recruiter_headers)
    print_test("Recruiter: Resume Stats", response.status_code == 200,
               f"Status: {response.status_code}")


def test_permission_checks():
    """Test that permissions are working correctly"""
    print(f"\n{YELLOW}=== Testing Permission Checks ==={RESET}")
    
    job_seeker_headers = {"Authorization": f"Bearer {job_seeker_token}"}
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    
    # Job seeker trying to access recruiter endpoint
    response = requests.get(f"{BASE_URL}/recruiter/candidates/", headers=job_seeker_headers)
    print_test("Job Seeker Blocked from Recruiter Endpoint", response.status_code == 403,
               f"Status: {response.status_code}")
    
    # Recruiter trying to access job seeker endpoint
    response = requests.get(f"{BASE_URL}/job-seeker/applications/", headers=recruiter_headers)
    print_test("Recruiter Blocked from Job Seeker Endpoint", response.status_code == 403,
               f"Status: {response.status_code}")


def main():
    """Run all tests"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Starting API Tests for Job Seeker & Recruiter System{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    try:
        test_registration()
        
        if 'job_seeker_token' in globals() and 'recruiter_token' in globals():
            test_job_seeker_endpoints()
            test_recruiter_endpoints()
            test_resume_endpoints()
            test_permission_checks()
        else:
            print(f"\n{RED}Registration failed - cannot proceed with other tests{RESET}")
    
    except Exception as e:
        print(f"\n{RED}Error during testing: {str(e)}{RESET}")
    
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Testing Complete{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
