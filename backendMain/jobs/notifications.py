"""
Notification system for job applications and other events
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger('jobs')


def notify_recruiter_new_application(recruiter, application):
    """
    Notify recruiter when someone applies to their job
    """
    try:
        subject = f'New Application: {application.job.title}'

        # Prepare context for email template
        context = {
            'recruiter': recruiter,
            'applicant': application.applicant,
            'job': application.job,
            'application': application,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }

        # Render HTML email
        html_message = render_to_string('emails/new_application.html', context)
        plain_message = strip_tags(html_message)

        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[recruiter.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Notification sent to recruiter {recruiter.email} for application {application.id}")

    except Exception as e:
        logger.error(f"Failed to send notification to recruiter {recruiter.email}: {e}")
        raise


def notify_job_seeker_application_status_change(application):
    """
    Notify job seeker when application status changes
    """
    try:
        subject = f'Application Status Update: {application.job.title}'

        context = {
            'applicant': application.applicant,
            'job': application.job,
            'application': application,
            'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        }

        html_message = render_to_string('emails/application_status_update.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            recipient_list=[application.applicant.email],
            html_message=html_message,
            fail_silently=False,
        )

        logger.info(f"Status update notification sent to {application.applicant.email}")

    except Exception as e:
        logger.error(f"Failed to send status update notification: {e}")
        raise