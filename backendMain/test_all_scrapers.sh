#!/bin/bash

# Scraper Manager Testing Script
# Tests all scrapers with proper configuration

echo "========================================"
echo "SCRAPER MANAGER TEST SUITE"
echo "========================================"
echo ""

# Navigate to project directory
cd /home/rajat/Desktop/AeroOps\ Intel/aeroScrap_backend/backendMain

# Activate virtual environment if needed
source ../.venv/bin/activate

echo "Step 1: Testing Filter Manager"
echo "--------------------------------"
python3 -c "
from scraper_manager.filter_manager import JobFilterManager

try:
    filter_mgr = JobFilterManager('scraper_manager/filter_title.json')
    print(f'✅ Filter loaded: {len(filter_mgr.all_keywords)} keywords')
    
    # Test matching
    test_title = 'Flight Operations Officer - OCC'
    matches, cats, score, details = filter_mgr.matches_filter(test_title)
    print(f'✅ Filter test passed: score={score:.2f}')
except Exception as e:
    print(f'❌ Filter test failed: {e}')
"

echo ""
echo "Step 2: Testing Database Connection"
echo "--------------------------------"
python3 manage.py check --deploy

echo ""
echo "Step 3: List Available Scrapers"
echo "--------------------------------"
python3 manage.py run_scraper --list

echo ""
echo "Step 4: Test Individual Scrapers (5 jobs each)"
echo "--------------------------------"

# Test each scraper with limited jobs
SCRAPERS=(
    "signature"
    "flygosh"
    "aap"
    "goose"
    "aviationjobsearch"
    "linkedin"
)

for scraper in "${SCRAPERS[@]}"; do
    echo ""
    echo "Testing: $scraper"
    echo "----------------"
    
    # Run scraper with error handling
    python3 manage.py run_scraper "$scraper" --max-jobs 5 || echo "❌ $scraper failed"
    
    echo ""
    echo "Press Enter to continue to next scraper..."
    read
done

echo ""
echo "Step 5: View Database Statistics"
echo "--------------------------------"
python3 manage.py shell << EOF
from jobs.models import Job
from scraper_manager.models import ScraperJob, ScrapedURL

# Count jobs by source
from django.db.models import Count
job_counts = Job.objects.values('source').annotate(count=Count('id')).order_by('-count')

print("\n📊 Jobs by Source:")
for item in job_counts:
    source = item['source'] or 'Unknown'
    count = item['count']
    print(f"  • {source:20s}: {count:4d} jobs")

# Recent scraper runs
recent_runs = ScraperJob.objects.order_by('-started_at')[:10]
print(f"\n📝 Recent Scraper Runs (last 10):")
for run in recent_runs:
    status_icon = '✅' if run.status == 'completed' else '❌' if run.status == 'failed' else '⏳'
    started_time = run.started_at.strftime('%Y-%m-%d %H:%M') if run.started_at else 'N/A'
    print(f"  {status_icon} {run.scraper_name:20s} - {started_time} - {run.jobs_found or 0} jobs")

# Scraped URLs
url_count = ScrapedURL.objects.count()
print(f"\n🔗 Total Scraped URLs: {url_count}")

EOF

echo ""
echo "========================================"
echo "TEST SUITE COMPLETED"
echo "========================================"
echo ""
echo "Next Steps:"
echo "1. Review any errors above"
echo "2. Check Django admin for detailed results"
echo "3. Adjust config.py settings if needed"
echo "4. Enable Celery for scheduled scraping"
echo ""
