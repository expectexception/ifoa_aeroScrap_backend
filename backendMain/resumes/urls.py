"""
URL routing for Resume management
Shared between job seekers (own resumes) and recruiters (view all)
"""
from django.urls import path
from . import api_resumes

urlpatterns = [
    # Resume CRUD
    path('', api_resumes.list_resumes, name='list_resumes'),
    path('<int:resume_id>/', api_resumes.get_resume_detail, name='get_resume'),
    path('upload/', api_resumes.upload_resume_file, name='upload_resume'),
    path('upload-with-form/', api_resumes.upload_resume_with_form, name='upload_resume_with_form'),
    path('<int:resume_id>/update/', api_resumes.update_resume, name='update_resume'),
    path('<int:resume_id>/delete/', api_resumes.delete_resume, name='delete_resume'),
    path('<int:resume_id>/download/', api_resumes.download_resume_file, name='download_resume'),
    
    # Stats
    path('stats/', api_resumes.get_resume_stats, name='resume_stats'),
]
