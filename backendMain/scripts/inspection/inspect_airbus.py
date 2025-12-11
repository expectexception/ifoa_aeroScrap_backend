import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import asyncio
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("Navigating to Airbus Workday site...")
        # Capture network requests to find API
        page.on("request", lambda request: print(f"Request: {request.url}") if "wday/cxs" in request.url else None)
        
        await page.goto("https://ag.wd3.myworkdayjobs.com/Airbus", wait_until="networkidle")
        
        # Save HTML
        content = await page.content()
        with open("airbus_search.html", "w") as f:
            f.write(content)
            
        # Screenshot
        await page.screenshot(path="airbus_search.png")
        
        print("Inspection complete. Saved airbus_search.html and airbus_search.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect())
