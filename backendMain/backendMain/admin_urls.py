"""
Custom admin URLs for Unfold compatibility
"""
from django.urls import path
from django.shortcuts import render

def search_view(request):
    """Simple search view for Unfold"""
    return render(request, 'admin/search.html', {'query': request.GET.get('q', '')})

# These URLs will be included in the admin namespace
urlpatterns = [
    path('search/', search_view, name='search'),
]
