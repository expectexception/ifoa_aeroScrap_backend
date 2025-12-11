import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import os
import json
import logging
from scraper_manager.scrapers.airbus_scraper import AirbusScraper
from scraper_manager.config import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Airbus Scraper...")
    
    # Initialize scraper
    scraper = AirbusScraper(CONFIG)
    
    # Run scraper
    jobs = await scraper.fetch_jobs()
    
    print(f"Scraped {len(jobs)} jobs")
    
    if len(jobs) > 0:
        print("\nSample Job:")
        print(json.dumps(jobs[0], indent=2, default=str))
        
        # Verify fields
        sample = jobs[0]
        assert 'title' in sample
        assert 'source_url' in sample
        assert 'description' in sample
        # assert 'posted_date' in sample # Might be None or raw string
        
        print("\nVerification Passed!")
    else:
        print("\nNo jobs found. Verification Failed (or no matching jobs).")

if __name__ == "__main__":
    asyncio.run(test_scraper())
