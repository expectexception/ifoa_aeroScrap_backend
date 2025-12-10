"""
IndiGo Airlines Scraper
Extracts aviation job listings from goindigo.in careers page
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper


class IndiGoScraper(BaseScraper):
    """Scraper for IndiGo Airlines career page"""
    
    def __init__(self, config, db_manager=None):
        super().__init__(config, 'indigo', db_manager=db_manager)
        self.site_config = config['sites']['indigo']
        self.base_url = self.site_config['base_url']
        self.jobs_url = self.site_config['jobs_url']
        
    async def run(self):
        """Main execution method"""
        self.print_header()
        
        print(f"Fetching jobs from {self.site_config['name']}...")
        print(f"URL: {self.jobs_url}\n")
        
        jobs = await self.fetch_jobs_from_listing()
        
        if not jobs:
            print("❌ No jobs found")
            return []
        
        print(f"\n✓ Extracted {len(jobs)} jobs from listing")
        
        # Fetch detailed descriptions
        jobs_with_descriptions = await self.fetch_job_descriptions(jobs)
        
        # Save results
        self.save_results(jobs_with_descriptions, self.site_config['name'])
        self.print_sample(jobs_with_descriptions)
        
        return jobs_with_descriptions
    
    async def fetch_jobs_from_listing(self):
        """Fetch jobs from listing page"""
        jobs = []
        
        async with async_playwright() as p:
            # Launch with proper browser context to avoid detection
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            page, context = await self.setup_stealth_page(browser)
            
            try:
                print("Loading IndiGo careers page...")
                # Try with different wait strategies
                try:
                    await self.random_delay(1, 2)
                    await page.goto(self.jobs_url, wait_until='load', timeout=40000)
                except:
                    print("  Timeout on 'load', trying 'domcontentloaded'...")
                    await page.goto(self.jobs_url, wait_until='domcontentloaded', timeout=30000)
                
                # Wait for dynamic content to load
                print("Waiting for job listings to load...")
                await self.random_delay(8, 12)
                await self.simulate_human_behavior(page)
                
                # Try to wait for the job cards container specifically
                try:
                    await page.wait_for_selector('.search-result__job-cards, [class*="search-result"]', timeout=10000)
                    print("  ✓ Job cards container detected")
                except:
                    print("  ⚠ Job cards container not detected, continuing anyway...")
                
                # Save HTML for debugging
                html_content = await page.content()
                print(f"  Page HTML size: {len(html_content)} bytes")
                
                print("✓ Page loaded, extracting jobs...")
                
                # Try multiple selectors in order of specificity
                selectors_to_try = [
                    ('div.search-result__job-cards--card', 'Exact div with class'),
                    ('.search-result__job-cards--card', 'Class selector'),
                    ('div[class*="job-cards--card"]', 'Div containing class'),
                    ('.search-result__job-cards > div', 'Direct child divs'),
                    ('[class*="card-head"]', 'Elements with card-head'),
                ]
                
                job_elements = []
                for selector, desc in selectors_to_try:
                    elements = await page.query_selector_all(selector)
                    print(f"  Trying {desc} ({selector}): {len(elements)} elements")
                    if elements and len(elements) >= 3:
                        print(f"✓ Found {len(elements)} jobs using: {desc}")
                        job_elements = elements
                        break
                
                if not job_elements:
                    print("❌ No job elements found with known selectors")
                    # Try to get any links with job/career in them
                    job_links = await page.query_selector_all('a[href*="/job"], a[href*="/career"], a[href*="apply"]')
                    if job_links:
                        print(f"✓ Found {len(job_links)} job links as fallback")
                        for link in job_links[:self.max_jobs] if self.max_jobs else job_links:
                            try:
                                href = await link.get_attribute('href')
                                text = await link.inner_text()
                                if href and text and len(text) > 5:
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
            
            # Extract title using specific selector
            title = 'Unknown Position'
            title_elem = await element.query_selector('a.card-head--title')
            if title_elem:
                title = (await title_elem.inner_text()).strip()
                # Get job URL from title link
                href = await title_elem.get_attribute('href')
                if href:
                    if href.startswith('/'):
                        job_url = f"{self.base_url}/{href}"
                    elif href.startswith('http'):
                        job_url = href
                    else:
                        job_url = f"{self.base_url}/{href}"
                else:
                    job_url = None
            else:
                # Fallback to any link
                links = await element.query_selector_all('a')
                job_url = None
                if links:
                    for link in links:
                        href = await link.get_attribute('href')
                        if href and 'job-details' in href:
                            if href.startswith('/'):
                                job_url = f"{self.base_url}/{href}"
                            elif href.startswith('http'):
                                job_url = href
                            else:
                                job_url = f"{self.base_url}/{href}"
                            break
            
            # Extract location - it's in the text with date
            location = ''
            location_elem = await element.query_selector('p.card-body--location')
            if location_elem:
                location = (await location_elem.inner_text()).strip()
            else:
                # Parse from text - format is "DateLocation" like "25th Nov 25Gurgaon"
                for line in lines:
                    if any(keyword in line for keyword in ['Mumbai', 'Delhi', 'Gurgaon', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'India', 'Pan-India']):
                        # Extract just the location part
                        for loc in ['Mumbai', 'Delhi', 'Gurgaon', 'Bangalore', 'Hyderabad', 'Chennai', 'Kolkata', 'Pan-India']:
                            if loc in line:
                                location = loc
                                break
                        break
            
            # Extract job type
            job_type = ''
            type_elem = await element.query_selector('.job-type, [class*="type"], [class*="Type"]')
            if type_elem:
                job_type = (await type_elem.inner_text()).strip()
            else:
                for line in lines:
                    if any(keyword in line for keyword in ['Full-time', 'Part-time', 'Contract', 'Permanent', 'Temporary']):
                        job_type = line
                        break
            
            # Extract department
            department = ''
            dept_elem = await element.query_selector('.department, [class*="department"], [class*="Department"]')
            if dept_elem:
                department = (await dept_elem.inner_text()).strip()
            
            # Generate job ID
            job_id = f"indigo_{idx + 1}_{datetime.now().strftime('%Y%m%d')}"
            if job_url:
                # Try to extract ID from URL
                parts = job_url.split('/')
                for part in parts:
                    if part.isdigit() or (len(part) > 5 and any(c.isdigit() for c in part)):
                        job_id = f"indigo_{part}"
                        break
            
            job_data = {
                'job_id': job_id,
                'title': title,
                'company': 'IndiGo Airlines',
                'source': 'indigo',
                'url': job_url or self.jobs_url,
                'apply_url': job_url or self.jobs_url,
                'location': location,
                'job_type': job_type,
                'department': department,
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
        elif not url.startswith('http'):
            url = f"{self.base_url}/{url}"
        
        job_id = f"indigo_{idx + 1}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            'job_id': job_id,
            'title': title,
            'company': 'IndiGo Airlines',
            'source': 'indigo',
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
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
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
            await page.goto(job['url'], wait_until='load', timeout=35000)
            
            # Wait longer for dynamic content
            await self.random_delay(4, 6)
            await self.simulate_human_behavior(page)
            
            # Get page title
            page_title = await page.title()
            if page_title and len(page_title) > 10:
                job['title'] = page_title.replace(' - IndiGo', '').replace(' | IndiGo', '').strip()
            
            # Extract all headings
            headings = await page.query_selector_all('h1, h2, h3, h4')
            heading_texts = []
            for h in headings:
                text = await h.inner_text()
                if text.strip() and len(text.strip()) > 3:
                    heading_texts.append(text.strip())
            
            # Extract all paragraphs
            paragraphs = await page.query_selector_all('p')
            paragraph_texts = []
            for p in paragraphs:
                text = await p.inner_text()
                if text.strip() and len(text.strip()) > 20:
                    paragraph_texts.append(text.strip())
            
            # Extract lists
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
            
            if heading_texts:
                description_parts.append("=== Job Overview ===")
                description_parts.extend(heading_texts[:3])
                description_parts.append("")
            
            if paragraph_texts:
                description_parts.append("=== Description ===")
                description_parts.extend(paragraph_texts)
                description_parts.append("")
            
            if list_texts:
                description_parts.append("=== Requirements & Details ===")
                description_parts.extend(list_texts)
            
            # Combine all parts
            if description_parts:
                job['description'] = '\n'.join(description_parts)
            
            # If still no description, try main content area
            if not job['description'] or len(job['description']) < 100:
                main_selectors = ['main', 'article', '.content', '.job-detail', '[class*="detail"]', '.container']
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
                    'span:has-text("Mumbai")',
                    'span:has-text("Delhi")',
                    'span:has-text("Bangalore")',
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
                body_text = await page.inner_text('body')
                type_keywords = ['Permanent', 'Contract', 'Temporary', 'Full-time', 'Full time', 'Part-time']
                for keyword in type_keywords:
                    if keyword in body_text:
                        job['job_type'] = keyword
                        break
            
            # Extract department
            if not job['department']:
                dept_keywords = ['Cabin Crew', 'Pilot', 'Engineering', 'Ground Staff', 'Operations', 'Finance', 'IT', 'Customer Service']
                body_text = await page.inner_text('body')
                for keyword in dept_keywords:
                    if keyword in body_text:
                        job['department'] = keyword
                        break
            
            await page.close()
            await context.close()
            
        except asyncio.TimeoutError:
            print(f"  Timeout for {job['job_id']}")
        except Exception as e:
            print(f"  Error fetching description for {job['job_id']}: {e}")
