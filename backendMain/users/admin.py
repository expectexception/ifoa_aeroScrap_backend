from django.contrib import admin
from django.utils.html import format_html
from .models import UserProfile
from backendMain.admin import admin_site
from django.http import HttpResponse
from django.utils import timezone


@admin.register(UserProfile, site=admin_site)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('get_user_display', 'get_role_badge', 'department', 'phone', 'created_at')
    list_filter = ('role', 'created_at', 'department')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'department', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'get_profile_summary')
    date_hierarchy = 'created_at'
    list_per_page = 50
    save_on_top = True
    list_select_related = ('user',)
    actions = ('export_profiles_csv',)
    ordering = ('-created_at',)
    
    fieldsets = (
        ('👤 User Account', {
            'fields': ('user', 'get_profile_summary'),
            'description': 'Link to user account and basic profile information'
        }),
        ('🎯 Role & Department', {
            'fields': ('role', 'department'),
            'description': 'User role within the aviation operations system'
        }),
        ('📞 Contact Information', {
            'fields': ('phone',),
            'description': 'Direct contact details for this staff member'
        }),
        ('📝 About', {
            'fields': ('bio',),
            'description': 'Professional background and expertise in aviation industry'
        }),
        ('⏱️ Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form with helpful text"""
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['user'].help_text = 'Select the user account to create/edit profile for'
        form.base_fields['role'].help_text = 'Assign role: HR Manager for recruiting staff, Analyst for data review, Recruiter for talent acquisition'
        form.base_fields['department'].help_text = 'Department or division (e.g., Flight Operations, HR, Technical Recruiting)'
        form.base_fields['phone'].help_text = 'Direct phone number with country code (e.g., +1-555-123-4567)'
        form.base_fields['bio'].help_text = 'Brief professional background, certifications, or areas of expertise in aviation recruitment'
        return form
    
    def get_user_display(self, obj):
        """Display user with full name and email"""
        user = obj.user
        full_name = user.get_full_name() or user.username
        return format_html(
            '<div style="line-height: 1.6;">'
            '<strong style="color: #1e40af;">{}</strong><br>'
            '<span style="color: #6b7280; font-size: 11px;">📧 {}</span>'
            '</div>',
            full_name,
            user.email or 'No email'
        )
    get_user_display.short_description = 'User'
    get_user_display.admin_order_field = 'user__username'
    
    def get_role_badge(self, obj):
        """Display role with professional badge"""
        role_styles = {
            'hr_manager': ('background: #7c3aed; color: white;', '👔 HR Manager'),
            'recruiter': ('background: #0284c7; color: white;', '🎯 Recruiter'),
            'analyst': ('background: #059669; color: white;', '📊 Analyst'),
            'admin': ('background: #dc2626; color: white;', '⚙️ Administrator'),
        }
        style, label = role_styles.get(obj.role, ('background: #6b7280; color: white;', f'👤 {obj.role.title()}'))
        return format_html(
            '<span style="{}; padding: 5px 12px; border-radius: 8px; font-size: 11px; font-weight: 600; letter-spacing: 0.3px;">{}</span>',
            style, label
        )
    get_role_badge.short_description = 'Role'
    get_role_badge.admin_order_field = 'role'
    
    def get_profile_summary(self, obj):
        """Display comprehensive profile summary"""
        user = obj.user
        full_name = user.get_full_name() or user.username
        
        html = f"""
        <div style="border: 2px solid #3b82f6; padding: 15px; border-radius: 8px; background: #eff6ff;">
            <h3 style="margin: 0 0 15px 0; color: #1e40af;">👤 Staff Profile Overview</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold; width: 35%;">Full Name</td>
                    <td style="padding: 8px;"><strong>{full_name}</strong></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Username</td>
                    <td style="padding: 8px;">{user.username}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Email</td>
                    <td style="padding: 8px;"><a href="mailto:{user.email}">{user.email or 'Not provided'}</a></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Role</td>
                    <td style="padding: 8px;">{self.get_role_badge(obj)}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Department</td>
                    <td style="padding: 8px;"><span style="color: #3b82f6; font-weight: 600;">{obj.department or 'Not assigned'}</span></td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Phone</td>
                    <td style="padding: 8px;">{obj.phone or 'Not provided'}</td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Status</td>
                    <td style="padding: 8px;">
                        {'<span style="background: #10b981; color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">✓ ACTIVE</span>' if user.is_active else '<span style="background: #ef4444; color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">✗ INACTIVE</span>'}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Staff Member</td>
                    <td style="padding: 8px;">
                        {'<span style="background: #3b82f6; color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">👨‍✈️ YES</span>' if user.is_staff else '<span style="background: #9ca3af; color: white; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-weight: 600;">NO</span>'}
                    </td>
                </tr>
                <tr style="background: white;">
                    <td style="padding: 8px; font-weight: bold;">Joined</td>
                    <td style="padding: 8px;">{user.date_joined.strftime('%B %d, %Y at %I:%M %p') if user.date_joined else 'Unknown'}</td>
                </tr>
                <tr>
                    <td style="padding: 8px; font-weight: bold;">Profile Created</td>
                    <td style="padding: 8px;">{obj.created_at.strftime('%B %d, %Y at %I:%M %p') if obj.created_at else 'Unknown'}</td>
                </tr>
            </table>
            
            {f'<div style="margin-top: 15px; padding: 12px; background: white; border-left: 3px solid #3b82f6; border-radius: 4px;"><strong style="color: #1e40af;">📝 Bio:</strong><br><p style="margin: 8px 0 0 0; color: #4b5563;">{obj.bio}</p></div>' if obj.bio else ''}
        </div>
        """
        return format_html(html)
    get_profile_summary.short_description = 'Profile Summary'

    def export_profiles_csv(self, request, queryset):
        """Export selected profiles to CSV (name,username,email,role,department,phone)"""
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename=user_profiles_{timezone.now().strftime("%Y%m%d")}.csv'
        writer = csv.writer(response)
        writer.writerow(['Full Name', 'Username', 'Email', 'Role', 'Department', 'Phone', 'Created'])
        for p in queryset.select_related('user'):
            u = p.user
            writer.writerow([
                u.get_full_name() or u.username,
                u.username,
                u.email or '',
                p.role,
                p.department or '',
                p.phone or '',
                p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else ''
            ])
        return response
    export_profiles_csv.short_description = '🧾 Export selected profiles (CSV)'
