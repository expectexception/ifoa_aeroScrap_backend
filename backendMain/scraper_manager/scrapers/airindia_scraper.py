"""
Air India Careers Scraper
Extracts aviation job listings from careers.airindia.com (SuccessFactors)
"""

import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
from .base_scraper import BaseScraper
from .job_schema import get_job_dict
import re


class AirIndiaScraper(BaseScraper):
    """Scraper for Air India Careers (SuccessFactors)"""

    def __init__(self, config, db_manager=None):
        super().__init__(config, 'Air India', db_manager=db_manager)
        self.site_config = config.get('sites', {}).get('airindia', {})
        self.base_url = self.site_config.get('base_url', 'https://careers.airindia.com')
        self.jobs_url = self.site_config.get('jobs_url', 'https://careers.airindia.com/sfcareer/jobreqcareer?jobPipeline=AirIndia')

    async def run(self):
        """Main execution method"""
        self.print_header()

        print(f"Fetching jobs from {self.site_config.get('name', 'Air India Careers')}...")
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
        """Fetch jobs from SuccessFactors listing page"""
        jobs = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)

            try:
                print("Loading Air India careers page...")
                await self.random_delay(1, 2)
                await page.goto(self.jobs_url, wait_until='domcontentloaded', timeout=30000)

                # Wait for dynamic content to load
                await self.random_delay(4, 6)
                await self.simulate_human_behavior(page)

                print("✓ Page loaded, extracting jobs...")

                # SuccessFactors search page typically has job links with specific patterns
                selectors = [
                    'a[href*="/job/"]',
                    'a[href*="jobId="]',
                    '.job-link',
                    '[data-job-id] a',
                    '.search-result a',
                ]

                job_links = []
                for selector in selectors:
                    elements = await page.query_selector_all(selector)
                    if elements:
                        job_links.extend(elements)
                        print(f"✓ Found {len(elements)} jobs using selector: {selector}")
                        break

                if not job_links:
                    print("❌ No job links found with known selectors")
                    return jobs

                # Extract job data from links
                for link in job_links[:self.max_jobs] if self.max_jobs else job_links:
                    try:
                        href = await link.get_attribute('href')
                        if not href:
                            continue

                        # Build full URL
                        if href.startswith('/'):
                            job_url = f"{self.base_url}{href}"
                        elif href.startswith('http'):
                            job_url = href
                        else:
                            job_url = f"{self.base_url}/{href}"

                        # Extract title from link text
                        title = (await link.inner_text()).strip()
                        if not title or len(title) < 5:
                            continue

                        # Extract job ID from URL
                        job_id = None
                        if 'jobId=' in href:
                            import re
                            match = re.search(r'jobId=(\d+)', href)
                            if match:
                                job_id = match.group(1)

                        if not job_id:
                            job_id = f"airindia_{len(jobs) + 1}"

                        job_data = {
                            'job_id': f"airindia_{job_id}",
                            'title': title,
                            'company': 'Air India',
                            'source': 'Air India',
                            'url': job_url,
                            'apply_url': job_url,
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

                        jobs.append(job_data)

                        if self.max_jobs and len(jobs) >= self.max_jobs:
                            break

                    except Exception as e:
                        continue

            except asyncio.TimeoutError:
                print("❌ Timeout loading page")
            except Exception as e:
                print(f"❌ Error fetching jobs: {e}")
            finally:
                await context.close()
                await browser.close()

        return jobs

    async def fetch_job_descriptions(self, jobs):
        """Fetch detailed descriptions for each job"""
        print(f"\nFetching detailed descriptions for {len(jobs)} jobs...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for i in range(0, len(jobs), self.batch_size):
                batch = jobs[i:i + self.batch_size]
                tasks = []

                for job in batch:
                    if job.get('url'):
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
        """Extract detailed description from SuccessFactors job page"""
        try:
            page, context = await self.setup_stealth_page(browser)

            # Load job detail page
            await self.random_delay(1, 2)
            await page.goto(job['url'], wait_until='load', timeout=30000)
            await self.random_delay(2, 4)
            await self.simulate_human_behavior(page)

            # Extract title from page if better
            page_title = await page.title()
            if page_title and 'Air India' in page_title:
                # Clean up title
                title_clean = page_title.replace(' - Air India Careers', '').replace(' | Air India', '').strip()
                if len(title_clean) > len(job.get('title', '')):
                    job['title'] = title_clean

            # SuccessFactors pages often have content in specific containers
            desc_selectors = [
                '#jobDescription',
                '.job-description',
                '[class*="description"]',
                '.content',
                'article',
                'main',
                '#main-content',
            ]

            description = ''
            for selector in desc_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        text = await elem.inner_text()
                        if text and len(text) > 100:
                            description = text.strip()
                            break
                except Exception:
                    continue

            # Get body text for pattern matching
            body_text = await page.inner_text('body')

            # If no description found, try extracting from body text with patterns
            if not description:
                # Look for job details section
                # Find content between common headers
                patterns = [
                    r'(?:Job Description|Position Summary|About the Role)[:\s]*(.*?)(?:Requirements|Qualifications|How to Apply|$)',
                    r'(?:About Us|Company Overview)[:\s]*(.*?)(?:Job Description|$)',
                ]

                for pattern in patterns:
                    match = re.search(pattern, body_text, re.DOTALL | re.IGNORECASE)
                    if match:
                        description = match.group(1).strip()
                        if len(description) > 50:
                            break

            # Extract location
            if not job.get('location'):
                loc_patterns = [
                    r'Location[:\s]+([^\n\r]+)',
                    r'Work Location[:\s]+([^\n\r]+)',
                    r'City[:\s]+([^\n\r]+)',
                ]
                for pattern in loc_patterns:
                    match = re.search(pattern, body_text, re.IGNORECASE)
                    if match:
                        location = match.group(1).strip()
                        if location and len(location) < 100:
                            job['location'] = location
                            break

            # Extract posted date - SuccessFactors often has dates in meta or specific elements
            if not job.get('posted_date'):
                # Try JSON-LD first
                try:
                    scripts = await page.query_selector_all('script[type="application/ld+json"]')
                    for s in scripts:
                        try:
                            json_text = await s.inner_text()
                            import json as _json
                            data = _json.loads(json_text)
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                if isinstance(item, dict) and item.get('datePosted'):
                                    posted_candidate = item.get('datePosted')
                                    parsed = self.parse_posted_date(posted_candidate)
                                    job['posted_date'] = parsed if parsed else posted_candidate
                                    break
                        except Exception:
                            continue
                except Exception:
                    pass

                # Try meta tags and page patterns
                if not job.get('posted_date'):
                    date_patterns = [
                        r'Posted[:\s]+([^\n\r]+)',
                        r'Date Posted[:\s]+([^\n\r]+)',
                        r'Published[:\s]+([^\n\r]+)',
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, body_text, re.IGNORECASE)
                        if match:
                            date_text = match.group(1).strip()
                            parsed = self.parse_posted_date(date_text)
                            job['posted_date'] = parsed if parsed else date_text
                            break

            # Fallback: use base scraper helpers
            if not job.get('posted_date'):
                try:
                    fallback_pd = await self.extract_posted_date_from_page(page)
                    if fallback_pd:
                        job['posted_date'] = fallback_pd
                except Exception:
                    pass

            if not description or len(description) < 100:
                try:
                    fallback_desc = await self.extract_description_from_page(page)
                    if fallback_desc and len(fallback_desc) > len(description):
                        description = fallback_desc
                except Exception:
                    pass

            job['description'] = description

            await page.close()
            await context.close()

        except asyncio.TimeoutError:
            print(f"  Timeout for {job['job_id']}")
        except Exception as e:
            print(f"  Error fetching description for {job['job_id']}: {e}")