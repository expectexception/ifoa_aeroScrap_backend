from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.RegisterView.as_view(), name='auth_register'),
    path('login/', views.login_view, name='auth_login'),
    path('logout/', views.logout_view, name='auth_logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # User profile endpoints
    path('profile/', views.profile_view, name='auth_profile'),
    path('profile/update/', views.update_profile_view, name='auth_profile_update'),
    path('change-password/', views.change_password_view, name='auth_change_password'),
    
    # Role-specific profile endpoints
    path('profile/job-seeker/', views.job_seeker_profile_view, name='job_seeker_profile'),
    path('profile/recruiter/', views.recruiter_profile_view, name='recruiter_profile'),
    path('profile/completion/', views.profile_completion_view, name='profile_completion'),
    
    # Status endpoint
    path('status/', views.auth_status_view, name='auth_status'),
    
    # Role management endpoints (Admin only)
    path('users/', views.list_users_view, name='list_users'),
    path('users/<int:user_id>/', views.user_detail_view, name='user_detail'),
    path('users/update-role/', views.update_user_role_view, name='update_user_role'),
    path('roles/', views.list_roles_view, name='list_roles'),
]
