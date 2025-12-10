"""
Serializers for Jobs and Applications
"""
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Job
from .application_models import JobApplication, SavedJob, JobView, ShortlistedCandidate
from resumes.models import Resume


class JobListSerializer(serializers.ModelSerializer):
    """Simplified job listing for browse pages"""
    user_applied = serializers.BooleanField(read_only=True)
    user_saved = serializers.BooleanField(read_only=True)
    total_applications = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'location', 'country_code',
            'operation_type', 'status', 'senior_flag', 'posted_date',
            'source', 'url', 'user_applied', 'user_saved', 'total_applications'
        ]


class JobDetailSerializer(serializers.ModelSerializer):
    """Detailed job information"""
    total_applications = serializers.SerializerMethodField()
    total_views = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'normalized_title', 'company', 'company_id',
            'country_code', 'location', 'operation_type', 'status',
            'source', 'senior_flag', 'is_senior_position', 'posted_date',
            'retrieved_date', 'last_checked', 'url', 'description',
            'created_at', 'updated_at', 'total_applications', 'total_views'
        ]
    
    def get_total_applications(self, obj):
        return obj.applications.count()
    
    def get_total_views(self, obj):
        return obj.views.count()


class ApplicantUserSerializer(serializers.ModelSerializer):
    """User info for applicant"""
    role = serializers.CharField(source='profile.role', read_only=True)
    phone = serializers.CharField(source='profile.phone', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone']


class ResumeSimpleSerializer(serializers.ModelSerializer):
    """Simple resume info for application"""
    class Meta:
        model = Resume
        fields = ['id', 'filename', 'name', 'email', 'total_score', 'created_at']


class JobApplicationSerializer(serializers.ModelSerializer):
    """Full application details"""
    applicant = ApplicantUserSerializer(read_only=True)
    resume = ResumeSimpleSerializer(read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_company = serializers.CharField(source='job.company', read_only=True)
    days_since_application = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'job_company', 'applicant', 'resume',
            'status', 'cover_letter', 'applicant_notes', 'recruiter_notes',
            'reviewed_by', 'reviewed_at', 'rating', 'interview_date',
            'interview_notes', 'applied_at', 'updated_at', 'days_since_application'
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at', 'reviewed_by', 'reviewed_at']


class JobApplicationCreateSerializer(serializers.Serializer):
    """Create new application"""
    cover_letter = serializers.CharField(required=False, allow_blank=True)
    applicant_notes = serializers.CharField(required=False, allow_blank=True)
    
    def create(self, validated_data):
        return validated_data


class JobApplicationUpdateSerializer(serializers.ModelSerializer):
    """Update application (recruiter only)"""
    class Meta:
        model = JobApplication
        fields = [
            'status', 'recruiter_notes', 'rating', 'interview_date', 'interview_notes'
        ]


class SavedJobSerializer(serializers.ModelSerializer):
    """Saved job with details"""
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = SavedJob
        fields = ['id', 'job', 'saved_at', 'notes']


# ============= RECRUITER SERIALIZERS =============

class CandidateSerializer(serializers.ModelSerializer):
    """Candidate/Resume listing for recruiters"""
    username = serializers.CharField(source='user.username', read_only=True)
    email_verified = serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'filename', 'name', 'email', 'username', 'phones',
            'total_score', 'is_active', 'created_at', 'parsed_at',
            'email_verified', 'total_applications'
        ]
    
    def get_email_verified(self, obj):
        return bool(obj.email)
    
    def get_total_applications(self, obj):
        if obj.user:
            return obj.user.job_applications.count()
        return 0


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Detailed resume/candidate info for recruiters"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    profile = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = [
            'id', 'filename', 'name', 'email', 'phones', 'username', 'user_email',
            'skills', 'aviation', 'experience', 'total_score', 'raw_text',
            'is_public', 'is_active', 'parsed_at', 'additional_info',
            'created_at', 'updated_at', 'profile'
        ]
    
    def get_profile(self, obj):
        if obj.user and hasattr(obj.user, 'profile'):
            profile = obj.user.profile
            return {
                'desired_job_title': profile.desired_job_title,
                'desired_location': profile.desired_location,
                'experience_years': profile.experience_years,
                'skills': profile.skills,
                'certifications': profile.certifications,
                'availability': profile.availability,
            }
        return None


class RecruiterJobSerializer(serializers.ModelSerializer):
    """Job listing for recruiters with stats"""
    total_applications = serializers.IntegerField(read_only=True)
    pending_applications = serializers.IntegerField(read_only=True)
    total_views = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'company', 'location', 'country_code',
            'operation_type', 'status', 'senior_flag', 'posted_date',
            'source', 'url', 'total_applications', 'pending_applications',
            'total_views', 'created_at'
        ]


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating jobs by recruiters"""
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'company_id', 'location', 'country_code',
            'operation_type', 'status', 'senior_flag', 'senior_override',
            'posted_date', 'url', 'description'
        ]
        extra_kwargs = {
            'url': {'required': False},
            'status': {'required': False},
            'posted_date': {'required': False},
        }

    def create(self, validated_data):
        # Set defaults for recruiter-created jobs
        if 'status' not in validated_data:
            validated_data['status'] = 'active'
        if 'posted_date' not in validated_data:
            from django.utils import timezone
            validated_data['posted_date'] = timezone.now().date()
        if 'source' not in validated_data:
            validated_data['source'] = 'recruiter'

        return super().create(validated_data)


class ShortlistedCandidateSerializer(serializers.ModelSerializer):
    """Serializer for shortlisted candidates"""
    resume = ResumeSimpleSerializer(read_only=True)
    recruiter = serializers.CharField(source='recruiter.username', read_only=True)

    class Meta:
        model = ShortlistedCandidate
        fields = ['id', 'recruiter', 'resume', 'created_at']
