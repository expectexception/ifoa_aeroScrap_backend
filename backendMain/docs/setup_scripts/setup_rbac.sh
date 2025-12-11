#!/bin/bash
# Setup script for RBAC system - creates superuser for testing

echo "=========================================="
echo "RBAC System Setup"
echo "=========================================="
echo ""

# Ensure all users have profiles
echo "Step 1: Creating user profiles..."
python manage.py create_user_profiles
echo ""

# Check if server is running
if ! curl -s http://localhost:8000/api/health/ > /dev/null; then
    echo "⚠️  Django server is not running"
    echo "This is OK - continuing with setup"
fi

# Create superuser
echo "Step 2: Creating superuser for RBAC management..."
echo ""
echo "Please enter superuser credentials:"

python manage.py createsuperuser

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Superuser created successfully!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "1. Login to admin panel: http://localhost:8000/admin/"
    echo "2. Or use REST API to get token:"
    echo ""
    echo "   curl -X POST http://localhost:8000/api/auth/login/ \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"username\": \"your_username\", \"password\": \"your_password\"}'"
    echo ""
    echo "3. Run RBAC tests: python test_rbac.py"
    echo ""
else
    echo ""
    echo "❌ Failed to create superuser"
    exit 1
fi
