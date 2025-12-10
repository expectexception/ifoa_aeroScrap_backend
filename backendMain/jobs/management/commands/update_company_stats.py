"""
Management command to update company statistics
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Q, Max
from jobs.models import Job, CompanyMapping
from django.utils import timezone


class Command(BaseCommand):
    help = 'Update company statistics (total_jobs, active_jobs, last_job_date)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--company',
            type=str,
            help='Update statistics for a specific company'
        )
        parser.add_argument(
            '--create-missing',
            action='store_true',
            help='Create missing company mappings from jobs'
        )

    def handle(self, *args, **options):
        start_time = timezone.now()
        
        if options['create_missing']:
            self.stdout.write(self.style.WARNING('Creating missing company mappings...'))
            self.create_missing_mappings()
        
        if options['company']:
            self.update_company(options['company'])
        else:
            self.update_all_companies()
        
        duration = (timezone.now() - start_time).total_seconds()
        self.stdout.write(
            self.style.SUCCESS(f'✓ Completed in {duration:.2f} seconds')
        )
    
    def create_missing_mappings(self):
        """Create company mappings for companies that don't have one"""
        # Get all unique companies from jobs
        companies = Job.objects.values_list('company', flat=True).distinct()
        existing = set(
            CompanyMapping.objects.values_list('normalized_name', flat=True)
        )
        
        created = 0
        for company in companies:
            if not company or not company.strip():
                continue
            
            normalized = company.strip().lower()
            if normalized in existing:
                continue
            
            # Get most common operation_type and country for this company
            job_sample = Job.objects.filter(company__iexact=company).first()
            
            try:
                CompanyMapping.objects.create(
                    company_name=company,
                    normalized_name=normalized,
                    operation_type=job_sample.operation_type if job_sample else None,
                    country_code=job_sample.country_code if job_sample else None,
                )
                created += 1
                existing.add(normalized)
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creating mapping for {company}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Created {created} company mappings')
        )
    
    def update_company(self, company_name):
        """Update statistics for a specific company"""
        try:
            mapping = CompanyMapping.objects.get(
                normalized_name=company_name.strip().lower()
            )
            mapping.update_statistics()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Updated {mapping.company_name}: '
                    f'{mapping.total_jobs} total, {mapping.active_jobs} active'
                )
            )
        except CompanyMapping.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'Company mapping not found: {company_name}')
            )
    
    def update_all_companies(self):
        """Update statistics for all companies"""
        self.stdout.write('Updating all company statistics...')
        
        mappings = CompanyMapping.objects.all()
        total = mappings.count()
        updated = 0
        
        for i, mapping in enumerate(mappings, 1):
            try:
                mapping.update_statistics()
                updated += 1
                
                if i % 50 == 0:
                    self.stdout.write(f'Progress: {i}/{total}...')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f'Error updating {mapping.company_name}: {e}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'✓ Updated {updated}/{total} company mappings')
        )
