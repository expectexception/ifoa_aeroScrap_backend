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
        # Country code mapping - common patterns
        country_map = {
            # --- North America ---
            'united states': 'US', 'usa': 'US', 'us': 'US', 'america': 'US',
            'canada': 'CA', 'mexico': 'MX',
            # US Cities
            'new york': 'US', 'los angeles': 'US', 'chicago': 'US', 'houston': 'US', 'phoenix': 'US',
            'philadelphia': 'US', 'san antonio': 'US', 'san diego': 'US', 'dallas': 'US', 'san jose': 'US',
            'austin': 'US', 'jacksonville': 'US', 'san francisco': 'US', 'indianapolis': 'US', 'columbus': 'US',
            'fort worth': 'US', 'charlotte': 'US', 'seattle': 'US', 'denver': 'US', 'washington': 'US',
            'boston': 'US', 'el paso': 'US', 'nashville': 'US', 'detroit': 'US', 'oklahoma city': 'US',
            'portland': 'US', 'las vegas': 'US', 'memphis': 'US', 'louisville': 'US', 'baltimore': 'US',
            'milwaukee': 'US', 'albuquerque': 'US', 'tucson': 'US', 'fresno': 'US', 'sacramento': 'US',
            'atlanta': 'US', 'kansas city': 'US', 'miami': 'US', 'raleigh': 'US', 'omaha': 'US',
            # CA Cities
            'toronto': 'CA', 'montreal': 'CA', 'vancouver': 'CA', 'calgary': 'CA', 'edmonton': 'CA', 'ottawa': 'CA',

            # --- Europe ---
            'united kingdom': 'GB', 'uk': 'GB', 'britain': 'GB', 'england': 'GB', 'scotland': 'GB', 'wales': 'GB',
            'germany': 'DE', 'deutschland': 'DE', 'france': 'FR', 'italy': 'IT', 'italia': 'IT',
            'spain': 'ES', 'espana': 'ES', 'poland': 'PL', 'polska': 'PL', 'romania': 'RO',
            'netherlands': 'NL', 'holland': 'NL', 'belgium': 'BE', 'greece': 'GR', 'portugal': 'PT',
            'czech republic': 'CZ', 'czechia': 'CZ', 'hungary': 'HU', 'sweden': 'SE', 'austria': 'AT',
            'switzerland': 'CH', 'bulgaria': 'BG', 'denmark': 'DK', 'finland': 'FI', 'slovakia': 'SK',
            'norway': 'NO', 'ireland': 'IE', 'croatia': 'HR', 'moldova': 'MD', 'bosnia': 'BA',
            'albania': 'AL', 'lithuania': 'LT', 'macedonia': 'MK', 'slovenia': 'SI', 'latvia': 'LV',
            'estonia': 'EE', 'montenegro': 'ME', 'luxembourg': 'LU', 'malta': 'MT', 'iceland': 'IS',
            # EU Cities
            'london': 'GB', 'manchester': 'GB', 'birmingham': 'GB', 'glasgow': 'GB', 'liverpool': 'GB',
            'berlin': 'DE', 'hamburg': 'DE', 'munich': 'DE', 'cologne': 'DE', 'frankfurt': 'DE',
            'paris': 'FR', 'marseille': 'FR', 'lyon': 'FR', 'toulouse': 'FR', 'nice': 'FR',
            'rome': 'IT', 'milan': 'IT', 'naples': 'IT', 'turin': 'IT', 'palermo': 'IT',
            'madrid': 'ES', 'barcelona': 'ES', 'valencia': 'ES', 'seville': 'ES', 'bilbao': 'ES',
            'amsterdam': 'NL', 'rotterdam': 'NL', 'brussels': 'BE', 'antwerp': 'BE',
            'vienna': 'AT', 'zurich': 'CH', 'geneva': 'CH', 'stockholm': 'SE', 'oslo': 'NO',
            'copenhagen': 'DK', 'helsinki': 'FI', 'dublin': 'IE', 'lisbon': 'PT', 'athens': 'GR',
            'warsaw': 'PL', 'prague': 'CZ', 'budapest': 'HU', 'bucharest': 'RO', 'sofia': 'BG',

            # --- Asia / Pacific ---
            'china': 'CN', 'japan': 'JP', 'india': 'IN', 'indonesia': 'ID', 'pakistan': 'PK',
            'bangladesh': 'BD', 'philippines': 'PH', 'vietnam': 'VN', 'thailand': 'TH', 'myanmar': 'MM',
            'south korea': 'KR', 'korea': 'KR', 'malaysia': 'MY', 'nepal': 'NP', 'taiwan': 'TW',
            'australia': 'AU', 'sri lanka': 'LK', 'kazakhstan': 'KZ', 'cambodia': 'KH', 'singapore': 'SG',
            'hong kong': 'HK', 'new zealand': 'NZ',
            # Cities
            'tokyo': 'JP', 'osaka': 'JP', 'kyoto': 'JP', 'seoul': 'KR', 'beijing': 'CN', 'shanghai': 'CN',
            'mumbai': 'IN', 'delhi': 'IN', 'bangalore': 'IN', 'hyderabad': 'IN', 'chennai': 'IN',
            'kolkata': 'IN', 'pune': 'IN', 'jakarta': 'ID', 'manila': 'PH', 'bangkok': 'TH',
            'ho chi minh': 'VN', 'hanoi': 'VN', 'kuala lumpur': 'MY', 'singapore city': 'SG',
            'sydney': 'AU', 'melbourne': 'AU', 'brisbane': 'AU', 'perth': 'AU', 'auckland': 'NZ',

            # --- Middle East ---
            'turkey': 'TR', 'iran': 'IR', 'iraq': 'IQ', 'saudi arabia': 'SA', 'ksa': 'SA',
            'yemen': 'YE', 'syria': 'SY', 'jordan': 'JO', 'united arab emirates': 'AE', 'uae': 'AE',
            'israel': 'IL', 'lebanon': 'LB', 'oman': 'OM', 'kuwait': 'KW', 'qatar': 'QA', 'bahrain': 'BH',
            # Cities
            'istanbul': 'TR', 'ankara': 'TR', 'tehran': 'IR', 'baghdad': 'IQ', 'riyadh': 'SA',
            'jeddah': 'SA', 'dubai': 'AE', 'abu dhabi': 'AE', 'sharjah': 'AE', 'doha': 'QA',
            'kuwait city': 'KW', 'muscat': 'OM', 'manama': 'BH', 'amman': 'JO', 'beirut': 'LB',
            'tel aviv': 'IL', 'jerusalem': 'IL',

            # --- South America ---
            'brazil': 'BR', 'colombia': 'CO', 'argentina': 'AR', 'peru': 'PE', 'venezuela': 'VE',
            'chile': 'CL', 'ecuador': 'EC', 'bolivia': 'BO', 'paraguay': 'PY', 'uruguay': 'UY',
            # Cities
            'sao paulo': 'BR', 'rio de janeiro': 'BR', 'brasilia': 'BR', 'buenos aires': 'AR',
            'bogota': 'CO', 'lima': 'PE', 'santiago': 'CL', 'caracas': 'VE',

            # --- Africa ---
            'nigeria': 'NG', 'ethiopia': 'ET', 'egypt': 'EG', 'dr congo': 'CD', 'tanzania': 'TZ',
            'south africa': 'ZA', 'kenya': 'KE', 'uganda': 'UG', 'algeria': 'DZ', 'sudan': 'SD',
            'morocco': 'MA', 'ghana': 'GH', 'mozambique': 'MZ', 'angola': 'AO', 'ivory coast': 'CI',
            # Cities
            'cairo': 'EG', 'lagos': 'NG', 'johannesburg': 'ZA', 'cape town': 'ZA', 'nairobi': 'KE',
            'addis ababa': 'ET', 'casablanca': 'MA', 'accra': 'GH',
            
            # --- Airport Codes (Expanded) ---
            'lhr': 'GB', 'lgw': 'GB', 'man': 'GB', 'cdg': 'FR', 'ams': 'NL', 'fra': 'DE',
            'mad': 'ES', 'bcn': 'ES', 'fco': 'IT', 'mxp': 'IT', 'zrh': 'CH', 'vie': 'AT',
            'jfk': 'US', 'lax': 'US', 'ord': 'US', 'dfw': 'US', 'atl': 'US', 'den': 'US',
            'sfo': 'US', 'las': 'US', 'sea': 'US', 'mia': 'US', 'mco': 'US', 'ewr': 'US',
            'yyz': 'CA', 'yvr': 'CA', 'yul': 'CA',
            'dxb': 'AE', 'auh': 'AE', 'doh': 'QA', 'jyd': 'SA', 'ruh': 'SA', 'mcat': 'OM',
            'sin': 'SG', 'hkg': 'HK', 'hnd': 'JP', 'nrt': 'JP', 'icn': 'KR', 'bkk': 'TH',
            'del': 'IN', 'bom': 'IN', 'blr': 'IN', 'hyd': 'IN', 'maa': 'IN', 'ccu': 'IN',
            'syd': 'AU', 'mel': 'AU', 'bne': 'AU', 'akl': 'NZ',
            'gru': 'BR', 'bog': 'CO', 'lim': 'PE', 'scl': 'CL', 'eze': 'AR',
            'jnb': 'ZA', 'cpt': 'ZA', 'cai': 'EG', 'los': 'NG', 'nbo': 'KE'
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
            'cargo': [
                'cargo', 'freight', 'logistics', 'supply chain', 'warehouse',
                'fedex', 'ups', 'dhl', 'atlas air', 'kalitta', 'cargolux', 'western global',
                'polar air', 'amerijet', 'abx air', 'ati', 'omni air', 'national airlines'
            ],
            'helicopter': [
                'helicopter', 'rotor', 'vtol', 'rotary', 'hems', 'offshore',
                'bell', 'sikorsky', 'airbus helicopters', 'leonardo', 'robinson',
                'phi', 'air method', 'bristow', 'era', 'chn', 'cougar helicopters'
            ],
            'mro': [
                'mro', 'maintenance', 'repair', 'overhaul', 'mechanic', 'technician',
                'engineer', 'avionics', 'sheet metal', 'structure', 'a&p', 'b1', 'b2',
                'inspector', 'quality control', 'technical records', 'camu', 'planner',
                'mod center', 'completion', 'interior'
            ],
            'ground_ops': [
                'ground', 'ramp', 'airport operations', 'ground handling', 'baggage',
                'gate agent', 'station manager', 'dispatcher', 'loadmaster', 'turnaround',
                'fueler', 'passenger service', 'customer service agent', 'check-in',
                'lounge', 'concierge', 'security', 'screener'
            ],
            'atc': [
                'air traffic', 'atc', 'tower', 'approach control', 'radar', 'controller',
                'flight data', 'ground control', 'en route', 'center'
            ],
            'business': [
                'business aviation', 'private jet', 'executive', 'charter', 'corporate',
                'fractional', 'vip', 'v vip', 'bizjet',
                'netjets', 'flexjet', 'vista', 'xo', 'wheels up', 'flyexclusive',
                'jet aviation', 'signature', 'atlantic aviation', 'million air', 'gulfstream',
                'bombardier', 'dassault', 'embraer executive', 'citation'
            ],
            'low_cost': [
                'low cost', 'low-cost', 'budget airline', 'lcc', 'ulcc',
                'southwest', 'ryanair', 'easyjet', 'wizz', 'spirit', 'frontier',
                'allegiant', 'jetblue', 'indigo', 'airasia', 'scoot', 'volaris',
                'aig', 'flydubai', 'air arabia', 'pegasus', 'cebu pacific'
            ],
            'scheduled': [
                'scheduled', 'commercial airline', 'regular service', 'network carrier',
                'legacy carrier', 'flag carrier', 'regional airline',
                'american airlines', 'delta', 'united', 'british airways', 'lufthansa',
                'air france', 'klm', 'emirates', 'qatar airways', 'etihad',
                'singapore airlines', 'cathay pacific', 'ana', 'jal', 'qantas'
            ],
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
            # Parse posted_date if it's a string
            posted_date = job_data.get('posted_date')
            if isinstance(posted_date, str):
                from dateutil import parser
                try:
                    # Clean up common prefixes
                    clean_date = posted_date.lower().replace('posted', '').strip()
                    
                    # Handle relative dates
                    if 'yesterday' in clean_date:
                        posted_date = (timezone.now() - timedelta(days=1)).date()
                    elif 'today' in clean_date:
                        posted_date = timezone.now().date()
                    elif 'ago' in clean_date:
                        # "30+ days ago", "2 days ago"
                        import re
                        match = re.search(r'(\d+)', clean_date)
                        if match:
                            days = int(match.group(1))
                            posted_date = (timezone.now() - timedelta(days=days)).date()
                        else:
                            # Fallback to current date or None? 
                            # If "30+ days ago", assume 30.
                            posted_date = None
                    else:
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

    async def check_job_active(self, url: str, use_playwright: bool = False) -> tuple[bool, str]:
        """
        Check whether a job page is still active.
        Returns (is_active, reason) where reason describes why it was marked closed if False.
        """
        try:
            # 1. Lightweight requests check
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Use GET to check content
            # Allow redirects - if it redirects to search page, it might be closed
            try:
                r = await sync_to_async(requests.get)(url, headers=headers, timeout=10, allow_redirects=True)
            except Exception as e:
                logger.warning(f"Request failed for {url}: {e}")
                # If request fails connection, might be a temporary issue or site blocking
                return True, 'request_failed'

            status = r.status_code
            if status in (404, 410):
                return False, f'http_{status}'
            
            # Check redirects
            if len(r.history) > 0:
                final_url = r.url
                # Heuristic: If significant URL change (e.g. detailed slug to generic path), likely expired
                if len(final_url) < len(url) * 0.7 and 'login' not in final_url:
                    return False, 'redirected_to_generic'

            body = r.text or ''
            body_lower = body.lower()

            # Look for closed/expired keywords
            # Added more keywords
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
                'role has been filled',
                'posting is closed',
                'search results' # Sometimes redirects to search results
            ]
            
            # Limit search to first 50KB
            search_body = body_lower[:50000]
            
            for kw in closed_keywords:
                if kw in search_body:
                    # Check context? No, usually safe enough.
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

            # If requests didn't flag it, and we want to use playwright (e.g. for SPAs)
            if use_playwright:
                 # TODO: Implement Playwright check for JS-heavy sites
                 pass

            # If none matched, assume active
            return True, 'ok'

        except Exception as e:
            logger.debug(f"check_job_active error for {url}: {e}")
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
