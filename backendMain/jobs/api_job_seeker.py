"""
Job Seeker API Endpoints
Allows job seekers to browse jobs, apply, manage applications
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Exists, OuterRef
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from .models import Job
from .application_models import JobApplication, SavedJob, JobView
from resumes.models import Resume
from .serializers import (
    JobListSerializer,
    JobDetailSerializer,
    JobApplicationSerializer,
    JobApplicationCreateSerializer,
    SavedJobSerializer,
)

logger = logging.getLogger('jobs')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_jobs_for_job_seeker(request):
    """
    List all available jobs with filters
    GET /api/job-seeker/jobs/
    Query params: search, location, operation_type, senior_flag, status
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Base query - only active jobs
    jobs = Job.objects.filter(status='active')
    
    # Search by title or company
    search = request.query_params.get('search')
    if search:
        jobs = jobs.filter(
            Q(title__icontains=search) |
            Q(company__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Filter by location
    location = request.query_params.get('location')
    if location:
        jobs = jobs.filter(
            Q(location__icontains=location) |
            Q(country_code__iexact=location)
        )
    
    # Filter by operation type
    operation_type = request.query_params.get('operation_type')
    if operation_type:
        jobs = jobs.filter(operation_type=operation_type)
    
    # Filter by seniority
    senior_only = request.query_params.get('senior_only')
    if senior_only == 'true':
        jobs = jobs.filter(senior_flag=True)
    
    # Annotate with application status
    jobs = jobs.annotate(
        user_applied=Exists(
            JobApplication.objects.filter(
                job=OuterRef('pk'),
                applicant=request.user
            )
        ),
        user_saved=Exists(
            SavedJob.objects.filter(
                job=OuterRef('pk'),
                user=request.user
            )
        ),
        total_applications=Count('applications')
    )
    
    # Ordering
    order_by = request.query_params.get('order_by', '-posted_date')
    jobs = jobs.order_by(order_by)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = jobs.count()
    jobs_page = jobs[start:end]
    
    serializer = JobListSerializer(jobs_page, many=True, context={'request': request})
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_detail(request, job_id):
    """
    Get detailed job information
    GET /api/job-seeker/jobs/{job_id}/
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    job = get_object_or_404(Job, id=job_id, status='active')
    
    # Track job view
    JobView.objects.create(
        job=job,
        user=request.user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
    )
    
    # Check if user applied or saved
    user_applied = JobApplication.objects.filter(
        job=job,
        applicant=request.user
    ).exists()
    
    user_saved = SavedJob.objects.filter(
        job=job,
        user=request.user
    ).exists()
    
    serializer = JobDetailSerializer(job, context={'request': request})
    data = serializer.data
    data['user_applied'] = user_applied
    data['user_saved'] = user_saved
    
    logger.info(f"Job seeker {request.user.username} viewed job {job.id}")
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_to_job(request, job_id):
    """
    Apply to a job
    POST /api/job-seeker/jobs/{job_id}/apply/
    Body: {resume_id, cover_letter, applicant_notes}
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can apply to jobs'
        }, status=status.HTTP_403_FORBIDDEN)
    
    job = get_object_or_404(Job, id=job_id, status='active')
    
    # Check if already applied
    if JobApplication.objects.filter(job=job, applicant=request.user).exists():
        return Response({
            'error': 'You have already applied to this job'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Validate resume
    resume_id = request.data.get('resume_id')
    resume = None
    if resume_id:
        try:
            resume = Resume.objects.get(id=resume_id, user=request.user)
        except Resume.DoesNotExist:
            return Response({
                'error': 'Resume not found or does not belong to you'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Create application
    serializer = JobApplicationCreateSerializer(data=request.data, context={'request': request, 'job': job, 'resume': resume})
    
    if serializer.is_valid():
        application = serializer.save(
            job=job,
            applicant=request.user,
            resume=resume,
            ip_address=request.META.get('REMOTE_ADDR'),
            source_device=request.META.get('HTTP_USER_AGENT', '')[:50]
        )
        
        logger.info(f"Job seeker {request.user.username} applied to job {job.id}")
        
        # Notify the recruiter who posted the job
        if job.posted_by and job.posted_by.profile.is_recruiter:
            try:
                from .notifications import notify_recruiter_new_application
                notify_recruiter_new_application(job.posted_by, application)
            except Exception as e:
                logger.error(f"Failed to notify recruiter: {e}")
        
        return Response({
            'message': 'Application submitted successfully',
            'application': JobApplicationSerializer(application).data
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_applications(request):
    """
    Get all my applications
    GET /api/job-seeker/applications/
    Query params: status (filter by status)
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    applications = JobApplication.objects.filter(applicant=request.user).select_related('job', 'resume')
    
    # Filter by status
    app_status = request.query_params.get('status')
    if app_status:
        applications = applications.filter(status=app_status)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = applications.count()
    apps_page = applications[start:end]
    
    serializer = JobApplicationSerializer(apps_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def application_detail(request, application_id):
    """
    Get application details
    GET /api/job-seeker/applications/{application_id}/
    """
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        applicant=request.user
    )
    
    serializer = JobApplicationSerializer(application)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw_application(request, application_id):
    """
    Withdraw an application
    POST /api/job-seeker/applications/{application_id}/withdraw/
    """
    application = get_object_or_404(
        JobApplication,
        id=application_id,
        applicant=request.user
    )
    
    if not application.is_active:
        return Response({
            'error': 'Application is already closed'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    application.status = 'withdrawn'
    application.save(update_fields=['status', 'updated_at'])
    
    logger.info(f"Job seeker {request.user.username} withdrew application {application_id}")
    
    return Response({
        'message': 'Application withdrawn successfully'
    }, status=status.HTTP_200_OK)


# ============= SAVED JOBS =============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_job(request, job_id):
    """
    Save/bookmark a job
    POST /api/job-seeker/jobs/{job_id}/save/
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can save jobs'
        }, status=status.HTTP_403_FORBIDDEN)
    
    job = get_object_or_404(Job, id=job_id)
    
    # Check if already saved
    saved, created = SavedJob.objects.get_or_create(
        user=request.user,
        job=job,
        defaults={'notes': request.data.get('notes', '')}
    )
    
    if not created:
        return Response({
            'message': 'Job already saved'
        }, status=status.HTTP_200_OK)
    
    logger.info(f"Job seeker {request.user.username} saved job {job_id}")
    
    return Response({
        'message': 'Job saved successfully',
        'saved_job': SavedJobSerializer(saved).data
    }, status=status.HTTP_201_CREATED)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def unsave_job(request, job_id):
    """
    Remove saved job
    DELETE /api/job-seeker/jobs/{job_id}/save/
    """
    saved_job = get_object_or_404(SavedJob, user=request.user, job_id=job_id)
    saved_job.delete()
    
    return Response({
        'message': 'Job removed from saved list'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_saved_jobs(request):
    """
    Get all saved jobs
    GET /api/job-seeker/saved-jobs/
    """
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related('job')
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = saved_jobs.count()
    saved_page = saved_jobs[start:end]
    
    serializer = SavedJobSerializer(saved_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


# ============= DASHBOARD/STATS =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_seeker_dashboard(request):
    """
    Get job seeker dashboard stats
    GET /api/job-seeker/dashboard/
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Application stats
    applications = JobApplication.objects.filter(applicant=request.user)
    total_applications = applications.count()
    pending = applications.filter(status='pending').count()
    reviewing = applications.filter(status='reviewing').count()
    shortlisted = applications.filter(status='shortlisted').count()
    interviewed = applications.filter(status='interviewed').count()
    offers = applications.filter(status='offer_sent').count()
    accepted = applications.filter(status='accepted').count()
    rejected = applications.filter(status='rejected').count()
    
    # Saved jobs
    saved_count = SavedJob.objects.filter(user=request.user).count()
    
    # Resumes
    resume_count = Resume.objects.filter(user=request.user).count()
    active_resumes = Resume.objects.filter(user=request.user, is_active=True).count()
    
    # Recent applications
    recent_apps = applications.order_by('-applied_at')[:5]
    
    return Response({
        'stats': {
            'total_applications': total_applications,
            'pending': pending,
            'reviewing': reviewing,
            'shortlisted': shortlisted,
            'interviewed': interviewed,
            'offers': offers,
            'accepted': accepted,
            'rejected': rejected,
            'saved_jobs': saved_count,
            'total_resumes': resume_count,
            'active_resumes': active_resumes,
        },
        'recent_applications': JobApplicationSerializer(recent_apps, many=True).data
    }, status=status.HTTP_200_OK)
