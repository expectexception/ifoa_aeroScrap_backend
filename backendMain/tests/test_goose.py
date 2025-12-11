import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
import os
import json
import logging
from scraper_manager.scrapers.goose_scraper import GooseRecruitmentScraper
from scraper_manager.config import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Testing Goose Scraper...")
    
    # Initialize scraper
    # Check if 'goose' is in config or add a default for testing
    if 'goose' not in CONFIG['scrapers']:
        CONFIG['scrapers']['goose'] = {'max_jobs': 10}
    if 'goose' not in CONFIG['sites']:
        CONFIG['sites']['goose'] = {
            'name': 'Goose Recruitment',
            'base_url': 'https://www.goose-recruitment.com',
            'jobs_url': 'https://www.goose-recruitment.com/job-search'
        }
        
    scraper = GooseRecruitmentScraper(CONFIG)
    
    # Run scraper
    jobs = await scraper.fetch_jobs_from_listing()
    print(f"Fetcher from listing found: {len(jobs)} jobs")
    
    # Analyze listing data
    if jobs:
        print("\nSample Listing Job:")
        print(json.dumps(jobs[0], indent=2, default=str))
    
    # Fetch descriptions
    if jobs:
        print("\nFetching descriptions...")
        jobs_with_desc = await scraper.fetch_job_descriptions(jobs[:5]) # Limit to 5 for speed
        
        print(f"\nSample Job with Description:")
        print(json.dumps(jobs_with_desc[0], indent=2, default=str))
        
        # Validation checks
        no_desc = sum(1 for j in jobs_with_desc if not j.get('description'))
        print(f"\nAnalysis:")
        print(f"- Total jobs checked: {len(jobs_with_desc)}")
        print(f"- Jobs missing description: {no_desc}")
        
    else:
        print("\nNo jobs found to analyze.")

if __name__ == "__main__":
    asyncio.run(test_scraper())
