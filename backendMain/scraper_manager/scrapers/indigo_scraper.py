"""
IndiGo Airlines Scraper
Extracts aviation job listings from goindigo.in careers page
"""

import asyncio
import re
import json
import os
import tempfile
from datetime import datetime
from playwright.async_api import async_playwright
import requests
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
        await self.save_results(jobs_with_descriptions, self.site_config['name'])
        self.print_sample(jobs_with_descriptions)
        
        return jobs_with_descriptions
    
    async def fetch_jobs_from_listing(self):
        """Fetch jobs from listing page"""
        jobs = []

        # Try proxy if available (set PROXY_URL environment variable)
        proxy_url = os.getenv('PROXY_URL')
        proxy_config = None
        if proxy_url:
            proxy_config = {
                'server': proxy_url
            }
            print(f"Using proxy: {proxy_url}")

        async with async_playwright() as p:
            # Launch with proxy if configured
            launch_args = {
                'headless': True,
                'args': ['--disable-blink-features=AutomationControlled']
            }
            if proxy_config:
                launch_args['proxy'] = proxy_config

            browser = await p.chromium.launch(**launch_args)
            page, context = await self.setup_stealth_page(browser)

            try:
                print("Loading IndiGo careers page...")
                # Try with different wait strategies
                try:
                    await self.random_delay(2, 4)
                    await page.goto(self.jobs_url, wait_until='load', timeout=40000)
                except Exception:
                    print("  Timeout on 'load', trying 'domcontentloaded'...")
                    await self.random_delay(3, 5)
                    await page.goto(self.jobs_url, wait_until='domcontentloaded', timeout=30000)

                # Wait for dynamic content to load with longer delay to avoid blocking
                print("Waiting for job listings to load...")
                await self.random_delay(12, 18)
                await self.simulate_human_behavior(page)

                # Try to wait for the job cards container specifically
                try:
                    await page.wait_for_selector('.search-result__job-cards, [class*="search-result"]', timeout=10000)
                    print("  ✓ Job cards container detected")
                except Exception:
                    print("  ⚠ Job cards container not detected, continuing anyway...")

                # Save HTML for debugging
                html_content = await page.content()
                html_len = len(html_content)
                print(f"  Page HTML size: {html_len} bytes")

                # Detect common blocking / failover pages (Akamai, CDN blocks)
                blocked_page = False
                if html_len < 2000 or 'Something went wrong' in html_content or 'akamfailoverpage' in html_content.lower():
                    blocked_page = True
                    print("⚠ Detected an error / CDN failover page from IndiGo (site may be blocking automated requests)")
                    print("  - HTML appears minimal or contains failover text. Will attempt broader fallbacks (anchors & JSON-LD) before giving up.")

                print("✓ Page loaded, extracting jobs...")

                # Try multiple selectors in order of specificity FIRST (since HTML is already rendered)
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

                if job_elements:
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
                    
                    if jobs:
                        print(f"✓ Extracted {len(jobs)} jobs from selectors")
                        await context.close()
                        await browser.close()
                        return jobs

                # If selectors failed, try API
                try:
                    api_jobs = await self._attempt_api_jobs_fetch(html_content)
                    if api_jobs:
                        print(f"✓ Extracted {len(api_jobs)} jobs from careers API")
                        await context.close()
                        await browser.close()
                        return api_jobs
                except Exception as e:
                    print(f"  ⚠ careers-API attempt failed: {e}")

                # Try JSON-LD structured data
                jsonld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
                found_json_jobs = 0
                for s in jsonld_scripts:
                    try:
                        txt = (await s.inner_text()).strip()
                        import json as _json
                        data = _json.loads(txt)
                        items = data if isinstance(data, list) else [data]
                        for item in items:
                            if isinstance(item, dict) and (item.get('@type') and 'JobPosting' in item.get('@type')):
                                title = item.get('title') or item.get('name') or 'No Title'
                                job_url = item.get('url') or self.jobs_url
                                jd = item.get('description') or ''
                                job_data = self._create_basic_job(job_url, title, len(jobs))
                                job_data['description'] = jd
                                if item.get('datePosted'):
                                    job_data['posted_date'] = item.get('datePosted')
                                jobs.append(job_data)
                                found_json_jobs += 1
                    except Exception:
                        continue

                if found_json_jobs:
                    print(f"✓ Found {found_json_jobs} jobs in JSON-LD")
                    await context.close()
                    await browser.close()
                    return jobs

                # Fallback to anchors
                anchors = await page.query_selector_all('a')
                candidate_links = []
                for a in anchors:
                    try:
                        href = await a.get_attribute('href')
                        text = (await a.inner_text() or '').strip()
                        if not href or not text or len(text) < 6:
                            continue
                        href_low = href.lower()
                        if any(k in href_low for k in ['/job', '/career', 'careers', 'apply', '/vacancies', '/vacancy', '/openings', 'job-search']):
                            candidate_links.append((href, text))
                    except Exception:
                        continue

                # Deduplicate and create jobs
                seen = set()
                for href, text in candidate_links:
                    if self.max_jobs and len(jobs) >= self.max_jobs:
                        break
                    key = (href, text)
                    if key in seen:
                        continue
                    seen.add(key)
                    job_data = self._create_basic_job(href, text, len(jobs))
                    jobs.append(job_data)

                if jobs:
                    print(f"✓ Extracted {len(jobs)} jobs from anchor fallbacks")
                    await context.close()
                    await browser.close()
                    return jobs

                # If page appeared blocked, try persistent render retry
                if 'blocked_page' in locals() and blocked_page:
                    print("⚠ Page looks blocked (failover). Will attempt a persistent browser retry before giving up.")
                    # Try persistent context retry
                    try:
                        persistent = await self._fetch_with_persistent_context(browser, self.jobs_url, max_wait=20)
                        if persistent:
                            print(f"✓ Persistent render extracted {len(persistent)} jobs")
                            await context.close()
                            await browser.close()
                            return persistent
                    except Exception as e:
                        print(f"  ⚠ Persistent render failed: {e}")

                    print("❌ Page looks blocked (failover). No jobs extracted from fallbacks.")
                    await context.close()
                    await browser.close()
                    return []

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

        # If live API/rendering failed (e.g., blocked), try using a saved local HTML snapshot as a fallback for testing
        try:
            local_path = os.path.join(os.path.dirname(__file__), '..', 'tmp_indigo_page.html')
            # also check project root fallback
            project_root_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmp_indigo_page.html')
            candidate_paths = [local_path, project_root_path, '/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/tmp_indigo_page.html']
            for p in candidate_paths:
                if p and os.path.exists(p):
                    html = open(p, 'r', encoding='utf-8').read()
                    jobs_local = []
                    # find title links
                    for m in re.finditer(r'<a[^>]*class=["\']card-head--title["\'][^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', html, re.IGNORECASE):
                        href = m.group(1)
                        title = m.group(2).strip()
                        # look ahead for date-text within next 500 chars
                        snippet = html[m.end():m.end()+800]
                        date_m = re.search(r'<span[^>]*class=["\']date-text["\'][^>]*>(.*?)</span>', snippet, re.IGNORECASE|re.DOTALL)
                        location_m = re.search(r'<span[^>]*class=["\']location-text["\'][^>]*>\s*<span[^>]*>([^<]+)</span>', snippet, re.IGNORECASE|re.DOTALL)
                        date_text = None
                        if date_m:
                            dt_raw = date_m.group(1)
                            # strip tags like <sup>
                            dt_clean = re.sub(r'<[^>]+>', '', dt_raw).strip()
                            date_text = dt_clean
                        location = location_m.group(1).strip() if location_m else ''
                        # normalize href
                        if href.startswith('/'):
                            url = f"https://www.goindigo.in/{href.lstrip('/')}"
                        elif href.startswith('http'):
                            url = href
                        else:
                            url = f"https://www.goindigo.in/{href}"
                        job = self._create_basic_job(url, title, len(jobs_local))
                        if date_text:
                            parsed = self.parse_posted_date(date_text)
                            job['posted_date'] = parsed if parsed else date_text
                        job['location'] = location
                        jobs_local.append(job)
                        if self.max_jobs and len(jobs_local) >= self.max_jobs:
                            break
                    if jobs_local:
                        return jobs_local
        except Exception:
            pass
    
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
            
            # Extract posted date (prefer explicit span.date-text if present)
            posted_date = ''
            date_elem = await element.query_selector('span.date-text')
            if not date_elem:
                date_elem = await element.query_selector('[class*="date"], [class*="Date"], [class*="posted"], time')
            if date_elem:
                date_text = (await date_elem.inner_text()).strip()
                # Normalize ordinals like '2nd' -> '2' (base parser also handles but keep local safety)
                date_text = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_text, flags=re.IGNORECASE)
                parsed_date = self.parse_posted_date(date_text)
                posted_date = parsed_date if parsed_date else date_text
            else:
                # Try to extract from lines (format: "25th Nov 25" or similar)
                for line in lines:
                    if re.search(r'\d+(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', line, re.IGNORECASE):
                        parsed_date = self.parse_posted_date(line)
                        posted_date = parsed_date if parsed_date else line
                        break
            
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
                'posted_date': posted_date,
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

    async def _attempt_api_jobs_fetch(self, html_content: str):
        """Try to discover a careers JSON endpoint in the page HTML and fetch jobs from it."""
        # Look for an AEM careers API or static JSON marker seen in tmp_indigo_page.html
        candidates = []
        m = re.search(r"CAREER_JOB_SEARCH_AEM_DATA\s*:\s*'([^']+)'", html_content)
        if m:
            candidates.append(m.group(1))

        # Look for direct JSON endpoints
        for m in re.finditer(r"/content/[\w\-/]+careers-job-search[\w\-\.]*\.json", html_content):
            candidates.append(m.group(0))

        # Look for mf-careers-prod domain endpoints (avoid quoting issues)
        for m in re.finditer(r'mf-careers-prod\.goindigo\.in[^\s\'" ]+\.json', html_content):
            # prepend scheme if missing
            part = m.group(0)
            if part.startswith('http'):
                candidates.append(part)
            else:
                candidates.append('https://' + part)

        # Normalize and dedupe
        candidates = [c for c in dict.fromkeys(candidates)]
        if not candidates:
            candidates = []

        # Also try to extract the ms-careers-prod job-list endpoint from inline JS vars
        m2 = re.search(r"CAREER_JOB_SEARCH_RESULT_LIST\s*:\s*'([^']+)'", html_content)
        if m2:
            candidates.insert(0, m2.group(1))

        if not candidates:
            # If nothing discoverable from the page (blocked), try the known AEM JSON and ms-careers endpoints
            candidates = [
                '/content/careers-api/skypluscareers/in/en/v1/careers-job-search.json',
                'https://ms-careers-prod.goindigo.in/career-job-list',
            ]

        jobs = []
        for path in candidates:
            if path.startswith('/'):
                url = f"https://www.goindigo.in{path}"
            elif path.startswith('http'):
                url = path
            else:
                url = f"https://www.goindigo.in{path}"

            try:
                # Do a synchronous request in thread executor to avoid blocking event loop
                loop = asyncio.get_event_loop()
                resp = await loop.run_in_executor(None, lambda: requests.get(url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Referer': self.jobs_url,
                    'Origin': self.base_url,
                }))

                if resp.status_code != 200:
                    # If this looks like the ms-careers-prod job-list endpoint, try POST with a typical payload
                    if 'career-job-list' in url or 'ms-careers-prod' in url:
                        try:
                            payload = {
                                'start': 0,
                                'limit': self.max_jobs or 50,
                                'filters': {},
                            }
                            resp2 = await loop.run_in_executor(None, lambda: requests.post(url, json=payload, timeout=20, headers={
                                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                                'Accept': 'application/json, text/javascript, */*; q=0.01',
                                'Referer': self.jobs_url,
                                'Origin': self.base_url,
                                'Content-Type': 'application/json'
                            }))
                            if resp2.status_code == 200:
                                data = resp2.json()
                            else:
                                continue
                        except Exception:
                            continue
                    else:
                        continue
                else:
                    data = resp.json()

                # Try to find job entries in common keys
                items = None
                for key in ['jobs', 'results', 'items', 'data']:
                    if isinstance(data, dict) and key in data and isinstance(data[key], list):
                        items = data[key]
                        break
                if items is None and isinstance(data, list):
                    items = data

                if not items:
                    continue

                for it in items:
                    title = it.get('title') or it.get('name') or it.get('jobTitle') or it.get('position')
                    url = it.get('url') or it.get('detailUrl') or it.get('applyUrl')
                    if url and url.startswith('/'):
                        url = f"https://www.goindigo.in{url}"
                    posted = it.get('datePosted') or it.get('postedDate') or it.get('publishDate') or it.get('created')
                    job = self._create_basic_job(url or self.jobs_url, title or 'No Title', len(jobs))
                    if isinstance(posted, str):
                        parsed = self.parse_posted_date(posted)
                        job['posted_date'] = parsed if parsed else posted
                    jobs.append(job)

                if jobs:
                    return jobs
            except Exception:
                continue

        # If live API attempts failed (network / blocking), try parsing a local snapshot for testing
        try:
            snapshot_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'tmp_indigo_page.html'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'tmp_indigo_page.html'),
                '/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/tmp_indigo_page.html'
            ]
            for p in snapshot_paths:
                if p and os.path.exists(p):
                    html = open(p, 'r', encoding='utf-8').read()
                    jobs_local = []
                    for m in re.finditer(r'<a[^>]*class=["\']card-head--title["\'][^>]*href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>', html, re.IGNORECASE):
                        href = m.group(1)
                        title = m.group(2).strip()
                        snippet = html[m.end():m.end()+800]
                        date_m = re.search(r'<span[^>]*class=["\']date-text["\'][^>]*>(.*?)</span>', snippet, re.IGNORECASE|re.DOTALL)
                        location_m = re.search(r'<span[^>]*class=["\']location-text["\'][^>]*>\s*<span[^>]*>([^<]+)</span>', snippet, re.IGNORECASE|re.DOTALL)
                        date_text = None
                        if date_m:
                            dt_raw = date_m.group(1)
                            dt_clean = re.sub(r'<[^>]+>', '', dt_raw).strip()
                            date_text = dt_clean
                        location = location_m.group(1).strip() if location_m else ''
                        if href.startswith('/'):
                            url = f"https://www.goindigo.in/{href.lstrip('/')}"
                        elif href.startswith('http'):
                            url = href
                        else:
                            url = f"https://www.goindigo.in/{href}"
                        job = self._create_basic_job(url, title, len(jobs_local))
                        if date_text:
                            parsed = self.parse_posted_date(date_text)
                            job['posted_date'] = parsed if parsed else date_text
                        job['location'] = location
                        jobs_local.append(job)
                        if self.max_jobs and len(jobs_local) >= self.max_jobs:
                            break
                    if jobs_local:
                        return jobs_local
        except Exception:
            pass

        return jobs

    async def _fetch_with_persistent_context(self, browser, url, max_wait=20):
        """Retry rendering using a persistent context to reduce transient blocking. Returns job list or []"""
        # Use a temporary user-data-dir so Playwright creates a persistent profile
        temp_dir = tempfile.mkdtemp(prefix='indigo_profile_')
        try:
            # Use proxy if available
            proxy_url = os.getenv('PROXY_URL')
            launch_args = {
                'user_data_dir': temp_dir,
                'headless': True,
                'args': ['--disable-blink-features=AutomationControlled']
            }
            if proxy_url:
                launch_args['proxy'] = {'server': proxy_url}

            async with async_playwright() as p:
                ctx = await p.chromium.launch_persistent_context(**launch_args)
                page = await ctx.new_page()
                # Add stealth init script
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
                    Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
                    window.chrome = { runtime: {} };
                """)
                await page.goto(url, wait_until='load', timeout=40000)
                await asyncio.sleep(max_wait)
                await self.simulate_human_behavior(page)
                # Try selector extraction as before
                elems = await page.query_selector_all('.search-result__job-cards--card')
                jobs = []
                for idx, el in enumerate(elems):
                    job = await self._extract_job_from_card(el, idx)
                    if job:
                        jobs.append(job)
                        if self.max_jobs and len(jobs) >= self.max_jobs:
                            break
                await ctx.close()
                return jobs
        finally:
            try:
                # leave temp_dir for debugging if needed; don't remove automatically
                pass
            except Exception:
                pass
    
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
        """Extract detailed description from job page with retry logic"""
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            page = None
            context = None
            try:
                page, context = await self.setup_stealth_page(browser)
                
                # Increase delay on retries
                delay_min = 2 + (retry_count * 2)
                delay_max = 4 + (retry_count * 2)
                await self.random_delay(delay_min, delay_max)
                
                try:
                    await page.goto(job['url'], wait_until='load', timeout=35000)
                except Exception as timeout_err:
                    await self.random_delay(1, 2)
                    try:
                        await page.goto(job['url'], wait_until='domcontentloaded', timeout=30000)
                    except:
                        raise timeout_err
                
                # Wait longer for dynamic content
                await self.random_delay(4, 6)
                await self.simulate_human_behavior(page)
                
                # Get page title
                page_title = await page.title()
                if page_title and len(page_title) > 10:
                    job['title'] = page_title.replace(' - IndiGo', '').replace(' | IndiGo', '').strip()
                
                # PRIORITY 1: Try structured data extraction (JSON-LD)
                try:
                    jsonld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
                    for script in jsonld_scripts:
                        try:
                            txt = (await script.inner_text()).strip()
                            import json as _json
                            data = _json.loads(txt)
                            items = data if isinstance(data, list) else [data]
                            for item in items:
                                if isinstance(item, dict) and item.get('@type') and 'JobPosting' in item.get('@type'):
                                    if item.get('description'):
                                        job['description'] = item['description']
                                        break
                            if job['description']:
                                break
                        except:
                            continue
                except Exception:
                    pass
                
                # PRIORITY 2: Extract body text aggressively if no description yet
                if not job.get('description') or len(job.get('description') or '') < 100:
                    try:
                        body_text = await page.inner_text('body')
                        clean_text = body_text.strip()
                        
                        if len(clean_text) > 300:
                            lines = [l.strip() for l in clean_text.split('\n') if l.strip()]
                            main_lines = []
                            for line in lines:
                                if any(skip in line.lower() for skip in ['home', 'about', 'contact', 'privacy', 'terms', 'menu', 'search', 'sign in', 'login']):
                                    if len(main_lines) > 50:
                                        continue
                                
                                if len(line) > 20 or (len(line) > 10 and any(c.isalpha() for c in line)):
                                    main_lines.append(line)
                            
                            if main_lines:
                                job['description'] = '\n'.join(main_lines[:100])
                    except Exception:
                        pass
                
                # PRIORITY 3: Extract specific sections
                if not job.get('description') or len(job.get('description') or '') < 100:
                    description_parts = []
                    
                    try:
                        headings = await page.query_selector_all('h1, h2, h3, h4, h5, h6')
                        heading_texts = []
                        for h in headings:
                            text = await h.inner_text()
                            if text.strip() and len(text.strip()) > 3:
                                heading_texts.append(text.strip())
                        
                        if heading_texts:
                            description_parts.append("=== Job Overview ===")
                            description_parts.extend(heading_texts[:5])
                            description_parts.append("")
                    except Exception:
                        pass
                    
                    try:
                        paragraphs = await page.query_selector_all('p')
                        paragraph_texts = []
                        for p in paragraphs:
                            text = await p.inner_text()
                            if text.strip() and len(text.strip()) > 20:
                                paragraph_texts.append(text.strip())
                        
                        if paragraph_texts:
                            description_parts.append("=== Description ===")
                            description_parts.extend(paragraph_texts)
                            description_parts.append("")
                    except Exception:
                        pass
                    
                    try:
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
                        
                        if list_texts:
                            description_parts.append("=== Requirements & Details ===")
                            description_parts.extend(list_texts)
                    except Exception:
                        pass
                    
                    if description_parts:
                        job['description'] = '\n'.join(description_parts)
                
                # PRIORITY 4: Try common container selectors
                if not job.get('description') or len(job.get('description') or '') < 100:
                    main_selectors = [
                        'main', 'article', '[role="main"]', '.job-detail', '.job-description',
                        '.description', '.content', '[class*="detail"]', '[class*="description"]',
                        '.container', '.wrapper', '[class*="job-content"]'
                    ]
                    for selector in main_selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.inner_text()
                                if len(text) > 200:
                                    job['description'] = text.strip()
                                    break
                        except Exception:
                            continue
                
                # PRIORITY 5: Use BaseScraper heuristics as last resort
                if not job.get('description') or len(job.get('description') or '') < 100:
                    try:
                        fallback_desc = await self.extract_description_from_page(page)
                        if fallback_desc and len(fallback_desc) > 100:
                            job['description'] = fallback_desc
                    except Exception:
                        pass

                # Detect common error/failover text and clear if present
                if job.get('description'):
                    d_lower = job['description'].lower()
                    d_len = len(job['description'])
                    
                    is_error_page = False
                    
                    if d_len < 150:
                        error_keywords = ['something went wrong', 'please try again', 'akamai', 'error 5']
                        error_count = sum(1 for err in error_keywords if err in d_lower)
                        if error_count >= 2:
                            is_error_page = True
                    
                    if 'akamfailoverpage' in d_lower or (d_len < 200 and '404' in d_lower and 'not found' in d_lower):
                        is_error_page = True
                    
                    if is_error_page:
                        job['description'] = ''
                        retry_count += 1
                        continue
                
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
                    try:
                        body_text = await page.inner_text('body')
                        type_keywords = ['Permanent', 'Contract', 'Temporary', 'Full-time', 'Full time', 'Part-time']
                        for keyword in type_keywords:
                            if keyword in body_text:
                                job['job_type'] = keyword
                                break
                    except Exception:
                        pass
                
                # Extract department
                if not job['department']:
                    try:
                        body_text = await page.inner_text('body')
                        dept_keywords = ['Cabin Crew', 'Pilot', 'Engineering', 'Ground Staff', 'Operations', 'Finance', 'IT', 'Customer Service']
                        for keyword in dept_keywords:
                            if keyword in body_text:
                                job['department'] = keyword
                                break
                    except Exception:
                        pass
                
                # Extract posted date if not already set
                if not job['posted_date']:
                    date_selectors = ['[class*="date"]', '[class*="Date"]', '[class*="posted"]', 'time']
                    for selector in date_selectors:
                        try:
                            elem = await page.query_selector(selector)
                            if elem:
                                date_text = await elem.inner_text()
                                if date_text.strip():
                                    parsed_date = self.parse_posted_date(date_text.strip())
                                    job['posted_date'] = parsed_date if parsed_date else date_text.strip()
                                    break
                        except:
                            continue

                # Additional fallback: detect posted_date via page heuristics (meta tags or JSON-LD)
                if not job.get('posted_date'):
                    try:
                        fallback_pd = await self.extract_posted_date_from_page(page)
                        if fallback_pd:
                            job['posted_date'] = fallback_pd
                    except Exception:
                        pass
                
                # Success - exit retry loop
                break
                
            except asyncio.TimeoutError:
                print(f"  Timeout for {job['job_id']} (attempt {retry_count + 1}/{max_retries})")
                retry_count += 1
            except Exception as e:
                print(f"  Error fetching description for {job['job_id']} (attempt {retry_count + 1}/{max_retries}): {e}")
                retry_count += 1
            finally:
                if page and not page.is_closed():
                    await page.close()
                if context:
                    await context.close()
