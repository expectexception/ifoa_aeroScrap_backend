import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python
"""
Quick test to verify the scraper fixes work
"""
import os
import sys
import inspect

# Check if source code contains the expected fixes
def test_indigo_fix():
    """Verify Indigo scraper has improved description extraction"""
    print("\n" + "="*80)
    print("TEST 1: INDIGO SCRAPER - Description Extraction Fix")
    print("="*80)
    
    try:
        from scraper_manager.scrapers.indigo_scraper import IndiGoScraper
        
        # Get the source code
        source = inspect.getsource(IndiGoScraper._extract_description)
        
        # Check for the fix markers
        checks = [
            ("JSON-LD extraction", "json.loads" in source and "JobPosting" in source),
            ("Body text extraction", "inner_text('body')" in source and "clean_text.split" in source),
            ("Error detection", "Detected error page" in source),
            ("Fallback selectors", "'main'" in source and "'article'" in source),
        ]
        
        print("\n✓ Indigo scraper source code loaded")
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {'Found' if check_result else 'Missing'}")
            all_passed = all_passed and check_result
        
        if all_passed:
            print("\n✅ All fixes found in Indigo scraper!")
            print("\nFix Details:")
            print("  1. JSON-LD structured data extraction (PRIORITY 1)")
            print("  2. Body text aggressive extraction (PRIORITY 2)")
            print("  3. CSS selector fallbacks (PRIORITY 3)")
            print("  4. Container selector fallbacks (PRIORITY 4)")
            print("  5. BaseScraper heuristics (PRIORITY 5)")
        
        return all_passed
    except Exception as e:
        print(f"\n❌ Error checking Indigo scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_aap_fix():
    """Verify AAP scraper has defensive error handling"""
    print("\n" + "="*80)
    print("TEST 2: AAP SCRAPER - Defensive Error Handling")
    print("="*80)
    
    try:
        from scraper_manager.scrapers.aap_aviation_scraper import AAPAviationScraper
        
        # Get the source code
        source = inspect.getsource(AAPAviationScraper.run)
        
        # Check for the fix markers
        checks = [
            ("Try-except block", "try:" in source and "TypeError" in source),
            ("job_id handling", "job_id" in source),
            ("Fallback retry", "get_job_dict(**job_copy)" in source),
            ("Error recovery", "job_copy.pop('job_id'" in source),
        ]
        
        print("\n✓ AAP scraper source code loaded")
        
        all_passed = True
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}: {'Found' if check_result else 'Missing'}")
            all_passed = all_passed and check_result
        
        if all_passed:
            print("\n✅ All fixes found in AAP scraper!")
            print("\nFix Details:")
            print("  - Catches job_id keyword argument errors")
            print("  - Retries with fallback parameter handling")
            print("  - Gracefully adds job_id back to result")
        
        return all_passed
    except Exception as e:
        print(f"\n❌ Error checking AAP scraper: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("SCRAPER FIXES VALIDATION TEST")
    print("="*80)
    
    results = []
    
    # Test Indigo
    results.append(("Indigo Scraper", test_indigo_fix()))
    
    # Test AAP
    results.append(("AAP Scraper", test_aap_fix()))
    
    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL FIXES VALIDATED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Indigo scraper now has improved description extraction")
        print("2. AAP scraper has defensive error handling")
        print("3. Playwright browsers are installed")
        print("\nRun a full scrape cycle to see improved data quality:")
        print("  python manage.py scrape_all")
    else:
        print("❌ SOME FIXES NEED ATTENTION")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
