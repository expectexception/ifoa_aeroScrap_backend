import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test script for Role-Based Access Control (RBAC) system
Tests authentication, role assignment, and permission enforcement
"""
import requests
import json
import sys
from typing import Dict, Optional

BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api"


class Colors:
    """Terminal colors for output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message"""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


class RBACTester:
    """Test RBAC functionality"""
    
    def __init__(self):
        self.test_users = {}
        self.results = {"passed": 0, "failed": 0}
    
    def register_user(self, username: str, password: str, email: str) -> Optional[Dict]:
        """Register a new user"""
        print_info(f"Registering user: {username}")
        
        response = requests.post(
            f"{API_BASE}/auth/register/",
            json={
                "username": username,
                "email": email,
                "password": password,
                "password2": password,
                "first_name": username.title(),
                "last_name": "Test"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print_success(f"User {username} registered successfully")
            return {
                "username": username,
                "password": password,
                "user_id": data["user"]["id"],
                "access_token": data["access"],
                "refresh_token": data["refresh"],
                "role": data["user"]["role"]
            }
        else:
            print_error(f"Failed to register {username}: {response.text}")
            return None
    
    def login_user(self, username: str, password: str) -> Optional[Dict]:
        """Login existing user"""
        print_info(f"Logging in user: {username}")
        
        response = requests.post(
            f"{API_BASE}/auth/login/",
            json={"username": username, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User {username} logged in successfully")
            return {
                "username": username,
                "password": password,
                "user_id": data["user"]["id"],
                "access_token": data["access"],
                "refresh_token": data["refresh"],
                "role": data["user"]["role"]
            }
        else:
            print_error(f"Failed to login {username}: {response.text}")
            return None
    
    def update_user_role(self, admin_token: str, user_id: int, role: str) -> bool:
        """Update user role (admin only)"""
        print_info(f"Updating user {user_id} role to: {role}")
        
        response = requests.post(
            f"{API_BASE}/auth/users/update-role/",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"user_id": user_id, "role": role}
        )
        
        if response.status_code == 200:
            print_success(f"User role updated to {role}")
            return True
        else:
            print_error(f"Failed to update role: {response.text}")
            return False
    
    def get_profile(self, token: str) -> Optional[Dict]:
        """Get user profile"""
        response = requests.get(
            f"{API_BASE}/auth/profile/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            return response.json()
        return None
    
    def list_users(self, token: str) -> Optional[Dict]:
        """List all users (admin only)"""
        response = requests.get(
            f"{API_BASE}/auth/users/",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        return response
    
    def start_scraper(self, token: str, scraper: str) -> requests.Response:
        """Start a scraper (manager or admin only)"""
        response = requests.post(
            f"{API_BASE}/scrapers/start/",
            headers={"Authorization": f"Bearer {token}"},
            json={"scraper": scraper, "max_pages": 1, "max_jobs": 10}
        )
        
        return response
    
    def test_permission(self, test_name: str, expected_status: int, actual_status: int, 
                       role: str, action: str):
        """Test permission and record result"""
        success = actual_status == expected_status
        
        if success:
            print_success(f"{test_name}: {role} {action} - Status {actual_status} (Expected)")
            self.results["passed"] += 1
        else:
            print_error(f"{test_name}: {role} {action} - Status {actual_status} (Expected {expected_status})")
            self.results["failed"] += 1
        
        return success
    
    def run_tests(self):
        """Run all RBAC tests"""
        
        # Test 1: Register users
        print_header("TEST 1: User Registration")
        
        admin_user = self.register_user("admin_test", "AdminPass123!", "admin@test.com")
        manager_user = self.register_user("manager_test", "ManagerPass123!", "manager@test.com")
        regular_user = self.register_user("user_test", "UserPass123!", "user@test.com")
        viewer_user = self.register_user("viewer_test", "ViewerPass123!", "viewer@test.com")
        
        if not all([admin_user, manager_user, regular_user, viewer_user]):
            print_error("Failed to register all test users")
            return False
        
        self.test_users = {
            "admin": admin_user,
            "manager": manager_user,
            "user": regular_user,
            "viewer": viewer_user
        }
        
        # Test 2: Role Assignment (requires existing superuser)
        print_header("TEST 2: Role Assignment")
        print_warning("This test requires an existing superuser account")
        print_info("Please provide superuser credentials:")
        
        superuser = input("Superuser username: ").strip()
        superpass = input("Superuser password: ").strip()
        
        su_data = self.login_user(superuser, superpass)
        if not su_data:
            print_error("Failed to login as superuser - skipping role assignment tests")
            return False
        
        # Assign roles
        self.update_user_role(su_data["access_token"], admin_user["user_id"], "admin")
        self.update_user_role(su_data["access_token"], manager_user["user_id"], "manager")
        self.update_user_role(su_data["access_token"], viewer_user["user_id"], "viewer")
        
        # Re-login users to get updated tokens with roles
        print_info("\nRe-authenticating users with new roles...")
        self.test_users["admin"] = self.login_user("admin_test", "AdminPass123!")
        self.test_users["manager"] = self.login_user("manager_test", "ManagerPass123!")
        self.test_users["user"] = self.login_user("user_test", "UserPass123!")
        self.test_users["viewer"] = self.login_user("viewer_test", "ViewerPass123!")
        
        # Verify roles
        print_header("Verifying User Roles")
        for role_name, user_data in self.test_users.items():
            profile = self.get_profile(user_data["access_token"])
            if profile:
                print_success(f"{user_data['username']}: role = {profile.get('role', 'unknown')}")
            else:
                print_error(f"Failed to get profile for {user_data['username']}")
        
        # Test 3: List Users Permission
        print_header("TEST 3: List Users Endpoint (Admin Only)")
        
        for role_name, user_data in self.test_users.items():
            response = self.list_users(user_data["access_token"])
            expected = 200 if role_name == "admin" else 403
            self.test_permission(
                "List Users",
                expected,
                response.status_code,
                role_name,
                "list users"
            )
        
        # Test 4: Start Scraper Permission
        print_header("TEST 4: Start Scraper Endpoint (Manager/Admin Only)")
        
        for role_name, user_data in self.test_users.items():
            response = self.start_scraper(user_data["access_token"], "aviation")
            # Admin and Manager should succeed (202), others should fail (403)
            expected = 202 if role_name in ["admin", "manager"] else 403
            self.test_permission(
                "Start Scraper",
                expected,
                response.status_code,
                role_name,
                "start scraper"
            )
        
        # Test 5: Update Own Role (Should Fail)
        print_header("TEST 5: Prevent Role Self-Elevation")
        
        response = self.update_user_role(
            self.test_users["user"]["access_token"],
            self.test_users["user"]["user_id"],
            "admin"
        )
        self.test_permission(
            "Self Elevation",
            403,  # Should fail with 403
            403 if not response else 200,
            "user",
            "self-elevate to admin"
        )
        
        # Test 6: Admin Cannot Remove Own Admin Role
        print_header("TEST 6: Prevent Admin Self-Demotion")
        
        response = requests.post(
            f"{API_BASE}/auth/users/update-role/",
            headers={"Authorization": f"Bearer {self.test_users['admin']['access_token']}"},
            json={
                "user_id": self.test_users['admin']['user_id'],
                "role": "user"
            }
        )
        self.test_permission(
            "Admin Self-Demotion",
            400,  # Should fail with 400 (bad request)
            response.status_code,
            "admin",
            "remove own admin role"
        )
        
        # Test 7: Profile Access
        print_header("TEST 7: Profile Access (All Authenticated Users)")
        
        for role_name, user_data in self.test_users.items():
            profile = self.get_profile(user_data["access_token"])
            success = profile is not None
            self.test_permission(
                "Get Profile",
                200,
                200 if success else 401,
                role_name,
                "access own profile"
            )
        
        return True
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.results["passed"] + self.results["failed"]
        success_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print_success(f"Passed: {self.results['passed']}")
        print_error(f"Failed: {self.results['failed']}")
        print(f"\nSuccess Rate: {success_rate:.1f}%")
        
        if self.results["failed"] == 0:
            print_success("\n🎉 All tests passed! RBAC system working correctly.")
        else:
            print_error(f"\n⚠️  {self.results['failed']} test(s) failed. Please review.")


def main():
    """Main test runner"""
    print_header("RBAC System Test Suite")
    print_info("This script will test the Role-Based Access Control system")
    print_info("Make sure the Django server is running on http://localhost:8000")
    
    # Check server connectivity
    try:
        response = requests.get(f"{API_BASE}/health/")
        if response.status_code == 200:
            print_success("Server is reachable")
        else:
            print_warning("Server returned unexpected status")
    except requests.ConnectionError:
        print_error("Cannot connect to server. Please start the Django server.")
        sys.exit(1)
    
    # Run tests
    tester = RBACTester()
    
    try:
        success = tester.run_tests()
        tester.print_summary()
        
        # Exit with appropriate code
        sys.exit(0 if tester.results["failed"] == 0 else 1)
        
    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nTest suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
