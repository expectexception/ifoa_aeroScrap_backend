#!/usr/bin/env python3
"""
Test script to verify scraper manager endpoints are accessible
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from django.test import RequestFactory
from scraper_manager.api import list_scrapers
import json

def test_scraper_endpoints():
    """Test that scraper manager endpoints are working"""
    print("=" * 70)
    print("SCRAPER MANAGER ENDPOINTS TEST")
    print("=" * 70)
    print()
    
    # Create a test request
    factory = RequestFactory()
    request = factory.get('/api/scraper-manager/list/')
    
    # Test list_scrapers endpoint
    print("Testing: GET /api/scraper-manager/list/")
    print("-" * 70)
    
    try:
        response = list_scrapers(request)
        
        if response.status_code == 200:
            data = response.data
            print(f"✓ Status: {response.status_code} OK")
            print(f"✓ Scrapers count: {data.get('count', 0)}")
            print()
            print("Available scrapers:")
            for scraper in data.get('scrapers', []):
                print(f"  - {scraper['id']}: {scraper['name']}")
                print(f"    Available: {scraper['available']}")
                print(f"    Enabled: {scraper['enabled']}")
                print()
            
            print("=" * 70)
            print("✓ SCRAPER MANAGER API IS WORKING!")
            print()
            print("Available endpoints:")
            print("  GET  /api/scraper-manager/list/       - List all scrapers")
            print("  POST /api/scraper-manager/start/      - Start a scraper")
            print("  GET  /api/scraper-manager/status/<id>/ - Get job status")
            print("  GET  /api/scraper-manager/history/    - Get scraper history")
            print("  GET  /api/scraper-manager/stats/      - Get scraper statistics")
            print("=" * 70)
            return 0
        else:
            print(f"✗ Status: {response.status_code}")
            print(f"✗ Response: {response.data}")
            return 1
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(test_scraper_endpoints())
