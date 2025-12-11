"""
Celery Tasks for Job Scraping and Maintenance
"""
from celery import shared_task
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import logging

logger = logging.getLogger('jobs')


def is_scheduling_enabled():
    """Check if scheduling is enabled via ScheduleConfig"""
    try:
        from .models import ScheduleConfig
        config = ScheduleConfig.get_config()
        return config.scheduling_enabled
    except Exception as e:
        logger.warning(f"Could not check scheduling status: {e}")
        return False  # Default to disabled for safety


@shared_task(name='jobs.tasks.scheduled_scraper_run')
def scheduled_scraper_run(trigger='scheduled'):
    """
    Run all enabled scrapers (twice daily by default)
    Only runs if scheduling is enabled in admin panel
    """
    if not is_scheduling_enabled():
        logger.info(f"⏸️  Scheduled scraping skipped - scheduling disabled in admin panel")
        return {'status': 'skipped', 'reason': 'scheduling_disabled'}
    
    logger.info(f"🚀 Starting scheduled scraper run - trigger: {trigger}")
    
    from scraper_manager.models import ScraperConfig, ScraperJob
    from scraper_manager.services import ScraperService
    
    # Create master job record
    job = ScraperJob.objects.create(
        scraper_name='all',
        status='pending',
        triggered_by=f'celery_{trigger}'
    )
    
    try:
        # Run all enabled scrapers
        result = ScraperService.run_all_scrapers(job)
        
        logger.info(f"✅ Scheduled scraper run completed: {result}")
        
        # Send notification for senior roles if any found
        notify_new_senior_roles.delay()
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Scheduled scraper run failed: {e}", exc_info=True)
        job.status = 'failed'
        job.error_message = str(e)
        job.save()
        return {'status': 'failed', 'error': str(e)}


@shared_task(name='jobs.tasks.expire_old_jobs_task')
def expire_old_jobs_task():
    """
    Mark jobs older than 30 days as expired
    Only runs if scheduling is enabled
    """
    if not is_scheduling_enabled():
        logger.info("⏸️  Job expiry skipped - scheduling disabled")
        return {'status': 'skipped'}
    
    from .models import Job, ScheduleConfig
    
    config = ScheduleConfig.get_config()
    cutoff_days = config.job_expiry_days
    cutoff_date = timezone.now() - timedelta(days=cutoff_days)
    
    expired_count = Job.objects.filter(
        status='active',
        posted_date__lt=cutoff_date.date()
    ).update(
        status='expired',
        last_checked=timezone.now()
    )
    
    logger.info(f"🗑️  Expired {expired_count} jobs older than {cutoff_days} days")
    
    return {
        'expired_count': expired_count,
        'cutoff_date': cutoff_date.isoformat()
    }


@shared_task(name='jobs.tasks.recheck_active_jobs_task')
def recheck_active_jobs_task():
    """
    Re-check if active jobs still exist on source (sample check)
    Only runs if scheduling is enabled
    """
    if not is_scheduling_enabled():
        logger.info("⏸️  Job recheck skipped - scheduling disabled")
        return {'status': 'skipped'}
    
    from .models import Job
    import requests
    
    from scraper_manager.db_manager import DjangoDBManager
    from asgiref.sync import async_to_sync
    
    db_manager = DjangoDBManager()
    
    # Check 50 random active jobs that haven't been checked in 7 days
    jobs_to_check = Job.objects.filter(
        status='active',
        last_checked__lt=timezone.now() - timedelta(days=7)
    ).order_by('?')[:50]
    
    expired_count = 0
    checked_count = 0
    
    for job in jobs_to_check:
        try:
            # Use centralized check logic
            is_active, reason = async_to_sync(db_manager.check_job_active)(job.url)
            
            if not is_active:
                logger.info(f"🚫 Job {job.id} ({job.url}) is EXPIRED: {reason}")
                job.status = 'expired'
                expired_count += 1
            else:
                # job.status = 'active' # Keep as active
                pass
            
            job.last_checked = timezone.now()
            job.save()
            checked_count += 1
            
        except Exception as e:
            logger.warning(f"Could not check job {job.id}: {e}")
            continue
    
    logger.info(f"🔍 Rechecked {checked_count} jobs, expired {expired_count}")
    
    return {
        'checked': checked_count,
        'expired': expired_count
    }


@shared_task(name='jobs.tasks.generate_daily_report_task')
def generate_daily_report_task():
    """
    Generate and optionally email daily CSV report
    Only runs if scheduling is enabled
    """
    if not is_scheduling_enabled():
        logger.info("⏸️  Daily report skipped - scheduling disabled")
        return {'status': 'skipped'}
    
    from .models import Job, ScheduleConfig
    import csv
    from io import StringIO
    
    config = ScheduleConfig.get_config()
    
    if not config.daily_reports_enabled:
        logger.info("⏸️  Daily report skipped - reports disabled in config")
        return {'status': 'skipped', 'reason': 'reports_disabled'}
    
    today = timezone.now().date()
    
    jobs = Job.objects.filter(
        created_at__date=today,
        status='active'
    ).order_by('country_code', 'operation_type', '-posted_date')
    
    # Generate CSV
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Country', 'Operation Type', 'Job Title', 'Company', 
        'Date Posted', 'URL', 'Senior', 'Source'
    ])
    
    for job in jobs:
        writer.writerow([
            job.country_code or '-',
            job.operation_type or '-',
            job.title,
            job.company,
            job.posted_date or '-',
            job.url,
            'Yes' if job.senior_flag else 'No',
            job.source or '-'
        ])
    
    csv_content = output.getvalue()
    
    # Send email if configured
    if config.report_email_recipients:
        recipients = [email.strip() for email in config.report_email_recipients.split(',')]
        
        try:
            from django.core.mail import EmailMessage
            
            email = EmailMessage(
                subject=f'Daily Aviation Jobs Report - {today}',
                body=f'Daily report attached: {jobs.count()} new jobs found on {today}',
                to=recipients
            )
            email.attach(f'jobs_report_{today}.csv', csv_content, 'text/csv')
            email.send()
            
            logger.info(f"📧 Daily report emailed to {len(recipients)} recipients")
            
        except Exception as e:
            logger.error(f"❌ Failed to send daily report email: {e}")
    
    logger.info(f"📊 Daily report generated: {jobs.count()} jobs")
    
    return {
        'jobs_count': jobs.count(),
        'date': today.isoformat(),
        'emailed': bool(config.report_email_recipients)
    }


@shared_task(name='jobs.tasks.send_weekly_summary_task')
def send_weekly_summary_task():
    """
    Generate and email weekly summary report
    Only runs if scheduling is enabled
    """
    if not is_scheduling_enabled():
        logger.info("⏸️  Weekly summary skipped - scheduling disabled")
        return {'status': 'skipped'}
    
    from .models import Job, ScheduleConfig
    from django.db.models import Count
    
    config = ScheduleConfig.get_config()
    
    if not config.weekly_reports_enabled or not config.report_email_recipients:
        logger.info("⏸️  Weekly summary skipped - not configured")
        return {'status': 'skipped'}
    
    week_ago = timezone.now() - timedelta(days=7)
    
    stats = {
        'total_jobs': Job.objects.filter(created_at__gte=week_ago).count(),
        'by_country': list(Job.objects.filter(created_at__gte=week_ago)
                          .values('country_code')
                          .annotate(count=Count('id'))
                          .order_by('-count')[:10]),
        'by_operation': list(Job.objects.filter(created_at__gte=week_ago)
                           .values('operation_type')
                           .annotate(count=Count('id'))),
        'top_companies': list(Job.objects.filter(created_at__gte=week_ago)
                            .values('company')
                            .annotate(count=Count('id'))
                            .order_by('-count')[:10]),
        'senior_roles': Job.objects.filter(
            created_at__gte=week_ago, 
            senior_flag=True
        ).count()
    }
    
    # Build email body
    body = f"""
    📊 Weekly Aviation Jobs Summary
    Week: {week_ago.date()} to {timezone.now().date()}
    
    📈 Total New Jobs: {stats['total_jobs']}
    👔 Senior Roles: {stats['senior_roles']}
    
    🌍 Top Countries:
    {chr(10).join([f"  • {item['country_code'] or 'Unknown'}: {item['count']} jobs" for item in stats['by_country'][:5]])}
    
    ✈️ By Operation Type:
    {chr(10).join([f"  • {item['operation_type'] or 'Unknown'}: {item['count']} jobs" for item in stats['by_operation']])}
    
    🏢 Top Hiring Companies:
    {chr(10).join([f"  • {item['company']}: {item['count']} jobs" for item in stats['top_companies'][:5]])}
    """
    
    recipients = [email.strip() for email in config.report_email_recipients.split(',')]
    
    try:
        send_mail(
            subject=f'Weekly Aviation Jobs Summary - Week of {week_ago.date()}',
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        
        logger.info(f"📧 Weekly summary sent to {len(recipients)} recipients")
        
    except Exception as e:
        logger.error(f"❌ Failed to send weekly summary: {e}")
    
    return stats


@shared_task(name='jobs.tasks.health_check_task')
def health_check_task():
    """
    Check scraper health and send alerts if issues detected
    Only runs if scheduling is enabled
    """
    if not is_scheduling_enabled():
        return {'status': 'skipped'}
    
    from scraper_manager.models import ScraperJob
    from .models import Job, ScheduleConfig
    
    config = ScheduleConfig.get_config()
    
    issues = []
    
    # Check if scrapers ran in last 24 hours
    cutoff = timezone.now() - timedelta(hours=24)
    
    for scraper in ['aviation', 'airindia', 'goose', 'linkedin']:
        last_run = ScraperJob.objects.filter(
            scraper_name=scraper,
            created_at__gte=cutoff
        ).first()
        
        if not last_run:
            issues.append(f"⚠️  {scraper} hasn't run in 24+ hours")
    
    # Check if major countries have jobs
    major_countries = ['US', 'GB', 'AE', 'DE', 'SG', 'AU', 'IN']
    yesterday = timezone.now() - timedelta(days=1)
    
    for country in major_countries:
        count = Job.objects.filter(
            country_code=country,
            created_at__gte=yesterday
        ).count()
        
        if count == 0:
            issues.append(f"⚠️  Zero jobs found for {country} in last 24h")
    
    # Send alert if issues found
    if issues and config.alert_email_recipients:
        recipients = [email.strip() for email in config.alert_email_recipients.split(',')]
        
        try:
            send_mail(
                subject='⚠️ Aviation Jobs Scraper Health Alert',
                message='\n'.join(issues),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=False
            )
            
            logger.warning(f"🚨 Health check alert sent: {len(issues)} issues")
            
        except Exception as e:
            logger.error(f"❌ Failed to send health alert: {e}")
    
    return {
        'issues_found': len(issues),
        'issues': issues
    }


@shared_task(name='jobs.tasks.notify_new_senior_roles')
def notify_new_senior_roles():
    """
    Send email notification for new senior roles found in last hour
    """
    from .models import Job, ScheduleConfig
    
    config = ScheduleConfig.get_config()
    
    if not config.senior_role_alerts_enabled or not config.alert_email_recipients:
        return {'status': 'skipped'}
    
    hour_ago = timezone.now() - timedelta(hours=1)
    
    new_senior_jobs = Job.objects.filter(
        senior_flag=True,
        status='new',
        created_at__gte=hour_ago
    )
    
    if new_senior_jobs.count() == 0:
        return {'status': 'no_new_senior_jobs'}
    
    # Build email
    body = f"🚨 {new_senior_jobs.count()} New Senior Aviation Jobs\n\n"
    
    for job in new_senior_jobs[:10]:  # Limit to 10
        body += f"• {job.title}\n"
        body += f"  Company: {job.company}\n"
        body += f"  Country: {job.country_code or 'Unknown'}\n"
        body += f"  URL: {job.url}\n\n"
    
    recipients = [email.strip() for email in config.alert_email_recipients.split(',')]
    
    try:
        send_mail(
            subject=f'🚨 {new_senior_jobs.count()} New Senior Aviation Jobs',
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False
        )
        
        logger.info(f"📧 Senior role alert sent for {new_senior_jobs.count()} jobs")
        
        return {
            'sent': True,
            'jobs_count': new_senior_jobs.count()
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to send senior role alert: {e}")
        return {'sent': False, 'error': str(e)}


@shared_task(name='jobs.tasks.backfill_senior_flags')
def backfill_senior_flags(job_ids=None, batch_size=1000, dry_run=False):
    """
    Recompute senior flags for jobs that do not have an explicit override.
    - If job_ids is provided, limits to those IDs.
    - Respects overrides (only processes senior_override is NULL).
    - Processes in batches to avoid memory pressure.
    Returns summary counts.
    """
    # Respect global scheduling flag
    if not is_scheduling_enabled():
        logger.info("⏸️  Senior backfill skipped - scheduling disabled")
        return {'status': 'skipped'}
    from .models import Job
    from . import utils

    qs = Job.objects.filter(senior_override__isnull=True)
    if job_ids:
        qs = qs.filter(id__in=job_ids)

    total = qs.count()
    scanned = 0
    updated = 0

    # Iterate in chunks
    def chunked(iterable_qs, size):
        start = 0
        while True:
            batch = list(iterable_qs.order_by('id')[start:start+size])
            if not batch:
                break
            yield batch
            start += size

    for batch in chunked(qs, batch_size):
        for job in batch:
            scanned += 1
            expected = utils.is_senior(job.title) if job.title else False
            if expected != job.senior_flag or expected != job.is_senior_position:
                updated += 1
                if not dry_run:
                    job.senior_flag = expected
                    job.is_senior_position = expected
                    job.save(update_fields=['senior_flag', 'is_senior_position', 'updated_at'])

    result = {
        'total_candidates': total,
        'scanned': scanned,
        'updated': updated,
        'dry_run': bool(dry_run),
        'job_ids_filtered': bool(job_ids),
    }
    logger.info(f"👔 Senior backfill complete: {result}")
    return result
