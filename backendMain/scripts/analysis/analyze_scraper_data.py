import os
import django
from django.db.models import Count, Q
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from jobs.models import Job

def analyze_data():
    print("============================================")
    print("📊 Scraper Data Analysis Report")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("============================================")

    total_jobs = Job.objects.count()
    print(f"\nTotal Jobs in Database: {total_jobs}")

    # 1. Missing Descriptions
    missing_desc = Job.objects.filter(Q(description__isnull=True) | Q(description__exact='')).count()
    short_desc = Job.objects.filter(description__regex=r'^.{0,100}$').exclude(description__exact='').count() # < 100 chars
    
    print(f"\n1. Description Quality:")
    print(f"   - Missing/Empty: {missing_desc} ({(missing_desc/total_jobs*100):.1f}%)")
    print(f"   - Very Short (<100 chars): {short_desc} ({(short_desc/total_jobs*100):.1f}%)")
    
    # 2. Missing Locations
    missing_loc = Job.objects.filter(Q(location__isnull=True) | Q(location__exact='') | Q(location__iexact='Unknown')).count()
    print(f"\n2. Location Quality:")
    print(f"   - Missing/Unknown: {missing_loc} ({(missing_loc/total_jobs*100):.1f}%)")

    # 3. Missing Dates
    # posted_date is likely a DateField, so we check for null.
    # If it allows null=True, blank=True, empty string might be invalid or converted to null.
    missing_date = Job.objects.filter(posted_date__isnull=True).count()
    print(f"\n3. Date Quality:")
    print(f"   - Missing Posted Date: {missing_date} ({(missing_date/total_jobs*100):.1f}%)")

    # 4. Source Breakdown & specific issues
    print(f"\n4. Breakdown by Source:")
    sources = Job.objects.values('source').annotate(
        total=Count('id'),
        missing_desc=Count('id', filter=Q(description__exact='')),
        missing_loc=Count('id', filter=Q(location__exact='')),
    ).order_by('-total')

    print(f"   {'Source':<20} | {'Total':<6} | {'No Desc':<8} | {'No Loc':<8} | {'Quality'}")
    print(f"   {'-'*20}-+-{'-'*6}-+-{'-'*8}-+-{'-'*8}-+-{'-'*7}")
    
    for s in sources:
        quality = 100 * (1 - (s['missing_desc'] + s['missing_loc']) / (2 * s['total'])) if s['total'] > 0 else 0
        print(f"   {s['source']:<20} | {s['total']:<6} | {s['missing_desc']:<8} | {s['missing_loc']:<8} | {quality:.1f}%")

    # 5. Potential Duplicates (Same title + company)
    print(f"\n5. Potential Duplicates (Title + Company):")
    duplicates = Job.objects.values('title', 'company').annotate(count=Count('id')).filter(count__gt=1).order_by('-count')[:5]
    if duplicates:
        for d in duplicates:
            print(f"   - {d['count']}x: {d['title']} at {d['company']}")
    else:
        print("   - None found (top 5 check)")

if __name__ == "__main__":
    analyze_data()
