from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Job, CompanyMapping, CrawlLog, ScheduleConfig, JobApplication, SavedJob, JobView
from .application_models import ShortlistedCandidate
from .tasks import backfill_senior_flags
import csv
from django.http import HttpResponse
from backendMain.admin import admin_site


@admin.register(Job, site=admin_site)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'company_link',
        'get_operation_type_display',
        'get_country_code_display',
        'posted_date',
        'get_status_badge',
        'get_senior_flag_display',
        'get_senior_override_display',
        'get_source_badge'
    )
    list_display_links = ('id', 'title')  # Make ID and title clickable to open job details
    search_fields = ('title', 'company', 'description', 'url', 'company_id')
    list_filter = (
        'status',
        'operation_type',
        'country_code',
        'senior_flag',
        'senior_override',
        'source',
        'posted_date',
        'created_at'
    )
    date_hierarchy = 'posted_date'
    readonly_fields = ('created_at', 'updated_at', 'get_job_preview', 'senior_flag')
    ordering = ('-posted_date',)
    list_per_page = 50
    save_on_top = True
    actions = (
        'export_as_csv',
        'mark_reviewed',
        'create_company_mappings',
        'mark_as_new',
        'mark_as_reviewed_action',
        'mark_as_archived',
        'auto_fill_missing_data',
        'highlight_incomplete',
        'recompute_seniority_now',
        'enqueue_backfill_seniority'
    )
    
    fieldsets = (
        ('✈️ Basic Information', {
            'fields': ('title', 'company', 'url'),
            'description': 'Essential job details - title and employer are required fields'
        }),
        ('🌍 Classification & Location', {
            'fields': ('operation_type', 'country_code', 'location', 'senior_override', 'senior_flag'),
            'description': 'Categorize the role by operation type, location and seniority level'
        }),
        ('📋 Job Details', {
            'fields': ('description', 'posted_date'),
            'classes': ('collapse',),
            'description': 'Full position description and posting date'
        }),
        ('🏷️ Status & Source', {
            'fields': ('status', 'source', 'last_checked'),
            'description': 'Track job status and data source'
        }),
        ('🔧 Technical Fields', {
            'fields': ('normalized_title', 'company_id'),
            'classes': ('collapse',),
            'description': 'Auto-generated fields used for matching and deduplication'
        }),
        ('👁️ Preview', {
            'fields': ('get_job_preview',),
            'classes': ('collapse',),
            'description': 'Visual preview of how this job appears to users'
        }),
        ('📊 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('🗂️ Raw Data', {
            'fields': ('raw_json',),
            'classes': ('collapse',),
            'description': 'Original JSON payload from scraper source'
        }),
    )
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add helpful context to edit form"""
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = True
        extra_context['show_save_and_add_another'] = True
        return super().change_view(request, object_id, form_url, extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        """Add helpful context to add form"""
        extra_context = extra_context or {}
        extra_context['show_save_and_add_another'] = True
        extra_context['show_save_and_continue'] = True
        return super().add_view(request, form_url, extra_context)
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with help texts"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['title'].help_text = 'Job title as posted (e.g., "Captain - Boeing 737 NG")'
        form.base_fields['company'].help_text = 'Airline or aviation company name'
        form.base_fields['operation_type'].help_text = 'Primary flight operations category'
        form.base_fields['country_code'].help_text = 'ISO country code where job is based (IN, US, AE, etc.)'
        form.base_fields['description'].help_text = 'Complete job description with requirements and benefits'
        form.base_fields['url'].help_text = 'Direct link to job application page'
        form.base_fields['status'].help_text = 'Current job posting status in our system'
        if 'senior_override' in form.base_fields:
            form.base_fields['senior_override'].help_text = 'Override senior detection: Yes = force senior, No = force non-senior, blank = auto from title'
        if 'senior_flag' in form.base_fields:
            form.base_fields['senior_flag'].help_text = 'Auto-computed effective senior flag (read-only)'
        form.base_fields['company_id'].help_text = 'Employer ID from source website (auto-filled by scraper)'
        return form

    def short_title(self, obj):
        """Display shortened title with missing indicator"""
        if obj.title:
            title = (obj.title[:80] + '...') if len(obj.title) > 80 else obj.title
            return format_html('<strong>{}</strong>', title)
        return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 5px; font-weight: bold;">⚠️ MISSING TITLE</span>')
    short_title.short_description = 'Title'

    def company_link(self, obj):
        """Display company with link to mapping and missing indicator"""
        if not obj.company:
            return format_html('<span style="background: #dc3545; color: white; padding: 3px 8px; border-radius: 5px; font-weight: bold;">⚠️ NO COMPANY</span>')
        norm = obj.company.strip().lower()
        try:
            mapping = CompanyMapping.objects.get(normalized_name=norm)
            url = reverse('admin:jobs_companymapping_change', args=(mapping.id,))
            return format_html(
                '<a href="{}" style="color: #0066cc; font-weight: bold;">🏢 {}</a>',
                url, obj.company
            )
        except CompanyMapping.DoesNotExist:
            # No mapping exists - show warning
            return format_html(
                '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 5px; font-weight: bold;">⚠️ {} (No Mapping)</span>',
                obj.company
            )
    company_link.short_description = 'Company'
    
    def get_status_badge(self, obj):
        """Display status with color badge"""
        status_styles = {
            'new': ('background: #10b981; color: white;', 'NEW'),
            'active': ('background: #059669; color: white;', 'ACTIVE'),
            'reviewed': ('background: #0284c7; color: white;', 'REVIEW'),
            'expired': ('background: #f59e0b; color: white;', 'EXPIRE'),
            'archived': ('background: #6b7280; color: white;', 'ARCHIVE'),
            'closed': ('background: #ef4444; color: white;', 'CLOSED'),
        }
        style, label = status_styles.get(obj.status, ('background: #000; color: white;', obj.status.upper()))
        return format_html(
            '<span style="{}; padding: 3px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; display: inline-block; text-align: center; min-width: 50px;">{}</span>',
            style, label
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'status'
    
    def get_source_badge(self, obj):
        """Display source with icon"""
        if obj.source:
            source_icons = {
                'aviation': ('✈️', 'Aviation Jobs'),
                'linkedin': ('💼', 'LinkedIn'),
                'airindia': ('🇮🇳', 'Air India'),
                'goose': ('🦆', 'GooseRecruitment'),
                'indeed': ('🔍', 'Indeed'),
                'company': ('🏢', 'Company Site'),
            }
            icon, name = source_icons.get(obj.source.lower(), ('🔗', obj.source))
            return format_html(
                '<span style="background: #e2e8f0; color: #1e293b; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 600;">{} {}</span>',
                icon, name
            )
        return format_html('<span style="background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">⚠️ NO SOURCE</span>')
    get_source_badge.short_description = 'Source'
    get_source_badge.admin_order_field = 'source'
    
    def get_senior_flag_display(self, obj):
        """Display senior flag with badge"""
        if obj.senior_flag:
            return format_html('<span style="background: #7c3aed; color: white; padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 600;">👔 SENIOR</span>')
        return format_html('<span style="color: #94a3b8; font-size: 11px;">—</span>')
    get_senior_flag_display.short_description = 'Senior'
    get_senior_flag_display.admin_order_field = 'senior_flag'

    def get_senior_override_display(self, obj):
        """Display override state with compact badge (Yes/No/Auto)"""
        if obj.senior_override is True:
            return format_html('<span style="background: #16a34a; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">Override: YES</span>')
        if obj.senior_override is False:
            return format_html('<span style="background: #ef4444; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">Override: NO</span>')
        return format_html('<span style="background: #e5e7eb; color: #374151; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600;">Override: AUTO</span>')
    get_senior_override_display.short_description = 'Override'
    get_senior_override_display.admin_order_field = 'senior_override'
    
    def get_operation_type_display(self, obj):
        """Display operation type with aviation icons"""
        if obj.operation_type:
            op_icons = {
                'passenger': ('✈️', '#dbeafe', '#1e40af'),
                'cargo': ('📦', '#fef3c7', '#92400e'),
                'business': ('🎩', '#f3e8ff', '#6b21a8'),
                'scheduled': ('🗓️', '#dbeafe', '#1e40af'),
                'low_cost': ('💺', '#fce7f3', '#9f1239'),
                'ad_hoc_charter': ('🛩️', '#e0e7ff', '#3730a3'),
                'helicopter': ('🚁', '#ddd6fe', '#5b21b6'),
                'mro': ('🔧', '#fed7aa', '#9a3412'),
                'ground_ops': ('🏢', '#d1fae5', '#065f46'),
                'atc': ('🎯', '#fecaca', '#991b1b'),
            }
            icon, bg, color = op_icons.get(obj.operation_type, ('✈️', '#dbeafe', '#1e40af'))
            return format_html(
                '<span style="background: {}; color: {}; padding: 3px 6px; border-radius: 4px; font-size: 11px; display: inline-block; text-align: center;">{}</span>',
                bg, color, icon
            )
        return format_html('<span style="background: #f3f4f6; color: #9ca3af; padding: 2px 6px; border-radius: 4px; font-size: 9px; display: inline-block;">—</span>')
    get_operation_type_display.short_description = 'Aviation Type'
    get_operation_type_display.admin_order_field = 'operation_type'
    
    def get_country_code_display(self, obj):
        """Display country code with missing indicator"""
        if obj.country_code:
            return format_html('<span style="font-weight: 600; font-family: monospace; color: #059669;">{}</span>', obj.country_code.upper())
        return format_html('<span style="background: #f3f4f6; color: #9ca3af; padding: 2px 6px; border-radius: 4px; font-size: 9px; display: inline-block;">—</span>')
    get_country_code_display.short_description = 'Country'
    get_country_code_display.admin_order_field = 'country_code'
    
    def get_job_preview(self, obj):
        """Display job preview with key information"""
        html = f"""
        <div style="border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #f9f9f9;">
            <h3 style="margin: 0 0 10px 0; color: #333;">{obj.title or 'No Title'}</h3>
            <p style="margin: 5px 0;"><strong>Company:</strong> {obj.company or '-'}</p>
            <p style="margin: 5px 0;"><strong>Type:</strong> {obj.operation_type or '-'}</p>
            <p style="margin: 5px 0;"><strong>Location:</strong> {obj.country_code or '-'}</p>
            <p style="margin: 5px 0;"><strong>Posted:</strong> {obj.posted_date or '-'}</p>
            <p style="margin: 5px 0;"><strong>URL:</strong> <a href="{obj.url}" target="_blank">View Job</a></p>
            {f'<p style="margin: 10px 0 5px 0; padding-top: 10px; border-top: 1px solid #ddd;"><strong>Description Preview:</strong></p><p style="margin: 5px 0; color: #666;">{obj.description[:300]}...</p>' if obj.description else ''}
        </div>
        """
        return format_html(html)
    get_job_preview.short_description = 'Job Preview'

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=jobs_export.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, f) for f in field_names]
            writer.writerow(row)
        return response

    export_as_csv.short_description = "Export Selected to CSV"

    def mark_reviewed(self, request, queryset):
        """Mark jobs as reviewed"""
        now = timezone.now()
        updated = queryset.update(last_checked=now)
        self.message_user(request, f"✓ Marked {updated} job(s) as reviewed (last_checked updated)")
    mark_reviewed.short_description = "✓ Mark as reviewed"

    def create_company_mappings(self, request, queryset):
        """Create company mappings from selected jobs"""
        created = 0
        for job in queryset:
            if not job.company:
                continue
            norm = job.company.strip().lower()
            obj, created_flag = CompanyMapping.objects.get_or_create(
                normalized_name=norm,
                defaults={'company_name': job.company, 'operation_type': job.operation_type}
            )
            if created_flag:
                created += 1
        self.message_user(request, f"✓ Created {created} company mapping(s) from selected jobs")
    create_company_mappings.short_description = "🏢 Create company mappings"
    
    def mark_as_new(self, request, queryset):
        """Mark jobs as new"""
        updated = queryset.update(status='new')
        self.message_user(request, f'✓ Marked {updated} job(s) as new')
    mark_as_new.short_description = '✨ Mark as new'
    
    def mark_as_reviewed_action(self, request, queryset):
        """Mark jobs as reviewed"""
        updated = queryset.update(status='reviewed')
        self.message_user(request, f'✓ Marked {updated} job(s) as reviewed')
    mark_as_reviewed_action.short_description = '✓ Mark as reviewed status'
    
    def mark_as_archived(self, request, queryset):
        """Archive jobs"""
        updated = queryset.update(status='archived')
        self.message_user(request, f'✓ Archived {updated} job(s)')
    mark_as_archived.short_description = '📦 Archive jobs'
    
    def auto_fill_missing_data(self, request, queryset):
        """Auto-fill missing operation_type and country_code from company mappings"""
        updated = 0
        no_mapping = []
        for job in queryset:
            if job.company and (not job.operation_type or not job.country_code):
                norm = job.company.strip().lower()
                try:
                    mapping = CompanyMapping.objects.get(normalized_name=norm)
                    changed = False
                    if not job.operation_type and mapping.operation_type:
                        job.operation_type = mapping.operation_type
                        changed = True
                    if not job.country_code and mapping.country_code:
                        job.country_code = mapping.country_code
                        changed = True
                    if changed:
                        job.save()
                        updated += 1
                except CompanyMapping.DoesNotExist:
                    if job.company not in no_mapping:
                        no_mapping.append(job.company)
        
        message = f'✓ Auto-filled missing data for {updated} job(s) from company mappings'
        if no_mapping:
            message += f' | ⚠️ {len(no_mapping)} companies need mapping: {", ".join(no_mapping[:5])}'
            if len(no_mapping) > 5:
                message += f' and {len(no_mapping) - 5} more'
        self.message_user(request, message)
    auto_fill_missing_data.short_description = '🔄 Auto-fill missing data from mappings'
    
    def highlight_incomplete(self, request, queryset):
        """Show statistics about incomplete jobs"""
        total = queryset.count()
        missing_title = queryset.filter(title__isnull=True).count() + queryset.filter(title='').count()
        missing_company = queryset.filter(company__isnull=True).count() + queryset.filter(company='').count()
        missing_type = queryset.filter(operation_type__isnull=True).count() + queryset.filter(operation_type='').count()
        missing_country = queryset.filter(country_code__isnull=True).count() + queryset.filter(country_code='').count()
        missing_desc = queryset.filter(description__isnull=True).count() + queryset.filter(description='').count()
        
        message = f'📊 Incomplete Data Report (of {total} selected jobs): '
        issues = []
        if missing_title: issues.append(f'❌ {missing_title} missing TITLE')
        if missing_company: issues.append(f'❌ {missing_company} missing COMPANY')
        if missing_type: issues.append(f'⚠️ {missing_type} missing TYPE')
        if missing_country: issues.append(f'⚠️ {missing_country} missing COUNTRY')
        if missing_desc: issues.append(f'ℹ️ {missing_desc} missing DESCRIPTION')
        
        if issues:
            message += ' | '.join(issues)
            self.message_user(request, message, level='warning')
        else:
            self.message_user(request, f'✅ All {total} selected jobs have complete data!')
    highlight_incomplete.short_description = '📊 Show incomplete data report'

    def recompute_seniority_now(self, request, queryset):
        """Recompute senior flag for selected jobs (respects overrides)"""
        count = 0
        for job in queryset:
            if job.senior_override is None:
                # Recompute by saving (model save applies logic)
                job.save()
                count += 1
        self.message_user(request, f'✓ Recomputed senior flag for {count} job(s) without overrides')
    recompute_seniority_now.short_description = '👔 Recompute seniority now (selected)'

    def enqueue_backfill_seniority(self, request, queryset):
        """Enqueue a background task to backfill senior flags for selected jobs"""
        ids = list(queryset.values_list('id', flat=True))
        result = backfill_senior_flags.delay(job_ids=ids, dry_run=False)
        self.message_user(request, f'🚀 Backfill task enqueued for {len(ids)} job(s). Task ID: {result.id}')
    enqueue_backfill_seniority.short_description = '🧰 Backfill seniority in background'


@admin.register(CompanyMapping, site=admin_site)
class CompanyMappingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_company_display',
        'get_review_status',
        'normalized_name',
        'operation_type',
        'country_code',
        'get_jobs_count',
        'get_stats_display',
        'short_notes'
    )
    search_fields = ('company_name', 'normalized_name', 'notes', 'reviewed_by')
    list_filter = (
        'needs_review',
        'auto_created',
        'operation_type',
        'country_code',
        'created_at',
        'reviewed_at'
    )
    list_editable = ('operation_type', 'country_code')
    actions = (
        'export_as_csv',
        'mark_as_reviewed_action',
        'apply_to_jobs',
        'refresh_statistics',
        'auto_detect_operation_type'
    )
    list_per_page = 50
    save_on_top = True
    date_hierarchy = 'created_at'
    readonly_fields = (
        'normalized_name',
        'total_jobs',
        'active_jobs',
        'last_job_date',
        'auto_created',
        'reviewed_by',
        'reviewed_at',
        'created_at',
        'updated_at',
        'get_mapping_summary',
        'get_unmapped_jobs_preview'
    )
    
    fieldsets = (
        ('🏢 Company Information', {
            'fields': ('company_name', 'normalized_name', 'get_mapping_summary'),
            'description': 'Company name and its normalized form for matching. Normalized name is automatically generated from company name.'
        }),
        ('✅ Review Status', {
            'fields': ('needs_review', 'auto_created', 'reviewed_by', 'reviewed_at'),
            'description': 'Track review and approval status for this company mapping'
        }),
        ('✈️ Aviation Classification', {
            'fields': ('operation_type', 'country_code'),
            'description': 'Set operation type and country. These will auto-apply to all jobs from this company.'
        }),
        ('📊 Statistics (Auto-Updated)', {
            'fields': ('total_jobs', 'active_jobs', 'last_job_date'),
            'description': 'Job statistics for this company (updated automatically)',
            'classes': ('collapse',)
        }),
        ('🔗 Unmapped Jobs', {
            'fields': ('get_unmapped_jobs_preview',),
            'description': 'Preview of jobs that might belong to this company but aren\'t linked yet',
            'classes': ('collapse',)
        }),
        ('📝 Notes & Information', {
            'fields': ('notes',),
            'description': 'Internal notes: hiring patterns, special requirements, contact info, etc.'
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-generate normalized_name if not provided"""
        if not obj.normalized_name and obj.company_name:
            obj.normalized_name = obj.company_name.strip().lower()
        super().save_model(request, obj, form, change)
        # Optionally update job statistics
        self._update_company_stats(obj)
    
    def _update_company_stats(self, mapping):
        """Update statistics for this company mapping"""
        jobs = Job.objects.filter(company__iexact=mapping.company_name)
        mapping.total_jobs = jobs.count()
        mapping.active_jobs = jobs.filter(status='active').count()
        latest_job = jobs.order_by('-posted_date').first()
        if latest_job and latest_job.posted_date:
            mapping.last_job_date = latest_job.posted_date
        mapping.save(update_fields=['total_jobs', 'active_jobs', 'last_job_date'])
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with help texts"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['company_name'].help_text = 'Official airline or company name (e.g., "Emirates Airlines", "Air India")'
        form.base_fields['operation_type'].help_text = 'Primary aviation operation type - applies to all jobs from this company'
        form.base_fields['country_code'].help_text = 'Primary country (2-letter ISO: IN, AE, US, GB, SG, etc.)'
        form.base_fields['notes'].help_text = 'Internal notes: hiring patterns, requirements, contact person, typical positions, etc.'
        return form
    
    def short_notes(self, obj):
        """Display shortened notes"""
        if obj.notes:
            notes = (obj.notes[:60] + '...') if len(obj.notes) > 60 else obj.notes
            return format_html('<span style="color: #64748b; font-style: italic; font-size: 11px;">📝 {}</span>', notes)
        return format_html('<span style="color: #cbd5e1;">—</span>')
    short_notes.short_description = 'Notes'
    
    def get_company_display(self, obj):
        """Display company name with inline status"""
        is_complete = obj.operation_type and obj.country_code
        icon_color = '#10b981' if is_complete else '#f59e0b'
        status_icon = '✓' if is_complete else '⚠'
        
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<strong style="color: #1e40af; font-size: 13px;">🏢 {}</strong>'
            '<span style="color: {}; font-size: 12px; font-weight: 700;">{}</span>'
            '</div>',
            obj.company_name,
            icon_color,
            status_icon
        )
    get_company_display.short_description = 'Company Name'
    get_company_display.admin_order_field = 'company_name'
    
    def get_operation_type_badge(self, obj):
        """Display operation type with aviation icon"""
        if obj.operation_type:
            op_icons = {
                'passenger': ('✈️', '#dbeafe', '#1e40af'),
                'cargo': ('📦', '#fef3c7', '#92400e'),
                'business': ('🎩', '#f3e8ff', '#6b21a8'),
                'scheduled': ('🗓️', '#dbeafe', '#1e40af'),
                'low_cost': ('💺', '#fce7f3', '#9f1239'),
                'ad_hoc_charter': ('🛩️', '#e0e7ff', '#3730a3'),
                'helicopter': ('🚁', '#ddd6fe', '#5b21b6'),
                'mro': ('🔧', '#fed7aa', '#9a3412'),
                'ground_ops': ('🏢', '#d1fae5', '#065f46'),
                'atc': ('🎯', '#fecaca', '#991b1b'),
            }
            icon, bg, color = op_icons.get(obj.operation_type, ('✈️', '#dbeafe', '#1e40af'))
            return format_html(
                '<span style="background: {}; color: {}; padding: 4px 8px; border-radius: 4px; font-size: 13px; display: inline-block; text-align: center; min-width: 35px;">{}</span>',
                bg, color, icon
            )
        return format_html('<span style="background: #f3f4f6; color: #9ca3af; padding: 4px 8px; border-radius: 4px; font-size: 11px; display: inline-block; min-width: 35px; text-align: center;">—</span>')
    get_operation_type_badge.short_description = 'Aviation Type'
    get_operation_type_badge.admin_order_field = 'operation_type'
    
    def get_country_badge(self, obj):
        """Display country code badge"""
        if obj.country_code:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-weight: 700; font-family: monospace; display: inline-block; min-width: 40px; text-align: center;">{}</span>',
                obj.country_code.upper()
            )
        return format_html('<span style="background: #f3f4f6; color: #9ca3af; padding: 3px 8px; border-radius: 4px; font-size: 9px; display: inline-block; min-width: 40px; text-align: center;">—</span>')
    get_country_badge.short_description = 'Country'
    get_country_badge.admin_order_field = 'country_code'
    
    def get_stats_display(self, obj):
        """Display job statistics"""
        return format_html(
            '<div style="font-size: 11px; line-height: 1.7;">'
            '<span style="color: #3b82f6; font-weight: 600;">📊 {}</span><br>'
            '<span style="color: #10b981; font-weight: 600;">🟢 {}</span>'
            '</div>',
            f'{obj.total_jobs} total',
            f'{obj.active_jobs} active'
        )
    get_stats_display.short_description = 'Statistics'
    
    def get_jobs_count(self, obj):
        """Display count of jobs for this company with link"""
        count = Job.objects.filter(company__iexact=obj.company_name).count()
        if count > 0:
            from urllib.parse import quote
            url = f"/admin/jobs/job/?company__iexact={quote(obj.company_name)}"
            return format_html(
                '<a href="{}" style="background: #3b82f6; color: white; padding: 5px 12px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 11px; display: inline-block;">📋 {} Jobs</a>',
                url, count
            )
        return format_html('<span style="color: #94a3b8; font-size: 11px;">No jobs</span>')
    get_jobs_count.short_description = 'View Jobs'
    
    def get_mapping_summary(self, obj):
        """Display comprehensive mapping summary"""
        from django.utils.safestring import mark_safe
        
        jobs = Job.objects.filter(company__iexact=obj.company_name)
        total_jobs = jobs.count()
        active_jobs = jobs.filter(status='active').count()
        new_jobs = jobs.filter(status='new').count()
        latest_job = jobs.order_by('-posted_date').first()
        
        html = f"""
        <div style="border: 2px solid #3b82f6; padding: 15px; border-radius: 8px; background: #eff6ff;">
            <h3 style="margin: 0 0 15px 0; color: #1e40af;">🏢 Company Mapping Overview</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold; width: 35%;">Company Name</td>
                    <td style="padding: 8px;"><strong>{obj.company_name}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Normalized Name</td>
                    <td style="padding: 8px;"><code style="background: #f1f5f9; padding: 3px 8px; border-radius: 4px;">{obj.normalized_name}</code></td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Operation Type</td>
                    <td style="padding: 8px;">{self.get_operation_type_badge(obj)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Country</td>
                    <td style="padding: 8px;">{self.get_country_badge(obj)}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Total Jobs</td>
                    <td style="padding: 8px;"><span style="color: #3b82f6; font-weight: 700; font-size: 16px;">{total_jobs}</span></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Active Jobs</td>
                    <td style="padding: 8px;"><span style="color: #10b981; font-weight: 700; font-size: 16px;">{active_jobs}</span></td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">New Jobs</td>
                    <td style="padding: 8px;"><span style="color: #f59e0b; font-weight: 700; font-size: 16px;">{new_jobs}</span></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Latest Job Posted</td>
                    <td style="padding: 8px;">{latest_job.posted_date.strftime('%B %d, %Y') if latest_job and latest_job.posted_date else 'No jobs yet'}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Mapping Created</td>
                    <td style="padding: 8px;">{obj.created_at.strftime('%B %d, %Y at %I:%M %p') if obj.created_at else 'Unknown'}</td>
                </tr>
            </table>
            
            {f'<div style="margin-top: 15px; padding: 12px; background: white; border-left: 3px solid #3b82f6; border-radius: 4px;"><strong style="color: #1e40af;">📝 Notes:</strong><br><p style="margin: 8px 0 0 0; color: #475569;">{obj.notes}</p></div>' if obj.notes else ''}
            
            <div style="margin-top: 15px; padding: 12px; background: #dcfce7; border-left: 3px solid #10b981; border-radius: 4px;">
                <strong style="color: #065f46;">💡 Tip:</strong> 
                <span style="color: #166534;">Setting operation type and country here will automatically apply to all jobs from this company.</span>
            </div>
        </div>
        """
        return mark_safe(html)
    get_mapping_summary.short_description = 'Mapping Details'
    
    def apply_to_jobs(self, request, queryset):
        """Apply mapping settings to all matching jobs"""
        updated_type = 0
        updated_country = 0
        
        for mapping in queryset:
            if not mapping.operation_type and not mapping.country_code:
                continue
                
            jobs = Job.objects.filter(company__iexact=mapping.company_name)
            
            for job in jobs:
                changed = False
                if mapping.operation_type and not job.operation_type:
                    job.operation_type = mapping.operation_type
                    updated_type += 1
                    changed = True
                if mapping.country_code and not job.country_code:
                    job.country_code = mapping.country_code
                    updated_country += 1
                    changed = True
                if changed:
                    job.save(update_fields=['operation_type', 'country_code', 'updated_at'])
        
        message = f'✓ Applied mapping settings: {updated_type} jobs updated with operation type, {updated_country} with country code'
        self.message_user(request, message)
    apply_to_jobs.short_description = '🔄 Apply settings to matching jobs'
    
    def refresh_statistics(self, request, queryset):
        """Refresh job statistics for selected companies"""
        for mapping in queryset:
            self._update_company_stats(mapping)
        self.message_user(request, f'✓ Refreshed statistics for {queryset.count()} company mapping(s)')
    refresh_statistics.short_description = '📊 Refresh job statistics'
    
    def auto_detect_operation_type(self, request, queryset):
        """Auto-detect operation type based on existing jobs"""
        updated = 0
        for mapping in queryset:
            if mapping.operation_type:  # Skip if already set
                continue
            
            # Check most common operation type in jobs from this company
            jobs = Job.objects.filter(company__iexact=mapping.company_name).exclude(operation_type__isnull=True).exclude(operation_type='')
            if jobs.exists():
                from django.db.models import Count
                most_common = jobs.values('operation_type').annotate(count=Count('id')).order_by('-count').first()
                if most_common:
                    mapping.operation_type = most_common['operation_type']
                    mapping.save(update_fields=['operation_type'])
                    updated += 1
        
        if updated > 0:
            self.message_user(request, f'✓ Auto-detected operation type for {updated} company mapping(s)')
        else:
            self.message_user(request, '⚠️ No operation types could be auto-detected', level='warning')
    auto_detect_operation_type.short_description = '🤖 Auto-detect operation type'
    
    def get_review_status(self, obj):
        """Display review status badge"""
        if obj.needs_review:
            if obj.auto_created:
                return format_html(
                    '<div style="display: flex; flex-direction: column; gap: 2px; align-items: flex-start;">'
                    '<span style="background: #fef3c7; color: #92400e; padding: 2px 6px; border-radius: 3px; font-size: 8px; font-weight: 600; white-space: nowrap;">AUTO</span>'
                    '<span style="background: #fbbf24; color: #78350f; padding: 2px 6px; border-radius: 3px; font-size: 8px; font-weight: 600; white-space: nowrap;">REVIEW</span>'
                    '</div>'
                )
            return format_html(
                '<span style="background: #fbbf24; color: #78350f; padding: 3px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; display: inline-block; white-space: nowrap;">REVIEW</span>'
            )
        else:
            if obj.reviewed_by:
                return format_html(
                    '<div style="display: flex; flex-direction: column; gap: 1px; align-items: flex-start;">'
                    '<span style="background: #10b981; color: white; padding: 2px 6px; border-radius: 3px; font-size: 8px; font-weight: 600; white-space: nowrap;">✓ OK</span>'
                    '<span style="color: #9ca3af; font-size: 7px;">{}</span>'
                    '</div>',
                    obj.reviewed_by[:10]
                )
            return format_html(
                '<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 9px; font-weight: 600; display: inline-block; white-space: nowrap;">✓ OK</span>'
            )
    get_review_status.short_description = 'Review Status'
    get_review_status.admin_order_field = 'needs_review'
    
    def get_unmapped_jobs_preview(self, obj):
        """Show jobs that might need to be mapped to this company"""
        from django.utils.safestring import mark_safe
        from difflib import SequenceMatcher
        
        # Find jobs with similar company names that don't match exactly
        all_jobs = Job.objects.exclude(company__iexact=obj.company_name).values('company').distinct()[:200]
        
        similar_companies = []
        for job in all_jobs:
            company = job['company']
            if company and len(company) > 2:
                # Calculate similarity
                similarity = SequenceMatcher(None, obj.company_name.lower(), company.lower()).ratio()
                if similarity > 0.6:  # 60% similarity threshold
                    count = Job.objects.filter(company__iexact=company).count()
                    similar_companies.append({
                        'name': company,
                        'similarity': similarity,
                        'count': count
                    })
        
        # Sort by similarity
        similar_companies.sort(key=lambda x: x['similarity'], reverse=True)
        
        if not similar_companies:
            return mark_safe('<p style="color: #10b981; font-weight: 600;">✓ No similar unmapped companies found</p>')
        
        html = '<div style="border: 2px solid #fbbf24; padding: 15px; border-radius: 8px; background: #fef3c7;">'
        html += f'<h4 style="margin: 0 0 10px 0; color: #78350f;">🔍 Found {len(similar_companies)} potential matches:</h4>'
        html += '<table style="width: 100%; border-collapse: collapse;">'
        
        for company_info in similar_companies[:10]:  # Show top 10
            similarity_pct = int(company_info['similarity'] * 100)
            html += f'''
            <tr style="border-bottom: 1px solid #fbbf24;">
                <td style="padding: 8px; font-weight: 600;">{company_info['name']}</td>
                <td style="padding: 8px; text-align: center;">
                    <span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 10px;">{similarity_pct}% match</span>
                </td>
                <td style="padding: 8px; text-align: right;">{company_info['count']} jobs</td>
            </tr>
            '''
        
        html += '</table>'
        html += '<p style="margin: 10px 0 0 0; color: #78350f; font-size: 12px;"><strong>Tip:</strong> If these are the same company, update the company name in jobs to match this mapping.</p>'
        html += '</div>'
        
        return mark_safe(html)
    get_unmapped_jobs_preview.short_description = 'Similar Unmapped Companies'
    
    def mark_as_reviewed_action(self, request, queryset):
        """Mark selected company mappings as reviewed"""
        updated = 0
        for mapping in queryset.filter(needs_review=True):
            mapping.mark_as_reviewed(username=request.user.username if request.user.is_authenticated else 'admin')
            updated += 1
        
        if updated > 0:
            self.message_user(request, f'✓ Marked {updated} company mapping(s) as reviewed')
        else:
            self.message_user(request, '⚠️ No mappings needed review', level='warning')
    mark_as_reviewed_action.short_description = '✓ Mark as reviewed'

    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [f.name for f in meta.fields]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=company_mappings.csv'
        writer = csv.writer(response)
        writer.writerow(field_names)
        for obj in queryset:
            row = [getattr(obj, f) for f in field_names]
            writer.writerow(row)
        return response

    export_as_csv.short_description = "Export CompanyMappings to CSV"


@admin.register(ScheduleConfig, site=admin_site)
class ScheduleConfigAdmin(admin.ModelAdmin):
    """Admin interface for scheduling configuration"""
    
    def has_add_permission(self, request):
        # Allow adding only if config doesn't exist
        return not ScheduleConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Never allow deletion
        return False
    
    fieldsets = (
        ('🔴 MASTER CONTROL', {
            'fields': ('get_status_display', 'scheduling_enabled'),
            'description': 'Main on/off switch for ALL automated tasks. When disabled, NOTHING runs automatically.'
        }),
        ('🤖 Scraper Automation', {
            'fields': ('scraper_schedule_enabled', 'scraper_run_times'),
            'description': 'Control automated scraping schedule (twice daily by default)'
        }),
        ('🗑️ Job Expiry', {
            'fields': ('job_expiry_enabled', 'job_expiry_days'),
            'description': 'Automatically expire old job postings'
        }),
        ('📊 Reports', {
            'fields': ('daily_reports_enabled', 'weekly_reports_enabled', 'report_email_recipients'),
            'description': 'Automated report generation and delivery'
        }),
        ('🚨 Alerts', {
            'fields': ('senior_role_alerts_enabled', 'health_check_alerts_enabled', 'alert_email_recipients'),
            'description': 'Email notifications for important events'
        }),
        ('ℹ️ Metadata', {
            'fields': ('last_updated', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('get_status_display', 'last_updated')
    list_display = ['__str__', 'get_status_badge', 'get_active_features']
    save_on_top = True
    
    def get_status_display(self, obj):
        """Show visual status indicator"""
        if obj.scheduling_enabled:
            return format_html(
                '<div style="padding: 15px; background: #d4edda; border: 2px solid #28a745; border-radius: 5px; text-align: center;">'
                '<span style="font-size: 24px;">🟢</span><br>'
                '<strong style="color: #155724; font-size: 18px;">SCHEDULING ENABLED</strong><br>'
                '<span style="color: #155724;">All automated tasks are active</span>'
                '</div>'
            )
        else:
            return format_html(
                '<div style="padding: 15px; background: #f8d7da; border: 2px solid #dc3545; border-radius: 5px; text-align: center;">'
                '<span style="font-size: 24px;">🔴</span><br>'
                '<strong style="color: #721c24; font-size: 18px;">SCHEDULING DISABLED</strong><br>'
                '<span style="color: #721c24;">No automated tasks will run</span>'
                '</div>'
            )
    get_status_display.short_description = 'Current Status'
    
    def get_status_badge(self, obj):
        """Status badge for list view"""
        if obj.scheduling_enabled:
            return format_html(
                '<span style="background: #28a745; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">'
                '🟢 ENABLED'
                '</span>'
            )
        else:
            return format_html(
                '<span style="background: #dc3545; color: white; padding: 5px 10px; border-radius: 3px; font-weight: bold;">'
                '🔴 DISABLED'
                '</span>'
            )
    get_status_badge.short_description = 'Status'
    
    def get_active_features(self, obj):
        """Show which features are enabled"""
        if not obj.scheduling_enabled:
            return format_html('<span style="color: #999;">All features disabled</span>')
        
        features = []
        if obj.scraper_schedule_enabled:
            features.append('🤖 Scrapers')
        if obj.job_expiry_enabled:
            features.append('🗑️ Expiry')
        if obj.daily_reports_enabled:
            features.append('📊 Daily Reports')
        if obj.weekly_reports_enabled:
            features.append('📊 Weekly Reports')
        if obj.senior_role_alerts_enabled:
            features.append('🚨 Senior Alerts')
        if obj.health_check_alerts_enabled:
            features.append('🏥 Health Checks')
        
        if not features:
            return format_html('<span style="color: #ffc107;">⚠️ No features enabled</span>')
        
        return format_html('<br>'.join(features))
    get_active_features.short_description = 'Active Features'
    
    def save_model(self, request, obj, form, change):
        """Track who made changes"""
        if request.user.is_authenticated:
            obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def changelist_view(self, request, extra_context=None):
        """Redirect to edit page since this is a singleton"""
        obj = ScheduleConfig.get_config()
        from django.shortcuts import redirect
        return redirect(reverse('admin:jobs_scheduleconfig_change', args=[obj.id]))


@admin.register(JobApplication, site=admin_site)
class JobApplicationAdmin(admin.ModelAdmin):
    """Admin interface for job applications with detailed tracking"""
    list_display = (
        'id',
        'get_applicant_display',
        'get_job_display',
        'get_status_badge',
        'get_rating_display',
        'applied_at',
        'get_days_since',
        'get_reviewer_display'
    )
    list_display_links = ('id', 'get_applicant_display')
    search_fields = (
        'applicant__username',
        'applicant__email',
        'applicant__first_name',
        'applicant__last_name',
        'job__title',
        'job__company',
        'cover_letter',
        'recruiter_notes'
    )
    list_filter = (
        'status',
        'rating',
        'applied_at',
        'reviewed_at',
        'reviewed_by'
    )
    date_hierarchy = 'applied_at'
    readonly_fields = (
        'applied_at',
        'updated_at',
        'get_application_summary',
        # 'days_since_application' removed to fix admin error
    )
    ordering = ['-applied_at']
    list_per_page = 50
    save_on_top = True
    actions = (
        'mark_as_shortlisted',
        'mark_as_rejected',
        'mark_as_interview_scheduled',
        'export_applications_csv',
        'bulk_status_update'
    )
    
    fieldsets = (
        ('👨‍✈️ Applicant & Job', {
            'fields': ('applicant', 'job', 'resume', 'get_application_summary'),
            'description': 'Application details - which candidate applied for which position'
        }),
        ('📝 Application Content', {
            'fields': ('cover_letter', 'applicant_notes'),
            'description': 'Content submitted by the applicant',
            'classes': ('collapse',)
        }),
        ('⚡ Status & Rating', {
            'fields': ('status', 'rating'),
            'description': 'Current application status and rating'
        }),
        ('👔 Recruiter Feedback', {
            'fields': ('recruiter_notes', 'reviewed_by', 'reviewed_at'),
            'description': 'Internal notes and review details'
        }),
        ('📅 Interview Details', {
            'fields': ('interview_date', 'interview_notes'),
            'description': 'Interview scheduling and notes',
            'classes': ('collapse',)
        }),
        ('📊 Metadata', {
            'fields': ('applied_at', 'updated_at', 'days_since_application', 'source_device', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_applicant_display(self, obj):
        """Display applicant with full name and email"""
        user = obj.applicant
        full_name = user.get_full_name() or user.username
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #1e40af; font-size: 13px;">👤 {}</strong><br>'
            '<span style="color: #6b7280; font-size: 11px;">📧 {}</span>'
            '</div>',
            full_name,
            user.email or 'No email'
        )
    get_applicant_display.short_description = 'Applicant'
    get_applicant_display.admin_order_field = 'applicant__username'
    
    def get_job_display(self, obj):
        """Display job title and company"""
        title = (obj.job.title[:50] + '...') if len(obj.job.title) > 50 else obj.job.title
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #059669; font-size: 12px;">{}</strong><br>'
            '<span style="color: #6b7280; font-size: 11px;">🏢 {}</span>'
            '</div>',
            title,
            obj.job.company
        )
    get_job_display.short_description = 'Job Position'
    get_job_display.admin_order_field = 'job__title'
    
    def get_status_badge(self, obj):
        """Display status with color-coded badge"""
        status_styles = {
            'pending': ('background: #fbbf24; color: #78350f;', '⏳ PENDING'),
            'reviewing': ('background: #3b82f6; color: white;', '👀 REVIEWING'),
            'shortlisted': ('background: #8b5cf6; color: white;', '⭐ SHORTLISTED'),
            'interview_scheduled': ('background: #06b6d4; color: white;', '📅 INTERVIEW'),
            'interviewed': ('background: #0284c7; color: white;', '✓ INTERVIEWED'),
            'offer_sent': ('background: #10b981; color: white;', '📧 OFFER SENT'),
            'accepted': ('background: #059669; color: white;', '✅ ACCEPTED'),
            'rejected': ('background: #ef4444; color: white;', '❌ REJECTED'),
            'withdrawn': ('background: #6b7280; color: white;', '🚫 WITHDRAWN'),
        }
        style, label = status_styles.get(obj.status, ('background: #000; color: white;', obj.status.upper()))
        return format_html(
            '<span style="{}; padding: 5px 12px; border-radius: 10px; font-size: 10px; font-weight: 700; letter-spacing: 0.5px; display: inline-block;">{}</span>',
            style, label
        )
    get_status_badge.short_description = 'Status'
    get_status_badge.admin_order_field = 'status'
    
    def get_rating_display(self, obj):
        """Display rating with stars"""
        if obj.rating:
            stars = '⭐' * obj.rating + '☆' * (5 - obj.rating)
            color = '#f59e0b' if obj.rating >= 4 else '#3b82f6' if obj.rating >= 3 else '#6b7280'
            return format_html(
                '<span style="color: {}; font-size: 16px; letter-spacing: 2px;">{}</span><br>'
                '<span style="color: #6b7280; font-size: 10px;">({}/5)</span>',
                color, stars, obj.rating
            )
        return format_html('<span style="color: #cbd5e1;">Not rated</span>')
    get_rating_display.short_description = 'Rating'
    get_rating_display.admin_order_field = 'rating'
    
    def get_days_since(self, obj):
        """Show days since application"""
        days = obj.days_since_application
        if days == 0:
            return format_html('<span style="color: #10b981; font-weight: 600;">🆕 Today</span>')
        elif days == 1:
            return format_html('<span style="color: #3b82f6; font-weight: 600;">Yesterday</span>')
        elif days <= 7:
            return format_html('<span style="color: #059669;">{} days ago</span>', days)
        elif days <= 30:
            return format_html('<span style="color: #f59e0b;">{} days ago</span>', days)
        else:
            return format_html('<span style="color: #ef4444;">{} days ago</span>', days)
    get_days_since.short_description = 'Applied'
    
    def get_reviewer_display(self, obj):
        """Show who reviewed and when"""
        if obj.reviewed_by:
            return format_html(
                '<span style="color: #3b82f6; font-size: 11px;">👔 {}</span><br>'
                '<span style="color: #9ca3af; font-size: 10px;">{}</span>',
                obj.reviewed_by.username,
                obj.reviewed_at.strftime('%b %d, %Y') if obj.reviewed_at else 'Unknown'
            )
        return format_html('<span style="color: #cbd5e1; font-size: 11px;">Not reviewed</span>')
    get_reviewer_display.short_description = 'Reviewed By'
    
    def get_application_summary(self, obj):
        """Display comprehensive application summary"""
        from django.utils.safestring import mark_safe
        
        user = obj.applicant
        full_name = user.get_full_name() or user.username
        
        # Resume info
        resume_info = 'No resume attached'
        if obj.resume:
            resume_info = f'<a href="/admin/resumes/resume/{obj.resume.id}/change/" style="color: #3b82f6; text-decoration: underline;" target="_blank">View Resume: {obj.resume.filename}</a>'
            if obj.resume.total_score:
                resume_info += f'<br><span style="color: #059669; font-weight: 600;">Score: {obj.resume.total_score}</span>'
        
        html = f"""
        <div style="border: 2px solid #3b82f6; padding: 15px; border-radius: 8px; background: #eff6ff;">
            <h3 style="margin: 0 0 15px 0; color: #1e40af;">👨‍✈️ Application Overview</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold; width: 30%;">Applicant</td>
                    <td style="padding: 8px;"><strong>{full_name}</strong> ({user.username})</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Email</td>
                    <td style="padding: 8px;"><a href="mailto:{user.email}">{user.email or 'Not provided'}</a></td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Job Position</td>
                    <td style="padding: 8px;"><a href="/admin/jobs/job/{obj.job.id}/change/" target="_blank" style="color: #059669; font-weight: 600;">{obj.job.title}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Company</td>
                    <td style="padding: 8px;">{obj.job.company}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Resume</td>
                    <td style="padding: 8px;">{resume_info}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Status</td>
                    <td style="padding: 8px;">{self.get_status_badge(obj)}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Rating</td>
                    <td style="padding: 8px;">{self.get_rating_display(obj)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Applied</td>
                    <td style="padding: 8px;">{obj.applied_at.strftime('%B %d, %Y at %I:%M %p') if obj.applied_at else 'Unknown'} ({obj.days_since_application} days ago)</td>
                </tr>
                {'<tr style="background: white;"><td style="padding: 8px; font-weight: bold;">Reviewed By</td><td style="padding: 8px;">' + obj.reviewed_by.username + f' on {obj.reviewed_at.strftime("%B %d, %Y")}</td></tr>' if obj.reviewed_by else ''}
                {'<tr><td style="padding: 8px; font-weight: bold;">Interview Date</td><td style="padding: 8px;"><span style="color: #3b82f6; font-weight: 600;">' + obj.interview_date.strftime('%B %d, %Y at %I:%M %p') + '</span></td></tr>' if obj.interview_date else ''}
            </table>
            
            {f'<div style="margin-top: 15px; padding: 12px; background: white; border-left: 3px solid #10b981; border-radius: 4px;"><strong style="color: #065f46;">📝 Cover Letter:</strong><br><p style="margin: 8px 0 0 0; color: #4b5563; white-space: pre-wrap;">{obj.cover_letter[:500] + "..." if len(obj.cover_letter) > 500 else obj.cover_letter}</p></div>' if obj.cover_letter else ''}
            
            {f'<div style="margin-top: 12px; padding: 12px; background: white; border-left: 3px solid #f59e0b; border-radius: 4px;"><strong style="color: #92400e;">💼 Recruiter Notes:</strong><br><p style="margin: 8px 0 0 0; color: #4b5563; white-space: pre-wrap;">{obj.recruiter_notes}</p></div>' if obj.recruiter_notes else ''}
        </div>
        """
        return mark_safe(html)
    get_application_summary.short_description = 'Application Details'
    
    # Actions
    def mark_as_shortlisted(self, request, queryset):
        updated = queryset.update(status='shortlisted')
        self.message_user(request, f'✓ Marked {updated} application(s) as shortlisted')
    mark_as_shortlisted.short_description = '⭐ Mark as shortlisted'
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'✓ Marked {updated} application(s) as rejected')
    mark_as_rejected.short_description = '❌ Mark as rejected'
    
    def mark_as_interview_scheduled(self, request, queryset):
        updated = queryset.update(status='interview_scheduled')
        self.message_user(request, f'✓ Marked {updated} application(s) for interview')
    mark_as_interview_scheduled.short_description = '📅 Schedule interview'
    
    def export_applications_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=applications_{timezone.now().strftime("%Y%m%d")}.csv'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Applicant', 'Email', 'Job Title', 'Company', 'Status', 'Rating', 'Applied Date', 'Days Since'])
        
        for app in queryset:
            writer.writerow([
                app.id,
                app.applicant.get_full_name() or app.applicant.username,
                app.applicant.email,
                app.job.title,
                app.job.company,
                app.status,
                app.rating or 'N/A',
                app.applied_at.strftime('%Y-%m-%d'),
                app.days_since_application
            ])
        return response
    export_applications_csv.short_description = '📥 Export as CSV'


@admin.register(SavedJob, site=admin_site)
class SavedJobAdmin(admin.ModelAdmin):
    """Admin interface for saved/bookmarked jobs"""
    list_display = (
        'id',
        'get_user_display',
        'get_job_display',
        'saved_at',
        'get_has_notes',
        'get_job_status'
    )
    list_display_links = ('id', 'get_user_display')
    search_fields = (
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'job__title',
        'job__company',
        'notes'
    )
    list_filter = ('saved_at', 'job__status', 'job__company')
    date_hierarchy = 'saved_at'
    ordering = ['-saved_at']
    list_per_page = 50
    readonly_fields = ('saved_at',)
    
    fieldsets = (
        ('👤 User & Job', {
            'fields': ('user', 'job'),
            'description': 'Which user saved which job'
        }),
        ('📝 Notes', {
            'fields': ('notes',),
            'description': 'Personal notes from the user about this job'
        }),
        ('📊 Metadata', {
            'fields': ('saved_at',),
        }),
    )
    
    def get_user_display(self, obj):
        full_name = obj.user.get_full_name() or obj.user.username
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #1e40af;">👤 {}</strong><br>'
            '<span style="color: #6b7280; font-size: 11px;">{}</span>'
            '</div>',
            full_name,
            obj.user.email or 'No email'
        )
    get_user_display.short_description = 'User'
    get_user_display.admin_order_field = 'user__username'
    
    def get_job_display(self, obj):
        title = (obj.job.title[:50] + '...') if len(obj.job.title) > 50 else obj.job.title
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #059669;">{}</strong><br>'
            '<span style="color: #6b7280; font-size: 11px;">🏢 {}</span>'
            '</div>',
            title,
            obj.job.company
        )
    get_job_display.short_description = 'Job'
    get_job_display.admin_order_field = 'job__title'
    
    def get_has_notes(self, obj):
        if obj.notes:
            return format_html(
                '<span style="color: #059669; font-weight: 600;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: #cbd5e1;">—</span>'
        )
    get_has_notes.short_description = 'Has Notes'
    
    def get_job_status(self, obj):
        status_styles = {
            'new': ('background: #10b981; color: white;', '✨ NEW'),
            'active': ('background: #059669; color: white;', '🟢 ACTIVE'),
            'reviewed': ('background: #0284c7; color: white;', '✓ REVIEWED'),
            'expired': ('background: #f59e0b; color: white;', '⏰ EXPIRED'),
            'archived': ('background: #6b7280; color: white;', '📦 ARCHIVED'),
            'closed': ('background: #ef4444; color: white;', '🔒 CLOSED'),
        }
        style, label = status_styles.get(obj.job.status, ('background: #000; color: white;', obj.job.status.upper()))
        return format_html(
            '<span style="{}; padding: 3px 10px; border-radius: 8px; font-size: 10px; font-weight: 600;">{}</span>',
            style, label
        )
    get_job_status.short_description = 'Job Status'


@admin.register(CrawlLog, site=admin_site)
class CrawlLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'get_source_display',
        'run_time',
        'get_stats_display',
        'get_success_rate'
    )
    list_filter = ('source', 'run_time')
    readonly_fields = ('run_time',)
    date_hierarchy = 'run_time'
    ordering = ('-run_time',)
    list_per_page = 50
    
    def get_source_display(self, obj):
        """Display source with icon"""
        source_icons = {
            'aviation': '✈️',
            'linkedin': '💼',
            'airindia': '🛫',
            'goose': '🦆',
        }
        icon = source_icons.get(obj.source.lower() if obj.source else '', '🔗')
        return format_html(
            '<span style="background: #f0f0f0; padding: 5px 12px; border-radius: 8px; font-weight: bold;">{} {}</span>',
            icon, obj.source
        )
    get_source_display.short_description = 'Source'
    get_source_display.admin_order_field = 'source'
    
    def get_stats_display(self, obj):
        """Display statistics in a compact format"""
        return format_html(
            '<span style="color: #0066cc;">📊 Found: {}</span> | '
            '<span style="color: #28a745;">✓ Inserted: {}</span> | '
            '<span style="color: #fd7e14;">↻ Updated: {}</span>',
            obj.items_found, obj.items_inserted, obj.items_updated
        )
    get_stats_display.short_description = 'Statistics'
    
    def get_success_rate(self, obj):
        """Calculate and display success rate"""
        if obj.items_found > 0:
            success = obj.items_inserted + obj.items_updated
            rate = (success / obj.items_found) * 100
            color = '#28a745' if rate >= 80 else '#fd7e14' if rate >= 50 else '#dc3545'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}%</span>',
                color, round(rate, 1)
            )

