"""
Django management command to run scrapers
Usage: python manage.py run_scraper [scraper_name] [options]
"""

import asyncio
import sys
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand
from django.utils import timezone
from asgiref.sync import sync_to_async
from scraper_manager.models import ScraperJob, ScraperConfig
from scraper_manager.config import CONFIG
from scraper_manager.db_manager import DjangoDBManager
from scraper_manager.scrapers import get_scraper, list_scrapers

# Setup logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run aviation job scrapers'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'scraper',
            nargs='?',
            type=str,
            help='Scraper name (signature, flygosh, aviationindeed, aap, indigo, aviationjobsearch, goose, linkedin, all)'
        )
        parser.add_argument(
            '--max-jobs',
            type=int,
            help='Maximum number of jobs to scrape'
        )
        parser.add_argument(
            '--max-pages',
            type=int,
            help='Maximum number of pages to scrape'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all available scrapers'
        )
    
    def handle(self, *args, **options):
        # Setup logging for this command
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # List scrapers
        if options['list']:
            self.list_available_scrapers()
            return
        
        scraper_name = options.get('scraper')
        if not scraper_name:
            self.stdout.write(self.style.ERROR('Please specify a scraper name or --list'))
            self.stdout.write('Usage: python manage.py run_scraper [scraper_name]')
            self.stdout.write(f'Available: {", ".join(list_scrapers())}, all')
            return
        
        logger.info(f"Starting scraper command: {scraper_name}")
        
        # Run scraper
        if scraper_name == 'all':
            asyncio.run(self.run_all_scrapers(options))
        else:
            asyncio.run(self.run_single_scraper(scraper_name, options))
    
    def list_available_scrapers(self):
        """List all available scrapers"""
        self.stdout.write(self.style.SUCCESS('\n📋 Available Scrapers:\n'))
        
        for scraper_name in list_scrapers():
            site_config = CONFIG['sites'].get(scraper_name, {})
            enabled = site_config.get('enabled', False)
            status = self.style.SUCCESS('✓ Enabled') if enabled else self.style.WARNING('✗ Disabled')
            
            self.stdout.write(f"  • {scraper_name:20s} - {site_config.get('name', 'N/A'):30s} {status}")
        
        self.stdout.write('')
    
    async def run_single_scraper(self, scraper_name: str, options: dict):
        """Run a single scraper"""
        
        logger.info(f"Preparing to run scraper: {scraper_name}")
        
        # Check if scraper exists
        if scraper_name not in list_scrapers():
            error_msg = f'Unknown scraper: {scraper_name}'
            logger.error(error_msg)
            self.stdout.write(self.style.ERROR(error_msg))
            self.stdout.write(f'Available: {", ".join(list_scrapers())}')
            return
        
        # Check if enabled
        site_config = CONFIG['sites'].get(scraper_name, {})
        if not site_config.get('enabled', False):
            warning_msg = f'Scraper "{scraper_name}" is disabled in config'
            logger.warning(warning_msg)
            self.stdout.write(self.style.WARNING(warning_msg))
            return
        
        # Override config with command line options
        # Allow explicit 0 to mean 'no limit' (unlimited) - preserve explicit None handling
        if options.get('max_jobs') is not None:
            CONFIG['scrapers'][scraper_name]['max_jobs'] = options['max_jobs']
            logger.info(f"Override max_jobs: {options['max_jobs']}")
        if options.get('max_pages') is not None:
            CONFIG['scrapers'][scraper_name]['max_pages'] = options['max_pages']
            logger.info(f"Override max_pages: {options['max_pages']}")
        
        # Create ScraperJob
        scraper_job = await sync_to_async(ScraperJob.objects.create)(
            scraper_name=scraper_name,
            status='running',
            started_at=timezone.now(),
            triggered_by='management_command',
            parameters={
                'max_jobs': options.get('max_jobs'),
                'max_pages': options.get('max_pages'),
            }
        )
        
        logger.info(f"Created ScraperJob with ID: {scraper_job.id}")
        self.stdout.write(self.style.SUCCESS(f'\n🚀 Starting scraper: {scraper_name} (Job ID: {scraper_job.id})'))
        
        try:
            # Initialize database manager
            db_manager = DjangoDBManager()
            logger.info(f"Initialized DjangoDBManager for {scraper_name}")
            
            # Get scraper instance
            scraper = get_scraper(scraper_name, CONFIG, db_manager=db_manager)
            logger.info(f"Created scraper instance for {scraper_name}")
            
            # Run scraper
            logger.info(f"Starting scraper execution for {scraper_name}")
            jobs = await scraper.run()
            logger.info(f"Scraper execution completed, found {len(jobs)} jobs")
            
            # Update ScraperJob
            scraper_job.status = 'completed'
            scraper_job.completed_at = timezone.now()
            scraper_job.jobs_found = len(jobs)
            
            # Calculate stats from database
            stats = {
                'total': len(jobs),
                'new': sum(1 for j in jobs if j.get('_is_new', False)),
                'updated': sum(1 for j in jobs if not j.get('_is_new', True)),
            }
            
            scraper_job.jobs_new = stats['new']
            scraper_job.jobs_updated = stats['updated']
            scraper_job.jobs_duplicate = stats['total'] - stats['new']
            scraper_job.execution_time = (scraper_job.completed_at - scraper_job.started_at).total_seconds()
            await sync_to_async(scraper_job.save)()
            
            logger.info(f"Updated ScraperJob {scraper_job.id}: "
                       f"found={scraper_job.jobs_found}, new={scraper_job.jobs_new}, "
                       f"updated={scraper_job.jobs_updated}, time={scraper_job.execution_time:.1f}s")
            
            # Update config stats - create default ScraperConfig if missing
            try:
                site_cfg = CONFIG['sites'].get(scraper_name, {})
                defaults = {
                    'is_enabled': site_cfg.get('enabled', True),
                    'max_jobs': site_cfg.get('max_jobs'),
                    'max_pages': site_cfg.get('max_pages'),
                    'description': site_cfg.get('description', ''),
                }
                config, created = await sync_to_async(ScraperConfig.objects.get_or_create)(scraper_name=scraper_name, defaults=defaults)
                await sync_to_async(config.update_stats)(success=True)
                if created:
                    logger.info(f"Created default ScraperConfig for {scraper_name}")
                logger.debug(f"Updated ScraperConfig stats for {scraper_name}")
            except Exception as e:
                logger.warning(f"Failed to update/create ScraperConfig for {scraper_name}: {e}")
            
            self.stdout.write(self.style.SUCCESS(f'\n✓ Scraper completed successfully'))
            self.stdout.write(f'  Jobs found: {scraper_job.jobs_found}')
            self.stdout.write(f'  Jobs new: {scraper_job.jobs_new}')
            self.stdout.write(f'  Jobs updated: {scraper_job.jobs_updated}')
            self.stdout.write(f'  Duration: {scraper_job.execution_time:.1f}s')
            
        except Exception as e:
            logger.error(f"Scraper {scraper_name} failed: {e}", exc_info=True)
            
            scraper_job.status = 'failed'
            scraper_job.completed_at = timezone.now()
            scraper_job.error_message = str(e)
            await sync_to_async(scraper_job.save)()
            
            # Update config stats (ensure config exists)
            try:
                site_cfg = CONFIG['sites'].get(scraper_name, {})
                defaults = {
                    'is_enabled': site_cfg.get('enabled', True),
                    'max_jobs': site_cfg.get('max_jobs'),
                    'max_pages': site_cfg.get('max_pages'),
                    'description': site_cfg.get('description', ''),
                }
                config, created = await sync_to_async(ScraperConfig.objects.get_or_create)(scraper_name=scraper_name, defaults=defaults)
                await sync_to_async(config.update_stats)(success=False)
                if created:
                    logger.info(f"Created default ScraperConfig for {scraper_name} due to failure path")
            except Exception as e2:
                logger.warning(f"Failed to update/create ScraperConfig for {scraper_name}: {e2}")
            
            self.stdout.write(self.style.ERROR(f'\n✗ Scraper failed: {e}'))
            import traceback
            traceback.print_exc()
    
    async def run_all_scrapers(self, options: dict):
        """Run all enabled scrapers"""
        
        enabled_scrapers = [
            name for name, site in CONFIG['sites'].items()
            if site.get('enabled', False)
        ]
        
        if not enabled_scrapers:
            self.stdout.write(self.style.WARNING('No enabled scrapers found'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'\n🚀 Running {len(enabled_scrapers)} scrapers'))
        
        for scraper_name in enabled_scrapers:
            await self.run_single_scraper(scraper_name, options)
            self.stdout.write('')  # Blank line between scrapers
        
        self.stdout.write(self.style.SUCCESS('\n✓ All scrapers completed'))
