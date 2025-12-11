import sys; import os; sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
#!/usr/bin/env python3
"""
Test script to verify scraper parameter enforcement fixes
Tests that max_pages and max_jobs are properly respected
"""
import os
import sys
import django
import logging
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from scraper_manager.services import ScraperService
from scraper_manager.models import ScraperJob

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_aviation_scraper_max_jobs():
    """Test that aviation scraper stops at max_jobs limit"""
    logger.info("\n" + "="*60)
    logger.info("TEST 1: Aviation Scraper with max_jobs=5")
    logger.info("="*60)
    
    job = ScraperJob.objects.create(
        scraper_name='aviation',
        status='pending',
        triggered_by='test_script'
    )
    
    try:
        result = ScraperService.run_scraper(
            'aviation',
            job,
            max_pages=2,  # Allow 2 pages
            max_jobs=5    # But stop at 5 jobs
        )
        
        job.refresh_from_db()
        
        logger.info(f"Result: {result}")
        logger.info(f"Jobs found: {job.jobs_found}")
        logger.info(f"Jobs new: {job.jobs_new}")
        logger.info(f"Status: {job.status}")
        
        # Verify max_jobs was enforced
        if job.jobs_found <= 5:
            logger.info("✅ PASS: Aviation scraper respected max_jobs limit")
            return True
        else:
            logger.error(f"❌ FAIL: Aviation scraper exceeded max_jobs (found {job.jobs_found} > 5)")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def test_airindia_scraper_max_jobs():
    """Test that Air India scraper stops at max_jobs limit"""
    logger.info("\n" + "="*60)
    logger.info("TEST 2: Air India Scraper with max_jobs=3")
    logger.info("="*60)
    
    job = ScraperJob.objects.create(
        scraper_name='airindia',
        status='pending',
        triggered_by='test_script'
    )
    
    try:
        result = ScraperService.run_scraper(
            'airindia',
            job,
            max_pages=2,
            max_jobs=3
        )
        
        job.refresh_from_db()
        
        logger.info(f"Result: {result}")
        logger.info(f"Jobs found: {job.jobs_found}")
        logger.info(f"Status: {job.status}")
        
        if job.jobs_found <= 3:
            logger.info("✅ PASS: Air India scraper respected max_jobs limit")
            return True
        else:
            logger.error(f"❌ FAIL: Air India scraper exceeded max_jobs (found {job.jobs_found} > 3)")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def test_linkedin_scraper_max_jobs():
    """Test that LinkedIn scraper respects max_jobs"""
    logger.info("\n" + "="*60)
    logger.info("TEST 3: LinkedIn Scraper with max_jobs=3")
    logger.info("="*60)
    
    job = ScraperJob.objects.create(
        scraper_name='linkedin',
        status='pending',
        triggered_by='test_script'
    )
    
    try:
        result = ScraperService.run_scraper(
            'linkedin',
            job,
            max_jobs=3
        )
        
        job.refresh_from_db()
        
        logger.info(f"Result: {result}")
        logger.info(f"Jobs found: {job.jobs_found}")
        logger.info(f"Status: {job.status}")
        
        if job.jobs_found <= 3:
            logger.info("✅ PASS: LinkedIn scraper respected max_jobs limit")
            return True
        else:
            logger.error(f"❌ FAIL: LinkedIn scraper exceeded max_jobs (found {job.jobs_found} > 3)")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def test_async_execution():
    """Test that async scraper execution works properly"""
    logger.info("\n" + "="*60)
    logger.info("TEST 4: Async Scraper Execution")
    logger.info("="*60)
    
    job = ScraperJob.objects.create(
        scraper_name='aviation',
        status='pending',
        triggered_by='test_script_async'
    )
    
    try:
        future = ScraperService.run_scraper_async(
            'aviation',
            job.id,
            max_pages=1,
            max_jobs=2
        )
        
        logger.info(f"Scraper submitted to thread pool, waiting for completion...")
        
        # Wait for completion (with timeout)
        result = future.result(timeout=120)
        
        job.refresh_from_db()
        
        logger.info(f"Result: {result}")
        logger.info(f"Jobs found: {job.jobs_found}")
        logger.info(f"Status: {job.status}")
        
        if job.status == 'completed' and job.jobs_found <= 2:
            logger.info("✅ PASS: Async execution completed successfully")
            return True
        else:
            logger.error(f"❌ FAIL: Async execution issue (status={job.status}, jobs={job.jobs_found})")
            return False
            
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def test_resume_parser():
    """Test that resume parser is properly initialized"""
    logger.info("\n" + "="*60)
    logger.info("TEST 5: Resume Parser Initialization")
    logger.info("="*60)
    
    try:
        from resumes.utils import parser
        
        if parser is None:
            logger.error("❌ FAIL: Resume parser is None")
            return False
        
        logger.info(f"Parser type: {type(parser)}")
        logger.info(f"Config available: {bool(parser.config)}")
        
        if parser.config:
            logger.info(f"Skills in config: {len(parser.config.get('skills', {}))}")
            logger.info(f"Aviation certs: {len(parser.config.get('aviation', {}).get('certifications', []))}")
        
        logger.info("✅ PASS: Resume parser initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ ERROR: {e}", exc_info=True)
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "#"*60)
    logger.info("# SCRAPER PARAMETER ENFORCEMENT TEST SUITE")
    logger.info("#"*60)
    
    results = {
        'Aviation max_jobs': test_aviation_scraper_max_jobs(),
        'AirIndia max_jobs': test_airindia_scraper_max_jobs(),
        'LinkedIn max_jobs': test_linkedin_scraper_max_jobs(),
        'Async execution': test_async_execution(),
        'Resume parser': test_resume_parser(),
    }
    
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 ALL TESTS PASSED!")
        return 0
    else:
        logger.error(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
