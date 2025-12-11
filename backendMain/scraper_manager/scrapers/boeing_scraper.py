import asyncio
import random
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from playwright.async_api import async_playwright, Page

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class BoeingScraper(BaseScraper):
    """
    Scraper for Boeing Jobs
    
    Structure:
    - Search page with keyword and location inputs
    - Pagination via "Next" button
    - Job details on separate pages
    - OneTrust cookie banner
    """
    
    def __init__(self, config: Dict[str, Any], db_manager=None):
        super().__init__(config, site_key='boeing', db_manager=db_manager)
        self.base_url = "https://jobs.boeing.com"
        self.search_url = f"{self.base_url}/search-jobs"
        
    async def fetch_jobs(self) -> List[Dict[str, Any]]:
        """
        Scrape jobs from Boeing
        """
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)
            
            try:
                # 1. Navigate to search page
                logger.info(f"[{self.site_key}] Navigating to {self.search_url}")
                try:
                    await page.goto(self.search_url, wait_until='networkidle', timeout=60000)
                except Exception as e:
                    logger.warning(f"[{self.site_key}] Initial navigation timeout: {e}")
                
                 # 2. Handle Cookie Banner
                try:
                    accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=10000)
                    if accept_btn:
                        await accept_btn.click()
                        await page.wait_for_selector('#onetrust-banner-sdk', state='hidden', timeout=5000)
                        logger.info(f"[{self.site_key}] Accepted cookies")
                except Exception:
                    logger.info(f"[{self.site_key}] No cookie banner found or already accepted")
                
                # 3. Perform Search (if config has queries/locations)
                site_config = self.config.get('scrapers', {}).get('boeing', {})
                search_queries = site_config.get('search_queries', [])
                search_locations = site_config.get('search_locations', [])
                
                # For simplicity, we'll pick the first query/location combo or just default search if empty
                # Ideally we loop through combinations, but let's do the primary one for now
                if search_queries:
                    query = search_queries[0]
                    await page.fill('input.search-keyword', query)
                    logger.info(f"[{self.site_key}] Entered keyword: {query}")
                
                if search_locations:
                    loc = search_locations[0]
                    await page.fill('input.search-location', loc)
                    logger.info(f"[{self.site_key}] Entered location: {loc}")
                    
                if search_queries or search_locations:
                    await page.click('button.search-form__submit-btn')
                    logger.info(f"[{self.site_key}] Submitted search")
                    await page.wait_for_load_state('networkidle')
                
                # 4. Scrape Pages
                page_count = 0
                
                while len(jobs) < self.max_jobs:
                    logger.info(f"[{self.site_key}] Processing page {page_count + 1}")
                    
                    # Wait for results
                    try:
                        await page.wait_for_selector('#search-results-list ul li', timeout=10000)
                    except Exception:
                         logger.warning(f"[{self.site_key}] No results found on page {page_count + 1}")
                         break
                         
                    # Extract jobs from current list
                    job_elements = await page.query_selector_all('#search-results-list ul li')
                    logger.info(f"[{self.site_key}] Found {len(job_elements)} jobs on page")
                    
                    for el in job_elements:
                        if len(jobs) >= self.max_jobs:
                            break
                            
                        try:
                            link = await el.query_selector('a.search-results__job-link')
                            if not link:
                                continue
                                
                            title = await link.inner_text()
                            url_suffix = await link.get_attribute('href')
                            job_url = self.base_url + url_suffix if url_suffix.startswith('/') else url_suffix
                            
                            loc_el = await el.query_selector('.search-results__job-info.location')
                            location = await loc_el.inner_text() if loc_el else "Unknown"
                            
                            # Navigate to detail page for description
                            # To keep it fast, we could skip description or open new tab. 
                            # Let's open new tab for detail to preserve search state.
                            
                            detail_page = await context.new_page()
                            try:
                                await detail_page.goto(job_url, wait_until='domcontentloaded', timeout=30000)
                                desc_el = await detail_page.query_selector('div.ats-description') # Common selector, might need adjustment
                                if not desc_el:
                                     # Try fallback generic
                                     desc_el = await detail_page.query_selector('main') 
                                
                                description = await desc_el.inner_html() if desc_el else ""
                                
                                # Apply button usually on page
                                apply_url = job_url # Fallback
                                
                            except Exception as e:
                                logger.warning(f"[{self.site_key}] Failed to load detail {job_url}: {e}")
                                description = ""
                            finally:
                                await detail_page.close()
                                
                            job_data = {
                                'company': self.company_name,
                                'title': title.strip(),
                                'location': location.strip(),
                                'employment_type': 'Full-time',
                                'description': description.strip(),
                                'source_url': job_url,
                                'apply_url': job_url,
                                'posted_date': datetime.now(),
                                'is_active': True
                            }
                            jobs.append(job_data)
                            
                        except Exception as e:
                            logger.error(f"[{self.site_key}] Error parsing job card: {e}")
                    
                    # Pagination
                    next_btn = await page.query_selector('a.next:not(.disabled)')
                    if next_btn:
                        await next_btn.click()
                        await page.wait_for_load_state('networkidle')
                        page_count += 1
                        await asyncio.sleep(random.uniform(2, 4))
                    else:
                        logger.info(f"[{self.site_key}] Reached last page")
                        break
            
            except Exception as e:
                logger.error(f"[{self.site_key}] Global error: {e}")
                
        return jobs
