"""
Recruiter API Endpoints
Allows recruiters to view candidates, manage applications, search resumes
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Max
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging

from .models import Job
from .application_models import JobApplication, JobView
from resumes.models import Resume
from .serializers import (
    CandidateSerializer,
    ResumeDetailSerializer,
    JobApplicationSerializer,
    JobApplicationUpdateSerializer,
    RecruiterJobSerializer,
    ShortlistedCandidateSerializer,
)

logger = logging.getLogger('jobs')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_candidates(request):
    """
    List all candidates/resumes
    GET /api/recruiter/candidates/
    Query params: search, min_score, skills, location, is_active
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Base query - only public resumes
    resumes = Resume.objects.filter(is_public=True).select_related('user')
    
    # Filter by active status
    is_active = request.query_params.get('is_active')
    if is_active == 'true':
        resumes = resumes.filter(is_active=True)
    
    # Search by name or email
    search = request.query_params.get('search')
    if search:
        resumes = resumes.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(raw_text__icontains=search)
        )
    
    # Filter by minimum score
    min_score = request.query_params.get('min_score')
    if min_score:
        try:
            resumes = resumes.filter(total_score__gte=float(min_score))
        except ValueError:
            pass
    
    # Filter by skills (comma-separated)
    skills = request.query_params.get('skills')
    if skills:
        skill_list = [s.strip() for s in skills.split(',')]
        for skill in skill_list:
            resumes = resumes.filter(
                Q(skills__icontains=skill) |
                Q(raw_text__icontains=skill)
            )
    
    # Ordering
    order_by = request.query_params.get('order_by', '-total_score')
    resumes = resumes.order_by(order_by)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = resumes.count()
    resumes_page = resumes[start:end]
    
    serializer = CandidateSerializer(resumes_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_candidate_detail(request, resume_id):
    """
    Get detailed candidate/resume information
    GET /api/recruiter/candidates/{resume_id}/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    resume = get_object_or_404(Resume, id=resume_id, is_public=True)
    
    # Get application history for this candidate
    applications = JobApplication.objects.filter(
        applicant=resume.user
    ).select_related('job').order_by('-applied_at')[:10]
    
    serializer = ResumeDetailSerializer(resume)
    data = serializer.data
    data['applications'] = JobApplicationSerializer(applications, many=True).data
    
    logger.info(f"Recruiter {request.user.username} viewed candidate {resume_id}")
    
    return Response(data, status=status.HTTP_200_OK)


# ============= APPLICATION MANAGEMENT =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_applications(request):
    """
    List all applications (for recruiter's jobs or all if admin)
    GET /api/recruiter/applications/
    Query params: job_id, status, rating
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    applications = JobApplication.objects.select_related('job', 'applicant', 'resume')
    
    # Filter by job
    job_id = request.query_params.get('job_id')
    if job_id:
        applications = applications.filter(job_id=job_id)
    
    # Filter by status
    app_status = request.query_params.get('status')
    if app_status:
        applications = applications.filter(status=app_status)
    
    # Filter by rating
    rating = request.query_params.get('rating')
    if rating:
        try:
            applications = applications.filter(rating=int(rating))
        except ValueError:
            pass
    
    # Only show unreviewed if requested
    if request.query_params.get('unreviewed') == 'true':
        applications = applications.filter(status='pending')
    
    # Ordering
    order_by = request.query_params.get('order_by', '-applied_at')
    applications = applications.order_by(order_by)
    
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
def get_application_detail(request, application_id):
    """
    Get application details
    GET /api/recruiter/applications/{application_id}/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    application = get_object_or_404(
        JobApplication.objects.select_related('job', 'applicant', 'resume'),
        id=application_id
    )
    
    serializer = JobApplicationSerializer(application)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status(request, application_id):
    """
    Update application status and add notes
    PATCH /api/recruiter/applications/{application_id}/
    Body: {status, recruiter_notes, rating, interview_date, interview_notes}
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can update applications'
        }, status=status.HTTP_403_FORBIDDEN)
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    serializer = JobApplicationUpdateSerializer(
        application,
        data=request.data,
        partial=True,
        context={'request': request}
    )
    
    if serializer.is_valid():
        # Check if status is changing for notification
        old_status = application.status
        new_status = request.data.get('status', old_status)
        status_changed = old_status != new_status
        
        # Mark as reviewed if status changes from pending
        if application.status == 'pending' and request.data.get('status') != 'pending':
            if not application.reviewed_by:
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
        
        serializer.save()
        
        logger.info(f"Recruiter {request.user.username} updated application {application_id}")
        
        # Notify job seeker if status changed
        if status_changed and application.applicant.profile.is_job_seeker:
            try:
                from .notifications import notify_job_seeker_application_status_change
                notify_job_seeker_application_status_change(application)
            except Exception as e:
                logger.error(f"Failed to notify job seeker: {e}")
        
        return Response({
            'message': 'Application updated successfully',
            'application': JobApplicationSerializer(application).data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def bulk_update_applications(request):
    """
    Bulk update multiple applications
    POST /api/recruiter/applications/bulk-update/
    Body: {application_ids: [], status, recruiter_notes}
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can update applications'
        }, status=status.HTTP_403_FORBIDDEN)
    
    application_ids = request.data.get('application_ids', [])
    new_status = request.data.get('status')
    notes = request.data.get('recruiter_notes')
    
    if not application_ids or not new_status:
        return Response({
            'error': 'application_ids and status are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    applications = JobApplication.objects.filter(id__in=application_ids)
    
    updated_count = 0
    for app in applications:
        app.status = new_status
        if notes:
            app.recruiter_notes = (app.recruiter_notes or '') + f"\n\n[{timezone.now()}] {notes}"
        if app.status == 'pending':
            app.reviewed_by = request.user
            app.reviewed_at = timezone.now()
        app.save()
        updated_count += 1
    
    logger.info(f"Recruiter {request.user.username} bulk updated {updated_count} applications")
    
    return Response({
        'message': f'{updated_count} applications updated successfully',
        'updated_count': updated_count
    }, status=status.HTTP_200_OK)


# ============= RECRUITER DASHBOARD =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recruiter_dashboard(request):
    """
    Get recruiter dashboard stats
    GET /api/recruiter/dashboard/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Application stats
    applications = JobApplication.objects.all()
    total_applications = applications.count()
    pending = applications.filter(status='pending').count()
    reviewing = applications.filter(status='reviewing').count()
    shortlisted = applications.filter(status='shortlisted').count()
    interviewed = applications.filter(status='interviewed').count()
    offers = applications.filter(status='offer_sent').count()
    
    # Candidate stats
    total_candidates = Resume.objects.filter(is_public=True).count()
    active_candidates = Resume.objects.filter(is_public=True, is_active=True).count()
    avg_score = Resume.objects.filter(is_public=True).aggregate(Avg('total_score'))['total_score__avg'] or 0
    
    # Recent applications
    recent_apps = applications.order_by('-applied_at')[:10]
    
    # Top jobs by applications
    top_jobs = Job.objects.annotate(
        app_count=Count('applications')
    ).order_by('-app_count')[:5]
    
    return Response({
        'application_stats': {
            'total': total_applications,
            'pending': pending,
            'reviewing': reviewing,
            'shortlisted': shortlisted,
            'interviewed': interviewed,
            'offers': offers,
        },
        'candidate_stats': {
            'total': total_candidates,
            'active': active_candidates,
            'average_score': round(avg_score, 2),
        },
        'recent_applications': JobApplicationSerializer(recent_apps, many=True).data,
        'top_jobs': RecruiterJobSerializer(top_jobs, many=True).data
    }, status=status.HTTP_200_OK)


# ============= SHORTLIST MANAGEMENT =============

from .application_models import ShortlistedCandidate

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shortlist_candidate(request, resume_id):
    """Add candidate to recruiter shortlist"""
    if not request.user.profile.is_recruiter:
        return Response({'error': 'Only recruiters can shortlist'}, status=status.HTTP_403_FORBIDDEN)
    resume = get_object_or_404(Resume, id=resume_id, is_public=True)
    obj, created = ShortlistedCandidate.objects.get_or_create(recruiter=request.user, resume=resume)
    return Response({
        'created': created,
        'shortlist': ShortlistedCandidateSerializer(obj).data
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_shortlist(request):
    """List recruiter shortlist"""
    if not request.user.profile.is_recruiter:
        return Response({'error': 'Only recruiters can view shortlist'}, status=status.HTTP_403_FORBIDDEN)
    qs = ShortlistedCandidate.objects.filter(recruiter=request.user).select_related('resume', 'recruiter')
    serializer = ShortlistedCandidateSerializer(qs, many=True)
    return Response({'count': len(serializer.data), 'results': serializer.data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_shortlisted(request, shortlist_id):
    """Remove a candidate from shortlist"""
    if not request.user.profile.is_recruiter:
        return Response({'error': 'Only recruiters can modify shortlist'}, status=status.HTTP_403_FORBIDDEN)
    obj = get_object_or_404(ShortlistedCandidate, id=shortlist_id, recruiter=request.user)
    obj.delete()
    return Response({'deleted': True}, status=status.HTTP_200_OK)


# ============= JOB MANAGEMENT FOR RECRUITERS =============

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_jobs_with_stats(request):
    """
    List jobs with application statistics
    GET /api/recruiter/jobs/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    jobs = Job.objects.annotate(
        total_applications=Count('applications'),
        pending_applications=Count('applications', filter=Q(applications__status='pending')),
        total_views=Count('views')
    ).order_by('-posted_date')
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = jobs.count()
    jobs_page = jobs[start:end]
    
    serializer = RecruiterJobSerializer(jobs_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_applications(request, job_id):
    """
    Get all applications for a specific job
    GET /api/recruiter/jobs/{job_id}/applications/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    job = get_object_or_404(Job, id=job_id)
    applications = JobApplication.objects.filter(job=job).select_related('applicant', 'resume')
    
    # Filter by status
    app_status = request.query_params.get('status')
    if app_status:
        applications = applications.filter(status=app_status)
    
    applications = applications.order_by('-applied_at')
    
    serializer = JobApplicationSerializer(applications, many=True)
    
    return Response({
        'job': {
            'id': job.id,
            'title': job.title,
            'company': job.company,
        },
        'count': applications.count(),
        'applications': serializer.data
    }, status=status.HTTP_200_OK)


# ============= JOB MANAGEMENT APIs =============

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job(request):
    """
    Create a new job posting
    POST /api/recruiter/jobs/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can create jobs'
        }, status=status.HTTP_403_FORBIDDEN)

    from .serializers import JobCreateSerializer

    serializer = JobCreateSerializer(data=request.data)
    if serializer.is_valid():
        job = serializer.save(posted_by=request.user)
        return Response({
            'success': True,
            'message': 'Job created successfully',
            'job': RecruiterJobSerializer(job).data
        }, status=status.HTTP_201_CREATED)

    return Response({
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_job(request, job_id):
    """
    Update an existing job posting
    PUT /api/recruiter/jobs/{job_id}/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can update jobs'
        }, status=status.HTTP_403_FORBIDDEN)

    job = get_object_or_404(Job, id=job_id, posted_by=request.user)

    from .serializers import JobCreateSerializer
    serializer = JobCreateSerializer(job, data=request.data, partial=True)
    if serializer.is_valid():
        job = serializer.save()
        return Response({
            'success': True,
            'message': 'Job updated successfully',
            'job': RecruiterJobSerializer(job).data
        }, status=status.HTTP_200_OK)

    return Response({
        'error': 'Invalid data',
        'details': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job(request, job_id):
    """
    Delete/archive a job posting
    DELETE /api/recruiter/jobs/{job_id}/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can delete jobs'
        }, status=status.HTTP_403_FORBIDDEN)

    job = get_object_or_404(Job, id=job_id, posted_by=request.user)

    # Soft delete by changing status to archived
    job.status = 'archived'
    job.save()

    return Response({
        'success': True,
        'message': 'Job archived successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_my_jobs(request):
    """
    List jobs posted by the recruiter
    GET /api/recruiter/my-jobs/
    """
    if not request.user.profile.is_recruiter:
        return Response({
            'error': 'Only recruiters can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)

    jobs = Job.objects.filter(posted_by=request.user).prefetch_related('applications')

    # Add application stats
    jobs_with_stats = []
    for job in jobs:
        applications = job.applications.all()
        stats = {
            'total': applications.count(),
            'pending': applications.filter(status='pending').count(),
            'reviewing': applications.filter(status='reviewing').count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'rejected': applications.filter(status='rejected').count(),
        }

        job_data = RecruiterJobSerializer(job).data
        job_data['application_stats'] = stats
        jobs_with_stats.append(job_data)

    return Response({
        'count': len(jobs_with_stats),
        'jobs': jobs_with_stats
    }, status=status.HTTP_200_OK)
