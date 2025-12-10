# Documentation & Scripts Directory

This directory contains all documentation, setup scripts, and test files for the AeroOps Backend.

## Directory Structure

### 📁 setup_scripts/
Contains all deployment and configuration scripts:
- `quick_setup.sh` - Quick setup for development environment
- `optimize_backend.sh` - Backend optimization script
- `setup_celery.sh` - Celery configuration script
- `setup_postgres.sh` - PostgreSQL database setup
- `setup_rbac.sh` - Role-based access control setup
- `setup_service.sh` - Systemd service configuration
- `setup_scrapers.sh` - Web scraper initialization
- `*.service` files - Systemd service definitions

**Usage:**
```bash
cd documentation/setup_scripts
chmod +x *.sh
./quick_setup.sh  # Run any script
```

### 📁 test_scripts/
Contains all test files:
- `test_api_endpoints.py` - API endpoint testing
- `test_profile_endpoints.py` - Profile management tests
- `test_auto_mapping.py` - Auto-mapping functionality tests
- `test_fresh_scrape.py` - Scraper tests
- `test_job_seeker_recruiter.py` - Role-based functionality tests
- `test_quick_verify.py` - Quick verification tests

**Usage:**
```bash
cd ../..  # Return to backendMain
python documentation/test_scripts/test_api_endpoints.py
```

### 📁 archived/
Contains archived documentation (kept for reference):
- Implementation guides
- Optimization reports
- Feature documentation
- Quick reference guides

## Main Project Documentation

For API documentation and integration guides, see the `docs/` folder in the main project directory.

## Production Deployment

1. Review scripts in `setup_scripts/`
2. Configure `.env.production` with your settings
3. Run setup scripts in order:
   ```bash
   ./setup_postgres.sh
   ./setup_rbac.sh
   ./setup_celery.sh
   ./setup_service.sh
   ```
4. Configure systemd services using the `.service` files

## Testing

Run tests before deployment:
```bash
python manage.py test
# Or run specific test files
python documentation/test_scripts/test_api_endpoints.py
```

## Notes

- All scripts are version controlled
- Service files should be copied to `/etc/systemd/system/`
- Update environment variables in `.env` before running scripts
- Check logs in `../logs/` for debugging

---
Last Updated: November 26, 2025
