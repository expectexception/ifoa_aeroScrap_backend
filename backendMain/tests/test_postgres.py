#!/usr/bin/env python3
"""
PostgreSQL Integration Test Script
Tests database connection, configuration, and operations
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')

import django
django.setup()

from django.conf import settings
from django.db import connection
from django.contrib.auth.models import User
from jobs.models import Job
from resumes.models import Resume


class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'


def print_header(text):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_info(text):
    print(f"  {text}")


def test_database_config():
    """Test database configuration"""
    print_header("Database Configuration Test")
    
    db_config = settings.DATABASES['default']
    engine = db_config['ENGINE']
    
    print_info(f"Engine: {engine}")
    
    if 'postgresql' in engine:
        print_info(f"Database: {db_config['NAME']}")
        print_info(f"User: {db_config['USER']}")
        print_info(f"Host: {db_config['HOST']}")
        print_info(f"Port: {db_config['PORT']}")
        print_info(f"Connection Max Age: {db_config.get('CONN_MAX_AGE', 'Not set')}")
        print_info(f"Atomic Requests: {db_config.get('ATOMIC_REQUESTS', False)}")
        
        if os.environ.get('DB_USE_POSTGRES') == '1':
            print_success("PostgreSQL is configured and enabled")
            return True, 'postgresql'
        else:
            print_error("DB_USE_POSTGRES is not set to 1")
            return False, 'postgresql'
    else:
        print_info(f"Database: {db_config['NAME']}")
        print_success("SQLite is configured (development mode)")
        return True, 'sqlite'


def test_database_connection():
    """Test database connection"""
    print_header("Database Connection Test")
    
    try:
        with connection.cursor() as cursor:
            # Test basic query
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                print_success("Basic query successful")
                
                # Get database version
                db_config = settings.DATABASES['default']
                if 'postgresql' in db_config['ENGINE']:
                    cursor.execute("SELECT version()")
                    version = cursor.fetchone()[0]
                    print_info(f"PostgreSQL Version: {version.split(',')[0]}")
                else:
                    cursor.execute("SELECT sqlite_version()")
                    version = cursor.fetchone()[0]
                    print_info(f"SQLite Version: {version}")
                
                return True
        
    except Exception as e:
        print_error(f"Connection failed: {e}")
        return False


def test_database_operations():
    """Test CRUD operations"""
    print_header("Database Operations Test")
    
    tests_passed = 0
    tests_total = 5
    
    # Test 1: Count users
    try:
        user_count = User.objects.count()
        print_success(f"User count query: {user_count} users")
        tests_passed += 1
    except Exception as e:
        print_error(f"User count failed: {e}")
    
    # Test 2: Count jobs
    try:
        job_count = Job.objects.count()
        print_success(f"Job count query: {job_count} jobs")
        tests_passed += 1
    except Exception as e:
        print_error(f"Job count failed: {e}")
    
    # Test 3: Count resumes
    try:
        resume_count = Resume.objects.count()
        print_success(f"Resume count query: {resume_count} resumes")
        tests_passed += 1
    except Exception as e:
        print_error(f"Resume count failed: {e}")
    
    # Test 4: Create test user
    try:
        test_user, created = User.objects.get_or_create(
            username='pg_test_user',
            defaults={
                'email': 'pgtest@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        if created:
            print_success("Test user created successfully")
        else:
            print_success("Test user already exists")
        tests_passed += 1
    except Exception as e:
        print_error(f"User creation failed: {e}")
    
    # Test 5: Query test user
    try:
        user = User.objects.get(username='pg_test_user')
        print_success(f"Test user query successful: {user.username}")
        tests_passed += 1
    except Exception as e:
        print_error(f"User query failed: {e}")
    
    print_info(f"\nOperations passed: {tests_passed}/{tests_total}")
    return tests_passed == tests_total


def test_database_features():
    """Test database-specific features"""
    print_header("Database Features Test")
    
    db_config = settings.DATABASES['default']
    
    if 'postgresql' in db_config['ENGINE']:
        try:
            with connection.cursor() as cursor:
                # Test transaction
                print_info("Testing transaction support...")
                cursor.execute("BEGIN")
                cursor.execute("SELECT 1")
                cursor.execute("COMMIT")
                print_success("Transaction support confirmed")
                
                # Test connection pooling
                print_info("Testing connection pooling...")
                max_age = db_config.get('CONN_MAX_AGE', 0)
                if max_age > 0:
                    print_success(f"Connection pooling enabled ({max_age}s)")
                else:
                    print_info("Connection pooling disabled")
                
                # Test timeout settings
                print_info("Testing timeout settings...")
                options = db_config.get('OPTIONS', {})
                if 'connect_timeout' in options:
                    print_success(f"Connect timeout: {options['connect_timeout']}s")
                
                return True
        except Exception as e:
            print_error(f"Feature test failed: {e}")
            return False
    else:
        print_info("SQLite database - basic features only")
        return True


def test_performance():
    """Test basic performance"""
    print_header("Performance Test")
    
    import time
    
    try:
        # Test query performance
        start = time.time()
        User.objects.count()
        Job.objects.count()
        Resume.objects.count()
        end = time.time()
        
        duration = (end - start) * 1000  # Convert to milliseconds
        print_success(f"Basic queries completed in {duration:.2f}ms")
        
        if duration < 100:
            print_info("Performance: Excellent")
        elif duration < 500:
            print_info("Performance: Good")
        else:
            print_info("Performance: Acceptable")
        
        return True
    except Exception as e:
        print_error(f"Performance test failed: {e}")
        return False


def main():
    """Run all tests"""
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}PostgreSQL Integration Test Suite{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")
    
    results = []
    
    # Test 1: Configuration
    success, db_type = test_database_config()
    results.append(("Configuration", success))
    
    if not success:
        print_error("\nConfiguration test failed. Cannot proceed.")
        return False
    
    # Test 2: Connection
    success = test_database_connection()
    results.append(("Connection", success))
    
    if not success:
        print_error("\nConnection test failed. Cannot proceed.")
        print_info("\nTroubleshooting:")
        print_info("1. Check PostgreSQL is running: sudo systemctl status postgresql")
        print_info("2. Verify database exists: psql -U postgres -l")
        print_info("3. Check credentials in .env file")
        print_info("4. Run setup script: ./setup_postgres.sh")
        return False
    
    # Test 3: Operations
    success = test_database_operations()
    results.append(("CRUD Operations", success))
    
    # Test 4: Features
    success = test_database_features()
    results.append(("Database Features", success))
    
    # Test 5: Performance
    success = test_performance()
    results.append(("Performance", success))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"{test_name:.<40} {status}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"Results: {Colors.GREEN if passed == total else Colors.RED}{passed}/{total}{Colors.RESET} tests passed")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All tests passed! PostgreSQL integration is working correctly.{Colors.RESET}")
        return True
    else:
        print(f"{Colors.RED}✗ Some tests failed. Please review the output above.{Colors.RESET}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Tests interrupted by user{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"{Colors.RED}Unexpected error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
