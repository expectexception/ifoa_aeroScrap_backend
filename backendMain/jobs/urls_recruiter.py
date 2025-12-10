"""
URL routing for Recruiter endpoints
"""
from django.urls import path
from . import api_recruiter

urlpatterns = [
    # Candidate browsing
    path('candidates/', api_recruiter.list_candidates, name='recruiter_list_candidates'),
    path('candidates/<int:resume_id>/', api_recruiter.get_candidate_detail, name='recruiter_candidate_detail'),
    
    # Application management
    path('applications/', api_recruiter.list_applications, name='recruiter_list_applications'),
    path('applications/<int:application_id>/', api_recruiter.get_application_detail, name='recruiter_application_detail'),
    path('applications/<int:application_id>/update/', api_recruiter.update_application_status, name='recruiter_update_application'),
    path('applications/bulk-update/', api_recruiter.bulk_update_applications, name='recruiter_bulk_update'),
    
    # Job management
    path('jobs/', api_recruiter.list_jobs_with_stats, name='recruiter_list_jobs'),
    path('jobs/<int:job_id>/applications/', api_recruiter.get_job_applications, name='recruiter_job_applications'),
    
    # Job creation and management
    path('my-jobs/', api_recruiter.list_my_jobs, name='recruiter_my_jobs'),
    path('jobs/create/', api_recruiter.create_job, name='recruiter_create_job'),
    path('jobs/<int:job_id>/update/', api_recruiter.update_job, name='recruiter_update_job'),
    path('jobs/<int:job_id>/delete/', api_recruiter.delete_job, name='recruiter_delete_job'),
    
    # Dashboard
    path('dashboard/', api_recruiter.recruiter_dashboard, name='recruiter_dashboard'),
    # Shortlist
    path('shortlist/<int:resume_id>/', api_recruiter.shortlist_candidate, name='recruiter_shortlist_add'),
    path('shortlist/', api_recruiter.list_shortlist, name='recruiter_shortlist_list'),
    path('shortlist/remove/<int:shortlist_id>/', api_recruiter.remove_shortlisted, name='recruiter_shortlist_remove'),
]
