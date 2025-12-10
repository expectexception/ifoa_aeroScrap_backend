#!/usr/bin/env python3
"""
Job Category Viewer
Display scraped jobs organized by categories with detailed filtering information
"""

import json
from collections import defaultdict
from typing import List, Dict


def load_jobs(filename: str = 'job_output.json') -> List[Dict]:
    """Load jobs from JSON file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        return jobs
    except Exception as e:
        print(f"❌ Error loading jobs: {e}")
        return []


def print_job_details(job: Dict, show_description: bool = False):
    """Print detailed job information"""
    print(f"\n  📌 {job.get('title', 'N/A')}")
    print(f"     Company: {job.get('company', 'N/A')}")
    print(f"     Location: {job.get('location', 'N/A')}")
    print(f"     Source: {job.get('source', 'N/A')}")
    
    if job.get('filter_match'):
        score = job.get('filter_score', 0.0)
        print(f"     🎯 Score: {score:.2f}")
        
        if job.get('matched_keywords'):
            keywords = job['matched_keywords'][:5]
            print(f"     🔑 Keywords: {', '.join(keywords)}")
        
        if job.get('matched_categories'):
            cats = job['matched_categories'][:3]
            print(f"     📁 Categories: {', '.join(cats)}")
    
    if show_description and job.get('description'):
        desc = job['description'][:200]
        print(f"     📄 {desc}...")


def view_by_category(jobs: List[Dict]):
    """Display jobs organized by primary category"""
    # Filter matched jobs only
    matched_jobs = [j for j in jobs if j.get('filter_match')]
    
    if not matched_jobs:
        print("❌ No matched jobs found")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 JOBS BY CATEGORY ({len(matched_jobs)} matched jobs)")
    print(f"{'='*80}\n")
    
    # Group by primary category
    by_category = defaultdict(list)
    for job in matched_jobs:
        primary = job.get('primary_category', 'Uncategorized')
        by_category[primary].append(job)
    
    # Sort categories by job count
    sorted_categories = sorted(by_category.items(), key=lambda x: len(x[1]), reverse=True)
    
    for category, cat_jobs in sorted_categories:
        # Sort jobs by score within category
        cat_jobs.sort(key=lambda x: x.get('filter_score', 0.0), reverse=True)
        
        print(f"\n{'─'*80}")
        print(f"🏷️  {category} - {len(cat_jobs)} jobs")
        print(f"{'─'*80}")
        
        for job in cat_jobs:
            print_job_details(job)
    
    print(f"\n{'='*80}\n")


def view_statistics(jobs: List[Dict]):
    """Display filtering statistics"""
    matched_jobs = [j for j in jobs if j.get('filter_match')]
    unmatched_jobs = [j for j in jobs if not j.get('filter_match')]
    
    print(f"\n{'='*80}")
    print(f"📈 FILTERING STATISTICS")
    print(f"{'='*80}\n")
    
    print(f"Total jobs: {len(jobs)}")
    print(f"✅ Matched: {len(matched_jobs)} ({len(matched_jobs)/len(jobs)*100:.1f}%)")
    print(f"❌ Not matched: {len(unmatched_jobs)}")
    
    if matched_jobs:
        # Score distribution
        high_score = [j for j in matched_jobs if j.get('filter_score', 0) >= 5.0]
        med_score = [j for j in matched_jobs if 3.0 <= j.get('filter_score', 0) < 5.0]
        low_score = [j for j in matched_jobs if 1.5 <= j.get('filter_score', 0) < 3.0]
        
        print(f"\n🎯 Score Distribution:")
        print(f"  • High confidence (≥5.0):   {len(high_score)} jobs")
        print(f"  • Medium confidence (≥3.0):  {len(med_score)} jobs")
        print(f"  • Low confidence (≥1.5):    {len(low_score)} jobs")
        
        # Category distribution
        category_counts = defaultdict(int)
        for job in matched_jobs:
            for cat in job.get('matched_categories', []):
                category_counts[cat] += 1
        
        print(f"\n📁 Matches by Category:")
        for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {cat}: {count} jobs")
        
        # Source distribution
        source_counts = defaultdict(int)
        for job in matched_jobs:
            source_counts[job.get('source', 'unknown')] += 1
        
        print(f"\n🌐 Matches by Source:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  • {source}: {count} jobs")
        
        # Top scoring jobs
        top_jobs = sorted(matched_jobs, key=lambda x: x.get('filter_score', 0), reverse=True)[:5]
        
        print(f"\n⭐ Top 5 Scoring Jobs:")
        for i, job in enumerate(top_jobs, 1):
            score = job.get('filter_score', 0.0)
            title = job.get('title', 'N/A')
            if len(title) > 50:
                title = title[:47] + '...'
            print(f"  {i}. [{score:.1f}] {title}")
    
    print(f"\n{'='*80}\n")


def view_by_source(jobs: List[Dict]):
    """Display matched jobs organized by source"""
    matched_jobs = [j for j in jobs if j.get('filter_match')]
    
    if not matched_jobs:
        print("❌ No matched jobs found")
        return
    
    print(f"\n{'='*80}")
    print(f"🌐 MATCHED JOBS BY SOURCE")
    print(f"{'='*80}\n")
    
    # Group by source
    by_source = defaultdict(list)
    for job in matched_jobs:
        source = job.get('source', 'unknown')
        by_source[source].append(job)
    
    for source, source_jobs in sorted(by_source.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n{'─'*80}")
        print(f"📍 {source.upper()} - {len(source_jobs)} matched jobs")
        print(f"{'─'*80}")
        
        # Sort by score
        source_jobs.sort(key=lambda x: x.get('filter_score', 0.0), reverse=True)
        
        for job in source_jobs:
            print_job_details(job)
    
    print(f"\n{'='*80}\n")


def search_jobs(jobs: List[Dict], keyword: str):
    """Search jobs by keyword in title or categories"""
    keyword_lower = keyword.lower()
    matched_jobs = []
    
    for job in jobs:
        if not job.get('filter_match'):
            continue
        
        # Search in title
        if keyword_lower in job.get('title', '').lower():
            matched_jobs.append(job)
            continue
        
        # Search in categories
        for cat in job.get('matched_categories', []):
            if keyword_lower in cat.lower():
                matched_jobs.append(job)
                break
        
        # Search in keywords
        for kw in job.get('matched_keywords', []):
            if keyword_lower in kw.lower():
                matched_jobs.append(job)
                break
    
    if not matched_jobs:
        print(f"❌ No jobs found matching '{keyword}'")
        return
    
    print(f"\n{'='*80}")
    print(f"🔍 SEARCH RESULTS for '{keyword}' ({len(matched_jobs)} jobs)")
    print(f"{'='*80}")
    
    matched_jobs.sort(key=lambda x: x.get('filter_score', 0.0), reverse=True)
    
    for job in matched_jobs:
        print_job_details(job)
    
    print(f"\n{'='*80}\n")


def main():
    """Main function"""
    import sys
    
    jobs = load_jobs()
    
    if not jobs:
        print("❌ No jobs loaded")
        return
    
    print(f"\n✓ Loaded {len(jobs)} jobs")
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'stats':
            view_statistics(jobs)
        elif command == 'category':
            view_by_category(jobs)
        elif command == 'source':
            view_by_source(jobs)
        elif command == 'search' and len(sys.argv) > 2:
            keyword = ' '.join(sys.argv[2:])
            search_jobs(jobs, keyword)
        else:
            print("\nUsage:")
            print("  python view_categories.py                  # Show all views")
            print("  python view_categories.py stats            # Show statistics only")
            print("  python view_categories.py category         # Show by category only")
            print("  python view_categories.py source           # Show by source only")
            print("  python view_categories.py search <keyword> # Search jobs")
    else:
        # Show all views
        view_statistics(jobs)
        view_by_category(jobs)


if __name__ == '__main__':
    main()
