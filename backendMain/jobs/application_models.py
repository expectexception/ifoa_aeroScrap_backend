"""
Job Application Models - Track applications from job seekers
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Job


class JobApplication(models.Model):
    """
    Tracks job applications from candidates
    """
    STATUS_CHOICES = [
        ('pending', '⏳ Pending Review'),
        ('reviewing', '👀 Under Review'),
        ('shortlisted', '⭐ Shortlisted'),
        ('interview_scheduled', '📅 Interview Scheduled'),
        ('interviewed', '✓ Interviewed'),
        ('offer_sent', '📧 Offer Sent'),
        ('accepted', '✅ Accepted'),
        ('rejected', '❌ Rejected'),
        ('withdrawn', '🚫 Withdrawn'),
    ]
    
    # Core relationships
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        help_text='Job being applied for'
    )
    applicant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        help_text='User who applied'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='applications',
        help_text='Resume used for application'
    )
    
    # Application status
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    # Cover letter and notes
    cover_letter = models.TextField(
        blank=True,
        null=True,
        help_text='Applicant cover letter'
    )
    applicant_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Additional notes from applicant'
    )
    
    # Recruiter feedback
    recruiter_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Internal notes from recruiter'
    )
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_applications',
        help_text='Recruiter who reviewed'
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When application was reviewed'
    )
    
    # Rating system
    rating = models.IntegerField(
        null=True,
        blank=True,
        help_text='Rating from 1-5',
        choices=[(i, f'{i} stars') for i in range(1, 6)]
    )
    
    # Interview details
    interview_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Scheduled interview date'
    )
    interview_notes = models.TextField(
        blank=True,
        null=True,
        help_text='Interview notes'
    )
    
    # Metadata
    applied_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When application was submitted'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional tracking
    source_device = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text='mobile/desktop/tablet'
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text='Applicant IP address'
    )
    
    class Meta:
        db_table = 'job_applications'
        unique_together = [['job', 'applicant']]  # One application per job per user
        indexes = [
            models.Index(fields=['status', '-applied_at'], name='app_status_date_idx'),
            models.Index(fields=['applicant', '-applied_at'], name='app_user_date_idx'),
            models.Index(fields=['job', '-applied_at'], name='app_job_date_idx'),
            models.Index(fields=['reviewed_by', '-reviewed_at'], name='app_reviewer_idx'),
            models.Index(fields=['-applied_at'], name='app_date_desc_idx'),
        ]
        ordering = ['-applied_at']
    
    def save(self, *args, **kwargs):
        # Auto-set reviewed_at when status changes from pending
        if self.pk:
            old = JobApplication.objects.filter(pk=self.pk).first()
            if old and old.status == 'pending' and self.status != 'pending':
                if not self.reviewed_at:
                    self.reviewed_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    def mark_as_reviewed(self, reviewer, new_status='reviewing'):
        """Mark application as reviewed by a recruiter"""
        self.status = new_status
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'updated_at'])
    
    def update_status(self, new_status, notes=None):
        """Update application status with optional notes"""
        self.status = new_status
        if notes:
            self.recruiter_notes = (self.recruiter_notes or '') + f"\n\n[{timezone.now()}] {notes}"
        self.save(update_fields=['status', 'recruiter_notes', 'updated_at'])


class ShortlistedCandidate(models.Model):
    """Shortlist relationship between recruiter and a candidate resume"""
    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shortlisted_candidates',
        help_text='Recruiter who shortlisted'
    )
    resume = models.ForeignKey(
        'resumes.Resume',
        on_delete=models.CASCADE,
        related_name='shortlists',
        help_text='Resume shortlisted'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shortlisted_candidates'
        unique_together = [['recruiter', 'resume']]
        indexes = [
            models.Index(fields=['recruiter', '-created_at'], name='shortlist_recruiter_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recruiter_id}-{self.resume_id}"
    
    def schedule_interview(self, interview_date, notes=None):
        """Schedule an interview for this application"""
        self.status = 'interview_scheduled'
        self.interview_date = interview_date
        if notes:
            self.interview_notes = notes
        self.save(update_fields=['status', 'interview_date', 'interview_notes', 'updated_at'])
    
    @property
    def days_since_application(self):
        """Calculate days since application was submitted"""
        delta = timezone.now() - self.applied_at
        return delta.days
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_active(self):
        """Check if application is still in active consideration"""
        return self.status not in ['accepted', 'rejected', 'withdrawn']
    
    def __str__(self):
        return f"{self.applicant.username} → {self.job.title[:30]} ({self.status})"


class SavedJob(models.Model):
    """
    Allows job seekers to save/bookmark jobs for later
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        help_text='User who saved the job'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by_users',
        help_text='Saved job'
    )
    saved_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text='Personal notes about this job'
    )
    
    class Meta:
        db_table = 'saved_jobs'
        unique_together = [['user', 'job']]
        indexes = [
            models.Index(fields=['user', '-saved_at'], name='saved_user_date_idx'),
        ]
        ordering = ['-saved_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.job.title[:30]}"


class JobView(models.Model):
    """
    Track job views for analytics
    """
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='views',
        help_text='Viewed job'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='job_views',
        help_text='User who viewed (null for anonymous)'
    )
    viewed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'job_views'
        indexes = [
            models.Index(fields=['job', '-viewed_at'], name='view_job_date_idx'),
            models.Index(fields=['-viewed_at'], name='view_date_desc_idx'),
        ]
        ordering = ['-viewed_at']
    
    def __str__(self):
        username = self.user.username if self.user else 'Anonymous'
        return f"{username} viewed {self.job.title[:30]}"
