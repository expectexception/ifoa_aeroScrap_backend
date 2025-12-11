import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright
import os

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        url = "https://www.emiratesgroupcareers.com/search-and-apply/"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Take screenshot
            await page.screenshot(path='emirates_search.png', full_page=True)
            print("Saved screenshot to emirates_search.png")
            
            # Save HTML
            content = await page.content()
            with open('emirates_search.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Saved HTML to emirates_search.html")
            
            # Handle Cookie Banner
            try:
                print("Waiting for cookie banner...")
                accept_btn = await page.wait_for_selector('#onetrust-accept-btn-handler', timeout=5000)
                if accept_btn:
                    await accept_btn.click()
                    print("Clicked Accept Cookies")
                    await page.wait_for_selector('#onetrust-banner-sdk', state='hidden', timeout=5000)
                    print("Cookie banner hidden")
            except Exception as e:
                print(f"Cookie banner handling skipped: {e}")

            # Try to identify search elements
            search_input = await page.query_selector('input.search-jobs__control')
            
            if search_input:
                print(f"Found input: {await search_input.get_attribute('class')}")
            
            # Click the first job card
            print("Clicking first job card...")
            
            # Setup popup listener
            async with context.expect_page() as new_page_info:
                # We need to click an element that is clickable inside the card. Maybe the title?
                await page.click('section.job-card .job-card__title')
                # Or maybe the card itself
                # await page.click('section.job-card')

            new_page = await new_page_info.value
            await new_page.waitForLoadState()
            print(f"New page opened: {new_page.url}")
            
        except Exception as e:
            print(f"Error: {e}")
            if "Timeout" in str(e):
                print("Click did not open a new page.")
                print(f"Current URL: {page.url}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
