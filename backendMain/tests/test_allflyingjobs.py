import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import os
import json
from scraper_manager.scrapers.allflyingjobs_scraper import AllFlyingJobsScraper

async def test_allflyingjobs():
    print("Testing AllFlyingJobs Scraper...")
    
    # Configuration for testing
    config = {
        'max_jobs': 5, 
        'search_queries': ['Captain']
    }
    
    scraper = AllFlyingJobsScraper(config)
    
    print(f"Initializing scraper with config: {config}")
    jobs = await scraper.fetch_jobs()
    
    print(f"\nScraping complete. Found {len(jobs)} jobs.")
    
    if len(jobs) > 0:
        print("\nFirst job details:")
        first_job = jobs[0]
        print(json.dumps(first_job, indent=2))
        
        # Validation checks
        assert first_job.get('title'), "Job title is missing"
        assert first_job.get('company'), "Company is missing"
        assert first_job.get('url'), "URL is missing"
        # We can't strictly assert description because some jobs might fail to load details, but we check presence key
        assert 'description' in first_job, "Description field missing"
        
        print("\nTest PASSED: Jobs found and basic fields present.")
    else:
        print("\nTest FAILED: No jobs found. Check selectors or network.")

if __name__ == "__main__":
    asyncio.run(test_allflyingjobs())
