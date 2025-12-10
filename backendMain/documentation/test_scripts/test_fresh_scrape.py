#!/usr/bin/env python3
"""
Fresh Scrape Test - Clean DB + Air India + Aviation scrapers
"""
import os
import sys
import time
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from scraper_manager.scrapers.aviation_scraper import onCallWorker as aviation_worker
from scraper_manager.scrapers.airindia_scraper import onCallWorker as airindia_worker
from scraper_manager.services import ScraperService
from jobs.models import Job, CompanyMapping

def main():
    print('🚀 Starting Fresh Scraper Test')
    print('='*70)
    print('Configuration:')
    print('  • Scrapers: Air India, Aviation Job Search')
    print('  • Max Pages: 2 per scraper')
    print('  • Max Jobs: 50 per scraper')
    print('='*70)
    print()
    
    # Air India
    print('⏱️  Starting Air India scraper...')
    start_ai = time.time()
    
    try:
        airindia_jobs = airindia_worker(max_pages=2, max_jobs=50)
        print(f'  ✅ Air India: {len(airindia_jobs)} jobs scraped')
        
        airindia_stats = ScraperService._save_jobs_to_db(airindia_jobs, 'Air India')
        airindia_time = time.time() - start_ai
        
        print(f'    📊 New: {airindia_stats["new"]}, Updated: {airindia_stats["updated"]}, Duplicates: {airindia_stats["duplicates"]}, Errors: {airindia_stats["errors"]}')
        print(f'    ⏱️  Duration: {airindia_time:.2f}s')
    except Exception as e:
        print(f'  ❌ Air India Error: {e}')
        import traceback
        traceback.print_exc()
        airindia_stats = {'new': 0, 'updated': 0, 'duplicates': 0, 'errors': 1}
        airindia_time = time.time() - start_ai
    
    print()
    
    # Aviation Job Search
    print('⏱️  Starting Aviation Job Search scraper...')
    start_av = time.time()
    
    try:
        aviation_jobs = aviation_worker(max_pages=2, max_jobs=50)
        print(f'  ✅ Aviation: {len(aviation_jobs)} jobs scraped')
        
        aviation_stats = ScraperService._save_jobs_to_db(aviation_jobs, 'Aviation Job Search')
        aviation_time = time.time() - start_av
        
        print(f'    📊 New: {aviation_stats["new"]}, Updated: {aviation_stats["updated"]}, Duplicates: {aviation_stats["duplicates"]}, Errors: {aviation_stats["errors"]}')
        print(f'    ⏱️  Duration: {aviation_time:.2f}s')
    except Exception as e:
        print(f'  ❌ Aviation Error: {e}')
        import traceback
        traceback.print_exc()
        aviation_stats = {'new': 0, 'updated': 0, 'duplicates': 0, 'errors': 1}
        aviation_time = time.time() - start_av
    
    print()
    print('='*70)
    print('✅ SCRAPING COMPLETED')
    print('='*70)
    
    # Database analysis
    total_jobs = Job.objects.count()
    total_mappings = CompanyMapping.objects.count()
    auto_created = CompanyMapping.objects.filter(auto_created=True).count()
    needs_review = CompanyMapping.objects.filter(needs_review=True).count()
    jobs_linked = Job.objects.exclude(company_id__isnull=True).count()
    
    print(f'\n📊 Database Status:')
    print(f'  • Total Jobs: {total_jobs}')
    print(f'  • Total Company Mappings: {total_mappings}')
    print(f'  • Auto-created Mappings: {auto_created}')
    print(f'  • Needs Review: {needs_review}')
    print(f'  • Jobs Linked: {jobs_linked}/{total_jobs} ({jobs_linked/total_jobs*100:.1f}%)' if total_jobs > 0 else '  • Jobs Linked: 0/0')
    
    if auto_created > 0:
        print(f'\n🤖 Auto-created Company Mappings:')
        for mapping in CompanyMapping.objects.filter(auto_created=True).order_by('-created_at')[:15]:
            review = '⚠️' if mapping.needs_review else '✓'
            print(f'  {review} {mapping.company_name} ({mapping.total_jobs} jobs) - {mapping.operation_type or "?"}, {mapping.country_code or "?"}')
    
    # Check for unlinked jobs
    unlinked = Job.objects.filter(company_id__isnull=True).count()
    if unlinked > 0:
        print(f'\n⚠️  WARNING: {unlinked} jobs not linked to mappings!')
        print('   Sample unlinked jobs:')
        for job in Job.objects.filter(company_id__isnull=True)[:5]:
            print(f'     • {job.company} - {job.title[:50]}')
    
    total_time = airindia_time + aviation_time
    print(f'\n⏱️  Total Duration: {total_time:.2f}s')
    if total_jobs > 0:
        print(f'⚡ Jobs per second: {total_jobs/total_time:.2f}')
    
    # Error summary
    total_errors = airindia_stats.get('errors', 0) + aviation_stats.get('errors', 0)
    if total_errors > 0:
        print(f'\n❌ Total Errors: {total_errors}')
        print('   Check logs for details')
    else:
        print(f'\n✅ No errors detected!')
    
    print('\n' + '='*70)
    print('Test completed successfully!')
    print('='*70)

if __name__ == '__main__':
    main()
