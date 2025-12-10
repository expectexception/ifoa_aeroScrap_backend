#!/usr/bin/env python3
"""
Test script to validate filter effectiveness and identify gaps
"""
import sys
import os
import django

# Add the backend path
sys.path.insert(0, '/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from django.db import connection
from scraper_manager.filter_manager import JobFilterManager

# Get all jobs from database
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT DISTINCT title FROM jobs 
        WHERE title IS NOT NULL AND title != ''
        ORDER BY title
        LIMIT 500
    """)
    db_titles = [row[0] for row in cursor.fetchall()]

# Initialize filter manager
filter_mgr = JobFilterManager('/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/scraper_manager/filter_title.json')

print("="*80)
print("FILTER TEST REPORT - Testing Against Database Jobs")
print("="*80)

matched = []
not_matched = []

for title in db_titles:
    matches, categories, score, details = filter_mgr.matches_filter(title)
    if matches:
        matched.append({
            'title': title,
            'score': score,
            'categories': [c['display_name'] for c in categories]
        })
    else:
        not_matched.append(title)

print(f"\n✅ MATCHED: {len(matched)} jobs")
for job in matched[:20]:
    print(f"  • {job['title']}")
    print(f"    Score: {job['score']}, Categories: {', '.join(job['categories'])}")
    print()

print(f"\n❌ NOT MATCHED: {len(not_matched)} jobs")
print("Sample of unmatched titles:")
for title in not_matched[:30]:
    print(f"  • {title}")

# Test specific titles from user requirements
print("\n" + "="*80)
print("TESTING SPECIFIC TITLES FROM USER REQUIREMENTS")
print("="*80)

user_titles = [
    "Flight Operations Officer (FOO)",
    "Aircraft Dispatcher",
    "Flight Dispatcher",
    "Flight Operations Controller",
    "Operations Controller",
    "Operations Control Centre Officer (OCC Officer)",
    "Network Operations Controller",
    "Network Operations Officer",
    "Scheduler / Flight Scheduler",
    "Load Controller / Load Control Officer",
    "Crew Controller / Crew Control Officer",
    "Integrated Operations Controller",
    "Disruption Manager",
    "Senior Flight Operations Officer",
    "Senior Aircraft Dispatcher",
    "Supervisor Dispatch",
    "Crew Control Supervisor",
    "Manager – Operations Control Centre (OCC Manager)",
    "Manager – Flight Operations Control",
    "Head of Operations Control",
    "Director – Operations Control",
    "Movement Controller",
    "Flight Watch Officer",
    "Dispatch Officer",
    "Flight Operations Specialist",
    "Operations Planning Controller",
    "OCC Coordinator",
    "NOC Coordinator",
    "IOC (Integrated Operations Centre) Controller",
    "SOC (System Operations Centre) Controller",
]

print(f"\nTesting {len(user_titles)} specific titles from requirements:\n")

for title in user_titles:
    matches, categories, score, details = filter_mgr.matches_filter(title)
    status = "✅ MATCH" if matches else "❌ MISS"
    print(f"{status}: {title}")
    if matches:
        print(f"       Score: {score:.1f}, Keywords: {', '.join(details.get('matched_keywords', [])[:3])}")
    print()

print("="*80)
