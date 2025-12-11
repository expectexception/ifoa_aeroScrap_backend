import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright
import os

async def save_page_source(url, name):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a stealthy context
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        print(f"Loading {name}: {url}")
        try:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await page.wait_for_timeout(5000) # strict wait for dynamic content
            
            # Save HTML
            content = await page.content()
            filename = f"snapshot_{name}.html"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Saved {filename} ({len(content)} bytes)")
            
            # Screenshot for debugging visual layout
            await page.screenshot(path=f"snapshot_{name}.png")
            print(f"Saved snapshot_{name}.png")
            
        except Exception as e:
            print(f"Error loading {name}: {e}")
        finally:
            await browser.close()

async def main():
    targets = [
        ('aap', 'https://jobs.aapaviation.com/jobs'),
        ('cargolux', 'https://careers.peopleclick.eu.com/careerscp/client_cargolux/external/results/searchResult.html'),
        ('indigo', 'https://www.goindigo.in/careers/job-search.html')
    ]
    
    for name, url in targets:
        await save_page_source(url, name)

if __name__ == '__main__':
    asyncio.run(main())
