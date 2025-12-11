#!/usr/bin/env python
"""
Test script for new role-specific profile endpoints
Tests job seeker and recruiter profile management
"""
import os
import sys
import django

# Setup Django environment
sys.path.append('/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

import requests
import json
from django.contrib.auth.models import User
from users.models import UserProfile

# Base URL
BASE_URL = "http://localhost:8000/api"

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_test(message):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}TEST: {message}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

def print_response(response):
    print(f"\nStatus Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")


class ProfileEndpointTester:
    def __init__(self):
        self.job_seeker_token = None
        self.recruiter_token = None
        self.job_seeker_username = "test_pilot_profile"
        self.recruiter_username = "test_airline_profile"
        
    def cleanup_test_users(self):
        """Remove test users if they exist"""
        print_info("Cleaning up existing test users...")
        User.objects.filter(username__in=[self.job_seeker_username, self.recruiter_username]).delete()
        print_success("Cleanup complete")
    
    def register_job_seeker(self):
        """Register a test job seeker"""
        print_test("Registering Job Seeker")
        
        data = {
            "username": self.job_seeker_username,
            "email": "pilot@test.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Pilot",
            "user_type": "job_seeker",
            "phone": "+1234567890",
            "desired_job_title": "Commercial Pilot",
            "desired_location": "New York",
            "experience_years": 5
        }
        
        response = requests.post(f"{BASE_URL}/auth/register/", json=data)
        print_response(response)
        
        if response.status_code == 201:
            self.job_seeker_token = response.json()['access']
            print_success("Job seeker registered successfully")
            return True
        else:
            print_error("Job seeker registration failed")
            return False
    
    def register_recruiter(self):
        """Register a test recruiter"""
        print_test("Registering Recruiter")
        
        data = {
            "username": self.recruiter_username,
            "email": "recruiter@airline.com",
            "password": "TestPass123!",
            "password2": "TestPass123!",
            "first_name": "Test",
            "last_name": "Recruiter",
            "user_type": "recruiter",
            "phone": "+0987654321",
            "company_name": "Test Airlines",
            "company_website": "https://testairlines.com"
        }
        
        response = requests.post(f"{BASE_URL}/auth/register/", json=data)
        print_response(response)
        
        if response.status_code == 201:
            self.recruiter_token = response.json()['access']
            print_success("Recruiter registered successfully")
            return True
        else:
            print_error("Recruiter registration failed")
            return False
    
    def test_job_seeker_get_profile(self):
        """Test GET job seeker profile"""
        print_test("GET Job Seeker Profile")
        
        headers = {
            "Authorization": f"Bearer {self.job_seeker_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/job-seeker/", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if 'profile_completion' in data and 'desired_job_title' in data:
                print_success(f"Profile retrieved successfully. Completion: {data['profile_completion']}%")
                return True
            else:
                print_error("Profile missing expected fields")
                return False
        else:
            print_error("Failed to get job seeker profile")
            return False
    
    def test_job_seeker_update_profile(self):
        """Test UPDATE job seeker profile"""
        print_test("UPDATE Job Seeker Profile (PATCH)")
        
        headers = {
            "Authorization": f"Bearer {self.job_seeker_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "bio": "Experienced pilot with 5 years of commercial flying experience. Certified on Boeing 737 and Airbus A320.",
            "skills": ["Boeing 737", "Airbus A320", "IFR", "Night Flying", "CRM"],
            "certifications": ["ATP License", "Type Rating B737", "Type Rating A320"],
            "availability": "Immediate"
        }
        
        response = requests.patch(f"{BASE_URL}/auth/profile/job-seeker/", json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Job seeker profile updated successfully")
            return True
        else:
            print_error("Failed to update job seeker profile")
            return False
    
    def test_recruiter_get_profile(self):
        """Test GET recruiter profile"""
        print_test("GET Recruiter Profile")
        
        headers = {
            "Authorization": f"Bearer {self.recruiter_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/recruiter/", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if 'profile_completion' in data and 'company_name' in data:
                print_success(f"Profile retrieved successfully. Completion: {data['profile_completion']}%")
                return True
            else:
                print_error("Profile missing expected fields")
                return False
        else:
            print_error("Failed to get recruiter profile")
            return False
    
    def test_recruiter_update_profile(self):
        """Test UPDATE recruiter profile"""
        print_test("UPDATE Recruiter Profile (PATCH)")
        
        headers = {
            "Authorization": f"Bearer {self.recruiter_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "bio": "Senior HR Manager at Test Airlines with 10 years of experience in aviation recruitment.",
            "phone": "+1111111111"
        }
        
        response = requests.patch(f"{BASE_URL}/auth/profile/recruiter/", json=data, headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            print_success("Recruiter profile updated successfully")
            return True
        else:
            print_error("Failed to update recruiter profile")
            return False
    
    def test_profile_completion_job_seeker(self):
        """Test profile completion for job seeker"""
        print_test("GET Profile Completion (Job Seeker)")
        
        headers = {
            "Authorization": f"Bearer {self.job_seeker_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/completion/", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if 'completion_percentage' in data and 'missing_fields' in data:
                print_success(f"Completion: {data['completion_percentage']}%. Missing: {data['missing_fields']}")
                return True
            else:
                print_error("Response missing expected fields")
                return False
        else:
            print_error("Failed to get profile completion")
            return False
    
    def test_profile_completion_recruiter(self):
        """Test profile completion for recruiter"""
        print_test("GET Profile Completion (Recruiter)")
        
        headers = {
            "Authorization": f"Bearer {self.recruiter_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/completion/", headers=headers)
        print_response(response)
        
        if response.status_code == 200:
            data = response.json()
            if 'completion_percentage' in data and 'missing_fields' in data:
                print_success(f"Completion: {data['completion_percentage']}%. Missing: {data['missing_fields']}")
                return True
            else:
                print_error("Response missing expected fields")
                return False
        else:
            print_error("Failed to get profile completion")
            return False
    
    def test_wrong_role_access_job_seeker(self):
        """Test that job seeker cannot access recruiter endpoint"""
        print_test("Test Access Control: Job Seeker -> Recruiter Endpoint")
        
        headers = {
            "Authorization": f"Bearer {self.job_seeker_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/recruiter/", headers=headers)
        print_response(response)
        
        if response.status_code == 403:
            print_success("Access correctly denied (403)")
            return True
        else:
            print_error("Should have returned 403")
            return False
    
    def test_wrong_role_access_recruiter(self):
        """Test that recruiter cannot access job seeker endpoint"""
        print_test("Test Access Control: Recruiter -> Job Seeker Endpoint")
        
        headers = {
            "Authorization": f"Bearer {self.recruiter_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{BASE_URL}/auth/profile/job-seeker/", headers=headers)
        print_response(response)
        
        if response.status_code == 403:
            print_success("Access correctly denied (403)")
            return True
        else:
            print_error("Should have returned 403")
            return False
    
    def run_all_tests(self):
        """Run all tests"""
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}Starting Profile Endpoint Tests{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        # Cleanup
        self.cleanup_test_users()
        
        # Registration
        if not self.register_job_seeker():
            print_error("Cannot continue without job seeker registration")
            return
        
        if not self.register_recruiter():
            print_error("Cannot continue without recruiter registration")
            return
        
        # Run tests
        results = []
        
        # Job Seeker Tests
        results.append(("Job Seeker GET Profile", self.test_job_seeker_get_profile()))
        results.append(("Job Seeker UPDATE Profile", self.test_job_seeker_update_profile()))
        results.append(("Job Seeker Profile Completion", self.test_profile_completion_job_seeker()))
        
        # Recruiter Tests
        results.append(("Recruiter GET Profile", self.test_recruiter_get_profile()))
        results.append(("Recruiter UPDATE Profile", self.test_recruiter_update_profile()))
        results.append(("Recruiter Profile Completion", self.test_profile_completion_recruiter()))
        
        # Access Control Tests
        results.append(("Access Control: Job Seeker -> Recruiter", self.test_wrong_role_access_job_seeker()))
        results.append(("Access Control: Recruiter -> Job Seeker", self.test_wrong_role_access_recruiter()))
        
        # Summary
        print(f"\n{BLUE}{'='*60}{RESET}")
        print(f"{BLUE}TEST SUMMARY{RESET}")
        print(f"{BLUE}{'='*60}{RESET}")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            if result:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")
        
        print(f"\n{BLUE}{'='*60}{RESET}")
        if passed == total:
            print(f"{GREEN}ALL TESTS PASSED: {passed}/{total}{RESET}")
        else:
            print(f"{YELLOW}TESTS PASSED: {passed}/{total}{RESET}")
        print(f"{BLUE}{'='*60}{RESET}\n")


if __name__ == "__main__":
    print_info("Make sure Django server is running on http://localhost:8000")
    input("Press Enter to start tests...")
    
    tester = ProfileEndpointTester()
    tester.run_all_tests()
