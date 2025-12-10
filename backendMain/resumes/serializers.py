"""
Resume Serializers
"""
from rest_framework import serializers
from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    """Basic resume serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'filename', 'name', 'email', 'username', 'total_score',
            'is_public', 'is_active', 'created_at', 'updated_at'
        ]


class ResumeDetailSerializer(serializers.ModelSerializer):
    """Detailed resume serializer"""
    username = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Resume
        fields = [
            'id', 'filename', 'name', 'email', 'phones', 'username', 'user_email',
            'skills', 'aviation', 'experience', 'total_score', 'raw_text',
            'is_public', 'is_active', 'parsed_at', 'additional_info',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'user_email', 'created_at', 'updated_at', 'parsed_at']
