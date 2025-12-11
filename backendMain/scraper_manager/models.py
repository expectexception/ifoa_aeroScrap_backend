from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator


class ScraperJob(models.Model):
    """Track scraper execution jobs"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SCRAPER_CHOICES = [
        ('signature', 'Signature Aviation'),
        ('flygosh', 'Flygosh Jobs'),
        ('aviationindeed', 'Aviation Indeed'),
        ('aap', 'AAP Aviation'),
        ('indigo', 'IndiGo Airlines'),
        ('aviationjobsearch', 'Aviation Job Search'),
        ('goose', 'GOOSE Recruitment'),
        ('linkedin', 'LinkedIn Jobs'),
        ('pilots_global', 'PilotsGlobal'),
        ('all', 'All Scrapers'),
    ]
    
    scraper_name = models.CharField(max_length=50, choices=SCRAPER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Timing
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    execution_time = models.FloatField(null=True, blank=True, help_text='Execution time in seconds')
    
    # Results
    jobs_found = models.IntegerField(default=0)
    jobs_new = models.IntegerField(default=0)
    jobs_updated = models.IntegerField(default=0)
    jobs_duplicate = models.IntegerField(default=0)
    
    # Output
    output_file = models.CharField(max_length=500, blank=True)
    error_message = models.TextField(blank=True)
    
    # Metadata
    triggered_by = models.CharField(max_length=100, blank=True)
    parameters = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['scraper_name']),
        ]
    
    def __str__(self):
        return f"{self.scraper_name} - {self.status} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"
    
    @property
    def duration(self):
        """Calculate duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class ScraperConfig(models.Model):
    """Configuration for individual scrapers"""
    
    scraper_name = models.CharField(max_length=50, unique=True)
    is_enabled = models.BooleanField(default=True)
    
    # Limits
    max_jobs = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of jobs to scrape (null = unlimited)'
    )
    max_pages = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1)],
        help_text='Maximum number of pages to scrape (null = unlimited)'
    )
    
    # Settings
    timeout = models.IntegerField(default=300, help_text='Timeout in seconds')
    retry_count = models.IntegerField(default=3, help_text='Number of retries on failure')
    
    # Scheduling
    schedule_enabled = models.BooleanField(default=False)
    schedule_cron = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Cron expression for scheduling (e.g., "0 */6 * * *")'
    )
    
    # Statistics
    last_run = models.DateTimeField(null=True, blank=True)
    total_runs = models.IntegerField(default=0)
    successful_runs = models.IntegerField(default=0)
    failed_runs = models.IntegerField(default=0)
    
    # Metadata
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scraper_name']
    
    def __str__(self):
        return f"{self.scraper_name} ({'Enabled' if self.is_enabled else 'Disabled'})"
    
    def update_stats(self, success=True):
        """Update run statistics"""
        self.total_runs += 1
        if success:
            self.successful_runs += 1
        else:
            self.failed_runs += 1
        self.last_run = timezone.now()
        self.save(update_fields=['total_runs', 'successful_runs', 'failed_runs', 'last_run'])


class ScrapedURL(models.Model):
    """Track scraped URLs to prevent duplicates"""
    
    url = models.URLField(max_length=1000, unique=True, db_index=True)
    job_id = models.CharField(max_length=200, db_index=True)
    source = models.CharField(max_length=50, db_index=True)
    
    # Job data
    title = models.CharField(max_length=500, blank=True)
    company = models.CharField(max_length=200, blank=True)
    
    # Tracking
    first_scraped = models.DateTimeField(auto_now_add=True)
    last_scraped = models.DateTimeField(auto_now=True)
    scrape_count = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Full job data (JSON)
    job_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-last_scraped']
        indexes = [
            models.Index(fields=['source', 'is_active']),
            models.Index(fields=['-last_scraped']),
        ]
    
    def __str__(self):
        return f"{self.source}: {self.title[:50]}"