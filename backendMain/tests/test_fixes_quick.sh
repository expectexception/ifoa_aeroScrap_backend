#!/bin/bash
# Test Indigo scraper only
source .venv/bin/activate

echo "Testing Indigo Scraper..."
python manage.py run_scraper indigo --max-jobs 3
