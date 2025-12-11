import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to AllFlyingJobs...")
        await page.goto("https://www.allflyingjobs.com/", wait_until='domcontentloaded')
        
        # Save homepage to inspect search form
        content = await page.content()
        with open("allflyingjobs_home.html", "w") as f:
            f.write(content)
        print("Saved allflyingjobs_home.html")
        
        # Search for "Captain"
        print("Entering search query 'Captain'...")
        await page.fill('#edit-s', 'Captain')
        await page.click('#edit-submit-all-jobs-text-search')
        
        print("Waiting for results...")
        await page.wait_for_load_state('domcontentloaded')
        # Wait for at least one job row or generic result container
        try:
            await page.wait_for_selector('div.views-row', timeout=10000)
        except:
            print("Warning: No views-row found, possibly no results or different structure.")

        content = await page.content()
        with open("allflyingjobs_results.html", "w") as f:
            f.write(content)
        print("Saved allflyingjobs_results.html")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
