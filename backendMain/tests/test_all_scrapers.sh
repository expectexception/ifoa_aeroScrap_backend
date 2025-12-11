#!/bin/bash
source .venv/bin/activate

echo "========================================================"
echo "TESTING AAP AVIATION SCRAPER"
echo "========================================================"
python manage.py run_scraper aap --max-jobs 3

echo ""
echo "========================================================"
echo "TESTING CARGOLUX SCRAPER"
echo "========================================================"
python manage.py run_scraper cargolux --max-jobs 3

echo ""
echo "========================================================"
echo "TESTING INDIGO SCRAPER"
echo "========================================================"
python manage.py run_scraper indigo --max-jobs 3
