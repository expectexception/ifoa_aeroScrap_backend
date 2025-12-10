"""
Django Database Manager for Scrapers
Integrates scraper system with Django ORM
"""

import logging
from typing import List, Dict, Set, Optional
from django.utils import timezone
from asgiref.sync import sync_to_async
from .models import ScrapedURL, ScraperJob
from jobs.models import Job, CompanyMapping

# Setup logging
logger = logging.getLogger(__name__)


class DjangoDBManager:
    """Database manager using Django ORM"""
    
    def __init__(self):
        """Initialize Django database manager"""
        pass
    
    def _extract_country_code(self, location: str, company: str = '') -> Optional[str]:
        """Extract country code from location string"""
        if not location:
            return None
        
        location_lower = location.lower()
        
        # Country code mapping - common patterns
        country_map = {
            # Full country names
            'india': 'IN', 'united states': 'US', 'usa': 'US', 'america': 'US',
            'united kingdom': 'GB', 'uk': 'GB', 'england': 'GB', 'scotland': 'GB',
            'united arab emirates': 'AE', 'uae': 'AE', 'dubai': 'AE', 'abu dhabi': 'AE',
            'singapore': 'SG', 'hong kong': 'HK', 'china': 'CN',
            'australia': 'AU', 'canada': 'CA', 'germany': 'DE', 'france': 'FR',
            'netherlands': 'NL', 'switzerland': 'CH', 'qatar': 'QA', 'doha': 'QA',
            'saudi arabia': 'SA', 'riyadh': 'SA', 'jeddah': 'SA',
            'ireland': 'IE', 'japan': 'JP', 'korea': 'KR', 'south korea': 'KR',
            'malaysia': 'MY', 'thailand': 'TH', 'indonesia': 'ID',
            'new zealand': 'NZ', 'spain': 'ES', 'italy': 'IT', 'portugal': 'PT',
            'turkey': 'TR', 'brazil': 'BR', 'mexico': 'MX', 'south africa': 'ZA',
            
            # Major cities that identify countries
            'london': 'GB', 'manchester': 'GB', 'birmingham': 'GB', 'edinburgh': 'GB',
            'new york': 'US', 'los angeles': 'US', 'chicago': 'US', 'houston': 'US',
            'miami': 'US', 'atlanta': 'US', 'dallas': 'US', 'seattle': 'US',
            'delhi': 'IN', 'mumbai': 'IN', 'bangalore': 'IN', 'hyderabad': 'IN',
            'chennai': 'IN', 'kolkata': 'IN', 'pune': 'IN', 'gurugram': 'IN',
            'paris': 'FR', 'frankfurt': 'DE', 'munich': 'DE', 'berlin': 'DE',
            'amsterdam': 'NL', 'zurich': 'CH', 'geneva': 'CH',
            'tokyo': 'JP', 'seoul': 'KR', 'bangkok': 'TH', 'kuala lumpur': 'MY',
            'sydney': 'AU', 'melbourne': 'AU', 'brisbane': 'AU', 'perth': 'AU',
            'toronto': 'CA', 'vancouver': 'CA', 'montreal': 'CA',
            
            # Airport codes (IATA)
            'del': 'IN', 'bom': 'IN', 'blr': 'IN', 'hyd': 'IN',
            'jfk': 'US', 'lax': 'US', 'ord': 'US', 'dfw': 'US', 'atl': 'US',
            'lhr': 'GB', 'lgw': 'GB', 'man': 'GB',
            'dxb': 'AE', 'auh': 'AE', 'sin': 'SG', 'hkg': 'HK',
            'cdg': 'FR', 'fra': 'DE', 'ams': 'NL', 'zrh': 'CH',
            'nrt': 'JP', 'icn': 'KR', 'bkk': 'TH', 'kul': 'MY',
            'syd': 'AU', 'mel': 'AU', 'yyz': 'CA',
        }
        
        # Check each pattern
        for pattern, code in country_map.items():
            if pattern in location_lower:
                return code
        
        # Check if location ends with 2-letter code (e.g., "New York, US")
        parts = location.strip().split(',')
        if len(parts) >= 2:
            potential_code = parts[-1].strip().upper()
            if len(potential_code) == 2:
                return potential_code
        
        return None
    
    def _infer_operation_type(self, title: str, company: str, description: str = '') -> Optional[str]:
        """Infer operation type from job title, company name, and description"""
        text = f"{title} {company} {description}".lower()
        
        # Keywords for each operation type
        operation_patterns = {
            'cargo': ['cargo', 'freight', 'fedex', 'ups', 'dhl', 'logistics', 'supply chain'],
            'helicopter': ['helicopter', 'rotor', 'vtol', 'bell ', 'sikorsky', 'airbus helicopters'],
            'mro': ['mro', 'maintenance', 'repair', 'overhaul', 'mechanic', 'engineer', 'technician', 'avionics'],
            'ground_ops': ['ground', 'ramp', 'airport operations', 'ground handling', 'baggage', 'gate agent'],
            'atc': ['air traffic', 'atc', 'tower', 'approach control', 'radar'],
            'business': ['business aviation', 'private jet', 'executive', 'charter', 'fractional', 'netjets', 'flexjet'],
            'low_cost': ['low cost', 'low-cost', 'budget airline', 'easyjet', 'ryanair', 'southwest', 'spirit', 'frontier'],
            'scheduled': ['scheduled', 'commercial airline', 'regular service'],
        }
        
        # Check patterns
        for op_type, patterns in operation_patterns.items():
            for pattern in patterns:
                if pattern in text:
                    return op_type
        
        # Default to passenger if it's clearly an airline job
        airline_keywords = ['airline', 'airways', 'flight', 'pilot', 'cabin crew', 'flight attendant', 'aircraft']
        if any(keyword in text for keyword in airline_keywords):
            return 'passenger'
        
        return None
    
    @sync_to_async
    def is_url_scraped(self, url: str) -> bool:
        """Check if URL has been scraped before"""
        exists = ScrapedURL.objects.filter(url=url).exists()
        if exists:
            logger.debug(f"URL already in database: {url[:100]}...")
        return exists
    
    @sync_to_async
    def get_scraped_urls(self, source: Optional[str] = None) -> Set[str]:
        """Get set of all scraped URLs, optionally filtered by source"""
        queryset = ScrapedURL.objects.all()
        if source:
            queryset = queryset.filter(source=source)
            logger.debug(f"Retrieved {queryset.count()} URLs for source: {source}")
        else:
            logger.debug(f"Retrieved {queryset.count()} URLs from all sources")
        return set(queryset.values_list('url', flat=True))
    
    def add_or_update_job(self, job_data: Dict, source: str) -> tuple[bool, str]:
        """
        Add new job or update existing one
        Returns: (is_new, message)
        """
        url = job_data.get('url')
        job_id = job_data.get('job_id')
        title = job_data.get('title', 'No Title')[:50]
        
        if not url:
            logger.warning(f"Job missing URL, skipping: {title}")
            return False, "Missing required field: url"
        
        try:
            # Update or create ScrapedURL (for tracking/deduplication)
            scraped_url, url_created = ScrapedURL.objects.update_or_create(
                url=url,
                defaults={
                    'job_id': job_id or url,
                    'source': source,
                    'title': job_data.get('title', 'No Title'),
                    'company': job_data.get('company', 'Unknown'),
                    'job_data': job_data,
                    'is_active': True,
                }
            )
            
            if not url_created:
                scraped_url.scrape_count += 1
                scraped_url.save(update_fields=['scrape_count', 'last_scraped'])
                logger.debug(f"Updated ScrapedURL (count={scraped_url.scrape_count}): {title}")
            else:
                logger.debug(f"Created new ScrapedURL: {title}")
            
            # Save to main jobs.Job model for application use
            job_obj, job_created = self._save_to_jobs_model(job_data, source)
            
            # Return True if it's a new job in the main Job table
            if job_created:
                logger.info(f"[{source}] New job added: {title}")
                return True, "New job added"
            else:
                logger.debug(f"[{source}] Job updated: {title}")
                return False, "Job updated"
        except Exception as e:
            logger.error(f"[{source}] Error adding/updating job '{title}': {e}", exc_info=True)
            return False, f"Error: {str(e)}"
    
    def _save_to_jobs_model(self, job_data: Dict, source: str):
        """Save job to main jobs.Job model for application use"""
        try:
            # Extract and normalize fields
            title = job_data.get('title', 'No Title').strip()
            company = job_data.get('company', 'Unknown').strip()
            url = job_data.get('url', '').strip()
            location = job_data.get('location', '').strip()
            description = job_data.get('description', '').strip()
            
            if not url:
                logger.error(f"Job URL is required for: {title}")
                return None, False
            
            # Parse posted_date if it's a string
            posted_date = job_data.get('posted_date')
            if isinstance(posted_date, str):
                from dateutil import parser
                try:
                    posted_date = parser.parse(posted_date).date()
                except Exception as e:
                    logger.debug(f"Could not parse posted_date '{posted_date}': {e}")
                    posted_date = None
            
            # Extract country code from location
            country_code = self._extract_country_code(location, company)
            
            # Infer operation type from job data
            operation_type = self._infer_operation_type(title, company, description)
            
            # Build defaults dict but avoid overwriting existing fields with None
            defaults = {
                'title': title,
                'company': company if company else 'Unknown Company',
                'location': location,
                'description': description,
                'source': source,
                # We'll only set 'status' for new records. Existing 'closed' statuses should not be reopened
                'country_code': country_code,
                'operation_type': operation_type,
                'raw_json': job_data,
                'retrieved_date': timezone.now(),
            }

            # Only set posted_date if we actually parsed one (don't overwrite an existing DB value with None)
            if posted_date is not None:
                defaults['posted_date'] = posted_date

            # Create or update Job in main jobs table
            # Create or update by retrieving first; don't overwrite status on updates
            job = Job.objects.filter(url=url).first()
            if job:
                # Keep existing status if closed; otherwise update fields
                current_status = job.status
                for k, v in defaults.items():
                    setattr(job, k, v)
                # Only overwrite status if it isn't 'closed'
                if current_status != 'closed':
                    job.status = 'active'
                job.last_checked = timezone.now()
                job.save()
                job_created = False
            else:
                # Create a new Job record and set status to active
                defaults['status'] = 'active'
                job = Job.objects.create(url=url, **defaults)
                job_created = True
            
            if job_created:
                logger.info(f"Created new Job record: {title[:50]}")
            else:
                logger.debug(f"Updated existing Job record: {title[:50]}")
            
            # Auto-create company mapping for standardization
            if company and company != 'Unknown':
                self._auto_create_company_mapping(company, source)
            
            return job, job_created
            
        except Exception as e:
            logger.error(f"Error saving to Job model: {e}", exc_info=True)
            return None, False
    
    def _auto_create_company_mapping(self, company_name: str, source: str):
        """Auto-create company mapping for standardization"""
        if not company_name:
            return
        
        normalized = company_name.strip().lower()
        
        mapping, created = CompanyMapping.objects.get_or_create(
            normalized_name=normalized,
            defaults={
                'company_name': company_name,
                'auto_created': True,
                'needs_review': True,
            }
        )
        
        if created:
            logger.debug(f"[{source}] Created company mapping: {company_name} -> {normalized}")
    
    def add_jobs_batch(self, jobs: List[Dict], source: str) -> Dict[str, int]:
        """ 
        Add multiple jobs at once - saves to both ScrapedURL and Job models
        Returns: Statistics dictionary
        """
        from django.db import transaction
        
        stats = {
            'total': len(jobs),
            'new': 0,
            'updated': 0,
            'duplicate': 0,
            'errors': 0
        }
        
        logger.info(f"[{source}] Starting batch processing of {len(jobs)} jobs")
        
        for idx, job in enumerate(jobs, 1):
            try:
                with transaction.atomic():
                    is_new, message = self.add_or_update_job(job, source)
                    if is_new:
                        stats['new'] += 1
                    else:
                        stats['updated'] += 1
                
                # Log progress every 10 jobs
                if idx % 10 == 0:
                    logger.debug(f"[{source}] Processed {idx}/{len(jobs)} jobs")
                    
            except Exception as e:
                stats['errors'] += 1
                job_title = job.get('title', 'unknown')[:50]
                logger.error(f"[{source}] Error adding job '{job_title}': {e}")
        
        stats['duplicate'] = stats['total'] - stats['new']
        
        logger.info(f"[{source}] Batch complete: new={stats['new']}, "
                   f"updated={stats['updated']}, duplicates={stats['duplicate']}, "
                   f"errors={stats['errors']}")
        
        return stats
    
    @sync_to_async
    def log_scrape_session(self, source: str, stats: Dict, duration: float):
        """Log scraping session - already handled by ScraperJob model"""
        pass
    
    def get_all_jobs(self, source: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Get all jobs from database"""
        queryset = ScrapedURL.objects.all()
        
        if source:
            queryset = queryset.filter(source=source)
        
        if active_only:
            queryset = queryset.filter(is_active=True)
        
        return [obj.job_data for obj in queryset]
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        from django.db.models import Count
        
        total_jobs = ScrapedURL.objects.count()
        by_source = dict(ScrapedURL.objects.values('source').annotate(count=Count('id')))
        
        recent_scrapes = list(
            ScraperJob.objects
            .order_by('-created_at')[:10]
            .values('scraper_name', 'created_at', 'jobs_found', 'jobs_new', 'jobs_duplicate')
        )
        
        most_scraped = list(
            ScrapedURL.objects
            .order_by('-scrape_count')[:5]
            .values('url', 'title', 'company', 'scrape_count')
        )
        
        return {
            'total_jobs': total_jobs,
            'jobs_by_source': by_source,
            'recent_scrapes': recent_scrapes,
            'most_scraped': most_scraped
        }
    
    def mark_job_inactive(self, url: str):
        """Mark a job as inactive"""
        ScrapedURL.objects.filter(url=url).update(is_active=False)

    def mark_job_closed(self, url: str, reason: Optional[str] = None):
        """Mark a job as closed/expired in both ScrapedURL and Job models"""
        try:
            ScrapedURL.objects.filter(url=url).update(is_active=False)
            Job.objects.filter(url=url).update(status='closed', last_checked=timezone.now())
            logger.info(f"Marked job closed: {url} reason={reason}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark job closed for {url}: {e}", exc_info=True)
            return False

    def check_job_active(self, url: str, use_playwright: bool = False) -> tuple[bool, str]:
        """
        Check whether a job page is still active.
        Returns (is_active, reason) where reason describes why it was marked closed if False.

        Logic:
        - If HTTP status is 404/410 => closed
        - If JSON-LD contains validThrough < today => closed
        - If body contains closed words like 'position has been filled', 'no longer accepting applications' => closed
        - Otherwise assume active.
        """
        try:
            # Lightweight requests check first
            import requests
            headers = {'User-Agent': self._extract_country_code.__name__}
            r = requests.get(url, headers=headers, timeout=10)
            status = r.status_code
            if status in (404, 410):
                return False, f'http_{status}'

            body = r.text or ''
            body_lower = body.lower()

            # Look for some closed/expired keywords
            closed_keywords = [
                'position has been filled',
                'position is filled',
                'this job is no longer available',
                'no longer accepting applications',
                'application closed',
                'job expired',
                'job is closed',
                'vacancy closed',
                'the listing has expired',
                'this job has expired',
                'role has been filled'
            ]
            for kw in closed_keywords:
                if kw in body_lower:
                    return False, f'closed_keyword:{kw}'

            # JSON-LD date checks
            import re, json
            for match in re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', body, re.DOTALL | re.IGNORECASE):
                try:
                    data = json.loads(match)
                except Exception:
                    continue
                items = data if isinstance(data, list) else [data]
                for item in items:
                    if isinstance(item, dict) and ('JobPosting' in item.get('@type', '') or item.get('@type') == 'JobPosting'):
                        valid_through = item.get('validThrough') or item.get('valid_through')
                        if valid_through:
                            try:
                                from dateutil import parser
                                vt_date = parser.parse(valid_through).date()
                                if vt_date < timezone.now().date():
                                    return False, 'validThrough_expired'
                            except Exception:
                                pass

            # If none matched, assume active
            return True, 'ok'

        except Exception as e:
            logger.debug(f"check_job_active error for {url}: {e}")
            # If errors reach here, we conservatively treat job as active
            return True, 'check_error'
    
    def print_statistics(self):
        """Log database statistics"""
        stats = self.get_statistics()
        
        logger.info("=" * 70)
        logger.info("📊 DATABASE STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total Jobs in Database: {stats['total_jobs']}")
        
        logger.info("Jobs by Source:")
        for source, count in stats['jobs_by_source'].items():
            logger.info(f"  • {source}: {count} jobs")
        
        if stats['most_scraped']:
            logger.info("Most Frequently Scraped Jobs:")
            for job in stats['most_scraped']:
                logger.info(f"  • {job['title']} at {job['company']} - {job['scrape_count']} times")
        
        logger.info("=" * 70)
