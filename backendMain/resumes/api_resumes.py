"""
Resume API Views (REST Framework)
Handles resume upload, management for job seekers
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import FileResponse
import base64
import os
from tempfile import NamedTemporaryFile
import logging

from .models import Resume
from . import utils
from .serializers import ResumeSerializer, ResumeDetailSerializer

logger = logging.getLogger('resumes')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_resumes(request):
    """
    List resumes - job seekers see their own, recruiters see all public
    GET /api/resumes/
    """
    if request.user.profile.is_job_seeker:
        # Job seekers see only their resumes
        resumes = Resume.objects.filter(user=request.user)
    elif request.user.profile.is_recruiter:
        # Recruiters see all public resumes
        resumes = Resume.objects.filter(is_public=True)
    else:
        # Admins see everything
        resumes = Resume.objects.all()
    
    # Search filter
    search = request.query_params.get('search')
    if search:
        resumes = resumes.filter(
            name__icontains=search
        ) | resumes.filter(email__icontains=search)
    
    # Pagination
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 20))
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = resumes.count()
    resumes_page = resumes[start:end]
    
    serializer = ResumeSerializer(resumes_page, many=True)
    
    return Response({
        'count': total_count,
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_detail(request, resume_id):
    """
    Get resume details
    GET /api/resumes/{resume_id}/
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    # Permission check
    if request.user.profile.is_job_seeker:
        if resume.user != request.user:
            return Response({
                'error': 'You can only view your own resumes'
            }, status=status.HTTP_403_FORBIDDEN)
    elif request.user.profile.is_recruiter:
        if not resume.is_public:
            return Response({
                'error': 'This resume is not public'
            }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = ResumeDetailSerializer(resume)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_resume_file(request):
    """
    Upload resume file
    POST /api/resumes/upload/
    """
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can upload resumes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    file = request.FILES.get('file')
    if not file:
        return Response({
            'error': 'No file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not file.name.lower().endswith(('.pdf', '.txt', '.docx', '.doc')):
        return Response({
            'error': 'Supported formats: PDF, TXT, DOC, DOCX'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    content = file.read()
    if not content:
        return Response({
            'error': 'Empty file provided'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Parse resume
    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    parsed_result = {}
    raw_text = ''
    try:
        if utils.parser:
            parsed_result = utils.parser.parse(tmp_path)
            raw_text = utils.parser.extract_text(tmp_path)
    except Exception as e:
        logger.error(f"Error parsing resume: {str(e)}")
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
    
    # Create resume record
    resume = Resume.objects.create(
        user=request.user,
        filename=file.name,
        name=parsed_result.get('name', request.user.get_full_name() or request.user.username),
        email=(parsed_result.get('emails', [''])[0] if parsed_result.get('emails') else request.user.email),
        phones=parsed_result.get('phones', []),
        skills=parsed_result.get('skills', {}),
        aviation=parsed_result.get('aviation', {}),
        experience={
            'items': parsed_result.get('experience_items', []),
            'summary': parsed_result.get('experience_summary', {})
        },
        total_score=parsed_result.get('total_score', 0.0),
        raw_text=raw_text,
        file_content=base64.b64encode(content).decode('utf-8'),
        parsed_at=parsed_result.get('parsed_at'),
        is_public=True,
        is_active=True
    )
    
    logger.info(f"Job seeker {request.user.username} uploaded resume {resume.id}")
    
    serializer = ResumeDetailSerializer(resume)
    return Response({
        'message': 'Resume uploaded successfully',
        'resume': serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_resume(request, resume_id):
    """
    Update resume metadata
    PATCH /api/resumes/{resume_id}/update/
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    if not request.user.profile.is_job_seeker or resume.user != request.user:
        return Response({
            'error': 'You can only update your own resumes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Allow updating: name, email, phones, is_public, is_active
    allowed_fields = ['name', 'email', 'phones', 'is_public', 'is_active']
    for field in allowed_fields:
        if field in request.data:
            setattr(resume, field, request.data[field])
    
    resume.save()
    
    serializer = ResumeDetailSerializer(resume)
    return Response({
        'message': 'Resume updated successfully',
        'resume': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_resume(request, resume_id):
    """
    Delete resume
    DELETE /api/resumes/{resume_id}/delete/
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    if not request.user.profile.is_job_seeker or resume.user != request.user:
        return Response({
            'error': 'You can only delete your own resumes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    resume.delete()
    
    logger.info(f"Job seeker {request.user.username} deleted resume {resume_id}")
    
    return Response({
        'message': 'Resume deleted successfully'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_resume_file(request, resume_id):
    """
    Download resume file
    GET /api/resumes/{resume_id}/download/
    """
    resume = get_object_or_404(Resume, id=resume_id)
    
    # Permission check
    if request.user.profile.is_job_seeker:
        if resume.user != request.user:
            return Response({
                'error': 'You can only download your own resumes'
            }, status=status.HTTP_403_FORBIDDEN)
    elif request.user.profile.is_recruiter:
        if not resume.is_public:
            return Response({
                'error': 'This resume is not public'
            }, status=status.HTTP_403_FORBIDDEN)
    
    if not resume.file_content:
        return Response({
            'error': 'No file stored for this resume'
        }, status=status.HTTP_404_NOT_FOUND)
    
    content = base64.b64decode(resume.file_content)
    ext = os.path.splitext(resume.filename)[1].lower()
    
    with NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    media_types = {
        '.pdf': 'application/pdf',
        '.doc': 'application/msword',
        '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        '.txt': 'text/plain'
    }
    media_type = media_types.get(ext, 'application/octet-stream')
    
    return FileResponse(open(tmp_path, 'rb'), content_type=media_type, filename=resume.filename)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_resume_stats(request):
    """
    Get resume statistics
    GET /api/resumes/stats/
    """
    if request.user.profile.is_job_seeker:
        # Job seeker stats (own resumes)
        resumes = Resume.objects.filter(user=request.user)
        total = resumes.count()
        active = resumes.filter(is_active=True).count()
        avg_score = sum(r.total_score for r in resumes) / total if total > 0 else 0
        
        return Response({
            'total_resumes': total,
            'active_resumes': active,
            'average_score': round(avg_score, 2),
        }, status=status.HTTP_200_OK)
    
    elif request.user.profile.is_recruiter:
        # Recruiter stats (all public resumes)
        resumes = Resume.objects.filter(is_public=True)
        total = resumes.count()
        active = resumes.filter(is_active=True).count()
        avg_score = sum(r.total_score for r in resumes) / total if total > 0 else 0
        
        return Response({
            'total_candidates': total,
            'active_candidates': active,
            'average_score': round(avg_score, 2),
        }, status=status.HTTP_200_OK)
    
    return Response({
        'error': 'Invalid user role'
    }, status=status.HTTP_403_FORBIDDEN)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_resume_with_form(request):
    """
    Upload resume with additional form data
    POST /api/resumes/upload-with-form/
    
    Form fields:
    - file: Resume file (optional if all info provided in form)
    - full_name: Full name (required)
    - email: Email address (required)
    - phone: Phone number (optional)
    - education: JSON array of education entries (optional)
    - experience: JSON array of experience entries (optional)
    - roles: JSON array of role preferences (optional)
    - certificates: JSON array of certificates (optional)
    - licenses: JSON array of licenses (optional)
    - skills: JSON array of skills (optional)
    - aviation_hours: Total flight hours (optional)
    - aircraft_types: JSON array of aircraft types (optional)
    """
    import json
    from datetime import datetime
    
    if not request.user.profile.is_job_seeker:
        return Response({
            'error': 'Only job seekers can upload resumes'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # Extract required fields
    full_name = request.data.get('full_name', '').strip()
    email = request.data.get('email', '').strip()
    
    if not full_name or not email:
        return Response({
            'error': 'full_name and email are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Extract optional fields
    phone = request.data.get('phone', '').strip()
    file = request.FILES.get('file')
    
    # Parse JSON fields
    def safe_json_parse(field_name, default=None):
        try:
            value = request.data.get(field_name, '')
            if isinstance(value, str) and value:
                return json.loads(value)
            return value if value else (default or [])
        except (json.JSONDecodeError, ValueError):
            return default or []
    
    education = safe_json_parse('education', [])
    experience = safe_json_parse('experience', [])
    roles = safe_json_parse('roles', [])
    certificates = safe_json_parse('certificates', [])
    licenses = safe_json_parse('licenses', [])
    skills = safe_json_parse('skills', [])
    aircraft_types = safe_json_parse('aircraft_types', [])
    
    aviation_hours = request.data.get('aviation_hours', '')
    try:
        aviation_hours = int(aviation_hours) if aviation_hours else 0
    except ValueError:
        aviation_hours = 0
    
    # Initialize parsing variables
    raw_text = ''
    parsed_result = {
        'skills': {},
        'aviation': {},
        'experience_items': [],
        'experience_summary': {},
        'total_score': 0.0
    }
    file_content = None
    filename = 'form_submission.txt'
    
    # If file is provided, parse it
    if file:
        if not file.name.lower().endswith(('.pdf', '.txt', '.docx', '.doc')):
            return Response({
                'error': 'Supported formats: PDF, TXT, DOC, DOCX'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        content = file.read()
        if content:
            file_content = base64.b64encode(content).decode('utf-8')
            filename = file.name
            
            # Parse the file
            with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                if utils.parser:
                    parsed_result = utils.parser.parse(tmp_path)
                    raw_text = utils.parser.extract_text(tmp_path)
            except Exception as e:
                logger.error(f"Error parsing resume: {str(e)}")
            finally:
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    
    # Merge form data with parsed data
    # Form data takes precedence over parsed data
    
    # Build skills object
    form_skills = {
        'manual': skills,  # Skills from form
        'parsed': parsed_result.get('skills', {}).get('matched', []),  # Skills from file
        'count': len(skills)
    }
    
    # Build aviation object
    form_aviation = {
        'licenses': licenses,
        'certifications': certificates,
        'aircraft_types': aircraft_types,
        'total_flight_hours': aviation_hours,
    }
    # Merge with parsed aviation data
    parsed_aviation = parsed_result.get('aviation', {})
    if isinstance(parsed_aviation, dict):
        for key, value in parsed_aviation.items():
            if key not in form_aviation or not form_aviation[key]:
                form_aviation[key] = value
    
    # Build experience object
    form_experience = {
        'items': experience if experience else parsed_result.get('experience_items', []),
        'summary': {
            'total_positions': len(experience),
            'manual_entry': True
        }
    }
    
    # Calculate score based on form + parsed data
    score = 0.0
    if aviation_hours > 0:
        score += min(aviation_hours / 100, 30)  # Up to 30 points for hours
    score += len(licenses) * 5  # 5 points per license
    score += len(certificates) * 3  # 3 points per certificate
    score += len(skills) * 2  # 2 points per skill
    score += len(experience) * 5  # 5 points per experience
    score = min(score, 100)  # Cap at 100
    
    # Add parsed score if available
    if parsed_result.get('total_score', 0) > 0:
        score = (score + parsed_result.get('total_score', 0)) / 2  # Average of both
    
    # Create additional_info object
    additional_info = {
        'education': education,
        'roles': roles,
        'form_submitted': True,
        'submission_date': datetime.now().isoformat()
    }
    
    # Create resume record
    resume = Resume.objects.create(
        user=request.user,
        filename=filename,
        name=full_name,
        email=email,
        phones=[phone] if phone else [],
        skills=form_skills,
        aviation=form_aviation,
        experience=form_experience,
        total_score=round(score, 2),
        raw_text=raw_text or f"Form submission by {full_name}",
        file_content=file_content,
        parsed_at=datetime.now() if file else None,
        additional_info=additional_info,
        is_public=True,
        is_active=True
    )
    
    logger.info(f"Job seeker {request.user.username} submitted resume form with ID {resume.id}")
    
    serializer = ResumeDetailSerializer(resume)
    return Response({
        'message': 'Resume submitted successfully',
        'resume': serializer.data,
        'score': round(score, 2)
    }, status=status.HTTP_201_CREATED)
