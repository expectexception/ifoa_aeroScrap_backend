"""
Flygosh Jobs Scraper
Extracts aviation jobs from flygoshjobs.com
"""

import requests
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import re
import asyncio
from datetime import datetime
from typing import List, Dict
from scrapers.base_scraper import BaseScraper


class FlygoshScraper(BaseScraper):
    """Scraper for Flygosh aviation job postings"""
    
    def __init__(self, config: dict, db_manager=None):
        super().__init__(config, 'flygosh', db_manager=db_manager)
        self.jobs_url = self.site_config.get('jobs_url', '')
        
    async def fetch_jobs_from_listing(self) -> List[Dict]:
        """Fetch job listings from the main jobs page using Playwright"""
        all_jobs = []
        
        print("Fetching jobs from listing page (JavaScript-rendered)...")
        
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page, context = await self.setup_stealth_page(browser)
                
                await self.random_delay(1, 2)
                await page.goto(self.jobs_url, wait_until='networkidle', timeout=30000)
                await self.random_delay(2, 4)
                await self.simulate_human_behavior(page)
                
                # Find job cards
                job_cards = await page.query_selector_all('[class*="job-card"]')
                
                print(f"  Found {len(job_cards)} job cards")
                
                for idx, card in enumerate(job_cards):
                    if self.max_jobs and len(all_jobs) >= self.max_jobs:
                        break
                    
                    job_data = await self._extract_job_from_card_playwright(card, idx)
                    if job_data:
                        all_jobs.append(job_data)
                
                print(f"  Extracted {len(all_jobs)} jobs")
                
                await context.close()
                await browser.close()
            
        except Exception as e:
            print(f"  Error fetching jobs: {e}")
        
        return all_jobs
    
    async def _extract_job_from_card_playwright(self, card, idx: int) -> Dict:
        """Extract job data from a job card element using Playwright"""
        
        try:
            # Get full text
            text = await card.inner_text()
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            
            # First line is usually the title
            title = lines[0] if lines else f"Job {idx+1}"
            
            # Second line is often location | company
            location = ''
            company = ''
            if len(lines) > 1:
                location_line = lines[1]
                if '|' in location_line:
                    parts = location_line.split('|')
                    location = parts[0].strip()
                    if len(parts) > 1:
                        company = parts[1].strip()
                else:
                    location = location_line
            
            # Extract URL
            link = await card.query_selector('a[href]')
            url = ''
            if link:
                href = await link.get_attribute('href')
                if href:
                    if href.startswith('http'):
                        url = href
                    elif href.startswith('/'):
                        url = self.base_url + href
                    else:
                        url = f"{self.base_url}/{href}"
            
            return {
                'job_id': str(idx + 1),
                'title': title,
                'company': company or self.company_name,
                'source': self.site_key,
                'url': url,
                'apply_url': url,
                'location': location,
                'job_type': '',
                'department': '',
                'posted_date': '',
                'closing_date': '',
                'timestamp': datetime.now().isoformat(),
            }
            
        except Exception as e:
            print(f"    Error extracting job card {idx}: {e}")
            return None
    

    
    async def fetch_job_descriptions(self, jobs: List[Dict]) -> List[Dict]:
        """Fetch detailed descriptions from job pages using Playwright"""
        
        print(f"\nExtracting descriptions for {len(jobs)} jobs...")
        print(f"Processing in batches of {self.batch_size}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            
            for i in range(0, len(jobs), self.batch_size):
                batch = jobs[i:i + self.batch_size]
                print(f"\nBatch {i//self.batch_size + 1}/{(len(jobs)-1)//self.batch_size + 1} (jobs {i+1}-{min(i+self.batch_size, len(jobs))})")
                
                tasks = [self._extract_description(browser, job) for job in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                
                completed = sum(1 for job in jobs if job.get('description'))
                print(f"  Progress: {completed}/{len(jobs)} complete")
                
                await self.random_delay(0.5, 1.0)
            
            await browser.close()
        
        return jobs
    
    async def _extract_description(self, browser, job: Dict):
        """Extract full information from job detail page"""
        
        if not job.get('url'):
            job['description'] = ''
            job['requirements'] = ''
            job['qualifications'] = ''
            return
        
        page, context = await self.setup_stealth_page(browser)
        
        try:
            await self.random_delay(1, 2)
            await page.goto(job['url'], wait_until='networkidle', timeout=30000)
            await self.random_delay(2, 4)
            await self.simulate_human_behavior(page)
            
            # Get full page content
            full_text = await page.inner_text('body')
            
            # Extract job title (may be more complete on detail page)
            title_elem = await page.query_selector('h1, [class*="title"]')
            if title_elem:
                title = await title_elem.inner_text()
                if len(title) > len(job.get('title', '')):
                    job['title'] = title.strip()
            
            # Extract location (may be more specific)
            location_elem = await page.query_selector('[class*="location"], .location')
            if location_elem:
                location = await location_elem.inner_text()
                if location.strip():
                    job['location'] = location.strip()
            
            # Extract job type
            type_elem = await page.query_selector('[class*="job-type"], [class*="employment"]')
            if type_elem:
                job_type = await type_elem.inner_text()
                job['job_type'] = job_type.strip()
            
            # Extract posted date
            date_elem = await page.query_selector('[class*="date"], time, [class*="posted"]')
            if date_elem:
                date = await date_elem.inner_text()
                job['posted_date'] = date.strip()
            
            # Extract full description
            desc_selectors = [
                '.job-description',
                '[class*="description"]',
                '.description',
                '.content',
                'article',
                'main'
            ]
            
            description = ''
            for selector in desc_selectors:
                desc_elem = await page.query_selector(selector)
                if desc_elem:
                    desc_html = await desc_elem.inner_html()
                    description = re.sub(r'<[^>]+>', ' ', desc_html)
                    description = re.sub(r'\s+', ' ', description).strip()
                    if len(description) > 100:  # Valid description
                        break
            
            job['description'] = description
            
            # Extract requirements section
            requirements = ''
            req_keywords = ['requirement', 'qualification', 'skill', 'experience']
            for keyword in req_keywords:
                req_elem = await page.query_selector(f'[class*="{keyword}"], [id*="{keyword}"]')
                if req_elem:
                    req_html = await req_elem.inner_html()
                    requirements = re.sub(r'<[^>]+>', ' ', req_html)
                    requirements = re.sub(r'\s+', ' ', requirements).strip()
                    if len(requirements) > 50:
                        break
            
            job['requirements'] = requirements
            
            # Extract qualifications
            qual_elem = await page.query_selector('[class*="qualification"]')
            if qual_elem:
                qual_html = await qual_elem.inner_html()
                qualifications = re.sub(r'<[^>]+>', ' ', qual_html)
                qualifications = re.sub(r'\s+', ' ', qualifications).strip()
                job['qualifications'] = qualifications
            else:
                job['qualifications'] = ''
            
        except Exception as e:
            print(f"    Error extracting {job['job_id']}: {str(e)[:50]}")
            job['description'] = job.get('description', '')
            job['requirements'] = ''
            job['qualifications'] = ''
        finally:
            await page.close()
            await context.close()
    
    async def run(self):
        """Main execution method"""
        
        self.print_header()
        
        # Step 1: Fetch from listing page
        jobs = await self.fetch_jobs_from_listing()
        
        if not jobs:
            print("No jobs found!")
            return []
        
        print(f"\n✓ Fetched {len(jobs)} jobs from listing")
        
        # Step 2: Always fetch full details from each job page
        jobs = await self.fetch_job_descriptions(jobs)
        
        # Step 3: Save results
        self.save_results(jobs)
        
        # Show sample
        self.print_sample(jobs)
        
        return jobs
