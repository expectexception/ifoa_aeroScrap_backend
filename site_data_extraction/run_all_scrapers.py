"""
Main Runner for All Aviation Job Scrapers
Runs all enabled scrapers, tracks URLs in database, and generates consolidated output
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

from config import CONFIG
from db_manager import JobDatabaseManager
from scrapers import get_scraper


async def run_single_scraper(scraper_name: str, db_manager: JobDatabaseManager):
    """Run a single scraper with database tracking"""
    try:
        print(f"\n{'='*70}")
        print(f"Starting: {scraper_name}")
        print(f"{'='*70}")
        
        scraper = get_scraper(scraper_name, CONFIG, db_manager=db_manager)
        if not scraper:
            print(f"❌ Scraper '{scraper_name}' not found")
            return None
        
        results = await scraper.run()
        
        print(f"\n{'='*70}")
        print(f"✓ {scraper_name} Complete!")
        print(f"{'='*70}\n")
        
        return results
        
    except Exception as e:
        print(f"\n❌ Error running {scraper_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


async def run_all_scrapers(db_manager: JobDatabaseManager, scraper_list=None):
    """Run all enabled scrapers"""
    
    # Get list of scrapers to run
    if scraper_list:
        scrapers_to_run = scraper_list
    else:
        scrapers_to_run = [
            name for name, site in CONFIG['sites'].items()
            if site.get('enabled', False)
        ]
    
    if not scrapers_to_run:
        print("❌ No enabled scrapers found!")
        return
    
    print("="*70)
    print("🚀 AVIATION JOB SCRAPER - BATCH RUN")
    print("="*70)
    print(f"\nScrapers to run: {', '.join(scrapers_to_run)}")
    print(f"Database: jobs.db")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Run all scrapers
    results = []
    for scraper_name in scrapers_to_run:
        result = await run_single_scraper(scraper_name, db_manager)
        if result:
            results.append((scraper_name, result))
        
        # Small delay between scrapers
        if scraper_name != scrapers_to_run[-1]:
            await asyncio.sleep(2)
    
    return results


def generate_final_output(db_manager: JobDatabaseManager, output_file='job_output.json'):
    """Generate consolidated job output from database"""
    print("\n" + "="*70)
    print("📝 GENERATING FINAL OUTPUT")
    print("="*70)
    
    try:
        # Export all jobs to final JSON
        count, path = db_manager.export_to_json(output_file)
        
        print(f"\n✓ Successfully exported {count} jobs to {path}")
        
        # Print statistics
        db_manager.print_statistics()
        
        return path
        
    except Exception as e:
        print(f"❌ Error generating final output: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main execution function"""
    
    # Initialize database
    db_manager = JobDatabaseManager('jobs.db')
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == 'stats':
            # Just show statistics
            db_manager.print_statistics()
            return
        elif sys.argv[1] == 'export':
            # Just export to JSON
            output_file = sys.argv[2] if len(sys.argv) > 2 else 'job_output.json'
            generate_final_output(db_manager, output_file)
            return
        elif sys.argv[1] == 'all':
            # Run all enabled scrapers
            scraper_list = None
        else:
            # Run specific scrapers
            scraper_list = sys.argv[1:]
    else:
        # Default: run all enabled scrapers
        scraper_list = None
    
    # Run scrapers
    start_time = datetime.now()
    results = await run_all_scrapers(db_manager, scraper_list)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Generate final consolidated output
    output_path = generate_final_output(db_manager, 'job_output.json')
    
    # Final summary
    print("\n" + "="*70)
    print("🎉 ALL SCRAPERS COMPLETE!")
    print("="*70)
    print(f"\nTotal duration: {duration:.1f}s")
    if output_path:
        print(f"Final output: {output_path}")
    print("\nTo view statistics: python run_all_scrapers.py stats")
    print("To export again: python run_all_scrapers.py export [filename]")
    print("="*70 + "\n")


if __name__ == '__main__':
    asyncio.run(main())
