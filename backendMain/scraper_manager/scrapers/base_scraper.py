"""
Base Scraper Class
Common functionality for all aviation job scrapers
"""

import asyncio
import json
import random
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta
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
            if not jobs:
                # No jobs to save is expected when all were duplicates
                logger.info(f"[{self.site_key}] No new jobs to save (all duplicates or filtered out)")
                print(f"\nℹ️  No new jobs to save (all duplicates or filtered out)")
            elif not (self.use_db and self.db_manager):
                # Database manager or DB use is disabled
                logger.warning(f"[{self.site_key}] Database manager not available (skipping save)")
                print(f"\n⚠️  Database manager not available (skipping save)")
            else:
                # Fallback - general warning
                logger.warning(f"[{self.site_key}] No jobs saved; check DB or job list")
                print(f"\n⚠️  No jobs saved; check DB or job list")
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
    
    def parse_posted_date(self, date_text: str) -> Optional[str]:
        """
        Parse various date formats and convert 'time ago' formats to ISO date strings.
        
        Handles formats like:
        - '3 days ago', '1 hour ago', '2 weeks ago', '1 month ago'
        - 'Posted 5 days ago', 'Updated 3 hours ago'
        - '30+ days ago', '30+ ago'
        - Actual dates: '2024-12-01', '01 Dec 2024', 'December 1, 2024'
        - Relative: 'Today', 'Yesterday'
        
        Returns ISO date string (YYYY-MM-DD) or None if parsing fails
        """
        if not date_text or not isinstance(date_text, str):
            return None
        
        # Normalize ordinals like '2nd', '1st', '3rd' -> '2', '1', '3'
        text_raw = date_text.strip()
        text_raw = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', text_raw, flags=re.IGNORECASE)
        text = text_raw.lower()
        now = datetime.utcnow()
        
        # Already ISO format
        if re.match(r'^\d{4}-\d{2}-\d{2}$', text):
            return text
        
        # Handle 'Today'
        if 'today' in text or 'just now' in text:
            return now.date().isoformat()
        
        # Handle 'Yesterday'
        if 'yesterday' in text:
            return (now - timedelta(days=1)).date().isoformat()
        
        # Hours ago
        match = re.search(r'(\d+)\s*(?:hour|hr|h)s?(?:\s+ago)?', text)
        if match:
            try:
                hours = int(match.group(1))
                return (now - timedelta(hours=hours)).date().isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Minutes ago (treat as today)
        if re.search(r'(\d+)\s*(?:minute|min|m)s?(?:\s+ago)?', text):
            return now.date().isoformat()
        
        # Days ago
        match = re.search(r'(\d+)\s*(?:day|d)s?(?:\s+ago)?', text)
        if match:
            try:
                days = int(match.group(1))
                return (now - timedelta(days=days)).date().isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Weeks ago
        match = re.search(r'(\d+)\s*(?:week|wk|w)s?(?:\s+ago)?', text)
        if match:
            try:
                weeks = int(match.group(1))
                return (now - timedelta(weeks=weeks)).date().isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Months ago (approximate as 30 days)
        match = re.search(r'(\d+)\s*(?:month|mon|mo)s?(?:\s+ago)?', text)
        if match:
            try:
                months = int(match.group(1))
                return (now - timedelta(days=months * 30)).date().isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Years ago (approximate as 365 days)
        match = re.search(r'(\d+)\s*(?:year|yr|y)s?(?:\s+ago)?', text)
        if match:
            try:
                years = int(match.group(1))
                return (now - timedelta(days=years * 365)).date().isoformat()
            except (ValueError, AttributeError):
                pass
        
        # Handle '30+' or '30+ days' format
        if re.search(r'30\+|more\s+than\s+30', text):
            return (now - timedelta(days=30)).date().isoformat()
        
        # Try common date formats (be permissive: strip commas and normalize separators)
        date_patterns = [
            # numeric dates: DD/MM/YYYY or DD-MM-YYYY
            (r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', ['%d-%m-%Y', '%d-%m-%y']),
            # numeric ISO: YYYY-MM-DD or YYYY/MM/DD
            (r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})', ['%Y-%m-%d']),
            # DD Mon YYYY (e.g., 01 Dec 2024) OR with ordinal (e.g., 1st Dec 2024)
            (r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{4})', ['%d %b %Y', '%d %B %Y']),
            # DD Mon YY (e.g., 01 Dec 25) - two-digit year
            (r'(\d{1,2})\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+(\d{2})', ['%d %b %y', '%d %B %y']),
            # Mon DD, YYYY or Mon DD YYYY (e.g., Dec 2, 2025)
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}', ['%b %d %Y', '%B %d %Y']),
            # Mon DD, YY (e.g., Dec 2, 25) - two-digit year
            (r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2}', ['%b %d %y', '%B %d %y']),
            # Full month name before day (e.g., December 1, 2024)
            (r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{1,2},?\s+\d{4}', ['%B %d %Y', '%b %d %Y']),
        ]

        for pattern, date_formats in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            try:
                date_str_raw = match.group(0)
                # Normalize: remove commas and slashes -> dashes for numeric formats
                date_str = date_str_raw.replace(',', ' ').strip()
                date_str = re.sub(r'\s+', ' ', date_str)
                # Replace common separators
                date_str_norm = date_str.replace('/', '-').strip()

                for df in date_formats:
                    try:
                        parsed_date_dt = datetime.strptime(date_str_norm, df).date()
                        # Validate parsed date is within reasonable range (not ancient or far future)
                        if parsed_date_dt < (now.date() - timedelta(days=3650)):
                            # Older than 10 years - treat as invalid
                            continue
                        if parsed_date_dt > (now.date() + timedelta(days=30)):
                            # More than 30 days in future - treat as invalid
                            continue
                        return parsed_date_dt.isoformat()
                    except ValueError:
                        # try without normalizing separators (some formats use spaces)
                        try:
                            parsed_date_dt = datetime.strptime(date_str, df).date()
                            if parsed_date_dt < (now.date() - timedelta(days=3650)):
                                continue
                            if parsed_date_dt > (now.date() + timedelta(days=30)):
                                continue
                            return parsed_date_dt.isoformat()
                        except ValueError:
                            continue
            except (AttributeError, IndexError):
                continue
        
        # If nothing matched, return None (don't return original text)
        logger.debug(f"[{self.site_key}] Could not parse date: {date_text}")
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
                scroll_amount = random.randint(200, 800)
                await page.evaluate(f'window.scrollBy(0, {scroll_amount})')
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                # Scroll back up a bit
                scroll_back = random.randint(100, 400)
                await page.evaluate(f'window.scrollBy(0, -{scroll_back})')
                await asyncio.sleep(random.uniform(0.3, 0.8))
        except Exception:
            pass  # Ignore errors in behavior simulation

    async def extract_posted_date_from_page(self, page):
        """Fallback: try to detect a posted/published date by searching the page body and meta tags"""
        try:
            # Try meta tags first
            metas = await page.query_selector_all('meta')
            for m in metas:
                name = await m.get_attribute('name') or ''
                prop = await m.get_attribute('property') or ''
                content = await m.get_attribute('content') or ''
                if any(k in (name + prop).lower() for k in ('date', 'publish', 'published', 'modified', 'updated', 'posted')):
                    parsed = self.parse_posted_date(content)
                    if parsed:
                        return parsed

            # JSON-LD
            scripts = await page.query_selector_all('script[type="application/ld+json"]')
            for s in scripts:
                try:
                    txt = (await s.inner_text())
                    import json as _json
                    data = _json.loads(txt)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict):
                            for key in ('datePublished', 'datePosted', 'publishDate', 'published'):
                                if key in item:
                                    parsed = self.parse_posted_date(item[key])
                                    if parsed:
                                        return parsed
                except Exception:
                    continue

            # Look in body text for relative date strings like 'Posted 3 days ago' or 'Published on Dec 2, 2025'
            body = await page.inner_text('body')
            # Basic patterns
            patterns = [r'posted\s*[:\-]?\s*([\w\s,\d]+ago)', r'published\s*[:\-]?\s*([\w\s,\d]+ago)', r'posted on\s*([\w\s,\d,]+)', r'published on\s*([\w\s,\d,]+)']
            for pat in patterns:
                m = re.search(pat, body, re.IGNORECASE)
                if m:
                    cand = m.group(1).strip()
                    parsed = self.parse_posted_date(cand)
                    if parsed:
                        return parsed
            # No parsed date found
        except Exception:
            pass
        return None

    async def extract_description_from_page(self, page, min_length=100):
        """Fallback: return the largest candidate description on the page"""
        try:
            # Common selectors
            selectors = ['#jobDescription', 'div[id*="job"]', 'div[class*="job"]', '.jobDescription', '.job-description', '.description', 'article', 'main', '.content']
            for sel in selectors:
                try:
                    el = await page.query_selector(sel)
                    if el:
                        txt = await el.inner_text()
                        if txt and len(txt.strip()) >= min_length:
                            return txt.strip()
                except Exception:
                    continue

            # If none found, find the largest text container on page
            # Evaluate all divs and pick the one with the longest text
            longest = ''
            els = await page.query_selector_all('div, section, article')
            for el in els:
                try:
                    txt = await el.inner_text()
                    if txt and len(txt) > len(longest):
                        longest = txt
                except Exception:
                    continue
            if longest and len(longest.strip()) >= min_length:
                return longest.strip()
        except Exception:
            pass
        return ''
    
    async def setup_stealth_page(self, browser, viewport_width: Optional[int] = None, viewport_height: Optional[int] = None):
        """Create a browser page with anti-detection measures"""
        # Random viewport size
        if viewport_width is None:
            viewport_width = random.randint(1366, 1920)
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
