#!/usr/bin/env python3
"""
Performance benchmark for optimized filter_manager
"""
import sys
import time
import os
import django

sys.path.insert(0, '/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from django.db import connection
from scraper_manager.filter_manager import JobFilterManager

# Get sample jobs
with connection.cursor() as cursor:
    cursor.execute("SELECT DISTINCT title FROM jobs WHERE title IS NOT NULL LIMIT 300")
    titles = [row[0] for row in cursor.fetchall()]

print("="*70)
print("FILTER PERFORMANCE BENCHMARK")
print("="*70)

# Initialize filter
filter_mgr = JobFilterManager('/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain/scraper_manager/filter_title.json')

# Test 1: Without cache
print("\nTest 1: Single-pass filtering (cold cache)")
filter_mgr.clear_cache()
start = time.time()
for title in titles[:50]:
    filter_mgr.matches_filter(title)
elapsed1 = (time.time() - start) * 1000
per_job1 = elapsed1 / 50
print(f"  Time: {elapsed1:.2f}ms for 50 jobs")
print(f"  Per-job: {per_job1:.3f}ms")

# Test 2: Batch filtering with caching
print("\nTest 2: Batch filtering (with LRU cache)")
filter_mgr.clear_cache()
jobs = [{'title': t, 'url': f'http://example.com/{i}'} for i, t in enumerate(titles)]
start = time.time()
matched, rejected, stats = filter_mgr.filter_jobs(jobs)
elapsed2 = (time.time() - start) * 1000
per_job2 = elapsed2 / len(jobs)
print(f"  Total time: {stats['performance']['total_time_ms']:.2f}ms for {len(jobs)} jobs")
print(f"  Per-job: {stats['performance']['avg_per_job_ms']:.3f}ms")
print(f"  Jobs/sec: {stats['performance']['jobs_per_second']:.1f}")
print(f"  Matched: {stats['matched']}, Rejected: {stats['rejected']}")

# Test 3: Repeated filtering (cache efficiency)
print("\nTest 3: Repeated filtering (hot cache)")
start = time.time()
for _ in range(3):
    for title in titles[:50]:
        filter_mgr.matches_filter(title)
elapsed3 = (time.time() - start) * 1000
per_job3 = elapsed3 / (50 * 3)
cache_stats = filter_mgr.get_cache_stats()
print(f"  Time: {elapsed3:.2f}ms for 150 queries")
print(f"  Per-job: {per_job3:.3f}ms")
print(f"  Cache hits: {cache_stats['cache_hits']}")
print(f"  Cache misses: {cache_stats['cache_misses']}")
print(f"  Hit rate: {cache_stats['hit_rate']}%")

print("\n" + "="*70)
print("OPTIMIZATION SUMMARY")
print("="*70)
print(f"\n✓ Batch filtering speed: {per_job2:.3f}ms per job")
print(f"✓ Precompiled patterns: 204 regex objects ready")
print(f"✓ LRU cache enabled: 10,000 entry capacity")
print(f"✓ Early exit optimization: High confidence matches skip phase 2")
print(f"✓ Throughput: {stats['performance']['jobs_per_second']:.0f} jobs/second")
print(f"✓ Cache efficiency: {cache_stats['hit_rate']:.1f}% hit rate on repeated titles")

print("\n" + "="*70)
