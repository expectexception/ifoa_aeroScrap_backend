from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
import json


class Resume(models.Model):
    """
    Resume/CV uploaded by job seekers
    """
    # User relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='resumes',
        null=True,
        blank=True,
        db_index=True,
        help_text='Job seeker who owns this resume'
    )
    
    # Basic fields
    filename = models.CharField(max_length=512)
    name = models.CharField(max_length=256, blank=True, null=True)
    email = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    phones = models.JSONField(default=list, blank=True)
    
    # Parsed data
    skills = models.JSONField(default=dict, blank=True)
    aviation = models.JSONField(default=dict, blank=True)
    experience = models.JSONField(default=dict, blank=True)
    total_score = models.FloatField(default=0.0, db_index=True)
    
    # File storage
    raw_text = models.TextField(blank=True, null=True)
    file_content = models.TextField(blank=True, null=True)
    parsed_at = models.DateTimeField(blank=True, null=True)
    additional_info = models.JSONField(default=dict, blank=True)
    
    # Visibility and status
    is_public = models.BooleanField(
        default=True,
        help_text='Visible to recruiters'
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text='Currently active/looking for jobs'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'resumes'
        indexes = [
            models.Index(fields=['user', '-created_at'], name='resume_user_date_idx'),
            models.Index(fields=['-total_score', 'is_public'], name='resume_score_public_idx'),
            models.Index(fields=['is_active', 'is_public', '-total_score'], name='resume_active_idx'),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id} - {self.filename}"

    def to_dict(self):
        # Return a dict similar to the previous FastAPI DB object's to_dict
        return {
            'id': self.id,
            'filename': self.filename,
            'name': self.name,
            'email': self.email,
            'phones': self.phones or [],
            'skills': self.skills or {},
            'aviation': self.aviation or {},
            'experience': self.experience or {},
            'total_score': self.total_score,
            'raw_text': self.raw_text or '',
            'file_content': self.file_content,
            'parsed_at': self.parsed_at.isoformat() if self.parsed_at else None,
            'additional_info': self.additional_info or {},
        }
