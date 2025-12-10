#!/bin/bash
# Test all scrapers one by one
# Usage: ./test_all_scrapers.sh [max_jobs]

MAX_JOBS="${1:-5}"  # Default to 5 jobs if not specified

echo "============================================"
echo "Testing All Aviation Job Scrapers"
echo "Max jobs per scraper: $MAX_JOBS"
echo "============================================"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Array of enabled scrapers
SCRAPERS=("signature" "flygosh" "aap" "indigo" "aviationjobsearch" "goose" "linkedin" "cargolux")

# Test each scraper
for scraper in "${SCRAPERS[@]}"; do
    echo ""
    echo "========================================"
    echo "Testing: $scraper"
    echo "========================================"
    
    # Run with timeout to prevent hanging
    timeout 300 python3 manage.py run_scraper "$scraper" --max-jobs "$MAX_JOBS" 2>&1 | tail -50
    
    exit_code=$?
    if [ $exit_code -eq 124 ]; then
        echo "⚠️  WARNING: $scraper timed out after 5 minutes"
    elif [ $exit_code -ne 0 ]; then
        echo "❌ ERROR: $scraper failed with exit code $exit_code"
    else
        echo "✅ $scraper completed successfully"
    fi
    
    echo ""
    echo "Waiting 5 seconds before next scraper..."
    sleep 5
done

echo ""
echo "============================================"
echo "All scrapers tested!"
echo "============================================"
echo ""
echo "Checking database statistics..."
python3 manage.py shell -c "
from jobs.models import Job
from django.db.models import Count

counts = Job.objects.values('source').annotate(count=Count('id')).order_by('-count')
print('\n📊 Jobs by Source:')
print('='*50)
for item in counts:
    print(f'{item[\"source\"]:20s}: {item[\"count\"]:4d} jobs')
print('='*50)
print(f'TOTAL: {Job.objects.count()} jobs\n')
"
