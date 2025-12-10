from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    # Use SerializerMethodField to get the correct role (respects is_superuser)
    role = serializers.SerializerMethodField()
    department = serializers.CharField(source='profile.department', read_only=True)
    is_admin = serializers.BooleanField(source='profile.is_admin', read_only=True)
    is_manager = serializers.BooleanField(source='profile.is_manager', read_only=True)
    can_write = serializers.BooleanField(source='profile.can_write', read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined', 
                  'role', 'department', 'is_admin', 'is_manager', 'can_write')
        read_only_fields = ('id', 'date_joined', 'role', 'department', 'is_admin', 'is_manager', 'can_write')
    
    def get_role(self, obj):
        """Get role using the user.role property which handles is_superuser correctly"""
        return obj.role


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)
    user_type = serializers.ChoiceField(
        choices=['job_seeker', 'recruiter'],
        required=True,
        help_text="User type: job_seeker or recruiter"
    )
    
    # Job seeker fields (optional)
    desired_job_title = serializers.CharField(required=False, allow_blank=True)
    desired_location = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, allow_null=True)
    
    # Recruiter fields (optional)
    company_name = serializers.CharField(required=False, allow_blank=True)
    company_website = serializers.URLField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name',
                  'user_type', 'desired_job_title', 'desired_location', 'experience_years',
                  'company_name', 'company_website', 'phone')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                {"email": "A user with this email already exists."}
            )
        
        # Validate recruiter requires company info
        if attrs['user_type'] == 'recruiter':
            if not attrs.get('company_name'):
                raise serializers.ValidationError(
                    {"company_name": "Company name is required for recruiters"}
                )
        
        return attrs

    def create(self, validated_data):
        # Extract user type and profile fields
        user_type = validated_data.pop('user_type')
        desired_job_title = validated_data.pop('desired_job_title', None)
        desired_location = validated_data.pop('desired_location', None)
        experience_years = validated_data.pop('experience_years', None)
        company_name = validated_data.pop('company_name', None)
        company_website = validated_data.pop('company_website', None)
        phone = validated_data.pop('phone', None)
        validated_data.pop('password2')
        
        # Create user
        user = User.objects.create_user(**validated_data)
        
        # Update profile with role and additional fields
        profile = user.profile
        profile.role = user_type
        profile.phone = phone
        
        if user_type == 'job_seeker':
            profile.desired_job_title = desired_job_title
            profile.desired_location = desired_location
            profile.experience_years = experience_years
        elif user_type == 'recruiter':
            profile.company_name = company_name
            profile.company_website = company_website
            profile.is_verified_recruiter = False  # Admin must verify
        
        profile.save()
        
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint"""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    """Serializer for login endpoint"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile management"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ('id', 'user', 'username', 'email', 'role', 'department', 'phone', 'bio', 
                  'is_admin', 'is_manager', 'can_write', 'created_at', 'updated_at')
        read_only_fields = ('id', 'user', 'username', 'email', 'is_admin', 'is_manager', 
                           'can_write', 'created_at', 'updated_at')


class UpdateUserRoleSerializer(serializers.Serializer):
    """Serializer for updating user role (admin only)"""
    user_id = serializers.IntegerField(required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    
    def validate_user_id(self, value):
        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User does not exist.")
        return value


class JobSeekerProfileSerializer(serializers.ModelSerializer):
    """Serializer for Job Seeker Profile with all relevant fields"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    profile_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'bio', 
            'desired_job_title', 'desired_location', 
            'experience_years', 'skills', 'certifications', 
            'availability',
            'profile_completion', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'username', 'email']
    
    def get_profile_completion(self, obj):
        """Calculate profile completion percentage for job seekers"""
        fields_to_check = [
            obj.user.first_name,
            obj.user.last_name,
            obj.phone,
            obj.bio,
            obj.desired_job_title,
            obj.desired_location,
            obj.experience_years is not None,
            obj.skills and len(obj.skills) > 0,
            obj.certifications and len(obj.certifications) > 0,
            obj.availability
        ]
        completed = sum(1 for field in fields_to_check if field)
        return round((completed / len(fields_to_check)) * 100)
    
    def update(self, instance, validated_data):
        """Update user and profile data"""
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        return super().update(instance, validated_data)


class RecruiterProfileSerializer(serializers.ModelSerializer):
    """Serializer for Recruiter Profile with all relevant fields"""
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', required=False, allow_blank=True)
    last_name = serializers.CharField(source='user.last_name', required=False, allow_blank=True)
    profile_completion = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone', 'bio',
            'company_name', 'company_website', 'is_verified_recruiter',
            'profile_completion', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'username', 'email', 'is_verified_recruiter']
    
    def get_profile_completion(self, obj):
        """Calculate profile completion percentage for recruiters"""
        fields_to_check = [
            obj.user.first_name,
            obj.user.last_name,
            obj.phone,
            obj.bio,
            obj.company_name,
            obj.company_website,
        ]
        completed = sum(1 for field in fields_to_check if field)
        return round((completed / len(fields_to_check)) * 100)
    
    def update(self, instance, validated_data):
        """Update user and profile data"""
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.save()
        
        return super().update(instance, validated_data)
