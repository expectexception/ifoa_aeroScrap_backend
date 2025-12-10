# Tests Directory

This directory contains all test files for the AeroOps backend.

## Test Files

### API Tests
- `test_all_apis.py` - Comprehensive API testing
- `test_auth.py` - Authentication tests
- `test_jwt_integration.py` - JWT integration tests
- `test_rbac.py` - Role-based access control tests

### Scraper Tests
- `test_airindia_scraper.py` - Air India scraper tests
- `test_restructured_scrapers.py` - Tests for restructured scraper system
- `test_scraper_apis.py` - Scraper API tests
- `test_scraper_db_save.py` - Database save functionality tests
- `test_scraper_endpoints.py` - Scraper endpoint tests
- `test_scraper_parameters.py` - Scraper parameter validation tests

### Database Tests
- `test_postgres.py` - PostgreSQL connection and functionality tests

### Serialization Tests
- `test_role_serialization.py` - Role serialization tests

### Shell Scripts
- `test_all_endpoints.sh` - Test all endpoints
- `test_endpoints_comprehensive.sh` - Comprehensive endpoint testing
- `test_production_readiness.sh` - Production readiness checks

## Running Tests

### Individual Test Files
```bash
# Activate virtual environment
source ../.venv/bin/activate

# Run specific test
python test_auth.py
python test_scraper_apis.py
```

### Shell Scripts
```bash
# Make executable
chmod +x test_all_endpoints.sh

# Run
./test_all_endpoints.sh
```

### All Tests
```bash
# Run all Python tests
for test in test_*.py; do
    echo "Running $test..."
    python "$test"
done
```
