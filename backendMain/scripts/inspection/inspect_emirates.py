import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from playwright.sync_api import sync_playwright
import time

def inspect():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        print("Navigating to Emirates Group Careers...")
        page.goto("https://www.emiratesgroupcareers.com/", timeout=60000)
        time.sleep(5)
        
        # Save homepage
        with open("emirates_home.html", "w") as f:
            f.write(page.content())
        print("Saved emirates_home.html")
        
        # Take a screenshot to see the layout
        page.screenshot(path="emirates_home.png")
        
        # Try to find a search input
        # Common search selectors
        search_selectors = ['input[type="search"]', 'input[placeholder*="search"]', 'input[placeholder*="Search"]', '#search', '.search-input']
        
        search_input = None
        for sel in search_selectors:
            if page.is_visible(sel):
                search_input = sel
                print(f"Found search input: {sel}")
                break
        
        if search_input:
            print("Entering search query 'Pilot'...")
            page.fill(search_input, "Pilot")
            page.keyboard.press("Enter")
            time.sleep(10)
            
            with open("emirates_results.html", "w") as f:
                f.write(page.content())
            print("Saved emirates_results.html")
            page.screenshot(path="emirates_results.png")
        else:
            print("Could not find a generic search input directly. Check the HTML.")
            
        browser.close()

if __name__ == "__main__":
    inspect()
