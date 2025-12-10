import json
from datetime import datetime
from typing import List, Optional

from ninja import Router, Body, Query
from django.utils.dateparse import parse_date

from .models import Job, CompanyMapping, CrawlLog
from . import utils
from .auth import JWTAuth

jwt_auth = JWTAuth()
from django.db import transaction
from django.utils import timezone
import csv
from django.http import HttpResponse
from ninja import Schema
from django.db.models import Count


class CompanyMappingIn(Schema):
    company_name: str
    normalized_name: Optional[str] = None
    operation_type: Optional[str] = None
    country_code: Optional[str] = None
    notes: Optional[str] = None

router = Router()


@router.post('/ingest', auth=jwt_auth)
def ingest(request, payload: dict = Body(...)):
    """Ingest a single job payload (from scraper)."""
    # Allowed fields
    fields = {}
    mapping = [
        'title', 'normalized_title', 'company', 'company_id', 'country_code',
        'operation_type', 'posted_date', 'url', 'description', 'status',
        'senior_flag', 'source', 'last_checked', 'raw_json'
    ]
    for k in mapping:
        if k in payload:
            fields[k] = payload[k]

    # Parse dates
    if 'posted_date' in fields and isinstance(fields['posted_date'], str):
        try:
            fields['posted_date'] = parse_date(fields['posted_date'])
        except Exception:
            fields['posted_date'] = None

    # Save raw_json if provided
    if 'raw_json' in fields and isinstance(fields['raw_json'], dict):
        raw = fields['raw_json']
    else:
        raw = payload
    fields['raw_json'] = raw

    # Auto-detect operation_type if missing using company heuristics
    if not fields.get('operation_type'):
        op = utils.classify_company_by_name(fields.get('company'))
        if op:
            fields['operation_type'] = op

    # Auto-create a CompanyMapping entry if company present and mapping missing
    comp_name = fields.get('company')
    if comp_name:
        norm = comp_name.strip().lower()
        try:
            CompanyMapping.objects.get(normalized_name=norm)
        except CompanyMapping.DoesNotExist:
            try:
                CompanyMapping.objects.create(
                    company_name=comp_name,
                    normalized_name=norm,
                    operation_type=fields.get('operation_type')
                )
            except Exception:
                pass

    # Respect explicit senior_override if provided; otherwise model will compute senior_flag

    # Create or update by URL if exists
    url = fields.get('url')
    job = None
    if url:
        try:
            job = Job.objects.get(url=url)
            for k, v in fields.items():
                setattr(job, k, v)
            job.save()
            return {'status': 'updated', 'id': job.id}
        except Job.DoesNotExist:
            pass

    # Secondary dedupe: exact title+company+posted_date
    title = fields.get('title')
    company = fields.get('company')
    posted_date = fields.get('posted_date')

    # look for possible duplicates
    possible = Job.objects.filter(company__iexact=company)
    for p in possible:
        if utils.is_duplicate(p.title, p.company, p.posted_date, title, company, posted_date):
            # update
            for k, v in fields.items():
                setattr(p, k, v)
            p.save()
            return {'status': 'dedup-updated', 'id': p.id}

    job = Job.objects.create(**{k: v for k, v in fields.items() if k in [f.name for f in Job._meta.fields]})
    return {'status': 'created', 'id': job.id}


@router.post('/bulk_ingest', auth=jwt_auth)
def bulk_ingest(request, payload: List[dict] = Body(...)):
    results = []
    run_time = timezone.now()
    found = len(payload)
    inserted = 0
    updated = 0
    errors = []
    with transaction.atomic():
        for p in payload:
            try:
                r = ingest(request, p)
                results.append(r)
                if r.get('status') in ('created',):
                    inserted += 1
                elif r.get('status') in ('updated', 'dedup-updated'):
                    updated += 1
            except Exception as e:
                errors.append(str(e))
                results.append({'status': 'error', 'error': str(e)})

    # Log crawl
    CrawlLog.objects.create(
        source='bulk_ingest',
        run_time=run_time,
        items_found=found,
        items_inserted=inserted,
        items_updated=updated,
        error='; '.join(errors) if errors else None
    )

    return {'results': results, 'found': found, 'inserted': inserted, 'updated': updated, 'errors': errors}


@router.get('/export/daily.csv')
def export_daily_csv(request, date: Optional[str] = None):
    """Export CSV for a date (YYYY-MM-DD). If not provided, use today."""
    if date:
        try:
            from django.utils.dateparse import parse_date
            target = parse_date(date)
        except Exception:
            target = None
    else:
        target = timezone.now().date()

    qs = Job.objects.filter(posted_date=target).order_by('country_code', 'operation_type', '-posted_date')

    # Build CSV
    response = HttpResponse(content_type='text/csv')
    filename = f'daily_export_{target}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(['Country', 'Operation Type', 'Job Title', 'Company', 'Date Posted', 'URL', 'Brief Description', 'Source', 'Senior Flag'])
    for j in qs:
        writer.writerow([
            j.country_code or '',
            j.operation_type or '',
            j.title or '',
            j.company or '',
            j.posted_date.isoformat() if j.posted_date else '',
            j.url or '',
            (j.description or '')[:200],
            j.source or '',
            'TRUE' if j.senior_flag else 'FALSE'
        ])
    return response


@router.get('/')
def list_jobs(
    request,
    skip: int = Query(0),
    limit: int = Query(100),
    country: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    senior: Optional[bool] = Query(None),
    company: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
):
    """List jobs with optional filters"""
    qs = Job.objects.all()
    
    if country:
        qs = qs.filter(country_code__iexact=country)
    if type:
        qs = qs.filter(operation_type__iexact=type)
    if senior is not None:
        qs = qs.filter(senior_flag=senior)
    if company:
        qs = qs.filter(company__icontains=company)
    if title:
        qs = qs.filter(title__icontains=title)

    total = qs.count()
    jobs = qs.order_by('-created_at')[skip:skip+limit]
    
    return {
        'count': total,
        'results': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'url': j.url,
                'posted_date': j.posted_date.isoformat() if j.posted_date else None,
                'status': j.status,
            }
            for j in jobs
        ]
    }


@router.get('/id/{job_id}')
def get_job(request, job_id: int):
    try:
        j = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return {'error': 'not found'}
    return {
        'id': j.id,
        'title': j.title,
        'company': j.company,
        'url': j.url,
        'description': j.description,
        'raw_json': j.raw_json,
        'operation_type': j.operation_type,
        'senior_flag': j.senior_flag,
        'posted_date': j.posted_date.isoformat() if j.posted_date else None,
        'created_at': j.created_at.isoformat(),
        'updated_at': j.updated_at.isoformat(),
    }


@router.patch('/{job_id}', auth=jwt_auth)
def update_job(request, job_id: int, payload: dict = Body(...)):
    """Partial update for a job"""
    try:
        j = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return {'error': 'not found'}

    allowed = [f.name for f in Job._meta.fields]
    for k, v in payload.items():
        if k in allowed:
            setattr(j, k, v)
    # If title changed but senior_flag wasn't provided, recompute from title
    if 'title' in payload and 'senior_flag' not in payload and j.title:
        try:
            from . import utils
            j.senior_flag = utils.is_senior(j.title)
        except Exception:
            pass
    j.save()
    return {'status': 'updated', 'id': j.id}


@router.delete('/{job_id}', auth=jwt_auth)
def delete_job(request, job_id: int):
    try:
        j = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return {'error': 'not found'}
    j.delete()
    return {'status': 'deleted', 'id': job_id}


@router.get('/search/')
def search_jobs(request, q: Optional[str] = Query(None), limit: int = Query(100)):
    """Search jobs by query text"""
    from django.db.models import Q
    qs = Job.objects.all()
    if q and q.strip():
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(company__icontains=q) | 
            Q(description__icontains=q)
        ).distinct()
    
    total = qs.count()
    qs = qs.order_by('-created_at')[:limit]
    
    return {
        'count': total,
        'results': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'url': j.url,
                'posted_date': j.posted_date.isoformat() if j.posted_date else None
            }
            for j in qs
        ]
    }


@router.get('/admin/company-mappings', auth=jwt_auth)
def list_company_mappings(request, skip: int = Query(0), limit: int = Query(100)):
    qs = CompanyMapping.objects.all().order_by('-updated_at')[skip:skip+limit]
    return [{'id': c.id, 'company_name': c.company_name, 'normalized_name': c.normalized_name, 'operation_type': c.operation_type, 'country_code': c.country_code, 'notes': c.notes} for c in qs]


@router.post('/admin/company-mappings', auth=jwt_auth)
def create_or_update_company_mapping(request, payload: CompanyMappingIn):
    norm = (payload.normalized_name or payload.company_name).strip().lower()
    obj, created = CompanyMapping.objects.update_or_create(
        normalized_name=norm,
        defaults={
            'company_name': payload.company_name,
            'operation_type': payload.operation_type,
            'country_code': payload.country_code,
            'notes': payload.notes,
        }
    )
    return {'id': obj.id, 'created': created}


@router.put('/admin/company-mappings/{mapping_id}', auth=jwt_auth)
def update_company_mapping(request, mapping_id: int, payload: CompanyMappingIn):
    try:
        obj = CompanyMapping.objects.get(id=mapping_id)
    except CompanyMapping.DoesNotExist:
        return {'error': 'not found'}
    obj.company_name = payload.company_name
    obj.normalized_name = (payload.normalized_name or payload.company_name).strip().lower()
    obj.operation_type = payload.operation_type
    obj.country_code = payload.country_code
    obj.notes = payload.notes
    obj.save()
    return {'id': obj.id, 'updated': True}


@router.delete('/admin/company-mappings/{mapping_id}', auth=jwt_auth)
def delete_company_mapping(request, mapping_id: int):
    try:
        obj = CompanyMapping.objects.get(id=mapping_id)
    except CompanyMapping.DoesNotExist:
        return {'error': 'not found'}
    obj.delete()
    return {'id': mapping_id, 'deleted': True}


@router.get('/health')
def health(request):
    """Simple healthcheck"""
    try:
        Job.objects.exists()
        return {'ok': True, 'db': 'ok'}
    except Exception as e:
        return {'ok': False, 'db': str(e)}


@router.post('/health')
def health_post(request):
    return health(request)


@router.get('/admin/unknown-companies')
def unknown_companies(request, limit: int = Query(100)):
    # list distinct company names from jobs that don't have a company_mapping
    mapped = CompanyMapping.objects.values_list('normalized_name', flat=True)
    qs = Job.objects.exclude(company__isnull=True).exclude(company__exact='').values('company').distinct()
    out = []
    for r in qs:
        name = r['company']
        if name.strip().lower() not in mapped:
            out.append(name)
            if len(out) >= limit:
                break
    return out


@router.get('/alerts/senior')
def senior_alerts(request, hours: int = Query(24)):
    since = timezone.now() - timezone.timedelta(hours=hours)
    qs = Job.objects.filter(senior_flag=True, created_at__gte=since).order_by('-created_at')[:200]
    return [{'id': j.id, 'title': j.title, 'company': j.company, 'url': j.url, 'created_at': j.created_at.isoformat()} for j in qs]


@router.get('/stats/')
def stats(request):
    """Get overall job statistics"""
    total = Job.objects.count()
    missing_op = Job.objects.filter(operation_type__isnull=True).count()
    by_country = Job.objects.values('country_code').annotate(count=Count('id')).order_by('-count')[:20]
    top_companies = Job.objects.values('company').annotate(count=Count('id')).order_by('-count')[:20]
    return {
        'total': total,
        'missing_operation_type': missing_op,
        'by_country': list(by_country),
        'top_companies': list(top_companies)
    }


# ============================================================================
# ADVANCED SEARCH & FILTERING
# ============================================================================

@router.get('/advanced-search/')
def advanced_search(
    request,
    q: Optional[str] = Query(None),
    countries: Optional[str] = Query(None),  # Comma-separated
    operation_types: Optional[str] = Query(None),  # Comma-separated
    senior_only: Optional[str] = Query(None),  # "true" or "false" as string
    date_from: Optional[str] = Query(None),  # YYYY-MM-DD
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query('active'),
    sort_by: Optional[str] = Query('posted_date'),  # posted_date, title, company, created_at
    order: Optional[str] = Query('desc'),  # asc, desc
    skip: int = Query(0),
    limit: int = Query(50)
):
    """Advanced search with multiple filters - matches requirements specification"""
    from django.db.models import Q
    
    qs = Job.objects.all()
    
    # Text search across title, company, and description
    if q and q.strip():
        qs = qs.filter(
            Q(title__icontains=q) | 
            Q(company__icontains=q) | 
            Q(description__icontains=q)
        )
    
    # Country filter (multiple) - handle empty/whitespace values
    if countries and countries.strip():
        country_list = [c.strip().upper() for c in countries.split(',') if c.strip()]
        if country_list:
            qs = qs.filter(country_code__in=country_list)
    
    # Operation type filter (multiple) - handle empty/whitespace values
    if operation_types and operation_types.strip():
        type_list = [t.strip() for t in operation_types.split(',') if t.strip()]
        if type_list:
            qs = qs.filter(operation_type__in=type_list)
    
    # Senior only - handle string boolean conversion
    if senior_only is not None and senior_only.strip():
        senior_bool = senior_only.lower() == 'true'
        qs = qs.filter(senior_flag=senior_bool)
    
    # Date range filters
    if date_from and date_from.strip():
        try:
            date_from_obj = parse_date(date_from)
            if date_from_obj:
                qs = qs.filter(posted_date__gte=date_from_obj)
        except Exception:
            pass
    
    if date_to and date_to.strip():
        try:
            date_to_obj = parse_date(date_to)
            if date_to_obj:
                qs = qs.filter(posted_date__lte=date_to_obj)
        except Exception:
            pass
    
    # Status filter
    if status and status.strip():
        qs = qs.filter(status=status)
    
    # Sorting - ensure valid sort field
    valid_sort_fields = ['created_at', 'posted_date', 'title', 'company']
    sort_field = sort_by if sort_by in valid_sort_fields else 'posted_date'
    if order == 'asc':
        qs = qs.order_by(sort_field)
    else:
        qs = qs.order_by(f'-{sort_field}')
    
    # Count before pagination
    total_results = qs.count()
    
    # Apply pagination limits
    limit = min(limit, 100)  # Cap at 100 for performance
    results = qs[skip:skip+limit]
    
    # Format response per requirements
    return {
        'count': total_results,
        'results': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or f"{j.country_code}",
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'status': j.status
            }
            for j in results
        ]
    }


# ============================================================================
# COMPANY APIs
# ============================================================================

@router.get('/companies/')
def list_companies(request, limit: int = Query(100)):
    """List all companies with job counts - matches requirements format"""
    from django.db.models import Q
    
    companies_data = Job.objects.values('company').annotate(
        total_jobs=Count('id'),
        active_jobs=Count('id', filter=Q(status='active'))
    ).order_by('-total_jobs')[:limit]
    
    result = []
    for c in companies_data:
        company_name = c['company']
        # Get unique countries and operation types for this company
        company_jobs = Job.objects.filter(company=company_name)
        countries = list(company_jobs.exclude(country_code__isnull=True).values_list('country_code', flat=True).distinct())
        op_types = list(company_jobs.exclude(operation_type__isnull=True).values_list('operation_type', flat=True).distinct())
        
        result.append({
            'company': company_name,
            'total_jobs': c['total_jobs'],
            'active_jobs': c['active_jobs'],
            'countries': countries,
            'operation_types': op_types
        })
    
    return {'companies': result}


@router.get('/companies/trending/')
def trending_companies(request, days: int = Query(30), limit: int = Query(10)):
    """Get companies with most job postings in recent days - matches requirements format"""
    from datetime import timedelta
    since = timezone.now() - timedelta(days=days)
    
    # Get new jobs per company in the period
    companies_data = Job.objects.filter(created_at__gte=since).values('company').annotate(
        new_jobs=Count('id')
    ).order_by('-new_jobs')[:limit]
    
    result = []
    for c in companies_data:
        company_name = c['company']
        # Calculate growth percentage (new jobs vs total jobs)
        total_jobs = Job.objects.filter(company=company_name).count()
        growth_percentage = (c['new_jobs'] / total_jobs * 100) if total_jobs > 0 else 0
        
        result.append({
            'company': company_name,
            'new_jobs': c['new_jobs'],
            'growth_percentage': round(growth_percentage, 1)
        })
    
    return {'companies': result}


@router.get('/companies/{company_name}/')
def company_profile(request, company_name: str):
    """Get company profile with statistics - matches requirements format"""
    jobs = Job.objects.filter(company__iexact=company_name)
    
    if not jobs.exists():
        from ninja.errors import HttpError
        raise HttpError(404, 'Company not found')
    
    total_jobs = jobs.count()
    active_jobs = jobs.filter(status='active').count()
    closed_jobs = jobs.filter(status__in=['closed', 'expired', 'removed']).count()
    
    # Unique countries and locations
    countries = list(jobs.exclude(country_code__isnull=True).values_list('country_code', flat=True).distinct())
    locations = list(jobs.exclude(location__isnull=True).values_list('location', flat=True).distinct())
    
    # Operation types
    operation_types = list(jobs.exclude(operation_type__isnull=True).values_list('operation_type', flat=True).distinct())
    
    # Hiring trends
    from datetime import timedelta
    now = timezone.now()
    last_7_days = jobs.filter(created_at__gte=now - timedelta(days=7)).count()
    last_30_days = jobs.filter(created_at__gte=now - timedelta(days=30)).count()
    
    return {
        'name': company_name,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'closed_jobs': closed_jobs,
        'countries': countries,
        'locations': locations if locations else [f"{c}" for c in countries],
        'operation_types': operation_types,
        'hiring_trends': {
            'last_7_days': last_7_days,
            'last_30_days': last_30_days
        }
    }


@router.get('/companies/{company_name}/jobs/')
def company_jobs(request, company_name: str, skip: int = Query(0), limit: int = Query(20)):
    """Get all jobs from a specific company - matches requirements format"""
    all_jobs = Job.objects.filter(company__iexact=company_name)
    total_count = all_jobs.count()
    
    jobs = all_jobs.order_by('-posted_date', '-created_at')[skip:skip+limit]
    
    return {
        'count': total_count,
        'jobs': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or j.country_code,
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'status': j.status
            }
            for j in jobs
        ]
    }


# ============================================================================
# ANALYTICS APIs
# ============================================================================

@router.get('/analytics/trends/')
def job_trends(request, days: int = Query(30)):
    """Job posting trends over time - matches requirements format"""
    from datetime import timedelta
    from django.db.models.functions import TruncDate
    
    since = timezone.now() - timedelta(days=days)
    
    # Jobs by date
    daily_jobs = Job.objects.filter(created_at__gte=since).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(count=Count('id')).order_by('date')
    
    total_jobs = Job.objects.filter(created_at__gte=since).count()
    average_per_day = total_jobs / days if days > 0 else 0
    
    return {
        'total_jobs': total_jobs,
        'average_per_day': round(average_per_day, 1),
        'daily_trends': [
            {
                'date': d['date'].isoformat(),
                'count': d['count']
            }
            for d in daily_jobs
        ]
    }


@router.get('/analytics/geographic/')
def geographic_distribution(request):
    """Jobs distribution by location - matches requirements format"""
    by_country = Job.objects.exclude(country_code__isnull=True).exclude(country_code='').values('country_code').annotate(
        count=Count('id')
    ).order_by('-count')
    
    total_countries = by_country.count()
    
    return {
        'total_countries': total_countries,
        'distribution': [
            {
                'country': item['country_code'],
                'count': item['count']
            }
            for item in by_country
        ]
    }


@router.get('/analytics/operation-types/')
def operation_type_stats(request):
    """Statistics by operation type - matches requirements format"""
    stats = Job.objects.exclude(operation_type__isnull=True).exclude(operation_type='').values('operation_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    total_types = stats.count()
    
    return {
        'total_types': total_types,
        'distribution': [
            {
                'operation_type': item['operation_type'],
                'count': item['count']
            }
            for item in stats
        ]
    }


# ============================================================================
# RECENT ACTIVITY
# ============================================================================

@router.get('/recent/')
def recent_jobs(request, hours: int = Query(48), limit: int = Query(10)):
    """Recently added jobs - matches requirements format"""
    from datetime import timedelta
    since = timezone.now() - timedelta(hours=hours)
    jobs = Job.objects.filter(created_at__gte=since).order_by('-created_at')[:limit]
    
    return {
        'jobs': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or j.country_code,
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'status': j.status
            }
            for j in jobs
        ]
    }


@router.get('/updated/')
def recently_updated(request, hours: int = Query(24), limit: int = Query(10)):
    """Recently updated jobs - matches requirements format"""
    from datetime import timedelta
    since = timezone.now() - timedelta(hours=hours)
    jobs = Job.objects.filter(last_updated__gte=since).order_by('-last_updated')[:limit]
    
    return {
        'jobs': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or j.country_code,
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'last_updated': j.last_updated.isoformat() + 'Z' if j.last_updated else None,
                'status': j.status
            }
            for j in jobs
        ]
    }


# ============================================================================
# JOB COMPARISON
# ============================================================================

class CompareJobsRequest(Schema):
    job_ids: List[int]


@router.post('/compare/')
def compare_jobs(request, payload: CompareJobsRequest):
    """Compare multiple jobs side by side - matches requirements format"""
    job_ids = payload.job_ids
    
    if len(job_ids) > 10:
        from ninja.errors import HttpError
        raise HttpError(400, 'Maximum 10 jobs can be compared at once')
    
    jobs = Job.objects.filter(id__in=job_ids)
    jobs_list = list(jobs)
    
    # Analyze common fields and differences
    common_fields = {}
    differences = []
    
    if len(jobs_list) > 1:
        # Check for common country
        countries = set(j.country_code for j in jobs_list if j.country_code)
        if len(countries) == 1:
            common_fields['country'] = list(countries)[0]
        else:
            differences.append('Country codes differ')
        
        # Check for common operation type
        op_types = set(j.operation_type for j in jobs_list if j.operation_type)
        if len(op_types) == 1:
            common_fields['operation_type'] = list(op_types)[0]
        else:
            differences.append('Operation types differ')
        
        # Check for common company
        companies = set(j.company for j in jobs_list)
        if len(companies) > 1:
            differences.append('Company names differ')
        
        # Check for experience requirements
        senior_flags = set(j.senior_flag for j in jobs_list)
        if len(senior_flags) > 1:
            differences.append('Experience requirements differ')
    
    return {
        'jobs': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or j.country_code,
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'status': j.status
            }
            for j in jobs_list
        ],
        'summary': {
            'common_fields': common_fields,
            'differences': differences
        }
    }


@router.get('/similar/{job_id}/')
def similar_jobs(request, job_id: int, limit: int = Query(5)):
    """Find similar jobs based on title and company - matches requirements format"""
    from django.db.models import Q
    
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        from ninja.errors import HttpError
        raise HttpError(404, 'Job not found')
    
    similar_list = []
    
    # 1. Find by same company
    same_company = Job.objects.filter(
        company__iexact=job.company
    ).exclude(id=job_id).order_by('-posted_date', '-created_at')[:limit]
    similar_list.extend(same_company)
    
    # 2. If not enough, find by same operation type and country
    if len(similar_list) < limit and job.operation_type and job.country_code:
        by_type_country = Job.objects.filter(
            operation_type=job.operation_type,
            country_code=job.country_code
        ).exclude(id=job_id).exclude(
            id__in=[s.id for s in similar_list]
        ).order_by('-posted_date')[:limit - len(similar_list)]
        similar_list.extend(by_type_country)
    
    # 3. If still not enough, search by title keywords
    if len(similar_list) < limit:
        title_words = [w for w in job.title.lower().split() if len(w) > 3]
        if title_words:
            title_query = Q()
            for word in title_words[:3]:  # Use top 3 keywords
                title_query |= Q(title__icontains=word)
            
            by_title = Job.objects.filter(title_query).exclude(
                id=job_id
            ).exclude(
                id__in=[s.id for s in similar_list]
            ).order_by('-posted_date')[:limit - len(similar_list)]
            similar_list.extend(by_title)
    
    return {
        'jobs': [
            {
                'id': j.id,
                'title': j.title,
                'company': j.company,
                'country': j.country_code,
                'location': j.location or j.country_code,
                'operation_type': j.operation_type,
                'is_senior_position': j.senior_flag,
                'posted_date': j.posted_date.isoformat() + 'Z' if j.posted_date else None,
                'status': j.status
            }
            for j in similar_list[:limit]
        ]
    }


# ============================================================================
# BULK EXPORT
# ============================================================================

@router.get('/export/json/')
def export_json(
    request,
    country: Optional[str] = Query(None),
    operation_type: Optional[str] = Query(None),
    status: Optional[str] = Query('active'),
    limit: int = Query(1000)
):
    """Export jobs as JSON"""
    qs = Job.objects.all()
    
    if country:
        qs = qs.filter(country_code__iexact=country)
    if operation_type:
        qs = qs.filter(operation_type__iexact=operation_type)
    if status:
        qs = qs.filter(status=status)
    
    qs = qs.order_by('-created_at')[:limit]
    
    data = [
        {
            'id': j.id,
            'title': j.title,
            'company': j.company,
            'url': j.url,
            'description': j.description,
            'country_code': j.country_code,
            'operation_type': j.operation_type,
            'posted_date': j.posted_date.isoformat() if j.posted_date else None,
            'status': j.status,
            'senior_flag': j.senior_flag,
            'source': j.source,
            'created_at': j.created_at.isoformat()
        }
        for j in qs
    ]
    
    response = HttpResponse(
        json.dumps(data, indent=2),
        content_type='application/json'
    )
    response['Content-Disposition'] = f'attachment; filename="jobs_export_{timezone.now().strftime("%Y%m%d")}.json"'
    return response


# ============================================================================
# SCRAPER MANAGEMENT
# ============================================================================

@router.get('/admin/scrapers/status', auth=jwt_auth)
def scraper_status(request):
    """Get status of all scrapers"""
    # Get recent crawl logs
    recent_logs = CrawlLog.objects.order_by('-run_time')[:20]
    
    # Group by source
    from collections import defaultdict
    by_source = defaultdict(list)
    for log in recent_logs:
        by_source[log.source].append({
            'run_time': log.run_time.isoformat(),
            'items_found': log.items_found,
            'items_inserted': log.items_inserted,
            'items_updated': log.items_updated,
            'error': log.error
        })
    
    return {
        'scrapers': dict(by_source),
        'total_runs': CrawlLog.objects.count(),
        'last_run': recent_logs[0].run_time.isoformat() if recent_logs else None
    }


@router.get('/admin/scrapers/logs', auth=jwt_auth)
def scraper_logs(request, source: Optional[str] = Query(None), limit: int = Query(50)):
    """Get scraper execution logs"""
    qs = CrawlLog.objects.all()
    
    if source:
        qs = qs.filter(source=source)
    
    qs = qs.order_by('-run_time')[:limit]
    
    return [
        {
            'id': log.id,
            'source': log.source,
            'run_time': log.run_time.isoformat(),
            'items_found': log.items_found,
            'items_inserted': log.items_inserted,
            'items_updated': log.items_updated,
            'success_rate': round((log.items_inserted + log.items_updated) / log.items_found * 100, 2) if log.items_found > 0 else 0,
            'error': log.error
        }
        for log in qs
    ]
