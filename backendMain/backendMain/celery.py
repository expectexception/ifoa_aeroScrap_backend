"""
Celery Configuration for AeroOps Backend
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')

app = Celery('backendMain')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all registered Django apps
app.autodiscover_tasks()

# Build beat schedule from AUTO_SCHEDULE config
def build_beat_schedule():
    """Build Celery Beat schedule from AUTO_SCHEDULE config"""
    from scraper_manager.config import AUTO_SCHEDULE
    from croniter import croniter
    from datetime import datetime
    
    beat_schedule = {}
    
    if AUTO_SCHEDULE.get('enabled', False):
        # Run all scrapers
        if AUTO_SCHEDULE.get('run_all_scrapers', {}).get('enabled'):
            schedule_cfg = AUTO_SCHEDULE['run_all_scrapers']
            cron_expr = schedule_cfg.get('schedule', '0 */3 * * *')
            # Parse cron to crontab
            cron = croniter(cron_expr)
            # Convert to celery crontab (simplified)
            parts = cron_expr.split()
            beat_schedule['run-all-scrapers'] = {
                'task': 'scraper_manager.tasks.run_all_scrapers_task',
                'schedule': crontab(
                    minute=parts[0] if parts[0] != '*' else '*',
                    hour=parts[1] if parts[1] != '*' else '*',
                    day_of_month=parts[2] if parts[2] != '*' else '*',
                    month_of_year=parts[3] if parts[3] != '*' else '*',
                    day_of_week=parts[4] if parts[4] != '*' else '*',
                ),
                'kwargs': {
                    'max_jobs': schedule_cfg.get('max_jobs'),
                    'max_pages': schedule_cfg.get('max_pages'),
                }
            }
        
        # Run priority scrapers
        if AUTO_SCHEDULE.get('run_priority_scrapers', {}).get('enabled'):
            schedule_cfg = AUTO_SCHEDULE['run_priority_scrapers']
            cron_expr = schedule_cfg.get('schedule', '0 */6 * * *')
            parts = cron_expr.split()
            beat_schedule['run-priority-scrapers'] = {
                'task': 'scraper_manager.tasks.run_specific_scrapers_task',
                'schedule': crontab(
                    minute=parts[0] if parts[0] != '*' else '*',
                    hour=parts[1] if parts[1] != '*' else '*',
                    day_of_month=parts[2] if parts[2] != '*' else '*',
                    month_of_year=parts[3] if parts[3] != '*' else '*',
                    day_of_week=parts[4] if parts[4] != '*' else '*',
                ),
                'kwargs': {
                    'scrapers': schedule_cfg.get('scrapers', []),
                    'max_jobs': schedule_cfg.get('max_jobs'),
                }
            }
        
        # Run specialty scrapers
        if AUTO_SCHEDULE.get('run_specialty_scrapers', {}).get('enabled'):
            schedule_cfg = AUTO_SCHEDULE['run_specialty_scrapers']
            cron_expr = schedule_cfg.get('schedule', '0 1 * * *')
            parts = cron_expr.split()
            beat_schedule['run-specialty-scrapers'] = {
                'task': 'scraper_manager.tasks.run_specific_scrapers_task',
                'schedule': crontab(
                    minute=parts[0] if parts[0] != '*' else '*',
                    hour=parts[1] if parts[1] != '*' else '*',
                    day_of_month=parts[2] if parts[2] != '*' else '*',
                    month_of_year=parts[3] if parts[3] != '*' else '*',
                    day_of_week=parts[4] if parts[4] != '*' else '*',
                ),
                'kwargs': {
                    'scrapers': schedule_cfg.get('scrapers', []),
                    'max_jobs': schedule_cfg.get('max_jobs'),
                }
            }
    
    # Add other system tasks
    beat_schedule.update({
        # Daily job expiry check (01:00 UTC)
        'expire-old-jobs': {
            'task': 'jobs.tasks.expire_old_jobs_task',
            'schedule': crontab(hour=1, minute=0),
        },
        
        # Re-check active jobs (02:00 UTC)
        'recheck-active-jobs': {
            'task': 'jobs.tasks.recheck_active_jobs_task',
            'schedule': crontab(hour=2, minute=0),
        },
        
        # Daily report generation (23:00 UTC)
        'generate-daily-report': {
            'task': 'jobs.tasks.generate_daily_report_task',
            'schedule': crontab(hour=23, minute=0),
        },
        
        # Weekly summary (Sunday 09:00 UTC)
        'send-weekly-summary': {
            'task': 'jobs.tasks.send_weekly_summary_task',
            'schedule': crontab(hour=9, minute=0, day_of_week=0),
        },
        
        # Hourly health check
        'health-check': {
            'task': 'jobs.tasks.health_check_task',
            'schedule': crontab(minute=0),  # Every hour at :00
        },

        # Nightly seniority backfill (03:00 UTC)
        'backfill-seniority-nightly': {
            'task': 'jobs.tasks.backfill_senior_flags',
            'schedule': crontab(hour=3, minute=0),
            'kwargs': {'job_ids': None, 'batch_size': 2000, 'dry_run': False}
        },
    })
    
    return beat_schedule

# Celery Beat Schedule - Dynamically built from AUTO_SCHEDULE config
app.conf.beat_schedule = build_beat_schedule()

# Celery configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
