"""
Django Admin Configuration
"""
from django.contrib import admin

# Configure default Django admin site
admin.site.site_header = 'AeroOps Intel Admin'
admin.site.site_title = 'AeroOps Admin Portal'
admin.site.index_title = 'Aviation Jobs Management'

# For backward compatibility with existing imports
admin_site = admin.site
