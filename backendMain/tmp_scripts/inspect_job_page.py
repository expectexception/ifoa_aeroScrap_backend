import asyncio
from playwright.async_api import async_playwright
import sys

async def inspect(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        print('Loading', url)
        try:
            await page.goto(url, timeout=60000)
        except Exception as e:
            print('Error loading page:', e)
            await browser.close()
            return

        # Print title
        title = await page.title()
        print('Title:', title)

        # Print first 500 chars of meta description
        metas = await page.query_selector_all('meta')
        for m in metas:
            name = await m.get_attribute('name')
            prop = await m.get_attribute('property')
            content = await m.get_attribute('content') or ''
            if name and 'date' in name.lower():
                print('Meta name date:', name, content)
            if prop and 'date' in prop.lower():
                print('Meta prop date:', prop, content)
            if 'description' in (name or '') or 'description' in (prop or ''):
                print('Meta description found (truncated):', content[:200])

        print('\nJSON-LD scripts (datePublished if present):')
        scripts = await page.query_selector_all('script[type="application/ld+json"]')
        for s in scripts:
            txt = (await s.inner_text())[:1000]
            if 'datePublished' in txt or 'datePosted' in txt:
                print(txt)

        print('\nTime tags:')
        times = await page.query_selector_all('time')
        for t in times[:10]:
            try:
                inner = await t.inner_text()
                attr = await t.get_attribute('datetime')
                print('time tag:', inner, attr)
            except Exception:
                continue

        # Search for text patterns in the body that contain 'Posted' or 'Published' or 'Date'
        body = await page.inner_text('body')
        found = []
        for kw in ['posted', 'published', 'date', 'posted on', 'posted:']:
            if kw in body.lower():
                found.append(kw)
        print('\nKeywords present in body:', found)

        # Check for description class containers (common ones)
        selectors = ['#jobDescription', '.jobAdBody', '.jobDescription', '.description', '.job-description', '.jobDetail', '.jobFullDescription', '.job-detail', 'article', 'main']
        for sel in selectors:
            try:
                elem = await page.query_selector(sel)
                if elem:
                    txt = await elem.inner_text()
                    print(f"Found selector {sel} text len=", len(txt))
            except Exception:
                pass

        # Print a short body snippet around 'Posted' if any
        pos = body.lower().find('posted')
        if pos >= 0:
            snippet = body[max(0,pos-100):pos+200]
            print('\nPosted snippet:', snippet.replace('\n',' ')[:400])

        await browser.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python inspect_job_page.py <url>')
        sys.exit(1)
    url = sys.argv[1]
    asyncio.run(inspect(url))
