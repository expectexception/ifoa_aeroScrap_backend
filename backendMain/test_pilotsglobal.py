import os
import sys
import asyncio
import logging
from datetime import datetime

# Setup paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backendMain.settings")

import django
django.setup()

from scraper_manager.scrapers.pilots_global_scraper import PilotsGlobalScraper
from scraper_manager.config import CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_pilots_global():
    logger.info("Starting PilotsGlobal Scraper Test")
    
    # Override config for testing
    CONFIG['scrapers']['pilots_global'] = {
        'max_jobs': 50,  # Test with higher limit to verify pagination
        'search_locations': []  # Use base /jobs URL for testing
    }
    
    # Initialize scraper
    scraper = PilotsGlobalScraper(config=CONFIG)
    
    try:
        # Test scraping - use run() method from BaseScraper
        jobs = await scraper.run()
        
        logger.info(f"Scraping completed. Found {len(jobs)} jobs.")
        
        if not jobs:
            logger.error("No jobs were found! Check selectors or network.")
            return

        # Summary statistics
        logger.info("\n" + "="*60)
        logger.info(f"SCRAPING SUMMARY")
        logger.info("="*60)
        logger.info(f"Total jobs scraped: {len(jobs)}")
        logger.info(f"Jobs with descriptions: {sum(1 for j in jobs if j.get('description'))}")
        logger.info(f"Unique companies: {len(set(j.get('company', 'Unknown') for j in jobs))}")
        logger.info("="*60)

        # Validate first job
        first_job = jobs[0]
        logger.info("\nFirst job details:")
        logger.info(f"Title: {first_job.get('title')}")
        logger.info(f"Company: {first_job.get('company')}")
        logger.info(f"Location: {first_job.get('location')}")
        logger.info(f"URL: {first_job.get('source_url')}")
        logger.info(f"Date: {first_job.get('posted_date')}")
        
        # Check description
        desc = first_job.get('description', '')
        if desc:
            logger.info(f"Description found ({len(desc)} chars): {desc[:100]}...")
        else:
            logger.warning("No description found for first job!")
        
        # Show last job too
        if len(jobs) > 1:
            last_job = jobs[-1]
            logger.info("\nLast job details:")
            logger.info(f"Title: {last_job.get('title')}")
            logger.info(f"Company: {last_job.get('company')}")
            logger.info(f"Location: {last_job.get('location')}")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_pilots_global())
