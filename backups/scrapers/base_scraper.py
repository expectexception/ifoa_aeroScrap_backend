"""
Base Scraper Class
Common functionality for all aviation job scrapers
"""

import asyncio
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import sync_to_async

# Import filter manager
try:
    from filter_manager import JobFilterManager
except ImportError:
    JobFilterManager = None

# Setup logging
logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers with common functionality"""
    
    def __init__(self, config: dict, site_key: str, db_manager=None):
        """
        Initialize base scraper
        
        Args:
            config: Configuration dictionary with scraper settings
            site_key: Site identifier (e.g., 'signature', 'flygosh')
            db_manager: Optional database manager for URL tracking
        """
        self.site_key = site_key
        self.config = config
        self.site_config = config.get('sites', {}).get(site_key, {})
        self.db_manager = db_manager
        self.scrape_start_time = None
        self.use_db = db_manager is not None
        
        # Limits
        self.max_jobs = config.get('scrapers', {}).get(site_key, {}).get('max_jobs')
        self.max_pages = config.get('scrapers', {}).get(site_key, {}).get('max_pages')
        self.batch_size = config.get('scraper_settings', {}).get('batch_size', 5)
        
        # NO MORE FILE OUTPUT - database only
        logger.info(f"[{site_key}] Initializing scraper (Database-only mode)")
        
        # Site info
        self.company_name = self.site_config.get('name', 'Unknown')
        self.base_url = self.site_config.get('base_url', '')
        
        # Anti-Detection Settings
        scraper_settings = config.get('scraper_settings', {})
        self.stealth_mode = scraper_settings.get('stealth_mode', True)
        self.request_delay_min = scraper_settings.get('request_delay_min', 2)
        self.request_delay_max = scraper_settings.get('request_delay_max', 5)
        self.page_load_delay = scraper_settings.get('page_load_delay', 3)
        self.random_scroll = scraper_settings.get('random_scroll', True)
        self.random_mouse = scraper_settings.get('random_mouse', True)
        self.user_agents = scraper_settings.get('user_agents', [])
        self.proxy_list = scraper_settings.get('proxy_list', [])
        self.rotate_proxy = scraper_settings.get('rotate_proxy', False)
        
        # Filter settings
        self.use_filter = scraper_settings.get('use_filter', False)
        self.filter_manager = None
        if self.use_filter and JobFilterManager:
            filter_file = scraper_settings.get('filter_file', 'filter_title.json')
            try:
                self.filter_manager = JobFilterManager(filter_file)
                logger.info(f"[{site_key}] Loaded filter with {len(self.filter_manager.all_keywords)} keywords")
            except Exception as e:
                logger.warning(f"[{site_key}] Failed to load filter: {e}")
        
    async def is_url_already_scraped(self, url: str) -> bool:
        """Check if URL was already scraped (using database if available)"""
        if self.use_db and self.db_manager:
            is_scraped = await self.db_manager.is_url_scraped(url)
            if is_scraped:
                logger.debug(f"[{self.site_key}] URL already scraped: {url}")
            return is_scraped
        return False
    
    async def filter_new_jobs(self, jobs: List[Dict]) -> tuple[List[Dict], int]:
        """
        Filter out already scraped jobs
        Returns: (new_jobs, duplicate_count)
        """
        if not self.use_db or not self.db_manager:
            logger.warning(f"[{self.site_key}] Database not available, cannot filter duplicates")
            return jobs, 0
        
        logger.info(f"[{self.site_key}] Filtering {len(jobs)} jobs against database...")
        scraped_urls = await self.db_manager.get_scraped_urls(source=self.site_key)
        new_jobs = [job for job in jobs if job.get('url') not in scraped_urls]
        duplicate_count = len(jobs) - len(new_jobs)
        
        logger.info(f"[{self.site_key}] Found {len(new_jobs)} new jobs, {duplicate_count} duplicates")
        return new_jobs, duplicate_count
    
    def apply_title_filter(self, jobs: List[Dict]) -> tuple[List[Dict], List[Dict], Dict]:
        """
        Filter jobs by title keywords
        Returns: (matched_jobs, rejected_jobs, stats)
        """
        if not self.use_filter or not self.filter_manager:
            # No filtering - return all jobs as matched
            return jobs, [], {'total': len(jobs), 'matched': len(jobs), 'rejected': 0, 'by_category': {}}
        
        return self.filter_manager.filter_jobs(jobs)
    
    async def save_results(self, jobs: List[Dict], filename: Optional[str] = None):
        """Save results to database only (no file generation)"""
        
        # Calculate duration
        duration = 0
        if self.scrape_start_time:
            duration = time.time() - self.scrape_start_time
        
        logger.info(f"[{self.site_key}] Saving {len(jobs)} jobs to database...")
        
        # Save to database if enabled
        db_stats = None
        if self.use_db and self.db_manager and jobs:
            try:
                # Wrap the synchronous add_jobs_batch call with sync_to_async
                add_jobs_async = sync_to_async(self.db_manager.add_jobs_batch, thread_sensitive=True)
                db_stats = await add_jobs_async(jobs, self.site_key)
                await self.db_manager.log_scrape_session(self.site_key, db_stats, duration)
                
                logger.info(f"[{self.site_key}] Database updated: "
                          f"new={db_stats['new']}, updated={db_stats['updated']}, "
                          f"duplicates={db_stats['duplicate']}, errors={db_stats['errors']}")
                
                print(f"\n✅ Database updated:")
                print(f"    - New jobs: {db_stats['new']}")
                print(f"    - Updated jobs: {db_stats['updated']}")
                print(f"    - Duplicates skipped: {db_stats['duplicate']}")
                if db_stats['errors'] > 0:
                    print(f"    - Errors: {db_stats['errors']}")
            except Exception as e:
                logger.error(f"[{self.site_key}] Database save failed: {e}", exc_info=True)
                print(f"\n❌ Database save failed: {e}")
                return None
        else:
            logger.warning(f"[{self.site_key}] Database not available or no jobs to save")
            print(f"\n⚠️  Database not available or no jobs to save")
            return None
        
        # Print stats
        jobs_with_desc = sum(1 for job in jobs if job.get('description'))
        logger.info(f"[{self.site_key}] Extraction stats: total={len(jobs)}, "
                   f"with_desc={jobs_with_desc}, duration={duration:.1f}s")
        
        print(f"\n📊 Extraction Stats:")
        print(f"  Total jobs extracted: {len(jobs)}")
        print(f"  With descriptions: {jobs_with_desc}")
        if jobs:
            print(f"  Coverage: {jobs_with_desc/len(jobs)*100:.1f}%")
        if duration > 0:
            print(f"  Duration: {duration:.1f}s")
        
        return db_stats
    
    def print_header(self):
        """Print scraper header"""
        self.scrape_start_time = time.time()
        
        logger.info(f"[{self.site_key}] Starting scraper: {self.company_name}")
        logger.info(f"[{self.site_key}] Database tracking: {'ENABLED' if self.use_db else 'DISABLED'}")
        logger.info(f"[{self.site_key}] Title filtering: {'ENABLED' if self.use_filter else 'DISABLED'}")
        
        print("=" * 60)
        print(f"{self.company_name} Job Scraper")
        print("=" * 60)
        
        if self.use_db:
            print("📊 Database tracking: ENABLED")
        else:
            print("📊 Database tracking: DISABLED")
        
        if self.use_filter:
            print("🔍 Title filtering: ENABLED")
            if self.filter_manager:
                print(f"   Loaded {len(self.filter_manager.all_keywords)} keywords in {len(self.filter_manager.filters)} categories")
        else:
            print("🔍 Title filtering: DISABLED")
        
        if self.max_jobs:
            print(f"Max jobs limit: {self.max_jobs}")
            logger.info(f"[{self.site_key}] Max jobs limit: {self.max_jobs}")
        if self.max_pages:
            print(f"Max pages limit: {self.max_pages}")
            logger.info(f"[{self.site_key}] Max pages limit: {self.max_pages}")
        print()
    
    def print_sample(self, jobs: List[Dict]):
        """Print sample job with category information"""
        if jobs and jobs[0].get('description'):
            job = jobs[0]
            print(f"\n{'='*70}")
            print("📄 SAMPLE JOB")
            print(f"{'='*70}")
            print(f"  ID: {job.get('job_id', 'N/A')}")
            print(f"  Title: {job['title']}")
            print(f"  Company: {job.get('company', 'N/A')}")
            print(f"  Location: {job.get('location', 'N/A')}")
            
            # Show filter information if available
            if job.get('filter_match'):
                print(f"\n  🎯 Filter Match: YES")
                print(f"  📊 Score: {job.get('filter_score', 0.0)}")
                print(f"  🏷️  Primary Category: {job.get('primary_category', 'N/A')}")
                if job.get('matched_categories'):
                    print(f"  📁 All Categories: {', '.join(job['matched_categories'][:3])}")
                if job.get('matched_keywords'):
                    keywords = job['matched_keywords'][:5]
                    print(f"  🔑 Keywords: {', '.join(keywords)}")
            
            print(f"\n  Description Preview: {job['description'][:150]}...")
            print(f"{'='*70}\n")
    
    def get_random_user_agent(self) -> str:
        """Get random user agent for anti-detection"""
        if self.user_agents:
            return random.choice(self.user_agents)
        # Fallback user agent
        return 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    def get_random_proxy(self) -> Optional[Dict]:
        """Get random proxy for anti-detection"""
        if self.rotate_proxy and self.proxy_list:
            proxy_url = random.choice(self.proxy_list)
            return {'server': proxy_url}
        return None
    
    async def random_delay(self, min_seconds: Optional[float] = None, max_seconds: Optional[float] = None):
        """Add random delay to mimic human behavior"""
        min_delay = min_seconds if min_seconds is not None else self.request_delay_min
        max_delay = max_seconds if max_seconds is not None else self.request_delay_max
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)
    
    async def simulate_human_behavior(self, page):
        """Simulate human-like behavior on page"""
        if not self.stealth_mode:
            return
        
        try:
            # Random mouse movements
            if self.random_mouse:
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, 800)
                    y = random.randint(100, 600)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Random scrolling
            if self.random_scroll:
                scroll_amount = random.randint(200, 800)
                await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Scroll back up a bit
                scroll_back = random.randint(100, 400)
                await page.evaluate(f'window.scrollBy(0, -{scroll_back})')
                await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass  # Ignore errors in behavior simulation
    
    async def setup_stealth_page(self, browser, viewport_width: Optional[int] = None, viewport_height: Optional[int] = None):
        """Create a browser page with anti-detection measures"""
        # Random viewport size
        if viewport_width is None:
            viewport_width = random.randint(1366, 1920)
        if viewport_height is None:
            viewport_height = random.randint(768, 1080)
        
        # Context options with anti-detection
        context_options = {
            'viewport': {'width': viewport_width, 'height': viewport_height},
            'user_agent': self.get_random_user_agent(),
            'locale': 'en-US',
            'timezone_id': 'America/New_York',
            'permissions': ['geolocation', 'notifications'],
            'color_scheme': 'light',
        }
        
        # Add proxy if configured
        proxy = self.get_random_proxy()
        if proxy:
            context_options['proxy'] = proxy
        
        # Create context
        context = await browser.new_context(**context_options)
        
        # Create page
        page = await context.new_page()
        
        # Anti-detection scripts
        if self.stealth_mode:
            await page.add_init_script("""
                // Remove webdriver flag
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
                
                // Mock chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Override permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
        
        return page, context
    
    async def run(self):
        """Main execution method - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement run() method")
