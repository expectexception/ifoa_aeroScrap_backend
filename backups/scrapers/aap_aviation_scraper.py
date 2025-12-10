"""
AAP Aviation Scraper - Job board scraper
Extracts aviation job listings from jobs.aapaviation.com
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper
from .job_schema import get_job_dict


class AAPAviationScraper(BaseScraper):
    """Scraper for AAP Aviation jobs"""
    
    def __init__(self, config, db_manager=None):
        super().__init__(config, 'aap', db_manager=db_manager)
        self.site_config = config['sites']['aap']
        self.base_url = self.site_config['base_url']
        self.jobs_url = self.site_config['jobs_url']
        
    async def run(self):
        """Main execution method"""
        self.print_header()
        
        print(f"Fetching jobs from {self.site_config['name']}...")
        print(f"URL: {self.jobs_url}\n")
        
        jobs_raw = await self.fetch_jobs_from_listing()
        jobs = [get_job_dict(**job) for job in jobs_raw]
        
        if not jobs:
            print("❌ No jobs found")
            return []
        
        print(f"\n✓ Extracted {len(jobs)} jobs from listing")
        
        # Apply title filtering BEFORE fetching descriptions
        if self.use_filter and self.filter_manager:
            print(f"\n🔍 Applying title filter...")
            matched_jobs, rejected_jobs, filter_stats = self.apply_title_filter(jobs)
            
            self.filter_manager.print_filter_stats(filter_stats)
            
            if not matched_jobs:
                print("❌ No jobs matched the filter criteria")
                return []
            
            print(f"✓ {len(matched_jobs)} jobs matched filter (will fetch descriptions)")
            print(f"✗ {len(rejected_jobs)} jobs rejected (not relevant)")
            jobs = matched_jobs
        
        # Filter duplicates
        jobs, duplicate_count = await self.filter_new_jobs(jobs)
        if duplicate_count > 0:
            print(f"\n🔄 Filtered out {duplicate_count} duplicate jobs")
        
        # Fetch detailed descriptions
        jobs_with_descriptions = await self.fetch_job_descriptions(jobs)
        
        # Save results
        await self.save_results(jobs_with_descriptions)
        self.print_sample(jobs_with_descriptions)
        
        return jobs_with_descriptions
    
    async def fetch_jobs_from_listing(self):
        """Fetch jobs from listing page"""
        jobs = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)
            
            try:
                print("Loading jobs page...")
                await self.random_delay(1, 2)
                await page.goto(self.jobs_url, wait_until='domcontentloaded', timeout=25000)
                
                # Wait for dynamic content to load
                await self.random_delay(3, 5)
                await self.simulate_human_behavior(page)
                
                print("✓ Page loaded, extracting jobs...")
                
                # Try multiple selectors for job cards
                selectors = [
                    'article',
                    '.job-card',
                    '.job-item',
                    '[class*="job-listing"]',
                    '[class*="JobCard"]',
                    'div[data-job-id]',
                    '.listing-item',
                ]
                
                job_elements = []
                used_selector = None
                
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 2:  # At least 3 jobs
                        print(f"✓ Found {len(elements)} jobs using selector: {selector}")
                        job_elements = elements
                        used_selector = selector
                        break
                
                if not job_elements:
                    print("❌ No job elements found with known selectors")
                    # Try to get any links with /job in them
                    job_links = await page.query_selector_all('a[href*="/job"]')
                    if job_links:
                        print(f"✓ Found {len(job_links)} job links as fallback")
                        for link in job_links[:self.max_jobs] if self.max_jobs else job_links:
                            try:
                                href = await link.get_attribute('href')
                                text = await link.inner_text()
                                if href and text:
                                    job_data = self._create_basic_job(href, text.strip(), len(jobs))
                                    jobs.append(job_data)
                            except Exception as e:
                                continue
                    await browser.close()
                    return jobs
                
                # Extract job data from elements
                for idx, element in enumerate(job_elements):
                    if self.max_jobs and len(jobs) >= self.max_jobs:
                        break
                    
                    try:
                        job_data = await self._extract_job_from_card(element, idx)
                        if job_data:
                            jobs.append(job_data)
                    except Exception as e:
                        print(f"Error extracting job {idx + 1}: {e}")
                
            except asyncio.TimeoutError:
                print("❌ Timeout loading page")
            except Exception as e:
                print(f"❌ Error fetching jobs: {e}")
            finally:
                await context.close()
                await browser.close()
        
        return jobs
    
    async def _extract_job_from_card(self, element, idx):
        """Extract job data from a job card element"""
        try:
            # Get all text content
            text = await element.inner_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # Try to find links within the element
            links = await element.query_selector_all('a')
            job_url = None
            
            if links:
                for link in links:
                    href = await link.get_attribute('href')
                    if href:
                        # Build full URL
                        if href.startswith('/'):
                            job_url = f"{self.base_url}{href}"
                        elif href.startswith('http'):
                            job_url = href
                        else:
                            job_url = f"{self.base_url}/{href}"
                        break
            
            # Extract title (usually first line or in h2/h3)
            title = 'Unknown Position'
            title_elem = await element.query_selector('h1, h2, h3, h4, .title, [class*="title"]')
            if title_elem:
                title = (await title_elem.inner_text()).strip()
            elif lines:
                title = lines[0]
            
            # Extract location
            location = ''
            location_elem = await element.query_selector('.location, [class*="location"], [data-location]')
            if location_elem:
                location = (await location_elem.inner_text()).strip()
            elif len(lines) > 1:
                # Location often on second line
                for line in lines[1:3]:
                    if any(word in line.lower() for word in ['airport', 'city', 'state', 'country', 'remote']):
                        location = line
                        break
            
            # Extract job type
            job_type = ''
            type_elem = await element.query_selector('.job-type, [class*="type"]')
            if type_elem:
                job_type = (await type_elem.inner_text()).strip()
            
            # Generate job ID
            job_id = f"aap_{idx + 1}_{datetime.now().strftime('%Y%m%d')}"
            if job_url and '/job/' in job_url:
                # Try to extract ID from URL
                parts = job_url.split('/')
                for part in parts:
                    if part.isdigit() or (len(part) > 5 and any(c.isdigit() for c in part)):
                        job_id = f"aap_{part}"
                        break
            
            job_data = {
                'job_id': job_id,
                'title': title,
                'company': 'AAP Aviation',
                'source': 'aap',
                'url': job_url or self.jobs_url,
                'apply_url': job_url or self.jobs_url,
                'location': location,
                'job_type': job_type,
                'department': '',
                'posted_date': '',
                'closing_date': '',
                'timestamp': datetime.now().isoformat(),
                'description': '',
                'requirements': '',
                'qualifications': '',
            }
            
            return job_data
            
        except Exception as e:
            print(f"Error parsing job card: {e}")
            return None
    
    def _create_basic_job(self, url, title, idx):
        """Create basic job data from URL and title"""
        if url.startswith('/'):
            url = f"{self.base_url}{url}"
        
        job_id = f"aap_{idx + 1}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            'job_id': job_id,
            'title': title,
            'company': 'AAP Aviation',
            'source': 'aap',
            'url': url,
            'apply_url': url,
            'location': '',
            'job_type': '',
            'department': '',
            'posted_date': '',
            'closing_date': '',
            'timestamp': datetime.now().isoformat(),
            'description': '',
            'requirements': '',
            'qualifications': '',
        }
    
    async def fetch_job_descriptions(self, jobs):
        """Fetch detailed descriptions for each job"""
        print(f"\nFetching detailed descriptions for {len(jobs)} jobs...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for i in range(0, len(jobs), self.batch_size):
                batch = jobs[i:i + self.batch_size]
                tasks = []
                
                for job in batch:
                    if job.get('url') and job['url'] != self.jobs_url:
                        tasks.append(self._extract_description(browser, job))
                
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
                
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
            
            # Set longer timeout and wait for full load
            await self.random_delay(1, 2)
            await page.goto(job['url'], wait_until='load', timeout=30000)
            
            # Wait longer for dynamic content
            await self.random_delay(4, 6)
            await self.simulate_human_behavior(page)
            
            # Get page title for better job title
            page_title = await page.title()
            if page_title and len(page_title) > len(job['title']):
                job['title'] = page_title.strip()
            
            # Extract all headings for better structure
            headings = await page.query_selector_all('h1, h2, h3, h4')
            heading_texts = []
            for h in headings:
                text = await h.inner_text()
                if text.strip():
                    heading_texts.append(text.strip())
            
            # Extract all paragraphs for description
            paragraphs = await page.query_selector_all('p')
            paragraph_texts = []
            for p in paragraphs:
                text = await p.inner_text()
                if text.strip() and len(text.strip()) > 20:  # Skip short/empty paragraphs
                    paragraph_texts.append(text.strip())
            
            # Extract lists (requirements often in lists)
            lists = await page.query_selector_all('ul, ol')
            list_texts = []
            for lst in lists:
                items = await lst.query_selector_all('li')
                if items:
                    list_items = []
                    for item in items:
                        text = await item.inner_text()
                        if text.strip():
                            list_items.append(f"• {text.strip()}")
                    if list_items:
                        list_texts.append('\n'.join(list_items))
            
            # Build comprehensive description
            description_parts = []
            
            # Add headings context
            if heading_texts:
                description_parts.append("=== Job Overview ===")
                description_parts.extend(heading_texts[:3])
                description_parts.append("")
            
            # Add paragraphs (main content)
            if paragraph_texts:
                description_parts.append("=== Description ===")
                description_parts.extend(paragraph_texts)
                description_parts.append("")
            
            # Add lists (requirements/qualifications)
            if list_texts:
                description_parts.append("=== Requirements & Details ===")
                description_parts.extend(list_texts)
            
            # Combine all parts
            if description_parts:
                job['description'] = '\n'.join(description_parts)
            
            # If still no description, try main content area
            if not job['description'] or len(job['description']) < 100:
                main_selectors = ['main', 'article', '.content', '.container']
                for selector in main_selectors:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if len(text) > 200:
                            job['description'] = text.strip()
                            break
            
            # Extract location from page if not already set
            if not job['location']:
                location_selectors = [
                    '[class*="location"]', 
                    '[class*="Location"]',
                    'span:has-text("Copenhagen")',
                    'span:has-text("Oslo")',
                    'span:has-text("Stockholm")',
                ]
                for selector in location_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            text = await elem.inner_text()
                            if text.strip():
                                job['location'] = text.strip()
                                break
                    except:
                        continue
            
            # Extract job type
            if not job['job_type']:
                type_keywords = ['Permanent', 'Contract', 'Temporary', 'Full-time', 'Part-time', 'Hourly']
                body_text = await page.inner_text('body')
                for keyword in type_keywords:
                    if keyword in body_text:
                        job['job_type'] = keyword
                        break
            
            # Extract deadline/closing date
            deadline_selectors = [
                '[class*="deadline"]',
                '[class*="closing"]',
                'span:has-text("Deadline")',
                'span:has-text("ASAP")',
            ]
            for selector in deadline_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text.strip():
                            job['closing_date'] = text.strip()
                            break
                except:
                    continue
            
            # Extract department/category
            category_selectors = [
                '[class*="category"]',
                '[class*="department"]',
                'span:has-text("Cabin Crew")',
            ]
            for selector in category_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text.strip():
                            job['department'] = text.strip()
                            break
                except:
                    continue
            
            await page.close()
            await context.close()
            
        except asyncio.TimeoutError:
            print(f"  Timeout for {job['job_id']}")
        except Exception as e:
            print(f"  Error fetching description for {job['job_id']}: {e}")
