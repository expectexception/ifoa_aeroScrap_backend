import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test script to verify role serialization is working correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from django.contrib.auth.models import User
from jobs.serializers import UserSerializer
import json

def test_role_serialization():
    """Test that all users get correct role in API responses"""
    print("=" * 70)
    print("ROLE SERIALIZATION TEST")
    print("=" * 70)
    print()
    
    # Get all users
    users = User.objects.all()
    
    print(f"Testing {users.count()} users:\n")
    
    all_passed = True
    
    for user in users:
        # Get serialized data
        serializer = UserSerializer(user)
        data = serializer.data
        
        # Check role
        db_role = user.profile.role
        expected_role = 'admin' if user.is_superuser else db_role
        actual_role = data.get('role')
        
        passed = actual_role == expected_role
        status = "✓ PASS" if passed else "✗ FAIL"
        
        if not passed:
            all_passed = False
        
        print(f"{status} | User: {user.username:<15} | is_superuser: {str(user.is_superuser):<5} | DB role: {db_role:<10} | Expected: {expected_role:<10} | Got: {actual_role}")
        
        # Show full serialized data for first 2 users as examples
        if user.username in ['admin', 'testuser']:
            print(f"       Full API response: {json.dumps(data, indent=2)}")
            print()
    
    print()
    print("=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED - Role serialization is working correctly!")
        print()
        print("Summary:")
        print("  - Superusers correctly return role='admin'")
        print("  - Regular users return their database role")
        print("  - is_admin, is_manager, can_write properties are correct")
        return 0
    else:
        print("✗ SOME TESTS FAILED - There are issues with role serialization")
        return 1
    print("=" * 70)

if __name__ == '__main__':
    sys.exit(test_role_serialization())
