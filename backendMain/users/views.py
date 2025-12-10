from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    ChangePasswordSerializer,
    LoginSerializer,
    UserProfileSerializer,
    UpdateUserRoleSerializer,
    JobSeekerProfileSerializer,
    RecruiterProfileSerializer
)
from .permissions import IsAdmin, IsAdminOrReadOnly
from .models import UserProfile
import logging

logger = logging.getLogger('users')


class RegisterView(generics.CreateAPIView):
    """
    API endpoint for user registration
    POST /api/auth/register/
    """
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate JWT tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        logger.info(f"New user registered: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    API endpoint for user login
    POST /api/auth/login/
    Body: {username, password}
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(username=username, password=password)
    
    if user is not None:
        refresh = RefreshToken.for_user(user)
        logger.info(f"User logged in: {user.username}")
        
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful'
        }, status=status.HTTP_200_OK)
    else:
        logger.warning(f"Failed login attempt for username: {username}")
        return Response({
            'error': 'Invalid credentials'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    API endpoint for user logout (blacklist refresh token)
    POST /api/auth/logout/
    Body: {refresh}
    """
    try:
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({
                'error': 'Refresh token is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        token = RefreshToken(refresh_token)
        token.blacklist()
        
        logger.info(f"User logged out: {request.user.username}")
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    """
    API endpoint to get current user profile
    GET /api/auth/profile/
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_profile_view(request):
    """
    API endpoint to update current user profile
    PUT/PATCH /api/auth/profile/update/
    """
    user = request.user
    serializer = UserSerializer(user, data=request.data, partial=True)
    
    if serializer.is_valid():
        serializer.save()
        logger.info(f"User profile updated: {user.username}")
        return Response({
            'user': serializer.data,
            'message': 'Profile updated successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    API endpoint to change user password
    POST /api/auth/change-password/
    Body: {old_password, new_password, new_password2}
    """
    serializer = ChangePasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        user = request.user
        
        # Check old password
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({
                'error': 'Wrong password'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return Response({
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def auth_status_view(request):
    """
    API endpoint to check authentication status
    GET /api/auth/status/
    """
    if request.user.is_authenticated:
        return Response({
            'authenticated': True,
            'user': UserSerializer(request.user).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'authenticated': False
        }, status=status.HTTP_200_OK)


# ============= ROLE MANAGEMENT ENDPOINTS (Admin Only) =============

@api_view(['GET'])
@permission_classes([IsAdmin])
def list_users_view(request):
    """
    API endpoint to list all users with their roles (Admin only)
    GET /api/auth/users/
    """
    users = User.objects.select_related('profile').all()
    serializer = UserSerializer(users, many=True)
    
    logger.info(f"Admin {request.user.username} listed all users")
    
    return Response({
        'count': users.count(),
        'users': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdmin])
def user_detail_view(request, user_id):
    """
    API endpoint to get user details (Admin only)
    GET /api/auth/users/<user_id>/
    """
    try:
        user = User.objects.select_related('profile').get(id=user_id)
        serializer = UserSerializer(user)
        profile_serializer = UserProfileSerializer(user.profile)
        
        return Response({
            'user': serializer.data,
            'profile': profile_serializer.data
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            'error': 'User not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAdmin])
def update_user_role_view(request):
    """
    API endpoint to update user role (Admin only)
    POST /api/auth/users/update-role/
    Body: {user_id, role}
    """
    serializer = UpdateUserRoleSerializer(data=request.data)
    
    if serializer.is_valid():
        user_id = serializer.validated_data['user_id']
        new_role = serializer.validated_data['role']
        
        try:
            user = User.objects.get(id=user_id)
            profile = user.profile
            old_role = profile.role
            
            # Prevent admins from removing their own admin role
            if request.user.id == user_id and new_role != 'admin':
                return Response({
                    'error': 'You cannot remove your own admin role'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile.role = new_role
            profile.save()
            
            logger.info(f"Admin {request.user.username} changed role of {user.username} from {old_role} to {new_role}")
            
            return Response({
                'message': f'User role updated successfully from {old_role} to {new_role}',
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrReadOnly])
def list_roles_view(request):
    """
    API endpoint to list available roles and their descriptions
    GET /api/auth/roles/
    """
    roles = [
        {
            'value': 'admin',
            'label': 'Admin',
            'description': 'Full system access - can manage users, roles, and all resources',
            'permissions': ['read', 'write', 'delete', 'manage_users', 'manage_roles']
        },
        {
            'value': 'manager',
            'label': 'Manager',
            'description': 'Can manage jobs and scrapers, view users',
            'permissions': ['read', 'write', 'delete', 'view_users']
        },
        {
            'value': 'user',
            'label': 'User',
            'description': 'Can create and edit own resources',
            'permissions': ['read', 'write']
        },
        {
            'value': 'viewer',
            'label': 'Viewer',
            'description': 'Read-only access to resources',
            'permissions': ['read']
        }
    ]
    
    return Response({
        'roles': roles
    }, status=status.HTTP_200_OK)


# ============= ROLE-SPECIFIC PROFILE ENDPOINTS =============

@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def job_seeker_profile_view(request):
    """
    API endpoint for job seeker profile management
    GET /api/auth/profile/job-seeker/ - Get job seeker profile
    PUT/PATCH /api/auth/profile/job-seeker/ - Update job seeker profile
    """
    profile = request.user.profile
    
    # Verify user is a job seeker
    if profile.role != 'job_seeker':
        return Response({
            'error': 'This endpoint is only for job seekers'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = JobSeekerProfileSerializer(profile)
        logger.info(f"Job seeker {request.user.username} retrieved profile")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PUT or PATCH request
    serializer = JobSeekerProfileSerializer(
        profile, 
        data=request.data, 
        partial=(request.method == 'PATCH')
    )
    
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Job seeker {request.user.username} updated profile")
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def recruiter_profile_view(request):
    """
    API endpoint for recruiter profile management
    GET /api/auth/profile/recruiter/ - Get recruiter profile
    PUT/PATCH /api/auth/profile/recruiter/ - Update recruiter profile
    """
    profile = request.user.profile
    
    # Verify user is a recruiter
    if profile.role != 'recruiter':
        return Response({
            'error': 'This endpoint is only for recruiters'
        }, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = RecruiterProfileSerializer(profile)
        logger.info(f"Recruiter {request.user.username} retrieved profile")
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    # PUT or PATCH request
    serializer = RecruiterProfileSerializer(
        profile, 
        data=request.data, 
        partial=(request.method == 'PATCH')
    )
    
    if serializer.is_valid():
        serializer.save()
        logger.info(f"Recruiter {request.user.username} updated profile")
        return Response({
            'message': 'Profile updated successfully',
            'profile': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_completion_view(request):
    """
    API endpoint to get profile completion percentage
    GET /api/auth/profile/completion/
    Returns completion percentage based on user role
    """
    profile = request.user.profile
    
    if profile.role == 'job_seeker':
        serializer = JobSeekerProfileSerializer(profile)
    elif profile.role == 'recruiter':
        serializer = RecruiterProfileSerializer(profile)
    else:
        return Response({
            'error': 'Profile completion is only available for job seekers and recruiters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    completion = serializer.data.get('profile_completion', 0)
    
    # Identify missing fields
    missing_fields = []
    if profile.role == 'job_seeker':
        if not request.user.first_name:
            missing_fields.append('first_name')
        if not request.user.last_name:
            missing_fields.append('last_name')
        if not profile.phone:
            missing_fields.append('phone')
        if not profile.bio:
            missing_fields.append('bio')
        if not profile.desired_job_title:
            missing_fields.append('desired_job_title')
        if not profile.desired_location:
            missing_fields.append('desired_location')
        if profile.experience_years is None:
            missing_fields.append('experience_years')
        if not profile.skills or len(profile.skills) == 0:
            missing_fields.append('skills')
        if not profile.certifications or len(profile.certifications) == 0:
            missing_fields.append('certifications')
        if not profile.availability:
            missing_fields.append('availability')
    elif profile.role == 'recruiter':
        if not request.user.first_name:
            missing_fields.append('first_name')
        if not request.user.last_name:
            missing_fields.append('last_name')
        if not profile.phone:
            missing_fields.append('phone')
        if not profile.bio:
            missing_fields.append('bio')
        if not profile.company_name:
            missing_fields.append('company_name')
        if not profile.company_website:
            missing_fields.append('company_website')
    
    logger.info(f"User {request.user.username} checked profile completion: {completion}%")
    
    return Response({
        'username': request.user.username,
        'role': profile.role,
        'completion_percentage': completion,
        'missing_fields': missing_fields,
        'is_complete': completion == 100
    }, status=status.HTTP_200_OK)
