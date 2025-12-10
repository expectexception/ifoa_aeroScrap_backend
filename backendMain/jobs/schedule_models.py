"""
Schedule Configuration Model
Allows controlling automated scheduling from Django admin panel
"""
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class ScheduleConfig(models.Model):
    """
    Singleton model for controlling scheduled tasks
    All settings can be managed from admin panel
    """
    
    # Main scheduling toggle
    scheduling_enabled = models.BooleanField(
        default=False,
        help_text="🔴 MASTER SWITCH: Enable/disable ALL automated scheduling. "
                  "When OFF, no scheduled tasks will run (scrapers, reports, alerts, etc.)"
    )
    
    # Scraper scheduling
    scraper_schedule_enabled = models.BooleanField(
        default=True,
        help_text="Enable twice-daily automated scraping (00:00 and 12:00 UTC)"
    )
    
    # Job expiry settings
    job_expiry_enabled = models.BooleanField(
        default=True,
        help_text="Automatically mark old jobs as expired"
    )
    job_expiry_days = models.IntegerField(
        default=30,
        validators=[MinValueValidator(1), MaxValueValidator(365)],
        help_text="Number of days before a job is marked as expired (default: 30)"
    )
    
    # Report settings
    daily_reports_enabled = models.BooleanField(
        default=False,
        help_text="Generate and email daily CSV reports at 23:00 UTC"
    )
    weekly_reports_enabled = models.BooleanField(
        default=False,
        help_text="Generate and email weekly summary reports (Sunday 09:00 UTC)"
    )
    report_email_recipients = models.TextField(
        blank=True,
        help_text="Comma-separated email addresses for reports (e.g., admin@example.com, team@example.com)"
    )
    
    # Alert settings
    senior_role_alerts_enabled = models.BooleanField(
        default=False,
        help_text="Send email alerts when new senior roles are found"
    )
    health_check_alerts_enabled = models.BooleanField(
        default=True,
        help_text="Send alerts if scrapers fail or data issues detected"
    )
    alert_email_recipients = models.TextField(
        blank=True,
        help_text="Comma-separated email addresses for alerts (e.g., ops@example.com)"
    )
    
    # Schedule customization
    scraper_run_times = models.CharField(
        max_length=200,
        default="0:00,12:00",
        help_text="Comma-separated times in HH:MM format (24-hour UTC). Example: 0:00,12:00 for midnight and noon"
    )
    
    # Metadata
    last_updated = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = 'schedule_config'
        verbose_name = 'Schedule Configuration'
        verbose_name_plural = 'Schedule Configuration'
    
    def __str__(self):
        status = "🟢 ENABLED" if self.scheduling_enabled else "🔴 DISABLED"
        return f"Schedule Configuration - {status}"
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration"""
        config, created = cls.objects.get_or_create(id=1)
        if created:
            config.scheduling_enabled = False  # Start disabled for safety
            config.save()
        return config
    
    def save(self, *args, **kwargs):
        # Enforce singleton
        self.id = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # Prevent deletion of singleton
        pass
