import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test script to verify scrapers save data to database correctly
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from jobs.models import Job
from scraper_manager.services import ScraperService

def test_scraper_field_mapping():
    """Test that field name normalization works correctly"""
    print("=" * 70)
    print("TESTING SCRAPER FIELD MAPPING")
    print("=" * 70)
    print()
    
    # Test data with different field names (like real scrapers return)
    test_jobs = [
        {
            'link': 'http://test1.com/job1',  # Note: 'link' instead of 'url'
            'job_title': 'Senior Pilot',       # Note: 'job_title' instead of 'title'
            'company_name': 'Test Airlines',   # Note: 'company_name' instead of 'company'
            'location': 'New York',
            'job_description': 'Fly planes'    # Note: 'job_description' instead of 'description'
        },
        {
            'url': 'http://test2.com/job2',    # Standard 'url'
            'title': 'Flight Attendant',       # Standard 'title'
            'company': 'Another Airline',      # Standard 'company'
            'location': 'London',
            'description': 'Serve passengers'  # Standard 'description'
        }
    ]
    
    # Count jobs before
    initial_count = Job.objects.count()
    print(f"Initial job count: {initial_count}")
    print()
    
    # Save test jobs
    print("Saving test jobs with different field names...")
    stats = ScraperService._save_jobs_to_db(test_jobs, 'test_scraper')
    
    print(f"✓ New jobs: {stats['new']}")
    print(f"✓ Updated jobs: {stats['updated']}")
    print(f"✓ Duplicates: {stats['duplicates']}")
    print(f"✓ Errors: {stats['errors']}")
    print()
    
    # Verify jobs were saved
    final_count = Job.objects.count()
    print(f"Final job count: {final_count}")
    print(f"Jobs added: {final_count - initial_count}")
    print()
    
    # Check the saved jobs
    if stats['new'] > 0:
        print("Verifying saved jobs:")
        for url in ['http://test1.com/job1', 'http://test2.com/job2']:
            job = Job.objects.filter(url=url).first()
            if job:
                print(f"  ✓ Job found: {job.title} at {job.company}")
                print(f"    URL: {job.url}")
                print(f"    Location: {job.location}")
            else:
                print(f"  ✗ Job not found: {url}")
        print()
    
    # Cleanup test data
    print("Cleaning up test data...")
    Job.objects.filter(url__in=['http://test1.com/job1', 'http://test2.com/job2']).delete()
    
    print()
    print("=" * 70)
    if stats['errors'] == 0 and stats['new'] == 2:
        print("✅ SUCCESS: Scraper field mapping is working correctly!")
        print()
        print("The fix handles:")
        print("  - 'link' → 'url' mapping")
        print("  - 'job_title' → 'title' mapping")
        print("  - 'company_name' → 'company' mapping")
        print("  - 'job_description' → 'description' mapping")
        return 0
    else:
        print("❌ FAILED: There were issues saving jobs")
        return 1
    print("=" * 70)

if __name__ == '__main__':
    sys.exit(test_scraper_field_mapping())
