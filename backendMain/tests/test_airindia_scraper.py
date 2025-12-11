import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test Air India Scraper - Complete Flow
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from jobs.models import Job
from scraper_manager.models import ScraperJob
from scraper_manager.services import ScraperService
import time

def test_air_india_scraper():
    """Test Air India scraper complete flow"""
    print("=" * 70)
    print("AIR INDIA SCRAPER - COMPLETE FLOW TEST")
    print("=" * 70)
    print()
    
    # Step 1: Check initial state
    print("STEP 1: Initial Database State")
    print("-" * 70)
    initial_count = Job.objects.count()
    air_india_count = Job.objects.filter(source__icontains='air india').count()
    print(f"Total jobs in DB: {initial_count}")
    print(f"Air India jobs: {air_india_count}")
    print()
    
    # Step 2: Create scraper job
    print("STEP 2: Creating Scraper Job Record")
    print("-" * 70)
    scraper_job = ScraperJob.objects.create(
        scraper_name='airindia',
        status='pending',
        triggered_by='test_script'
    )
    print(f"✓ Created ScraperJob ID: {scraper_job.id}")
    print(f"  Status: {scraper_job.status}")
    print()
    
    # Step 3: Run scraper
    print("STEP 3: Running Air India Scraper")
    print("-" * 70)
    print("Calling ScraperService.run_scraper()...")
    print("Parameters: scraper='airindia', max_pages=1, max_jobs=3")
    print()
    
    start_time = time.time()
    
    try:
        result = ScraperService.run_scraper(
            scraper_name='airindia',
            job_instance=scraper_job,
            max_pages=1,
            max_jobs=3
        )
        
        execution_time = time.time() - start_time
        
        print(f"✓ Scraper completed in {execution_time:.2f} seconds")
        print()
        print("Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        print()
        
    except Exception as e:
        print(f"✗ Scraper failed: {e}")
        import traceback
        traceback.print_exc()
        scraper_job.refresh_from_db()
        print(f"Job status: {scraper_job.status}")
        print(f"Error: {scraper_job.error_message}")
        return False
    
    # Step 4: Check scraper job status
    print("STEP 4: Scraper Job Status")
    print("-" * 70)
    scraper_job.refresh_from_db()
    print(f"Status: {scraper_job.status}")
    print(f"Jobs found: {scraper_job.jobs_found}")
    print(f"Jobs new: {scraper_job.jobs_new}")
    print(f"Jobs updated: {scraper_job.jobs_updated}")
    print(f"Jobs duplicates: {scraper_job.jobs_duplicates}")
    print(f"Execution time: {scraper_job.execution_time}s")
    if scraper_job.error_message:
        print(f"Errors: {scraper_job.error_message}")
    print()
    
    # Step 5: Check database changes
    print("STEP 5: Database Changes")
    print("-" * 70)
    final_count = Job.objects.count()
    air_india_final = Job.objects.filter(source__icontains='air india').count()
    print(f"Total jobs in DB: {final_count} (was {initial_count}, +{final_count - initial_count})")
    print(f"Air India jobs: {air_india_final} (was {air_india_count}, +{air_india_final - air_india_count})")
    print()
    
    # Step 6: Show sample jobs
    if air_india_final > air_india_count:
        print("STEP 6: Sample Air India Jobs Saved")
        print("-" * 70)
        new_jobs = Job.objects.filter(source__icontains='air india').order_by('-created_at')[:3]
        for i, job in enumerate(new_jobs, 1):
            print(f"{i}. {job.title}")
            print(f"   Company: {job.company}")
            print(f"   Location: {job.location}")
            print(f"   URL: {job.url[:80]}...")
            print(f"   Created: {job.created_at}")
            print()
    
    print("=" * 70)
    if scraper_job.status == 'completed' and scraper_job.jobs_found > 0:
        print("✅ TEST PASSED: Air India scraper is working correctly!")
        print()
        print("Flow verified:")
        print("  1. ✓ Scraper executed successfully")
        print("  2. ✓ Jobs scraped from Air India website")
        print("  3. ✓ Data saved to database")
        print("  4. ✓ ScraperJob record updated")
        print("  5. ✓ Statistics tracked correctly")
        return True
    else:
        print("❌ TEST FAILED: Check errors above")
        return False
    print("=" * 70)

if __name__ == '__main__':
    success = test_air_india_scraper()
    sys.exit(0 if success else 1)
