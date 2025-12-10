from django import setup
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
setup()
from jobs.models import Job
from django.db.models import Count, Q

stats = Job.objects.values('source').annotate(
    no_desc=Count('id', filter=Q(description__isnull=True) | Q(description='') | Q(description__length__lt=100)),
    no_loc=Count('id', filter=Q(location__isnull=True) | Q(location='')),
    no_post=Count('id', filter=Q(posted_date__isnull=True))
)
print('Source | no_desc | no_loc | no_post')
print('-'*48)
for s in stats:
    print(f"{s['source']:15s} | {s['no_desc']:7d} | {s['no_loc']:6d} | {s['no_post']:7d}")
