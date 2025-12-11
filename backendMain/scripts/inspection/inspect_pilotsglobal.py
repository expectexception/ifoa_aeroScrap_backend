import asyncio
from playwright.async_api import async_playwright
import sys
import os

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to PilotsGlobal...")
        # Try generic jobs page first to see structure
        await page.goto("https://pilotsglobal.com/jobs", wait_until="networkidle")
        
        print(f"Current URL: {page.url}")
        
        # Take screenshot of main page
        await page.screenshot(path="temp_artifacts/pilotsglobal_main.png")
        
        # Try to find search Inputs
        inputs = await page.evaluate('''() => {
            return Array.from(document.querySelectorAll('input')).map(i => ({
                id: i.id,
                name: i.name,
                placeholder: i.placeholder,
                type: i.type
            }));
        }''')
        print("Inputs found:", inputs)
        
        # Check if we can filter by URL injection e.g. /jobs/[country]
        # Let's try navigating to a location specific URL
        print("Testing location URL navigation...")
        await page.goto("https://pilotsglobal.com/jobs/united-states", wait_until="networkidle")
        print(f"Location URL: {page.url}")
        
        # Capture Content
        content = await page.content()
        with open("temp_artifacts/pilotsglobal_search.html", "w") as f:
            f.write(content)
            
        # Count job cards
        job_count = await page.evaluate("document.querySelectorAll('.job-card, .job-item, .card').length") 
        # Note: Class names are guesses, we'll check HTML.
        
        print(f"Inspection complete. URL: {page.url}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
