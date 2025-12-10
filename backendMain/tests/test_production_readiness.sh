#!/bin/bash

# AeroOps Backend - Production Readiness Test Suite
# Run this script to validate all optimizations

set -e  # Exit on error

PYTHON_PATH="/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/.venv/bin/python"
PROJECT_DIR="/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"

cd "$PROJECT_DIR"

echo "=================================="
echo "AeroOps Backend - Test Suite"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

test_passed() {
    echo -e "${GREEN}✓ PASSED:${NC} $1"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}✗ FAILED:${NC} $1"
    ((TESTS_FAILED++))
}

test_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

echo "1. Testing Database Migrations..."
echo "--------------------------------"
UNAPPLIED=$($PYTHON_PATH manage.py showmigrations 2>/dev/null | grep -c "^\s*\[ \]" || true)
if [ -z "$UNAPPLIED" ] || [ "$UNAPPLIED" -eq 0 ]; then
    test_passed "All migrations applied"
else
    test_failed "Unapplied migrations found: $UNAPPLIED"
fi
echo ""

echo "2. Testing Model Integrity..."
echo "--------------------------------"
if $PYTHON_PATH manage.py check --database default > /dev/null 2>&1; then
    test_passed "Database models are valid"
else
    test_failed "Database model errors found"
fi
echo ""

echo "3. Testing Database Indexes..."
echo "--------------------------------"
INDEX_COUNT=$($PYTHON_PATH -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT COUNT(*) FROM pg_indexes WHERE tablename IN (\'jobs\', \'company_mapping\', \'crawl_log\')')
print(cursor.fetchone()[0])
" 2>/dev/null)

if [ "$INDEX_COUNT" -gt 20 ]; then
    test_passed "Database indexes created ($INDEX_COUNT indexes found)"
else
    test_warning "Expected more indexes (found: $INDEX_COUNT)"
fi
echo ""

echo "4. Testing Company Statistics..."
echo "--------------------------------"
COMPANY_COUNT=$($PYTHON_PATH -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()
from jobs.models import CompanyMapping
print(CompanyMapping.objects.count())
" 2>/dev/null)

if [ "$COMPANY_COUNT" -gt 0 ]; then
    test_passed "Company mappings exist ($COMPANY_COUNT companies)"
else
    test_warning "No company mappings found"
fi
echo ""

echo "5. Testing User Profiles (RBAC)..."
echo "--------------------------------"
USER_COUNT=$($PYTHON_PATH -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()
from django.contrib.auth.models import User
from jobs.user_profile import UserProfile
users = User.objects.count()
profiles = UserProfile.objects.count()
print(f'{users},{profiles}')
" 2>/dev/null)

USER_NUM=$(echo $USER_COUNT | cut -d',' -f1)
PROFILE_NUM=$(echo $USER_COUNT | cut -d',' -f2)

if [ "$USER_NUM" == "$PROFILE_NUM" ] && [ "$USER_NUM" -gt 0 ]; then
    test_passed "All users have profiles ($USER_NUM users, $PROFILE_NUM profiles)"
elif [ "$USER_NUM" -gt 0 ]; then
    test_warning "User count mismatch: $USER_NUM users, $PROFILE_NUM profiles"
else
    test_warning "No users found in database"
fi
echo ""

echo "6. Testing Job Model..."
echo "--------------------------------"
JOB_COUNT=$($PYTHON_PATH -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()
from jobs.models import Job
print(Job.objects.count())
" 2>/dev/null)

if [ "$JOB_COUNT" -gt 0 ]; then
    test_passed "Jobs table populated ($JOB_COUNT jobs)"
else
    test_warning "Jobs table is empty"
fi
echo ""

echo "7. Testing Management Commands..."
echo "--------------------------------"
if $PYTHON_PATH manage.py help update_company_stats > /dev/null 2>&1; then
    test_passed "Management command 'update_company_stats' available"
else
    test_failed "Management command 'update_company_stats' not found"
fi

if $PYTHON_PATH manage.py help create_user_profiles > /dev/null 2>&1; then
    test_passed "Management command 'create_user_profiles' available"
else
    test_failed "Management command 'create_user_profiles' not found"
fi
echo ""

echo "8. Testing API Endpoints..."
echo "--------------------------------"
# Start server in background
$PYTHON_PATH manage.py runserver 8000 > /dev/null 2>&1 &
SERVER_PID=$!
sleep 3

# Test health endpoint
if curl -s http://localhost:8000/health/ | grep -q "ok"; then
    test_passed "Health endpoint responding"
else
    test_failed "Health endpoint not responding"
fi

# Test jobs API
if curl -s http://localhost:8000/api/jobs/ > /dev/null 2>&1; then
    test_passed "Jobs API endpoint accessible"
else
    test_failed "Jobs API endpoint not accessible"
fi

# Kill server
kill $SERVER_PID 2>/dev/null || true
wait $SERVER_PID 2>/dev/null || true
echo ""

echo "9. Testing Configuration Files..."
echo "--------------------------------"
if [ -f ".env.production.template" ]; then
    test_passed "Production environment template exists"
else
    test_warning "Production environment template not found"
fi

if [ -f "backendMain/middleware.py" ]; then
    test_passed "Custom middleware file exists"
else
    test_warning "Custom middleware file not found"
fi

if [ -f "backendMain/settings_production.py" ]; then
    test_passed "Production settings file exists"
else
    test_warning "Production settings file not found"
fi
echo ""

echo "10. Testing Documentation..."
echo "--------------------------------"
DOCS_DIR="../documents"
if [ -f "$DOCS_DIR/PRODUCTION_DEPLOYMENT.md" ]; then
    test_passed "Production deployment guide exists"
else
    test_warning "Production deployment guide not found"
fi

if [ -f "$DOCS_DIR/OPTIMIZATION_SUMMARY.md" ]; then
    test_passed "Optimization summary exists"
else
    test_warning "Optimization summary not found"
fi

if [ -f "$DOCS_DIR/FRONTEND_RBAC_INTEGRATION.md" ]; then
    test_passed "Frontend integration guide exists"
else
    test_warning "Frontend integration guide not found"
fi
echo ""

echo "=================================="
echo "TEST RESULTS"
echo "=================================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All critical tests passed!${NC}"
    echo -e "${GREEN}✓ System is production-ready${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Review documents/OPTIMIZATION_SUMMARY.md"
    echo "2. Configure production environment (.env)"
    echo "3. Follow documents/PRODUCTION_DEPLOYMENT.md for deployment"
    exit 0
else
    echo -e "${RED}✗ Some tests failed. Please review errors above.${NC}"
    exit 1
fi
