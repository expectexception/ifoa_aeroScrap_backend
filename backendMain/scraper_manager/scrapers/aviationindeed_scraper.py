"""
Aviation Indeed Scraper - CEIPAL-based job board
Handles iframe-embedded job listings from CEIPAL API
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import json
from urllib.parse import urlparse
from .base_scraper import BaseScraper


class AviationIndeedScraper(BaseScraper):
    """Scraper for Aviation Indeed (CEIPAL iframe-based)"""
    
    def __init__(self, config, db_manager=None):
        super().__init__(config, 'aviationindeed', db_manager=db_manager)
        self.site_config = config['sites']['aviationindeed']
        self.base_url = self.site_config['base_url']
        self.ceipal_url = self.site_config['ceipal_url']
        
    async def run(self):
        """Main execution method"""
        self.print_header()
        
        print(f"Fetching jobs from {self.site_config['name']}...")
        print(f"URL: {self.ceipal_url}\n")
        
        jobs = await self.fetch_jobs_from_iframe()
        
        if not jobs:
            print("❌ No jobs found")
            return []
        
        print(f"\n✓ Extracted {len(jobs)} jobs from listing")
        
        # Fetch detailed descriptions
        jobs_with_descriptions = await self.fetch_job_descriptions(jobs)
        
        # Save results
        await self.save_results(jobs_with_descriptions, self.site_config['name'])
        self.print_sample(jobs_with_descriptions)
        
        return jobs_with_descriptions
    
    async def fetch_jobs_from_iframe(self):
        """Fetch jobs from CEIPAL iframe"""
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)
            
            try:
                print("Loading page with CEIPAL iframe... or direct CEIPAL URL")
                await self.random_delay(1, 2)
                # Detect if ceipal_url already points to a CEIPAL jobsapi domain (direct access)
                parsed = urlparse(self.ceipal_url)
                if parsed.hostname and 'jobsapi.ceipal.com' in parsed.hostname:
                    # Handle direct CEIPAL API URL which sometimes returns JSON or HTML listing
                    print("Detected direct CEIPAL jobs API URL – parsing content directly")
                    # Use a dedicated helper to parse direct API/HTML responses
                    jobs = await self.fetch_jobs_from_ceipal_url()
                    return jobs
                await page.goto(self.ceipal_url, wait_until='load', timeout=25000)
                
                # Wait for iframe to load
                await self.random_delay(2, 3)
                await self.simulate_human_behavior(page)
                
                # Get the CEIPAL iframe
                iframe_element = await page.wait_for_selector('iframe[src*="ceipal"]', timeout=10000)
                await self.random_delay(1, 2)
                # If iframe src points directly to jobsapi.ceipal.com, fetch it directly
                try:
                    iframe_src = await iframe_element.get_attribute('src')
                except Exception:
                    iframe_src = None
                if iframe_src and 'jobsapi.ceipal.com' in iframe_src:
                    print(f"Detected jobsapi iframe src: {iframe_src} - fetching directly")
                    jobs = await self.fetch_jobs_from_ceipal_url(url=iframe_src)
                    return jobs
                iframe = await iframe_element.content_frame()
                
                if not iframe:
                    print("❌ Could not access iframe content")
                    return jobs
                
                print("✓ Accessed CEIPAL iframe")
                
                # Wait for job listings to load in iframe
                await self.random_delay(3, 5)
                
                # Try multiple selectors for CEIPAL job listings
                selectors = [
                    'table tbody tr',  # Common CEIPAL table format
                    '.job-item',
                    '.list-group-item',
                    '[class*="job"]',
                    'div[role="row"]',
                ]
                
                job_elements = []
                for selector in selectors:
                    try:
                        elements = await iframe.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            print(f"✓ Found {len(elements)} jobs using selector: {selector}")
                            job_elements = elements
                            break
                    except Exception as e:
                        print(f"  Selector {selector} failed: {e}")
                        continue
                
                if not job_elements:
                    print("❌ No job elements found with known selectors")
                    # Save page content for debugging
                    content = await iframe.content()
                    print(f"Iframe content length: {len(content)}")
                    return jobs
                
                # Extract job data
                for idx, element in enumerate(job_elements):
                    if self.max_jobs and len(jobs) >= self.max_jobs:
                        break
                    
                    try:
                        job_data = await self._extract_job_from_element(element, idx)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        print(f"Error extracting job {idx + 1}: {e}")
                
            except asyncio.TimeoutError:
                print("❌ Timeout loading page or iframe")
            except Exception as e:
                print(f"❌ Error fetching jobs: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return jobs

    async def fetch_jobs_from_ceipal_url(self, url=None):
        """Handle direct CEIPAL jobs endpoint pages (JSON or HTML)"""
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)
            try:
                target_url = url or self.ceipal_url
                resp = await page.goto(target_url, wait_until='load', timeout=25000)

                # If the response was JSON, parse it and extract job items
                if resp:
                    headers = resp.headers or {}
                    content_type = headers.get('content-type', '')
                    if 'application/json' in content_type or 'json' in content_type:
                        try:
                            text = await resp.text()
                            data = json.loads(text)
                            # Guess where jobs might be stored in the JSON
                            # Common keys: 'jobs', 'data', 'rows', 'joblist'
                            candidates = ['jobs', 'data', 'rows', 'joblist', 'results']
                            found = None
                            for key in candidates:
                                if isinstance(data, dict) and key in data and isinstance(data[key], list):
                                    found = data[key]
                                    break
                            if not found and isinstance(data, list):
                                found = data
                            if found:
                                for idx, item in enumerate(found):
                                    # Basic mapping: try to find title, location, url
                                    title = item.get('title') or item.get('jobTitle') or item.get('job_title') or item.get('positionTitle') or item.get('NAME')
                                    url = item.get('url') or item.get('apply_url') or item.get('applyurl') or item.get('link')
                                    location = item.get('location') or item.get('jobLocation') or item.get('job_location')
                                    job_id = item.get('id') or item.get('jobId') or item.get('job_id') or f"aviationindeed_{idx+1}_{datetime.now().strftime('%Y%m%d')}"
                                    job_data = {
                                        'job_id': job_id,
                                        'title': title or 'Unknown Position',
                                        'company': item.get('company') or self.site_config.get('name', 'Aviation Indeed'),
                                        'source': 'aviationindeed',
                                        'url': url or self.ceipal_url,
                                        'apply_url': url or self.ceipal_url,
                                        'location': location or 'Location not specified',
                                        'job_type': item.get('jobType', ''),
                                        'department': item.get('department', ''),
                                        'posted_date': item.get('posted_at') or item.get('postedDate') or '',
                                        'closing_date': item.get('closingDate', ''),
                                        'timestamp': datetime.now().isoformat(),
                                        'description': item.get('description', ''),
                                        'requirements': item.get('requirements', ''),
                                        'qualifications': item.get('qualifications', ''),
                                    }
                                    jobs.append(job_data)
                                return jobs
                        except Exception as e:
                            print(f"❌ Error parsing JSON response from CEIPAL API: {e}")

                # If not JSON, fall back to HTML parsing
                await self.random_delay(1, 2)
                await self.simulate_human_behavior(page)

                # Try multiple selectors for CEIPAL job listings in main page
                selectors = [
                    'table tbody tr',  # Common CEIPAL table format
                    '.job-item',
                    '.list-group-item',
                    '[class*="job"]',
                    'div[role="row"]',
                    'article',
                    '.job-listing',
                ]

                job_elements = []
                for selector in selectors:
                    try:
                        elements = await page.query_selector_all(selector)
                        if elements and len(elements) > 0:
                            print(f"✓ Found {len(elements)} jobs using selector: {selector} on CEIPAL page")
                            job_elements = elements
                            break
                    except Exception as e:
                        print(f"  Selector {selector} failed on CEIPAL page: {e}")
                        continue

                if not job_elements:
                    print("❌ No job elements found on CEIPAL page with known selectors")
                    content = await page.content()
                    print(f"CEIPAL page content length: {len(content)}")
                    return jobs

                for idx, element in enumerate(job_elements):
                    if self.max_jobs and len(jobs) >= self.max_jobs:
                        break
                    try:
                        job_data = await self._extract_job_from_element(element, idx)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        print(f"Error parsing CEIPAL job element {idx + 1}: {e}")

            except Exception as e:
                print(f"❌ Error fetching CEIPAL page directly: {e}")
            finally:
                await context.close()
                await browser.close()

        return jobs
    
    async def _extract_job_from_element(self, element, idx):
        """Extract job data from a single element"""
        try:
            # Get all text content
            text = await element.inner_text()
            
            # Try to find links within the element
            links = await element.query_selector_all('a')
            job_url = None
            job_id = None
            
            if links:
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        # Handle relative URLs
                        if href.startswith('/'):
                            job_url = f"{self.base_url}{href}"
                        elif href.startswith('http'):
                            job_url = href
                        else:
                            job_url = f"{self.base_url}/{href}"
                        
                        # Extract job ID from URL
                        if 'job' in href:
                            parts = href.split('/')
                            for part in parts:
                                if part.isdigit():
                                    job_id = part
                                    break
                        break
            
            # Parse text content (CEIPAL often has: Title | Location | Type | Date)
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            title = lines[0] if len(lines) > 0 else 'Unknown Position'
            location = lines[1] if len(lines) > 1 else 'Location not specified'
            
            # Extract posted date
            posted_date = ''
            date_elem = await element.query_selector('[class*="date"], [class*="posted"], time, [class*="Date"]')
            if date_elem:
                date_text = (await date_elem.inner_text()).strip()
                parsed_date = self.parse_posted_date(date_text)
                posted_date = parsed_date if parsed_date else date_text
            
            # Generate job_id if not found
            if not job_id:
                job_id = f"aviationindeed_{idx + 1}_{datetime.now().strftime('%Y%m%d')}"
            
            job_data = {
                'job_id': job_id,
                'title': title,
                'company': 'Aviation Indeed',
                'source': 'aviationindeed',
                'url': job_url or self.ceipal_url,
                'apply_url': job_url or self.ceipal_url,
                'location': location,
                'job_type': '',
                'department': '',
                'posted_date': posted_date,
                'closing_date': '',
                'timestamp': datetime.now().isoformat(),
                'description': '',
                'requirements': '',
                'qualifications': '',
            }
            
            return job_data
            
        except Exception as e:
            print(f"Error parsing job element: {e}")
            return None
    
    async def fetch_job_descriptions(self, jobs):
        """Fetch detailed descriptions for each job"""
        print(f"\nFetching detailed descriptions for {len(jobs)} jobs...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for i in range(0, len(jobs), self.batch_size):
                batch = jobs[i:i + self.batch_size]
                tasks = []
                
                for job in batch:
                    if job.get('url') and job['url'] != self.ceipal_url:
                        tasks.append(self._extract_description(browser, job))
                
                if tasks:
                    await asyncio.gather(*tasks)
                
                print(f"  Processed {min(i + self.batch_size, len(jobs))}/{len(jobs)} jobs")
            
            await browser.close()
        
        # Count jobs with descriptions
        with_desc = sum(1 for job in jobs if job.get('description'))
        print(f"✓ Successfully extracted {with_desc}/{len(jobs)} descriptions")
        
        return jobs
    
    async def _extract_description(self, browser, job):
        """Extract detailed description from job page"""
        try:
            page, context = await self.setup_stealth_page(browser)
            await self.random_delay(1, 2)
            await page.goto(job['url'], wait_until='domcontentloaded', timeout=15000)
            await self.random_delay(2, 3)
            await self.simulate_human_behavior(page)
            
            # Check if it's an iframe page or direct job page
            iframe_element = await page.query_selector('iframe[src*="ceipal"]')
            if iframe_element:
                iframe = await iframe_element.content_frame()
                if iframe:
                    page = iframe
            
            # Try multiple selectors for job details
            selectors = {
                'description': [
                    '.job-description',
                    '[class*="description"]',
                    '[class*="detail"]',
                    '.content',
                    'article',
                ],
                'requirements': [
                    '.requirements',
                    '[class*="requirement"]',
                    '[class*="qualification"]',
                ],
            }
            
            # Extract description
            for selector in selectors['description']:
                element = await page.query_selector(selector)
                if element:
                    job['description'] = (await element.inner_text()).strip()
                    break
            
            # Extract requirements
            for selector in selectors['requirements']:
                element = await page.query_selector(selector)
                if element:
                    job['requirements'] = (await element.inner_text()).strip()
                    break
            
            # If no description found, get main content
            if not job['description']:
                body = await page.query_selector('body')
                if body:
                    text = await body.inner_text()
                    # Take meaningful content (skip headers/footers)
                    lines = [l.strip() for l in text.split('\n') if l.strip()]
                    if len(lines) > 5:
                        job['description'] = '\n'.join(lines[:20])
            
            await page.close()
            await context.close()
            
        except Exception as e:
            print(f"  Error fetching description for {job['job_id']}: {e}")
