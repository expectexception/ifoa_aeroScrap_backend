#!/usr/bin/env python3
"""
Script to capture XHR requests from IndiGo careers page, focusing on ms-careers-prod.goindigo.in
"""

import asyncio
import json
from playwright.async_api import async_playwright

JOBS_URL = "https://www.goindigo.in/careers/job-search.html?type=&location=&department="

async def capture_xhrs():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = await browser.new_context()
        page = await context.new_page()

        # Add stealth script
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US','en']});
            window.chrome = { runtime: {} };
        """)

        # List to store captured requests
        captured_requests = []

        def log_request(request):
            url = request.url
            if 'ms-careers-prod.goindigo.in' in url:
                req_data = {
                    'method': request.method,
                    'url': url,
                    'headers': dict(request.headers),
                    'post_data': request.post_data if request.post_data else None
                }
                captured_requests.append(req_data)
                print(f"Captured {request.method} {url}")

        page.on('request', log_request)

        try:
            print("Loading IndiGo careers page to capture XHRs...")
            await page.goto(JOBS_URL, wait_until='load', timeout=60000)

            # Wait for potential XHRs
            await asyncio.sleep(15)

            # Simulate some interaction to trigger requests
            await page.mouse.move(100, 100)
            await page.keyboard.press('ArrowDown')
            await asyncio.sleep(5)

            print(f"Captured {len(captured_requests)} requests to ms-careers-prod.goindigo.in")

            if captured_requests:
                print("\nRequest details:")
                for i, req in enumerate(captured_requests):
                    print(f"\nRequest {i+1}:")
                    print(f"  Method: {req['method']}")
                    print(f"  URL: {req['url']}")
                    print(f"  Headers: {json.dumps(req['headers'], indent=2)}")
                    if req['post_data']:
                        print(f"  Post Data: {req['post_data']}")

        except Exception as e:
            print(f"Error: {e}")
        finally:
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_xhrs())