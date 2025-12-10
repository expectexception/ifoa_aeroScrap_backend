"""
Advanced Job Filter Manager
Uses sophisticated filtering techniques including:
- Phrase matching with context awareness
- Weighted scoring by category
- Exclusion patterns for false positives
- Multi-level category labeling
"""

import json
import re
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path


class JobFilterManager:
    """Advanced job filtering with weighted scoring and context analysis"""
    
    def __init__(self, filter_file: str = 'filter_title.json'):
        """Initialize filter manager with filter configuration"""
        self.filter_file = Path(filter_file)
        self.filters = []
        self.all_keywords = set()
        self.keyword_to_category = {}
        self.phrase_keywords = []  # Multi-word phrases
        self.single_keywords = []  # Single words
        
        # Exclusion patterns to filter out false positives
        self.exclusion_patterns = [
            r'\b(cabin crew|flight attendant|steward|stewardess)\b',
            r'\b(pilot recruitment|pilot jobs|careers|hiring)\b',
            r'\b(maintenance engineer|aircraft engineer|technician)\b',
            r'\b(software|developer|programmer|IT)\b',
            r'\b(sales|marketing|finance|HR|human resources)\b'
        ]
        
        # Category weights for scoring (higher = more important)
        self.category_weights = {
            'Core_Function_Terms_Only': 3.0,  # Highest priority
            'Operative_Functional_Control_Keywords': 2.5,
            'Supervisory_Level_Control_Keywords': 2.0,
            'Management_Executive_Control_Keywords': 1.5
        }
        
        self.load_filters()
    
    def load_filters(self):
        """Load filter configuration from JSON file with advanced processing"""
        if not self.filter_file.exists():
            print(f"⚠️  Filter file not found: {self.filter_file}")
            return
        
        try:
            with open(self.filter_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.filters = data.get('Filters', [])
            
            # Build keyword sets and mappings with phrase/single word separation
            for filter_group in self.filters:
                filter_type = filter_group.get('FilterType', '')
                display_name = filter_group.get('DisplayName', '')
                keywords = filter_group.get('Keywords', [])
                weight = self.category_weights.get(filter_type, 1.0)
                
                for keyword in keywords:
                    # Store lowercase for case-insensitive matching
                    keyword_lower = keyword.lower()
                    self.all_keywords.add(keyword_lower)
                    
                    # Separate phrases from single words
                    if ' ' in keyword_lower:
                        self.phrase_keywords.append(keyword_lower)
                    else:
                        self.single_keywords.append(keyword_lower)
                    
                    # Map keyword to its category with weight
                    if keyword_lower not in self.keyword_to_category:
                        self.keyword_to_category[keyword_lower] = []
                    self.keyword_to_category[keyword_lower].append({
                        'filter_type': filter_type,
                        'display_name': display_name,
                        'original_keyword': keyword,
                        'weight': weight
                    })
            
            print(f"✓ Loaded {len(self.filters)} filter categories")
            print(f"✓ Total keywords: {len(self.all_keywords)} ({len(self.phrase_keywords)} phrases, {len(self.single_keywords)} single words)")
            print(f"✓ Exclusion patterns: {len(self.exclusion_patterns)}")
            
        except Exception as e:
            print(f"❌ Error loading filters: {e}")
    
    def check_exclusions(self, job_title: str) -> bool:
        """
        Check if title matches exclusion patterns (false positives)
        
        Returns:
            True if title should be excluded
        """
        title_lower = job_title.lower()
        for pattern in self.exclusion_patterns:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True
        return False
    
    def matches_filter(self, job_title: str) -> Tuple[bool, List[Dict], float, Dict]:
        """
        Advanced filter matching with scoring and category labeling
        
        Returns:
            (matches: bool, matched_categories: List[Dict], score: float, match_details: Dict)
        """
        if not job_title:
            return False, [], 0.0, {}
        
        title_lower = job_title.lower()
        
        # Check exclusion patterns first
        if self.check_exclusions(title_lower):
            return False, [], 0.0, {'reason': 'excluded_pattern'}
        
        matched_categories = []
        matched_keywords = []
        total_score = 0.0
        category_scores = {}
        
        # Phase 1: Match multi-word phrases first (higher accuracy)
        for phrase in self.phrase_keywords:
            # Exact phrase matching
            pattern = r'\b' + re.escape(phrase) + r'\b'
            
            if re.search(pattern, title_lower):
                matched_keywords.append(phrase)
                
                # Add category information with weight
                categories = self.keyword_to_category.get(phrase, [])
                for cat in categories:
                    weight = cat['weight']
                    total_score += weight * 2.0  # Phrases get 2x weight
                    
                    # Track category scores
                    cat_name = cat['display_name']
                    if cat_name not in category_scores:
                        category_scores[cat_name] = 0.0
                    category_scores[cat_name] += weight * 2.0
                    
                    if cat not in matched_categories:
                        matched_categories.append(cat)
        
        # Phase 2: Match single words (lower priority)
        for keyword in self.single_keywords:
            # Word boundary matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            
            if re.search(pattern, title_lower):
                matched_keywords.append(keyword)
                
                # Add category information with weight
                categories = self.keyword_to_category.get(keyword, [])
                for cat in categories:
                    weight = cat['weight']
                    total_score += weight
                    
                    # Track category scores
                    cat_name = cat['display_name']
                    if cat_name not in category_scores:
                        category_scores[cat_name] = 0.0
                    category_scores[cat_name] += weight
                    
                    if cat not in matched_categories:
                        matched_categories.append(cat)
        
        match_details = {
            'matched_keywords': matched_keywords,
            'category_scores': category_scores,
            'keyword_count': len(matched_keywords)
        }
        
        # Consider it a match if score is significant enough
        is_match = total_score >= 1.5  # Minimum threshold
        
        return is_match, matched_categories, total_score, match_details
    
    def filter_jobs(self, jobs: List[Dict]) -> Tuple[List[Dict], List[Dict], Dict]:
        """
        Advanced filtering with scoring and detailed categorization
        
        Returns:
            (matched_jobs, rejected_jobs, statistics)
        """
        matched_jobs = []
        rejected_jobs = []
        
        stats = {
            'total': len(jobs),
            'matched': 0,
            'rejected': 0,
            'excluded': 0,
            'by_category': {},
            'score_distribution': {
                'high': 0,    # score >= 5.0
                'medium': 0,  # 3.0 <= score < 5.0
                'low': 0      # 1.5 <= score < 3.0
            }
        }
        
        for job in jobs:
            title = job.get('title', '')
            matches, categories, score, details = self.matches_filter(title)
            
            if matches:
                # Add comprehensive filter metadata to job
                job['filter_match'] = True
                job['filter_score'] = round(score, 2)
                job['matched_categories'] = [cat['display_name'] for cat in categories]
                job['matched_filter_types'] = [cat['filter_type'] for cat in categories]
                job['matched_keywords'] = details.get('matched_keywords', [])
                job['category_scores'] = details.get('category_scores', {})
                
                # Add primary category label (highest scoring)
                if details.get('category_scores'):
                    primary_category = max(details['category_scores'].items(), key=lambda x: x[1])[0]
                    job['primary_category'] = primary_category
                else:
                    job['primary_category'] = job['matched_categories'][0] if job['matched_categories'] else 'Unknown'
                
                matched_jobs.append(job)
                stats['matched'] += 1
                
                # Score distribution
                if score >= 5.0:
                    stats['score_distribution']['high'] += 1
                elif score >= 3.0:
                    stats['score_distribution']['medium'] += 1
                else:
                    stats['score_distribution']['low'] += 1
                
                # Count by category
                for cat in categories:
                    cat_name = cat['display_name']
                    if cat_name not in stats['by_category']:
                        stats['by_category'][cat_name] = 0
                    stats['by_category'][cat_name] += 1
            else:
                job['filter_match'] = False
                job['filter_score'] = 0.0
                job['matched_categories'] = []
                job['primary_category'] = None
                
                # Track exclusion reason
                if details.get('reason') == 'excluded_pattern':
                    stats['excluded'] += 1
                    job['rejection_reason'] = 'excluded_pattern'
                
                rejected_jobs.append(job)
                stats['rejected'] += 1
        
        return matched_jobs, rejected_jobs, stats
    
    def print_filter_stats(self, stats: Dict):
        """Print comprehensive filtering statistics"""
        print(f"\n{'='*70}")
        print("📊 ADVANCED FILTERING RESULTS")
        print(f"{'='*70}")
        print(f"\nTotal jobs analyzed: {stats['total']}")
        print(f"✅ Matched (will scrape): {stats['matched']}")
        print(f"❌ Rejected (skipped): {stats['rejected']}")
        
        if stats.get('excluded', 0) > 0:
            print(f"🚫 Excluded by pattern: {stats['excluded']}")
        
        if stats['matched'] > 0:
            match_rate = (stats['matched'] / stats['total']) * 100
            print(f"\n📈 Match rate: {match_rate:.1f}%")
            
            # Score distribution
            score_dist = stats.get('score_distribution', {})
            if any(score_dist.values()):
                print(f"\n🎯 Score Distribution:")
                print(f"  • High confidence (≥5.0):    {score_dist.get('high', 0)} jobs")
                print(f"  • Medium confidence (≥3.0):  {score_dist.get('medium', 0)} jobs")
                print(f"  • Low confidence (≥1.5):     {score_dist.get('low', 0)} jobs")
        
        if stats.get('by_category'):
            print(f"\n📁 Matches by Category:")
            for category, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {category}: {count} jobs")
        
        print(f"{'='*70}\n")
    
    def get_filter_summary(self) -> Dict:
        """Get summary of loaded filters"""
        summary = {
            'total_categories': len(self.filters),
            'total_keywords': len(self.all_keywords),
            'categories': []
        }
        
        for filter_group in self.filters:
            summary['categories'].append({
                'type': filter_group.get('FilterType', ''),
                'name': filter_group.get('DisplayName', ''),
                'description': filter_group.get('Description', ''),
                'keyword_count': len(filter_group.get('Keywords', []))
            })
        
        return summary
    
    def print_filter_info(self):
        """Print information about loaded filters"""
        print(f"\n{'='*70}")
        print("🔍 FILTER CONFIGURATION")
        print(f"{'='*70}")
        
        summary = self.get_filter_summary()
        print(f"\nTotal Categories: {summary['total_categories']}")
        print(f"Total Keywords: {summary['total_keywords']}")
        
        print("\nCategories:")
        for cat in summary['categories']:
            print(f"\n  📁 {cat['name']}")
            print(f"     Type: {cat['type']}")
            print(f"     Keywords: {cat['keyword_count']}")
            print(f"     {cat['description']}")
        
        print(f"\n{'='*70}\n")


if __name__ == '__main__':
    # Test the advanced filter manager
    filter_mgr = JobFilterManager('filter_title.json')
    filter_mgr.print_filter_info()
    
    # Test with sample titles including edge cases
    test_titles = [
        "Flight Operations Officer - OCC",
        "Senior Dispatcher - Network Control",
        "Aircraft Maintenance Engineer",
        "Software Developer",
        "OCC Manager - Operations Control",
        "Load Controller - Hub Operations",
        "Cabin Crew",
        "Flight Dispatch Supervisor",
        "Director Network Operations",
        "IOCC Controller - Night Shift",
        "Flight Operations Center Manager",
        "Crew Control Supervisor",
        "First Officer Jobs | Pilot Careers",  # Should be excluded
        "Network Recovery Officer",
        "Head of Flight Dispatch"
    ]
    
    print("\n" + "="*70)
    print("TEST: Advanced Matching with Scoring")
    print("="*70)
    
    for title in test_titles:
        matches, categories, score, details = filter_mgr.matches_filter(title)
        if matches:
            cat_names = [cat['display_name'] for cat in categories]
            primary = max(details['category_scores'].items(), key=lambda x: x[1])[0] if details['category_scores'] else 'N/A'
            print(f"\n✅ MATCH: {title}")
            print(f"   Score: {score:.2f}")
            print(f"   Primary Category: {primary}")
            print(f"   All Categories: {', '.join(cat_names)}")
            print(f"   Keywords: {', '.join(details['matched_keywords'][:5])}")  # Show first 5
        else:
            reason = details.get('reason', 'no match')
            print(f"\n❌ NO MATCH: {title}")
            print(f"   Reason: {reason}")
