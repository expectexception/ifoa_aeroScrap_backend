import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import os
import json
import logging
from scraper_manager.scrapers.boeing_scraper import BoeingScraper
from scraper_manager.config import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Boeing Scraper...")
    
    # Initialize scraper
    scraper = BoeingScraper(CONFIG)
    
    # Run scraper
    jobs = await scraper.fetch_jobs()
    
    print(f"Scraped {len(jobs)} jobs")
    
    if len(jobs) > 0:
        print("\nSample Job:")
        print(json.dumps(jobs[0], indent=2, default=str))
        
        # Verify fields
        sample = jobs[0]
        assert 'title' in sample
        assert 'apply_url' in sample
        assert 'description' in sample
        assert 'location' in sample
        
        print("\nVerification Passed!")
    else:
        print("\nNo jobs found. Verification Failed (or no matching jobs).")

if __name__ == "__main__":
    asyncio.run(test_scraper())
