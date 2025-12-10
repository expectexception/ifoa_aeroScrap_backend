"""
LinkedIn Jobs Scraper
Extracts aviation jobs from LinkedIn job search
"""

from playwright.async_api import async_playwright, TimeoutError
import asyncio
import time
import random
import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict
from .base_scraper import BaseScraper
from .job_schema import get_job_dict

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job postings"""

    def __init__(self, config: dict, db_manager=None):
        super().__init__(config, 'linkedin', db_manager=db_manager)
        self.search_url = "https://www.linkedin.com/jobs/search/"
        
        # Support both single values and lists
        self.default_posts = self.site_config.get('default_post', ['aviation'])
        if isinstance(self.default_posts, str):
            self.default_posts = [self.default_posts]
            
        self.default_locations = self.site_config.get('default_location', ['Worldwide'])
        if isinstance(self.default_locations, str):
            self.default_locations = [self.default_locations]

    async def dismiss_cookie_banner(self, page):
        """Try to dismiss the cookie banner if it appears"""
        try:
            await page.get_by_role("button", name="Dismiss").click(timeout=5000)
            print("Dismissed cookie banner.")
        except TimeoutError:
            print("No 'Dismiss' button found, continuing...")

    async def random_scroll_page(self, page):
        """Simulate human-like scrolling (renamed to avoid attribute name clash)"""
        scroll_amount = random.randint(200, 600)
        await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
        await asyncio.sleep(random.uniform(0.5, 1.5))

    def parse_linkedin_posted(self, text: str):
        """Normalize LinkedIn relative posted-time strings to ISO date strings when possible.

        Examples handled: '3 days ago', '1 hour ago', '30+ days ago', '2 weeks ago', '2 months ago'
        Falls back to returning the original text or None when empty.
        """
        if not text:
            return None

        t = text.strip().lower()
        now = datetime.utcnow()

        # Direct ISO date
        if re.match(r"^\d{4}-\d{2}-\d{2}$", t):
            return t

        # Hours
        m = re.search(r"(\d+)\s+hour", t)
        if m:
            try:
                return (now - timedelta(hours=int(m.group(1)))).date().isoformat()
            except Exception:
                return t

        # Days
        m = re.search(r"(\d+)\s+day", t)
        if m:
            try:
                return (now - timedelta(days=int(m.group(1)))).date().isoformat()
            except Exception:
                return t

        # Weeks
        m = re.search(r"(\d+)\s+week", t)
        if m:
            try:
                return (now - timedelta(weeks=int(m.group(1)))).date().isoformat()
            except Exception:
                return t

        # Months or '30+' fallback
        if "month" in t or "30+" in t or "+" in t:
            try:
                return (now - timedelta(days=30)).date().isoformat()
            except Exception:
                return t

        # Unknown format: return original trimmed string
        return t

    async def random_mouse_move(self, page):
        """Simulate random mouse movements"""
        x = random.randint(100, 800)
        y = random.randint(100, 600)
        await page.mouse.move(x, y)
        await asyncio.sleep(random.uniform(0.2, 0.8))

    async def scrape_linkedin_jobs(self, post_name: str, location_name: str, max_jobs: int) -> List[Dict]:
        """Scrape LinkedIn jobs for given search parameters"""
        all_jobs_data = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page, context = await self.setup_stealth_page(browser)

            try:
                # Initial navigation and load
                await page.goto(self.search_url, timeout=60000)
                print("Page loading...")
                await self.random_delay(3, 5)

                # Try to dismiss the cookie banner
                await self.dismiss_cookie_banner(page)

                await self.random_delay(1, 3)
                await self.random_scroll_page(page)
                await self.random_mouse_move(page)

                # Filling search form
                print("Filling out search form...")
                await self.random_scroll_page(page)
                await page.fill("input[id*='keywords']", post_name)
                await self.random_delay(0.5, 1.5)
                await self.random_mouse_move(page)
                await self.random_scroll_page(page)
                await page.fill("input[id*='location']", location_name)
                await self.random_delay(0.5, 1.5)
                await self.random_mouse_move(page)

                await self.random_scroll_page(page)
                await page.get_by_role("button", name="Search").click()
                print("Search button clicked. Waiting for results...")

                await self.random_delay(2, 4)
                await self.random_scroll_page(page)
                await self.random_mouse_move(page)

                # Waiting for results list
                try:
                    await page.wait_for_selector("ul.jobs-search__results-list", timeout=30000)
                    print("Job list found.")
                    await self.random_scroll_page(page)
                except TimeoutError:
                    print("Could not find job list. Page might have changed.")
                    return []

                # Get all the job cards from the left panel
                job_cards = await page.locator("ul.jobs-search__results-list div.base-search-card").all()

                print(f"Found {len(job_cards)} job cards on the page.")
                print("Scraping jobs and details one by one")

                count = 0

                # Loop through each job card
                for i, job_card in enumerate(job_cards):
                    # Check if we've already met the max_jobs before starting a new scrape
                    if count >= max_jobs:
                        print(f"Count break on {max_jobs} before starting job {i+1}")
                        break

                    await self.random_delay(4, 8)

                    job_data = {}

                    # Scrape basic info from the list card
                    try:
                        title = await job_card.locator("h3.base-search-card__title").inner_text()
                        title = title.strip()

                        company = await job_card.locator("h4.base-search-card__subtitle").inner_text()
                        company = company.strip()

                        location = await job_card.locator("span.job-search-card__location").inner_text()
                        location = location.strip()

                        link_element = job_card.locator("a.base-card__full-link")
                        link = await link_element.get_attribute("href")

                        # Link correction logic
                        if link and not link.startswith("http"):
                            link = f"https://www.linkedin.com{link}"

                        job_data['title'] = title
                        job_data['company'] = company
                        job_data['location'] = location
                        job_data['url'] = link
                        job_data['apply_url'] = link
                        job_data['source'] = self.site_key
                        job_data['job_id'] = f"linkedin_{post_name.replace(' ', '_')}_{location_name.replace(' ', '_')}_{i+1}"
                        job_data['timestamp'] = datetime.now().isoformat()

                        print(f"\nScraping job {i+1}: {title} at {company}")

                    except Exception as e:
                        print(f"Error scraping basic info for job {i+1}: {e}. Skipping card.")
                        continue

                    # Click the card and scrape the details pane
                    try:
                        # Scroll to the job card and simulate human interaction
                        await job_card.scroll_into_view_if_needed()
                        await self.random_delay(1, 2)
                        await self.random_mouse_move(page)

                        # Click the card to load the details on the right
                        await job_card.click()
                        await self.random_delay(2, 4)
                        await self.random_scroll_page(page)

                        # Wait for the details pane to update
                        await page.wait_for_selector("div.description__text", timeout=5000)

                        # Try to expand the full description
                        try:
                            show_more_button = page.locator("button:has-text('See more')").first
                            if not await show_more_button.is_visible():
                                show_more_button = page.locator("button:has-text('Show more')").first
                            if await show_more_button.is_visible():
                                await show_more_button.click()
                                await self.random_delay(1, 2)
                                print("Expanded full description")
                                await self.random_scroll_page(page)
                                await self.random_delay(1, 2)
                        except Exception as e:
                            print(f"No 'See more'/'Show more' button or error: {e}")

                        # Scrape the description and posted time
                        description_element = page.locator("div.description__text")
                        description = await description_element.inner_text()
                        description = description.strip()

                        # Posted time — make extraction robust and normalize
                        posted = None
                        try:
                            posted_element = page.locator('span.posted-time-ago__text')
                            posted_text = await posted_element.inner_text()
                            posted = posted_text.strip() if posted_text else None
                        except Exception:
                            # Attempt to read from list-card area as fallback
                            try:
                                posted_text = await job_card.locator("time").inner_text()
                                posted = posted_text.strip() if posted_text else None
                            except Exception:
                                posted = None

                        normalized_posted = self.parse_linkedin_posted(posted) if posted else None

                        job_data['description'] = description
                        job_data['posted_date'] = normalized_posted
                        print(f'Posted: {posted} -> {normalized_posted}')

                        # Scrape the job criteria
                        criteria = {}
                        criteria_items = await page.locator("li.description__job-criteria-item").all()
                        for item in criteria_items:
                            try:
                                subheader_element = item.locator("h3.description__job-criteria-subheader")
                                subheader = await subheader_element.inner_text()
                                subheader = subheader.strip()

                                text_element = item.locator("span.description__job-criteria-text")
                                text = await text_element.inner_text()
                                text = text.strip()

                                criteria[subheader] = text
                            except Exception:
                                continue

                        job_data['criteria'] = criteria

                        # Scrape additional details
                        additional_details = {}
                        try:
                            insight_items = await page.locator("div.job-details-jobs-unified-top-card__job-insight").all()
                            for item in insight_items:
                                try:
                                    text = await item.inner_text()
                                    text = text.strip()

                                    if "salary" in text.lower() or "$" in text:
                                        additional_details['salary'] = text
                                    elif "benefits" in text.lower():
                                        additional_details['benefits'] = text
                                    else:
                                        if 'other_insights' not in additional_details:
                                            additional_details['other_insights'] = []
                                        additional_details['other_insights'].append(text)
                                except Exception:
                                    continue
                        except Exception as e:
                            print(f"Error scraping additional details: {e}")

                        job_data['additional_details'] = additional_details

                        print(f"Successfully scraped details for: {title}")

                    except Exception as e:
                        print(f"Could not load or scrape details for '{title}'. Details will be blank. Error: {e}")
                        job_data['description'] = ""
                        job_data['criteria'] = {}
                        job_data['additional_details'] = {}

                    # Ensure posted_date key exists
                    job_data.setdefault('posted_date', None)

                    # Convert to canonical job dict before appending so all scrapers produce same structure
                    try:
                        job_record = get_job_dict(**job_data)
                    except Exception:
                        # If canonicalization fails for unexpected keys, fall back to raw dict but keep key names consistent
                        job_record = job_data

                    # Add this job's data to our main list
                    all_jobs_data.append(job_record)

                    # Update the count and check for the break condition
                    count += 1
                    print(f"--> Job {count} scraped. (Target: {max_jobs})")

                    # A small random delay
                    await self.random_delay(2.5, 4.5)

                    if count == max_jobs:
                        print(f"Count break reached on {max_jobs} ")
                        break

            finally:
                await context.close()
                await browser.close()

        return all_jobs_data

    async def run(self):
        """Main execution method"""
        self.print_header()

        # Get search parameters from config or use defaults
        posts = self.site_config.get('search_post', self.site_config.get('default_post', self.default_posts))
        if isinstance(posts, str):
            posts = [posts]
            
        locations = self.site_config.get('search_location', self.site_config.get('default_location', self.default_locations))
        if isinstance(locations, str):
            locations = [locations]
            
        max_jobs_per_search = self.max_jobs or 20  # Default to 20 if not set
        max_jobs_total = self.site_config.get('max_jobs_total', max_jobs_per_search * len(posts) * len(locations))

        print(f"Searching for {len(posts)} job terms in {len(locations)} locations")
        print(f"Job terms: {', '.join(posts)}")
        print(f"Locations: {', '.join(locations)}")
        print(f"Max jobs per search: {max_jobs_per_search}, Total limit: {max_jobs_total}")

        all_jobs = []
        search_count = 0
        total_searches = len(posts) * len(locations)

        # Step 1: Scrape jobs for all combinations
        for post_name in posts:
            for location_name in locations:
                search_count += 1
                print(f"\n{'='*60}")
                print(f"Search {search_count}/{total_searches}: '{post_name}' in '{location_name}'")
                print(f"{'='*60}")
                
                # Check if we've reached the total limit
                if len(all_jobs) >= max_jobs_total:
                    print(f"Reached total job limit: {max_jobs_total}")
                    break
                
                # Calculate remaining jobs for this search
                remaining_jobs = max_jobs_total - len(all_jobs)
                jobs_per_search = min(max_jobs_per_search, remaining_jobs)
                
                try:
                    jobs = await self.scrape_linkedin_jobs(post_name, location_name, jobs_per_search)
                    
                    if jobs:
                        # Add search metadata to each job
                        for job in jobs:
                            job['search_post'] = post_name
                            job['search_location'] = location_name
                        
                        all_jobs.extend(jobs)
                        print(f"✓ Found {len(jobs)} jobs for '{post_name}' in '{location_name}'")
                    else:
                        print(f"⚠️ No jobs found for '{post_name}' in '{location_name}'")
                        
                except Exception as e:
                    print(f"✗ Error scraping '{post_name}' in '{location_name}': {e}")
                    continue
                
                # Add delay between searches to avoid rate limiting
                if search_count < total_searches:
                    await self.random_delay(5, 10)  # 5-10 second delay between searches
            
            if len(all_jobs) >= max_jobs_total:
                break

        if not all_jobs:
            print("No jobs found in any search!")
            return []

        print(f"\n✓ Total scraped {len(all_jobs)} jobs from {search_count} searches")

        # Step 2: Apply title filtering BEFORE fetching full descriptions
        if self.use_filter and self.filter_manager:
            print(f"\n🔍 Applying title filter...")
            matched_jobs, rejected_jobs, filter_stats = self.apply_title_filter(all_jobs)
            
            self.filter_manager.print_filter_stats(filter_stats)
            
            if not matched_jobs:
                print("❌ No jobs matched the filter criteria")
                return []
            
            print(f"✓ {len(matched_jobs)} jobs matched filter")
            print(f"✗ {len(rejected_jobs)} jobs rejected (not relevant)")
            all_jobs = matched_jobs

        # Step 3: Filter duplicates (if database is available)
        all_jobs, duplicate_count = await self.filter_new_jobs(all_jobs)
        if duplicate_count > 0:
            print(f"\n🔄 Filtered out {duplicate_count} duplicate jobs")

        # Step 4: Save results to database
        await self.save_results(all_jobs)

        # Show sample
        self.print_sample(all_jobs)

        return all_jobs