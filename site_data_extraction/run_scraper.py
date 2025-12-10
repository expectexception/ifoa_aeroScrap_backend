"""
Multi-site Aviation Job Scraper Runner
Run with: python run_scraper.py [site_name]
Examples:
  python run_scraper.py signature
  python run_scraper.py flygosh
  python run_scraper.py all
"""

import asyncio
import sys
from scrapers import get_scraper, list_scrapers
from config import CONFIG


async def run_site(site_name: str):
    """Run scraper for a specific site"""
    
    site_config = CONFIG['sites'].get(site_name)
    
    if not site_config:
        print(f"Error: Site '{site_name}' not found in config")
        print(f"Available sites: {list_scrapers()}")
        return []
    
    if not site_config.get('enabled', True):
        print(f"Site '{site_name}' is disabled in config")
        return []
    
    print(f"\n{'='*60}")
    print(f"Running scraper for: {site_config['name']}")
    print(f"{'='*60}\n")
    
    try:
        scraper = get_scraper(site_name, CONFIG)
        jobs = await scraper.run()
        
        print(f"\n{'='*60}")
        print(f"✓ {site_config['name']} Complete!")
        print(f"Total jobs extracted: {len(jobs)}")
        print(f"{'='*60}")
        
        return jobs
        
    except Exception as e:
        print(f"\n✗ Error running {site_name} scraper: {e}")
        return []


async def run_all_sites():
    """Run scrapers for all enabled sites"""
    
    sites = [site for site, config in CONFIG['sites'].items() if config.get('enabled', True)]
    
    print(f"\n{'='*60}")
    print(f"Running scrapers for {len(sites)} sites")
    print(f"{'='*60}\n")
    
    all_results = {}
    
    for site_name in sites:
        jobs = await run_site(site_name)
        all_results[site_name] = jobs
        print()
    
    # Summary
    print(f"\n{'='*60}")
    print("ALL SITES COMPLETE - SUMMARY")
    print(f"{'='*60}")
    
    total_jobs = 0
    for site_name, jobs in all_results.items():
        site_config = CONFIG['sites'][site_name]
        print(f"  {site_config['name']}: {len(jobs)} jobs")
        total_jobs += len(jobs)
    
    print(f"\nTotal jobs extracted: {total_jobs}")
    print(f"{'='*60}\n")
    
    return all_results


async def main():
    """Main entry point"""
    
    # Get site name from command line
    if len(sys.argv) > 1:
        site_name = sys.argv[1].lower()
    else:
        print("Usage: python run_scraper.py [site_name]")
        print(f"Available sites: {', '.join(list_scrapers())}, all")
        print(f"\nExample: python run_scraper.py signature")
        print(f"Example: python run_scraper.py all")
        sys.exit(1)
    
    if site_name == 'all':
        await run_all_sites()
    else:
        await run_site(site_name)


if __name__ == '__main__':
    asyncio.run(main())
