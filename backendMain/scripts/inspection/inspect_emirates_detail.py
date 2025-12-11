import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    
        )
        
        url = "https://www.emiratesgroupcareers.com/search-and-apply/267"
        print(f"Navigating to {url}...")
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            print("Navigation successful.")
            
            # Save HTML
            content = await page.content()
            with open('emirates_detail.html', 'w', encoding='utf-8') as f:
                f.write(content)
            print("Saved HTML to emirates_detail.html")
            
            # Check for title and description
            title = await page.query_selector('h1')
            if title:
                print(f"Title: {await title.text_content()}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
