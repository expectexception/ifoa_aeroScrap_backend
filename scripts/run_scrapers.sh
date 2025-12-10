#!/usr/bin/env bash

# Wrapper to run all scrapers from project root using the project's virtualenv
# Logs appended to backendMain/logs/scraper_cron.log

# Project root
PROJECT_ROOT="/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend"
VENV_ACTIVATE="$PROJECT_ROOT/backendMain/.venv/bin/activate"
LOGFILE="$PROJECT_ROOT/backendMain/logs/scraper_cron.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOGFILE")"

# Change to project root
cd "$PROJECT_ROOT" || exit 1

# Activate virtualenv if available
if [ -f "$VENV_ACTIVATE" ]; then
  # shellcheck disable=SC1090
  source "$VENV_ACTIVATE"
fi

# Run scrapers via Django management command and append output to logfile with timestamp
echo "\n=== Scraper run started: $(date -u +"%Y-%m-%d %H:%M:%S %Z") ===" >> "$LOGFILE"
# Use Django manage.py command to run scrapers (uses scraper_manager app)
if [ -f "$PROJECT_ROOT/backendMain/manage.py" ]; then
  cd "$PROJECT_ROOT/backendMain" || exit 1
  python3 manage.py run_scraper all >> "$LOGFILE" 2>&1 || echo "Scraper management command failed with exit $?" >> "$LOGFILE"
  cd "$PROJECT_ROOT" || exit 1
else
  # Fallback to legacy runner if manage.py not found
  python3 site_data_extraction/run_all_scrapers.py all >> "$LOGFILE" 2>&1 || echo "Legacy scraper runner failed with exit $?" >> "$LOGFILE"
fi

echo "=== Scraper run finished: $(date -u +"%Y-%m-%d %H:%M:%S %Z") ===\n" >> "$LOGFILE"
