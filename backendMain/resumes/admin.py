from django.contrib import admin
from django.utils.html import format_html
from django.contrib.admin import SimpleListFilter
from .models import Resume
from django.http import HttpResponse
import json
from django.utils import timezone
from backendMain.admin import admin_site


class ScoreRangeListFilter(SimpleListFilter):
    title = 'score band'
    parameter_name = 'score_band'

    def lookups(self, request, model_admin):
        return (
            ('90+', 'Excellent (90-100)'),
            ('80+', 'Strong (80-89)'),
            ('60+', 'Good (60-79)'),
            ('40+', 'Fair (40-59)'),
            ('1-39', 'Low (1-39)'),
            ('0', 'Unscored (0 or null)'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == '90+':
            return queryset.filter(total_score__gte=90)
        if val == '80+':
            return queryset.filter(total_score__gte=80, total_score__lt=90)
        if val == '60+':
            return queryset.filter(total_score__gte=60, total_score__lt=80)
        if val == '40+':
            return queryset.filter(total_score__gte=40, total_score__lt=60)
        if val == '1-39':
            return queryset.filter(total_score__gte=1, total_score__lt=40)
        if val == '0':
            return queryset.filter(total_score__isnull=True) | queryset.filter(total_score=0)
        return queryset


class ParsedStatusListFilter(SimpleListFilter):
    title = 'parsed status'
    parameter_name = 'parsed_status'

    def lookups(self, request, model_admin):
        return (
            ('parsed', 'Parsed'),
            ('pending', 'Pending'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'parsed':
            return queryset.filter(parsed_at__isnull=False)
        if val == 'pending':
            return queryset.filter(parsed_at__isnull=True)
        return queryset


@admin.register(Resume, site=admin_site)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('get_candidate_display', 'get_contact_display', 'get_score_badge', 'get_parsed_status', 'created_at')
    search_fields = ('filename', 'name', 'email')
    list_filter = (ParsedStatusListFilter, ScoreRangeListFilter, 'created_at')
    readonly_fields = ('created_at', 'updated_at', 'parsed_at', 'get_resume_summary')
    date_hierarchy = 'created_at'
    list_per_page = 50
    actions = ('export_as_json', 'export_as_csv', 'mark_as_reviewed', 'export_selected_candidates')
    save_on_top = True
    ordering = ('-created_at',)
    
    fieldsets = (
        ('👤 Candidate Identity', {
            'fields': ('filename', 'name', 'get_resume_summary'),
            'description': 'Resume file and candidate identification details'
        }),
        ('📞 Contact Information', {
            'fields': ('email', 'phones'),
            'description': 'Direct contact details for reaching the candidate'
        }),
        ('✈️ Aviation Skills & Experience', {
            'fields': ('skills', 'aviation', 'experience'),
            'description': 'Professional qualifications, flight hours, certifications, and training'
        }),
        ('🎯 Candidate Evaluation', {
            'fields': ('total_score',),
            'description': 'Overall candidate rating based on qualifications and experience match'
        }),
        ('📄 Raw Data', {
            'fields': ('raw_text', 'file_content', 'additional_info'),
            'classes': ('collapse',),
            'description': 'Original parsed data and additional metadata'
        }),
        ('⏱️ Processing Timestamps', {
            'fields': ('created_at', 'updated_at', 'parsed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with aviation-specific guidance"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['filename'].help_text = 'Original resume file name (e.g., "John_Doe_Captain_B737.pdf")'
        form.base_fields['name'].help_text = 'Full name of the aviation professional (e.g., "Captain John Doe")'
        form.base_fields['email'].help_text = 'Primary email address for correspondence'
        form.base_fields['phones'].help_text = 'List of phone numbers with country codes (JSON format: ["phone1", "phone2"])'
        form.base_fields['skills'].help_text = 'Aviation skills and qualifications in JSON format'
        form.base_fields['aviation'].help_text = 'Aviation-specific details: licenses, certifications, type ratings (JSON format)'
        form.base_fields['experience'].help_text = 'Work experience details: flight hours, airlines, positions (JSON format)'
        form.base_fields['total_score'].help_text = 'Candidate match score (0-100): considers experience, qualifications, certifications'
        return form
    
    def get_candidate_display(self, obj):
        """Display candidate name with file reference"""
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #1e40af; font-size: 13px;">👨‍✈️ {}</strong><br>'
            '<span style="color: #6b7280; font-size: 10px;">📄 {}</span>'
            '</div>',
            obj.name or 'Unnamed Candidate',
            obj.filename or 'No file'
        )
    get_candidate_display.short_description = 'Candidate'
    get_candidate_display.admin_order_field = 'name'
    
    def get_contact_display(self, obj):
        """Display contact information"""
        phone_display = ''
        if obj.phones and isinstance(obj.phones, list) and len(obj.phones) > 0:
            phone_display = f'<span style="color: #059669;">📞 {obj.phones[0]}</span>'
        else:
            phone_display = '<span style="color: #9ca3af;">📞 No phone</span>'
        
        return format_html(
            '<div style="font-size: 11px; line-height: 1.8;">'
            '{}'
            '{}'
            '</div>',
            f'<span style="color: #3b82f6;">📧 {obj.email}</span><br>' if obj.email else '<span style="color: #9ca3af;">📧 No email</span><br>',
            phone_display
        )
    get_contact_display.short_description = 'Contact'
    
    def get_score_badge(self, obj):
        """Display qualification score with color coding"""
        if obj.total_score:
            score = obj.total_score
            if score >= 80:
                color = '#10b981'  # Green - Excellent match
                label = '🌟 EXCELLENT'
            elif score >= 60:
                color = '#3b82f6'  # Blue - Good match
                label = '✓ GOOD'
            elif score >= 40:
                color = '#f59e0b'  # Amber - Fair match
                label = '~ FAIR'
            else:
                color = '#6b7280'  # Gray - Low match
                label = '⚠ LOW'
            
            return format_html(
                '<div style="text-align: center;">'
                '<div style="background: {}; color: white; padding: 5px 10px; border-radius: 8px; font-weight: 700; font-size: 11px; margin-bottom: 3px;">{}</div>'
                '<div style="color: #6b7280; font-size: 10px; font-weight: 600;">Score: {}</div>'
                '</div>',
                color, label, score
            )
        return format_html('<span style="color: #9ca3af; font-size: 11px;">Not Scored</span>')
    get_score_badge.short_description = 'Match Quality'
    get_score_badge.admin_order_field = 'total_score'
    
    def get_parsed_status(self, obj):
        """Display parsing status"""
        if obj.parsed_at:
            return format_html(
                '<span style="background: #10b981; color: white; padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: 600;">✓ PARSED</span><br>'
                '<span style="color: #6b7280; font-size: 9px;">{}</span>',
                obj.parsed_at.strftime('%b %d, %Y')
            )
        return format_html(
            '<span style="background: #f59e0b; color: white; padding: 4px 10px; border-radius: 8px; font-size: 10px; font-weight: 600;">⏳ PENDING</span>'
        )
    get_parsed_status.short_description = 'Processing'
    get_parsed_status.admin_order_field = 'parsed_at'
    
    def get_resume_summary(self, obj):
        """Display comprehensive resume summary"""
        from django.utils.safestring import mark_safe
        
        # Format JSON data safely
        skills_json = json.dumps(obj.skills, indent=2) if obj.skills else "No skills data"
        aviation_json = json.dumps(obj.aviation, indent=2) if obj.aviation else "No aviation data"
        experience_json = json.dumps(obj.experience, indent=2) if obj.experience else "No experience data"
        
        phone_display = obj.phones[0] if obj.phones and isinstance(obj.phones, list) and len(obj.phones) > 0 else 'Not provided'
        
        html = f"""
        <div style="border: 2px solid #10b981; padding: 15px; border-radius: 8px; background: #ecfdf5;">
            <h3 style="margin: 0 0 15px 0; color: #065f46;">👨‍✈️ Aviation Professional Profile</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold; width: 30%;">Full Name</td>
                    <td style="padding: 8px;"><strong>{obj.name or 'Not provided'}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Resume File</td>
                    <td style="padding: 8px;">{obj.filename or 'Unknown'}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Email</td>
                    <td style="padding: 8px;"><a href="mailto:{obj.email or ''}">{obj.email or 'Not provided'}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Phone</td>
                    <td style="padding: 8px;">{phone_display}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Match Score</td>
                    <td style="padding: 8px;">{self.get_score_badge(obj)}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Status</td>
                    <td style="padding: 8px;">{self.get_parsed_status(obj)}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Submitted</td>
                    <td style="padding: 8px;">{obj.created_at.strftime('%B %d, %Y at %I:%M %p') if obj.created_at else 'Unknown'}</td>
                </tr>
            </table>
            
            {'<div style="margin-top: 15px; padding: 12px; background: white; border-left: 3px solid #10b981; border-radius: 4px;"><strong style="color: #065f46;">🛩️ Skills & Qualifications:</strong><br><pre style="margin: 8px 0 0 0; color: #4b5563; font-size: 11px; overflow-x: auto;">' + skills_json + '</pre></div>' if obj.skills else ''}
            
            {'<div style="margin-top: 12px; padding: 12px; background: white; border-left: 3px solid #3b82f6; border-radius: 4px;"><strong style="color: #1e40af;">✈️ Aviation Details:</strong><br><pre style="margin: 8px 0 0 0; color: #4b5563; font-size: 11px; overflow-x: auto;">' + aviation_json + '</pre></div>' if obj.aviation else ''}
            
            {'<div style="margin-top: 12px; padding: 12px; background: white; border-left: 3px solid #8b5cf6; border-radius: 4px;"><strong style="color: #6b21a8;">💼 Work Experience:</strong><br><pre style="margin: 8px 0 0 0; color: #4b5563; font-size: 11px; overflow-x: auto;">' + experience_json + '</pre></div>' if obj.experience else ''}
        </div>
        """
        return mark_safe(html)
    get_resume_summary.short_description = 'Candidate Overview'
    
    # Actions
    def export_as_json(self, request, queryset):
        """Export selected resumes to JSON format"""
        data = []
        for r in queryset:
            try:
                data.append(r.to_dict())
            except Exception:
                data.append({'id': r.id, 'filename': r.filename, 'name': r.name})
        resp = HttpResponse(json.dumps(data, indent=2, default=str), content_type='application/json')
        resp['Content-Disposition'] = f'attachment; filename=aviation_candidates_{timezone.now().strftime("%Y%m%d")}.json'
        return resp
    export_as_json.short_description = "📥 Export as JSON"

    def export_as_csv(self, request, queryset):
        """Export selected resumes to CSV (name,email,phone,score,filename)"""
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=candidates_{timezone.now().strftime("%Y%m%d")}.csv'
        writer = csv.writer(response)
        writer.writerow(['Name', 'Email', 'Phone', 'Score', 'Filename', 'Parsed'])
        for r in queryset:
            phone = r.phones[0] if r.phones and isinstance(r.phones, list) and len(r.phones) > 0 else ''
            writer.writerow([
                r.name or '',
                r.email or '',
                phone,
                r.total_score or '',
                r.filename or '',
                'yes' if r.parsed_at else 'no'
            ])
        return response
    export_as_csv.short_description = '🧾 Export as CSV'

    def mark_as_reviewed(self, request, queryset):
        """Mark resumes as reviewed/parsed"""
        now = timezone.now()
        updated = queryset.update(parsed_at=now)
        self.message_user(request, f"✓ Marked {updated} candidate(s) as reviewed")
    mark_as_reviewed.short_description = "✓ Mark as reviewed"
    
    def export_selected_candidates(self, request, queryset):
        """Export candidate contact list"""
        from django.core.serializers import serialize
        data = []
        for resume in queryset:
            phone = resume.phones[0] if resume.phones and isinstance(resume.phones, list) and len(resume.phones) > 0 else 'N/A'
            data.append({
                'name': resume.name or 'Unknown',
                'email': resume.email or 'N/A',
                'phone': phone,
                'filename': resume.filename,
                'score': resume.total_score or 0
            })
        resp = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
        resp['Content-Disposition'] = f'attachment; filename=candidate_contacts_{timezone.now().strftime("%Y%m%d")}.json'
        return resp
    export_selected_candidates.short_description = "📋 Export contact list"
