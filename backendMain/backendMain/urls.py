"""
URL configuration for backendMain project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
import logging

logger = logging.getLogger(__name__)

# Configure default admin site
admin.site.site_header = 'IFOA Dashboard Backend'
admin.site.site_title = 'IFOA Admin Portal'
admin.site.index_title = 'Welcome to IFOA Aviation Management System'

# Attempt to mount django-ninja API if available. This makes the project
# import-safe when `django-ninja` isn't installed (for lightweight testing).
try:
    from ninja import NinjaAPI
    from resumes.api import router as resumes_router
    from jobs.api import router as jobs_router

    api = NinjaAPI()
    api.add_router('', resumes_router)
    api.add_router('/jobs/', jobs_router)
    
    urlpatterns = [
        path('admin/', admin.site.urls),  # Django Unfold admin
        
        # Authentication endpoints (REST Framework)
        path('api/auth/', include('users.urls')),
        
        # Job Seeker endpoints (REST Framework)
        path('api/job-seeker/', include('jobs.urls_job_seeker')),
        
        # Recruiter endpoints (REST Framework)
        path('api/recruiter/', include('jobs.urls_recruiter')),
        
        # Resume management (REST Framework - shared between job seekers and recruiters)
        path('api/resumes/', include('resumes.urls')),
        
        # Scraper Management endpoints (REST Framework)
        path('api/scrapers/', include('scraper_manager.urls')),
        
        # Health check endpoints
        path('api/health/', lambda request: JsonResponse({'ok': True, 'source': 'django-url-health'})),
        path('api/jobs/health', lambda request: JsonResponse({'ok': True, 'source': 'django-jobs-health'})),
        
        # Legacy Ninja API (for backward compatibility)
        path('api/', api.urls),
    ]
except Exception as exc:
    # If Ninja isn't installed, fall back to admin only and log a helpful message.
    logger.warning('django-ninja not available; API routes not mounted: %s', exc)
    
    urlpatterns = [
        path('admin/', admin.site.urls),  # Django Unfold admin
        path('api/auth/', include('users.urls')),
        path('api/job-seeker/', include('jobs.urls_job_seeker')),
        path('api/recruiter/', include('jobs.urls_recruiter')),
        path('api/resumes/', include('resumes.urls')),
        path('api/scrapers/', include('scraper_manager.urls')),
    ]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
