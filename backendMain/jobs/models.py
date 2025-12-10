from django.db import models
from django.utils import timezone
## Removed import to avoid circular import; Django will auto-discover models in app


class Job(models.Model):
    OPERATION_CHOICES = [
        ('passenger', '✈️ Passenger Airlines'),
        ('cargo', '📦 Cargo & Freight'),
        ('business', '🎩 Business & Private Aviation'),
        ('scheduled', '🗓️ Scheduled Operations'),
        ('low_cost', '💺 Low-Cost Carrier'),
        ('ad_hoc_charter', '🛩️ Charter & On-Demand'),
        ('helicopter', '🚁 Helicopter Operations'),
        ('mro', '🔧 Maintenance & Repair'),
        ('ground_ops', '🏢 Ground Operations'),
        ('atc', '🎯 Air Traffic Control'),
    ]

    STATUS_CHOICES = [
        ('new', '✨ New'),
        ('active', '🟢 Active'),
        ('reviewed', '✓ Reviewed'),
        ('expired', '⏰ Expired'),
        ('archived', '📦 Archived'),
        ('closed', '🔒 Closed'),
    ]

    # Core fields - optimized with proper constraints
    title = models.CharField(max_length=500, db_index=True)  # Changed from TextField for better indexing
    normalized_title = models.CharField(max_length=500, null=True, blank=True, db_index=True)
    company = models.CharField(max_length=200, db_index=True)  # Changed from TextField
    company_id = models.IntegerField(null=True, blank=True, db_index=True)
    
    # Location fields
    country_code = models.CharField(max_length=3, null=True, blank=True, db_index=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    
    # Classification
    operation_type = models.CharField(max_length=20, choices=OPERATION_CHOICES, null=True, blank=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', db_index=True)
    source = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    
    # Experience level
    senior_flag = models.BooleanField(default=False, db_index=True)
    senior_override = models.BooleanField(null=True, blank=True, db_index=True)
    is_senior_position = models.BooleanField(default=False, db_index=True)
    
    # Dates
    posted_date = models.DateField(null=True, blank=True, db_index=True)
    retrieved_date = models.DateTimeField(default=timezone.now)
    last_checked = models.DateTimeField(null=True, blank=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # URL must be unique - optimized with hash index
    url = models.URLField(max_length=1000, unique=True, db_index=True)
    
    # Large text fields
    description = models.TextField(null=True, blank=True)
    raw_json = models.JSONField(null=True, blank=True)
    
    # Recruiter who posted this job (for manually created jobs)
    posted_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posted_jobs',
        help_text='Recruiter who posted this job (null for scraped jobs)'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'jobs'
        indexes = [
            # Composite indexes for common queries
            models.Index(fields=['status', '-posted_date'], name='jobs_status_date_idx'),
            models.Index(fields=['country_code', 'operation_type', '-posted_date'], name='jobs_country_op_date_idx'),
            models.Index(fields=['company', '-posted_date'], name='jobs_company_date_idx'),
            models.Index(fields=['source', '-created_at'], name='jobs_source_created_idx'),
            models.Index(fields=['senior_flag', 'status', '-posted_date'], name='jobs_senior_status_date_idx'),
            # Single field indexes
            models.Index(fields=['-created_at'], name='jobs_created_desc_idx'),
            models.Index(fields=['normalized_title'], name='jobs_norm_title_idx'),
        ]
        ordering = ['-posted_date', '-created_at']
        constraints = [
            # Ensure URL is not empty
            models.CheckConstraint(
                check=~models.Q(url=''),
                name='jobs_url_not_empty'
            ),
            # Ensure company is not empty
            models.CheckConstraint(
                check=~models.Q(company=''),
                name='jobs_company_not_empty'
            ),
        ]

    def save(self, *args, **kwargs):
        # Normalize title if not set
        if self.title and not self.normalized_title:
            self.normalized_title = self.title.lower().strip()
        
        # Compute senior_flag from override or title
        try:
            from . import utils
            if self.senior_override is not None:
                computed_senior = bool(self.senior_override)
            else:
                computed_senior = utils.is_senior(self.title) if self.title else False
            self.senior_flag = computed_senior
            self.is_senior_position = computed_senior
        except Exception:
            # Fallback: keep existing values
            self.is_senior_position = self.senior_flag
        
        # Ensure company is set
        if not self.company or not self.company.strip():
            self.company = 'Unknown Company'
        
        # Truncate description if too long (performance)
        if self.description and len(self.description) > 10000:
            self.description = self.description[:10000]
        
        super().save(*args, **kwargs)
    
    def clean(self):
        """Validate model before saving"""
        from django.core.exceptions import ValidationError
        if not self.url:
            raise ValidationError('URL is required')
        if not self.company or not self.company.strip():
            raise ValidationError('Company is required')

    def __str__(self):
        return f"{self.title[:50]} @ {self.company}"


class CompanyMapping(models.Model):
    OPERATION_CHOICES = Job.OPERATION_CHOICES

    company_name = models.CharField(max_length=200, db_index=True)
    normalized_name = models.CharField(max_length=200, unique=True, db_index=True)
    operation_type = models.CharField(max_length=20, choices=OPERATION_CHOICES, null=True, blank=True, db_index=True)
    country_code = models.CharField(max_length=3, null=True, blank=True, db_index=True)
    notes = models.TextField(null=True, blank=True)
    
    # Auto-mapping tracking
    auto_created = models.BooleanField(default=False, db_index=True, help_text='Automatically created by scraper')
    needs_review = models.BooleanField(default=True, db_index=True, help_text='Needs manual review and verification')
    reviewed_by = models.CharField(max_length=100, null=True, blank=True, help_text='Username who reviewed this mapping')
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text='When this mapping was reviewed')
    
    # Statistics caching
    total_jobs = models.IntegerField(default=0)
    active_jobs = models.IntegerField(default=0)
    last_job_date = models.DateField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'company_mapping'
        ordering = ['-total_jobs', 'company_name']
        indexes = [
            models.Index(fields=['normalized_name'], name='company_normalized_idx'),
            models.Index(fields=['operation_type', '-total_jobs'], name='company_op_jobs_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(company_name=''),
                name='company_name_not_empty'
            ),
        ]

    def save(self, *args, **kwargs):
        # Auto-normalize if not set
        if self.company_name and not self.normalized_name:
            self.normalized_name = self.company_name.strip().lower()
        
        # Ensure normalized_name is set
        if not self.normalized_name:
            self.normalized_name = 'unknown'
        
        super().save(*args, **kwargs)
    
    def update_statistics(self):
        """Update job statistics for this company"""
        from django.db.models import Count, Q, Max
        
        jobs = Job.objects.filter(company__iexact=self.company_name)
        stats = jobs.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(status='active')),
            latest_date=Max('posted_date')
        )
        
        self.total_jobs = stats['total'] or 0
        self.active_jobs = stats['active'] or 0
        self.last_job_date = stats['latest_date']
        self.save(update_fields=['total_jobs', 'active_jobs', 'last_job_date', 'updated_at'])
    
    def mark_as_reviewed(self, username=None):
        """Mark this company mapping as reviewed"""
        self.needs_review = False
        self.reviewed_by = username or 'admin'
        self.reviewed_at = timezone.now()
        self.save(update_fields=['needs_review', 'reviewed_by', 'reviewed_at', 'updated_at'])

    def __str__(self):
        status = '⚠️ ' if self.needs_review else '✓ '
        return f"{status}{self.company_name} ({self.total_jobs} jobs)"


class CrawlLog(models.Model):
    source = models.CharField(max_length=50, db_index=True)
    run_time = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Statistics
    items_found = models.IntegerField(default=0)
    items_inserted = models.IntegerField(default=0)
    items_updated = models.IntegerField(default=0)
    items_skipped = models.IntegerField(default=0)
    items_errors = models.IntegerField(default=0)
    
    # Execution details
    execution_time = models.FloatField(null=True, blank=True, help_text="Execution time in seconds")
    success_rate = models.FloatField(null=True, blank=True, help_text="Success rate percentage")
    
    # Error tracking
    error = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, default='success', choices=[
        ('success', 'Success'),
        ('partial', 'Partial Success'),
        ('failed', 'Failed'),
    ])
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'crawl_log'
        ordering = ['-run_time']
        indexes = [
            models.Index(fields=['source', '-run_time'], name='crawl_source_time_idx'),
            models.Index(fields=['-run_time'], name='crawl_time_desc_idx'),
            models.Index(fields=['status', '-run_time'], name='crawl_status_time_idx'),
        ]
    
    def save(self, *args, **kwargs):
        # Calculate success rate
        if self.items_found > 0:
            successful = self.items_inserted + self.items_updated
            self.success_rate = (successful / self.items_found) * 100
        else:
            self.success_rate = 0.0
        
        # Determine status
        if self.error:
            self.status = 'failed' if self.items_inserted == 0 else 'partial'
        else:
            self.status = 'success'
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.source} @ {self.run_time.isoformat()} ({self.status})"


# Import ScheduleConfig and application models
from .schedule_models import ScheduleConfig
from .application_models import JobApplication, SavedJob, JobView

__all__ = ['Job', 'CompanyMapping', 'CrawlLog', 'ScheduleConfig', 'JobApplication', 'SavedJob', 'JobView']
