"""
URL routing for Job Seeker endpoints
"""
from django.urls import path
from . import api_job_seeker

urlpatterns = [
    # Job browsing
    path('jobs/', api_job_seeker.list_jobs_for_job_seeker, name='job_seeker_list_jobs'),
    path('jobs/<int:job_id>/', api_job_seeker.get_job_detail, name='job_seeker_job_detail'),
    
    # Job application
    path('jobs/<int:job_id>/apply/', api_job_seeker.apply_to_job, name='job_seeker_apply'),
    path('applications/', api_job_seeker.my_applications, name='job_seeker_applications'),
    path('applications/<int:application_id>/', api_job_seeker.application_detail, name='job_seeker_application_detail'),
    path('applications/<int:application_id>/withdraw/', api_job_seeker.withdraw_application, name='job_seeker_withdraw'),
    
    # Saved jobs
    path('jobs/<int:job_id>/save/', api_job_seeker.save_job, name='job_seeker_save_job'),
    path('saved-jobs/', api_job_seeker.list_saved_jobs, name='job_seeker_saved_jobs'),
    
    # Dashboard
    path('dashboard/', api_job_seeker.job_seeker_dashboard, name='job_seeker_dashboard'),
]
