import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import Page

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class PilotsGlobalScraper(BaseScraper):
    """
    Scraper for PilotsGlobal.com
    Supports location filtering via URL path construction.
    """
    
    def __init__(self, config: Dict[str, Any], db_manager=None):
        super().__init__(config, site_key='pilots_global', db_manager=db_manager)
        self.base_url = "https://pilotsglobal.com"
        
    async def fetch_jobs(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from PilotsGlobal main jobs page
        """
        from playwright.async_api import async_playwright
        
        jobs = []
        
        # Always scrape from main jobs page
        url = f"{self.base_url}/jobs"
            
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            try:
                # Handle pagination
                current_page = 1
                max_pages = 5  # Limit pages to avoid excessive scraping
                
                while current_page <= max_pages and len(jobs) < self.max_jobs:
                    page_url = f"{url}?p={current_page}" if current_page > 1 else url
                    logger.info(f"[{self.site_key}] Scraping page {current_page}: {page_url}")
                    
                    try:
                        await page.goto(page_url, wait_until='domcontentloaded', timeout=60000)
                        await asyncio.sleep(2)  # Let page settle
                        
                        # Extract Job Cards using correct selector
                        job_elements = await page.query_selector_all('a.card.job')
                        
                        if not job_elements:
                            logger.info(f"[{self.site_key}] No more jobs found on page {current_page}")
                            break
                             
                        logger.info(f"[{self.site_key}] Found {len(job_elements)} job cards on page {current_page}")
                        
                        for element in job_elements:
                            if len(jobs) >= self.max_jobs:
                                break
                                
                            try:
                                # Extract Data
                                link = await element.get_attribute('href')
                                if not link:
                                    continue
                                    
                                full_url = f"{self.base_url}{link}" if link.startswith('/') else link
                                
                                # Skip if duplicate
                                if await self.is_url_already_scraped(full_url):
                                    continue
                                
                                # Extract Text Info from spans within the card
                                # Structure based on inspection: 
                                # span[0]: logo img, span[1]: title, span[2]: company|type, span[3+]: location/details
                                spans = await element.query_selector_all('span')
                                
                                title = ""
                                company = "Unknown"
                                location = ""
                                
                                # Get all text first for debugging
                                all_text = await element.inner_text()
                                lines = [l.strip() for l in all_text.split('\n') if l.strip()]
                                
                                # Parse based on line structure
                                # Line 0: Title
                                # Line 1: Company | Type
                                # Line 2+: Additional details (aircraft, location, etc.)
                                if len(lines) >= 1:
                                    title = lines[0]
                                
                                if len(lines) >= 2:
                                    company_line = lines[1]
                                    # Split by | to get company name
                                    company = company_line.split('|')[0].strip()
                                
                                # Look for location in remaining lines
                                for i in range(2, len(lines)):
                                    line = lines[i]
                                    # Location lines often contain country names or have | separator
                                    if '|' in line or any(keyword in line.lower() for keyword in 
                                        ['united states', 'canada', 'europe', 'asia', 'africa', 'australia', 
                                         'middle east', 'south america', 'caribbean', 'commuting']):
                                        location = line
                                        break
                                
                                if not title:
                                    continue
                                
                                job = {
                                    'company': company,
                                    'title': title,
                                    'location': location,
                                    'source_url': full_url,
                                    'apply_url': full_url,
                                    'posted_date': None,
                                    'is_active': True,
                                    'description': ''
                                }
                                
                                jobs.append(job)
                                
                            except Exception as e:
                                logger.error(f"Error parsing card: {e}")
                        
                        # Check for next page
                        current_page += 1
                        
                    except Exception as e:
                        logger.error(f"[{self.site_key}] Error scraping page {current_page}: {e}")
                        break
                
                await self._fetch_descriptions(page, jobs)
                
            finally:
                await browser.close()
            
        return jobs

    async def _fetch_descriptions(self, page: Page, jobs: List[Dict]):
        """Fetch full descriptions for jobs"""
        logger.info(f"[{self.site_key}] Fetching descriptions for {len(jobs)} jobs...")
        
        for i, job in enumerate(jobs):
            # Limit detailed scraping to save time/bandwidth
            if i >= 20: 
                break
                
            try:
                await page.goto(job['source_url'], wait_until='domcontentloaded')
                
                # Try to find description container
                # Common IDs/Classes
                desc_element = await page.query_selector('.job-description, .description, #job-details')
                
                if desc_element:
                    desc_text = await desc_element.inner_text()
                    job['description'] = desc_text
                    
                # Try to get posted date from detail page
                # e.g. "Posted 2 days ago"
                date_el = await page.query_selector('time, .date, .posted')
                if date_el:
                    date_text = await date_el.inner_text()
                    job['posted_date'] = date_text

                await asyncio.sleep(1) # Politeness
                
            except Exception as e:
                logger.warning(f"[{self.site_key}] Failed to fetch description for {job['title']}: {e}")

    async def run(self) -> List[Dict[str, Any]]:
        """Main execution method"""
        logger.info(f"[{self.site_key}] Starting scraper run...")
        
        # Fetch jobs
        jobs = await self.fetch_jobs()
        
        # Save to database if db_manager is available
        if self.use_db and jobs:
            logger.info(f"[{self.site_key}] Saving {len(jobs)} jobs to database...")
            await self.db_manager.save_jobs(jobs, source=self.site_key)
        
        return jobs
