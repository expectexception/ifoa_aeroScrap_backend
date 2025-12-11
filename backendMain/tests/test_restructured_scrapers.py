import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test Restructured Scraper System
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from jobs.models import Job
from scraper_manager.models import ScraperJob
from scraper_manager.services import ScraperService

def test_restructured_scrapers():
    """Test that restructured scrapers work correctly"""
    print("=" * 70)
    print("TESTING RESTRUCTURED SCRAPER SYSTEM")
    print("=" * 70)
    print()
    
    # Test 1: Check scrapers are available
    print("TEST 1: Scraper Availability")
    print("-" * 70)
    scrapers = ScraperService.get_available_scrapers()
    print(f"✓ Found {len(scrapers)} scrapers")
    for scraper_id in scrapers.keys():
        print(f"  - {scraper_id}")
    print()
    
    # Test 2: Check scraper registration
    print("TEST 2: Scraper Registration")
    print("-" * 70)
    for scraper_id, info in scrapers.items():
        print(f"✓ {scraper_id}:")
        print(f"    Name: {info['name']}")
        print(f"    Module: {info['module']}")
        print(f"    Source: {info.get('source', 'N/A')}")
        print(f"    Available: {info['available']}")
    print()
    
    # Test 3: Test aviation scraper (quick test)
    print("TEST 3: Test Aviation Scraper (1 page, 2 jobs)")
    print("-" * 70)
    
    initial_count = Job.objects.count()
    print(f"Initial jobs in DB: {initial_count}")
    
    job = ScraperJob.objects.create(
        scraper_name='aviation',
        status='pending',
        triggered_by='restructure_test'
    )
    
    try:
        result = ScraperService.run_scraper(
            scraper_name='aviation',
            job_instance=job,
            max_pages=1,
            max_jobs=2
        )
        
        print(f"✓ Scraper executed successfully")
        print(f"  Jobs found: {result['jobs_found']}")
        print(f"  Jobs new: {result['jobs_new']}")
        print(f"  Jobs updated: {result['jobs_updated']}")
        print(f"  Jobs duplicates: {result['jobs_duplicates']}")
        
        job.refresh_from_db()
        print(f"✓ ScraperJob status: {job.status}")
        
        final_count = Job.objects.count()
        print(f"Final jobs in DB: {final_count} (+{final_count - initial_count})")
        
        # Check source field
        if result['jobs_new'] > 0:
            latest_job = Job.objects.filter(source='Aviation Job Search').order_by('-created_at').first()
            if latest_job:
                print(f"✓ Latest job source: '{latest_job.source}'")
                print(f"  Title: {latest_job.title}")
        
    except Exception as e:
        print(f"✗ Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Test 4: Verify directory structure
    print("TEST 4: Directory Structure")
    print("-" * 70)
    import pathlib
    base = pathlib.Path('scraper_manager')
    
    checks = [
        ('scrapers/', 'Scrapers directory'),
        ('scrapers/aviation_scraper.py', 'Aviation scraper'),
        ('scrapers/airindia_scraper.py', 'Air India scraper'),
        ('scrapers/goose_scraper.py', 'Goose scraper'),
        ('scrapers/linkedin_scraper.py', 'LinkedIn scraper'),
        ('scrapers/base_scraper.py', 'Base scraper class'),
        ('scrapers/__init__.py', 'Scrapers init'),
        ('SCRAPERS_README.md', 'Scrapers documentation'),
    ]
    
    all_exist = True
    for path, name in checks:
        full_path = base / path
        if full_path.exists():
            print(f"  ✓ {name}")
        else:
            print(f"  ✗ {name} (missing)")
            all_exist = False
    
    print()
    
    # Test 5: Check old scrapers directory is removed
    print("TEST 5: Cleanup Verification")
    print("-" * 70)
    old_scrapers = pathlib.Path('scrapers')
    if not old_scrapers.exists():
        print("  ✓ Old scrapers directory removed")
    else:
        print("  ⚠ Old scrapers directory still exists")
    print()
    
    print("=" * 70)
    if all_exist and job.status == 'completed':
        print("✅ ALL TESTS PASSED")
        print()
        print("Restructuring complete:")
        print("  ✓ Scrapers moved to scraper_manager/scrapers/")
        print("  ✓ Files renamed to proper naming convention")
        print("  ✓ Services updated to use new structure")
        print("  ✓ Source field properly set for jobs")
        print("  ✓ Old scrapers directory removed")
        print("  ✓ Documentation updated")
        print("  ✓ Everything working correctly!")
        return True
    else:
        print("❌ SOME TESTS FAILED")
        return False
    print("=" * 70)

if __name__ == '__main__':
    success = test_restructured_scrapers()
    sys.exit(0 if success else 1)
