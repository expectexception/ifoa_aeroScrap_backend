"""
User Profile Model Extension for Role-Based Access
"""
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    """
    Extended User Profile with role-based access control
    """
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('recruiter', 'Recruiter'),
        ('job_seeker', 'Job Seeker'),
        ('user', 'User'),
        ('viewer', 'Viewer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')
    department = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    
    # Job Seeker specific fields
    desired_job_title = models.CharField(max_length=200, blank=True, null=True, help_text='Preferred job title')
    desired_location = models.CharField(max_length=200, blank=True, null=True, help_text='Preferred work location')
    experience_years = models.IntegerField(null=True, blank=True, help_text='Years of experience')
    skills = models.JSONField(default=list, blank=True, help_text='List of skills')
    certifications = models.JSONField(default=list, blank=True, help_text='Aviation certifications')
    availability = models.CharField(max_length=50, blank=True, null=True, help_text='Immediate/2 weeks/1 month')
    
    # Recruiter specific fields
    company_name = models.CharField(max_length=200, blank=True, null=True, help_text='Recruiter company name')
    company_website = models.URLField(blank=True, null=True, help_text='Company website')
    is_verified_recruiter = models.BooleanField(default=False, help_text='Admin-verified recruiter status')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
    
    @property
    def is_admin(self):
        return self.role == 'admin' or self.user.is_superuser
    
    @property
    def is_manager(self):
        return self.role in ['admin', 'manager'] or self.user.is_superuser
    
    @property
    def can_write(self):
        return self.role in ['admin', 'manager', 'user'] or self.user.is_superuser
    
    @property
    def is_job_seeker(self):
        return self.role == 'job_seeker'
    
    @property
    def is_recruiter(self):
        return self.role == 'recruiter' or self.is_admin
    
    def check_verified_recruiter(self):
        """Check if this is a verified recruiter"""
        return self.role == 'recruiter' and self.is_verified_recruiter


# Signal to create profile automatically when user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save UserProfile when User is saved"""
    if hasattr(instance, 'profile'):
        instance.profile.save()
    else:
        # Create profile if it doesn't exist
        UserProfile.objects.create(user=instance)


# Monkey patch User model to add role property for easy access
def get_user_role(self):
    """Get user role from profile"""
    if self.is_superuser:
        return 'admin'
    if hasattr(self, 'profile'):
        return self.profile.role
    return 'user'

User.add_to_class('role', property(get_user_role))
