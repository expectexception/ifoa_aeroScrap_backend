"""
Custom Permission Classes for Role-Based Access Control
"""
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class for Admin users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check superuser first
        if request.user.is_superuser:
            return True
        
        # Check role property (added by monkey patch)
        try:
            return request.user.role == 'admin'
        except AttributeError:
            return False


class IsManagerOrAbove(permissions.BasePermission):
    """
    Permission class for Manager and Admin users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Check superuser first
        if request.user.is_superuser:
            return True
        
        # Check role property (added by monkey patch)
        try:
            return request.user.role in ['admin', 'manager']
        except AttributeError:
            # If no profile exists, default to False
            return False


class IsUserOrAbove(permissions.BasePermission):
    """
    Permission class for any authenticated user
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated


class ReadOnly(permissions.BasePermission):
    """
    Permission class for read-only access
    Safe methods: GET, HEAD, OPTIONS
    """
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Admin can do anything, others can only read
    """
    def has_permission(self, request, view):
        # Allow read for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for admins
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_superuser:
            return True
        
        try:
            return request.user.role == 'admin'
        except AttributeError:
            return False


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Object-level permission to only allow owners or admins to edit
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_superuser:
            return True
        
        try:
            if request.user.role == 'admin':
                return True
        except AttributeError:
            pass
        
        # Check if object has owner attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        return False


class IsJobSeeker(permissions.BasePermission):
    """
    Permission class for Job Seeker users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            return request.user.profile.is_job_seeker
        except AttributeError:
            return False


class IsRecruiter(permissions.BasePermission):
    """
    Permission class for Recruiter users only
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            return request.user.profile.is_recruiter or request.user.is_superuser
        except AttributeError:
            return False


class IsJobSeekerOrReadOnly(permissions.BasePermission):
    """
    Job seekers can write, others can only read
    """
    def has_permission(self, request, view):
        # Allow read for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for job seekers
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            return request.user.profile.is_job_seeker
        except AttributeError:
            return False


class IsRecruiterOrReadOnly(permissions.BasePermission):
    """
    Recruiters can write, others can only read
    """
    def has_permission(self, request, view):
        # Allow read for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for recruiters
        if not request.user or not request.user.is_authenticated:
            return False
        
        try:
            return request.user.profile.is_recruiter or request.user.is_superuser
        except AttributeError:
            return False
