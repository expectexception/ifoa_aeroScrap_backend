import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright
import time

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        url = "https://jobs.boeing.com/search-jobs"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            print("Navigation successful.")
            
            # Save HTML
            content = await page.content()
            with open('boeing_search.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Saved HTML to boeing_search.html")
            await page.screenshot(path='boeing_search.png')
            print("Saved screenshot to boeing_search.png")
            
            # Identify search inputs
            keyword_input = await page.query_selector('input[type="text"]') 
            # Often generic, we might need specific attributes
            
            inputs = await page.query_selector_all('input')
            print(f"Found {len(inputs)} input elements.")
            for i, inp in enumerate(inputs):
                attr_id = await inp.get_attribute('id')
                attr_name = await inp.get_attribute('name')
                attr_class = await inp.get_attribute('class')
                print(f"Input {i}: id='{attr_id}', name='{attr_name}', class='{attr_class}'")
            
            # Check for generic job cards
            cards = await page.query_selector_all('section, div.card, li.job-listing, tr')
            print(f"Potential job containers found (generic check): {len(cards)}")

        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
