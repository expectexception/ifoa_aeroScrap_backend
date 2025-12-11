import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Comprehensive test script for JWT authentication endpoints
Tests registration, login, token refresh, profile, password change, and logout
"""

import requests
import json
import sys
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"

# ANSI color codes for pretty output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test(test_name: str):
    """Print test header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing: {test_name}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"  {message}")


def test_register(username: str, email: str, password: str) -> Optional[Dict]:
    """Test user registration"""
    print_test("User Registration")
    
    url = f"{API_BASE}/auth/register/"
    data = {
        "username": username,
        "email": email,
        "password": password,
        "password2": password,
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(url, json=data)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print_success("Registration successful")
            print_info(f"User: {result.get('user', {}).get('username')}")
            print_info(f"Access Token: {result.get('access', 'N/A')[:50]}...")
            print_info(f"Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
            return result
        else:
            print_error(f"Registration failed")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_login(username: str, password: str) -> Optional[Dict]:
    """Test user login"""
    print_test("User Login")
    
    url = f"{API_BASE}/auth/login/"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, json=data)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Login successful")
            print_info(f"User: {result.get('user', {}).get('username')}")
            print_info(f"Access Token: {result.get('access', 'N/A')[:50]}...")
            print_info(f"Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
            return result
        else:
            print_error(f"Login failed")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_token_refresh(refresh_token: str) -> Optional[Dict]:
    """Test token refresh"""
    print_test("Token Refresh")
    
    url = f"{API_BASE}/auth/token/refresh/"
    data = {
        "refresh": refresh_token
    }
    
    try:
        response = requests.post(url, json=data)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Token refresh successful")
            print_info(f"New Access Token: {result.get('access', 'N/A')[:50]}...")
            if 'refresh' in result:
                print_info(f"New Refresh Token: {result.get('refresh', 'N/A')[:50]}...")
            return result
        else:
            print_error(f"Token refresh failed")
            print_info(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return None


def test_profile(access_token: str) -> bool:
    """Test getting user profile"""
    print_test("Get User Profile")
    
    url = f"{API_BASE}/auth/profile/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Profile retrieved successfully")
            print_info(f"Username: {result.get('username')}")
            print_info(f"Email: {result.get('email')}")
            print_info(f"First Name: {result.get('first_name')}")
            print_info(f"Last Name: {result.get('last_name')}")
            return True
        else:
            print_error(f"Profile retrieval failed")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_update_profile(access_token: str) -> bool:
    """Test updating user profile"""
    print_test("Update User Profile")
    
    url = f"{API_BASE}/auth/profile/update/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "first_name": "Updated",
        "last_name": "Name"
    }
    
    try:
        response = requests.put(url, json=data, headers=headers)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Profile updated successfully")
            print_info(f"New First Name: {result.get('user', {}).get('first_name')}")
            print_info(f"New Last Name: {result.get('user', {}).get('last_name')}")
            return True
        else:
            print_error(f"Profile update failed")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_change_password(access_token: str, old_password: str, new_password: str) -> bool:
    """Test password change"""
    print_test("Change Password")
    
    url = f"{API_BASE}/auth/change-password/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "old_password": old_password,
        "new_password": new_password,
        "new_password2": new_password
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Password changed successfully")
            return True
        else:
            print_error(f"Password change failed")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_auth_status(access_token: Optional[str] = None) -> bool:
    """Test authentication status"""
    print_test("Check Authentication Status")
    
    url = f"{API_BASE}/auth/status/"
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    
    try:
        response = requests.get(url, headers=headers)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print_success("Status check successful")
            print_info(f"Authenticated: {result.get('authenticated')}")
            if result.get('authenticated'):
                print_info(f"User: {result.get('user', {}).get('username')}")
            return True
        else:
            print_error(f"Status check failed")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_logout(access_token: str, refresh_token: str) -> bool:
    """Test user logout"""
    print_test("User Logout")
    
    url = f"{API_BASE}/auth/logout/"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "refresh": refresh_token
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print_success("Logout successful")
            return True
        else:
            print_error(f"Logout failed")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def test_protected_endpoint_without_auth() -> bool:
    """Test accessing protected endpoint without authentication"""
    print_test("Access Protected Endpoint Without Auth")
    
    url = f"{API_BASE}/auth/profile/"
    
    try:
        response = requests.get(url)
        print_info(f"URL: {url}")
        print_info(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print_success("Protected endpoint correctly returned 401")
            return True
        else:
            print_warning(f"Expected 401, got {response.status_code}")
            print_info(f"Response: {response.text}")
            return False
    except Exception as e:
        print_error(f"Exception: {str(e)}")
        return False


def run_all_tests():
    """Run all authentication tests"""
    print(f"\n{BLUE}{'='*60}")
    print(f"JWT Authentication Test Suite")
    print(f"{'='*60}{RESET}\n")
    
    # Test credentials
    username = "testuser"
    email = "testuser@example.com"
    password = "TestPassword123!"
    new_password = "NewTestPassword123!"
    
    test_results = []
    
    # Test 1: Register a new user
    register_result = test_register(username, email, password)
    test_results.append(("Registration", register_result is not None))
    
    if not register_result:
        print_error("\nRegistration failed. Cannot proceed with other tests.")
        return
    
    access_token = register_result.get('access')
    refresh_token = register_result.get('refresh')
    
    # Test 2: Check auth status (authenticated)
    test_results.append(("Auth Status (authenticated)", test_auth_status(access_token)))
    
    # Test 3: Get user profile
    test_results.append(("Get Profile", test_profile(access_token)))
    
    # Test 4: Update user profile
    test_results.append(("Update Profile", test_update_profile(access_token)))
    
    # Test 5: Refresh token
    refresh_result = test_token_refresh(refresh_token)
    test_results.append(("Token Refresh", refresh_result is not None))
    
    if refresh_result:
        # Use new tokens if available
        access_token = refresh_result.get('access', access_token)
        refresh_token = refresh_result.get('refresh', refresh_token)
    
    # Test 6: Change password
    test_results.append(("Change Password", test_change_password(access_token, password, new_password)))
    
    # Test 7: Login with new password
    login_result = test_login(username, new_password)
    test_results.append(("Login (new password)", login_result is not None))
    
    if login_result:
        access_token = login_result.get('access')
        refresh_token = login_result.get('refresh')
    
    # Test 8: Logout
    test_results.append(("Logout", test_logout(access_token, refresh_token)))
    
    # Test 9: Try to refresh with logged out token (should fail)
    print_test("Token Refresh After Logout")
    refresh_after_logout = test_token_refresh(refresh_token)
    test_results.append(("Refresh token after logout", refresh_after_logout is None))
    
    # Note: Access tokens remain valid until expiry (JWT stateless design)
    # Only refresh tokens are blacklisted
    
    # Test 10: Protected endpoint without auth
    test_results.append(("Protected endpoint (no auth)", test_protected_endpoint_without_auth()))
    
    # Test 11: Check auth status (not authenticated)
    test_results.append(("Auth Status (not authenticated)", test_auth_status()))
    
    # Print summary
    print(f"\n{BLUE}{'='*60}")
    print(f"Test Summary")
    print(f"{'='*60}{RESET}\n")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"{test_name:.<50} {status}")
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"Results: {GREEN}{passed}/{total}{RESET} tests passed")
    
    if passed == total:
        print(f"{GREEN}All tests passed! ✓{RESET}")
    else:
        print(f"{RED}Some tests failed. Please review the output above.{RESET}")
    
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    return passed == total


if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Tests interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
