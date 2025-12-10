import base64
import json
import os
from tempfile import NamedTemporaryFile
from typing import Optional
from datetime import datetime

from ninja import Router, File, Form, UploadedFile, Query
from django.utils.dateparse import parse_datetime
from django.http import FileResponse, Http404
from django.core.exceptions import ValidationError

from .models import Resume
from . import utils

router = Router()


@router.post('/upload-resume-with-info')
def upload_resume_with_info(request, metadata: str = Form(...), file: Optional[UploadedFile] = File(None)):
    try:
        data = json.loads(metadata)
    except json.JSONDecodeError:
        return {'error': 'Invalid JSON provided in metadata'}

    personal = data.get('personal', {})
    education = data.get('education', [])
    experience = data.get('experience', [])
    roles = data.get('roles', [])
    certificates = data.get('certificates', [])
    licenses = data.get('licenses', [])
    file_name_from_meta = data.get('fileName')

    name = personal.get('fullName')
    email = personal.get('email')
    phone = personal.get('phone')

    if not name or not email:
        raise ValidationError('fullName and email are required inside metadata.personal')

    raw_text = ''
    parsed_result = {"skills": {}, "aviation": {}, "experience_items": [], "experience_summary": {}, "total_score": 0.0}
    encoded_file_content = None

    if file:
        if not file.name.lower().endswith(('.pdf', '.txt', '.docx')):
            raise ValidationError('Supported formats: PDF, TXT, DOCX')
        content = file.read()
        if not content:
            raise ValidationError('Uploaded file is empty')
        encoded_file_content = base64.b64encode(content).decode('utf-8')

        with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if utils.parser:
                parsed_result = utils.parser.parse(tmp_path)
                raw_text = utils.parser.extract_text(tmp_path)
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    additional_info = {"personal": personal, "education": education, "experience": experience, "roles": roles, "certificates": certificates, "licenses": licenses}

    # Normalize parsed_at to datetime if provided as string
    parsed_at_val = parsed_result.get('parsed_at')
    if isinstance(parsed_at_val, str):
        try:
            parsed_at_val = parse_datetime(parsed_at_val)
        except Exception:
            parsed_at_val = None

    save_obj = Resume.objects.create(
        filename=(file.name if file else file_name_from_meta or 'NoFileProvided'),
        name=name,
        email=email,
        phones=[phone] if phone else [],
        skills=parsed_result.get('skills', {}),
        aviation=parsed_result.get('aviation', {}),
        experience={
            'items': parsed_result.get('experience_items', []),
            'summary': parsed_result.get('experience_summary', {})
        },
        total_score=parsed_result.get('total_score', 0.0),
        raw_text=raw_text,
        file_content=encoded_file_content,
        parsed_at=parsed_at_val,
        additional_info=additional_info
    )

    json_store_data = {
        'filename': save_obj.filename,
        'name': name,
        'email': email,
        'file_content': encoded_file_content,
        'parsed_data': parsed_result,
        'additional_info': additional_info,
        'parsed_at': datetime.now().isoformat()
    }
    stored = utils.add_resume_to_store(json_store_data)

    response = utils.format_resume_response(save_obj.to_dict())
    response['json_store_id'] = stored['id']
    return response


@router.post('/upload-resume')
def upload_resume(request, file: UploadedFile = File(...)):
    if not file or not getattr(file, 'name', None):
        raise ValidationError('No file provided')
    if not file.name.lower().endswith(('.pdf', '.txt', '.docx')):
        raise ValidationError('Supported formats: PDF, TXT, DOCX')

    content = file.read()
    if not content:
        raise ValidationError('Empty file provided')

    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    parsed_result = {}
    raw_text = ''
    try:
        if utils.parser:
            parsed_result = utils.parser.parse(tmp_path)
            raw_text = utils.parser.extract_text(tmp_path)
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    # Normalize parsed_at to datetime if provided as string
    parsed_at_val = parsed_result.get('parsed_at')
    if isinstance(parsed_at_val, str):
        try:
            parsed_at_val = parse_datetime(parsed_at_val)
        except Exception:
            parsed_at_val = None

    saved = Resume.objects.create(
        filename=file.name,
        name=parsed_result.get('name', 'Unknown'),
        email=(parsed_result.get('emails', [''])[0] if parsed_result.get('emails') else ''),
        phones=parsed_result.get('phones', []),
        skills=parsed_result.get('skills', {}),
        aviation=parsed_result.get('aviation', {}),
        experience={'items': parsed_result.get('experience_items', []), 'summary': parsed_result.get('experience_summary', {})},
        total_score=parsed_result.get('total_score', 0.0),
        raw_text=raw_text,
        file_content=base64.b64encode(content).decode('utf-8'),
        parsed_at=parsed_at_val
    )

    json_store_data = {
        'filename': file.name,
        'name': parsed_result.get('name', 'Unknown'),
        'email': (parsed_result.get('emails', [''])[0] if parsed_result.get('emails') else ''),
        'file_content': base64.b64encode(content).decode('utf-8'),
        'parsed_data': {
            'skills': parsed_result.get('skills', {}),
            'aviation': parsed_result.get('aviation', {}),
            'experience': {'items': parsed_result.get('experience_items', []), 'summary': parsed_result.get('experience_summary', {})}
        },
        'parsed_at': datetime.now().isoformat()
    }
    stored = utils.add_resume_to_store(json_store_data)

    formatted = utils.format_resume_response(saved.to_dict())
    formatted['json_store_id'] = stored['id']
    return formatted


@router.get('/resumes')
def list_resumes(request, skip: int = Query(0), limit: int = Query(20), search: Optional[str] = Query(None)):
    """List all resumes with optional search"""
    qs = Resume.objects.all().order_by('-created_at')
    if search:
        qs = qs.filter(name__icontains=search) | qs.filter(email__icontains=search)
    
    total = qs.count()
    resumes = qs[skip:skip+limit]
    
    return {
        'count': total,
        'results': [utils.format_resume_response(r.to_dict()) for r in resumes]
    }


@router.get('/resumes/{resume_id}')
def get_resume_detail(request, resume_id: int):
    try:
        r = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        raise Http404('Resume not found')
    return utils.format_resume_response(r.to_dict())


@router.get('/resumes/{resume_id}/download')
def download_resume(request, resume_id: int):
    try:
        r = Resume.objects.get(id=resume_id)
    except Resume.DoesNotExist:
        raise Http404('Resume not found')

    if not r.file_content:
        raise Http404('No file stored for this resume')

    content = base64.b64decode(r.file_content)
    ext = os.path.splitext(r.filename)[1].lower()
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
    return FileResponse(tmp_path, content_type=media_type, filename=r.filename)


@router.delete('/resumes/{resume_id}')
def delete_resume_by_id(request, resume_id: int):
    deleted, _ = Resume.objects.filter(id=resume_id).delete()
    if deleted:
        return {'status': 'success', 'message': 'Resume deleted'}
    raise Http404('Resume not found')


@router.delete('/resumes')
def delete_all_resumes_endpoint(request):
    count, _ = Resume.objects.all().delete()
    return {'status': 'success', 'message': f'Deleted {count} resumes', 'deleted': count}


@router.get('/stats')
def get_stats(request):
    resumes = Resume.objects.all()[:1000]
    total = resumes.count()
    avg_score = round(sum((r.total_score or 0) for r in resumes) / total, 2) if total else 0

    skill_counts = {}
    cert_counts = {}
    for r in resumes:
        skills = r.skills.get('matched', {}) if isinstance(r.skills, dict) else {}
        for skill in skills:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
        for cert in (r.aviation.get('certifications', []) if isinstance(r.aviation, dict) else []):
            cert_counts[cert] = cert_counts.get(cert, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_certs = sorted(cert_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        'total': total,
        'avg_score': avg_score,
        'top_skills': [{'name': k, 'count': v} for k, v in top_skills],
        'certifications': [{'name': k, 'count': v} for k, v in top_certs]
    }


@router.get('/json-store/resumes/{resume_id}')
def get_json_store_resume(request, resume_id: str):
    store = utils.load_resume_store()
    resume = next((r for r in store['resumes'] if r['id'] == str(resume_id)), None)
    if not resume:
        raise Http404('Resume not found in JSON store')
    return resume


@router.get('/json-store/resumes')
def list_json_store_resumes(request):
    return utils.load_resume_store()


@router.get('/config')
def get_config(request):
    try:
        if utils.parser:
            return utils.parser.config
        return {'error': 'Parser not available'}
    except Exception as e:
        return {'error': str(e)}
