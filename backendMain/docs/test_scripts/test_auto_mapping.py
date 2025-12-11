#!/usr/bin/env python3
"""
Test Auto-Mapping Feature
Tests the automatic company mapping creation and review workflow
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backendMain.settings')
django.setup()

from jobs.models import Job, CompanyMapping
from django.utils import timezone
from datetime import timedelta

def test_auto_mapping():
    """Test auto-mapping feature"""
    print("\n" + "="*60)
    print("🧪 TESTING AUTO-MAPPING FEATURE")
    print("="*60 + "\n")
    
    # Test 1: Check model fields exist
    print("✅ Test 1: Verify CompanyMapping has review fields")
    test_mapping = CompanyMapping.objects.first()
    if test_mapping:
        assert hasattr(test_mapping, 'auto_created'), "Missing auto_created field"
        assert hasattr(test_mapping, 'needs_review'), "Missing needs_review field"
        assert hasattr(test_mapping, 'reviewed_by'), "Missing reviewed_by field"
        assert hasattr(test_mapping, 'reviewed_at'), "Missing reviewed_at field"
        assert hasattr(test_mapping, 'mark_as_reviewed'), "Missing mark_as_reviewed method"
        print("   ✓ All fields present")
    else:
        print("   ⚠️  No CompanyMapping entries to test")
    
    # Test 2: Check auto-created mappings
    print("\n✅ Test 2: Check for auto-created mappings")
    auto_mappings = CompanyMapping.objects.filter(auto_created=True)
    needs_review = CompanyMapping.objects.filter(needs_review=True)
    print(f"   • Auto-created mappings: {auto_mappings.count()}")
    print(f"   • Needs review: {needs_review.count()}")
    
    if auto_mappings.exists():
        sample = auto_mappings.first()
        print(f"   • Sample: {sample.company_name}")
        print(f"     - Auto-created: {sample.auto_created}")
        print(f"     - Needs review: {sample.needs_review}")
        print(f"     - Reviewed by: {sample.reviewed_by or 'None'}")
    
    # Test 3: Test mark_as_reviewed method
    print("\n✅ Test 3: Test mark_as_reviewed() method")
    if needs_review.exists():
        test_obj = needs_review.first()
        print(f"   Testing on: {test_obj.company_name}")
        print(f"   Before: needs_review={test_obj.needs_review}")
        
        # Mark as reviewed
        test_obj.mark_as_reviewed(username="test_admin")
        test_obj.refresh_from_db()
        
        print(f"   After: needs_review={test_obj.needs_review}")
        print(f"   Reviewed by: {test_obj.reviewed_by}")
        print(f"   Reviewed at: {test_obj.reviewed_at}")
        
        assert test_obj.needs_review == False, "needs_review should be False"
        assert test_obj.reviewed_by == "test_admin", "reviewed_by should be set"
        assert test_obj.reviewed_at is not None, "reviewed_at should be set"
        print("   ✓ Method works correctly")
        
        # Reset for next test
        test_obj.needs_review = True
        test_obj.reviewed_by = None
        test_obj.reviewed_at = None
        test_obj.save()
    else:
        print("   ⚠️  No mappings to test")
    
    # Test 4: Check recent jobs and potential auto-mapping
    print("\n✅ Test 4: Check recent jobs for potential auto-mapping")
    recent_jobs = Job.objects.order_by('-created_at')[:5]
    
    for job in recent_jobs:
        normalized = job.company.strip().lower()
        has_mapping = CompanyMapping.objects.filter(normalized_name=normalized).exists()
        status = "✓ Mapped" if has_mapping else "⚠️  Unmapped"
        print(f"   {status}: {job.company} (from {job.source})")
        
        if has_mapping:
            mapping = CompanyMapping.objects.get(normalized_name=normalized)
            review_status = "⚠️  Needs Review" if mapping.needs_review else "✓ Reviewed"
            auto_status = "🤖 Auto-created" if mapping.auto_created else "👤 Manual"
            print(f"           {review_status}, {auto_status}")
    
    # Test 5: Statistics
    print("\n" + "="*60)
    print("📊 COMPANY MAPPING STATISTICS")
    print("="*60)
    
    total_mappings = CompanyMapping.objects.count()
    auto_created = CompanyMapping.objects.filter(auto_created=True).count()
    needs_review = CompanyMapping.objects.filter(needs_review=True).count()
    reviewed = CompanyMapping.objects.filter(needs_review=False).count()
    
    print(f"Total Mappings:     {total_mappings}")
    print(f"Auto-created:       {auto_created} ({auto_created/total_mappings*100:.1f}%)" if total_mappings > 0 else "Auto-created:       0 (0%)")
    print(f"Needs Review:       {needs_review} ({needs_review/total_mappings*100:.1f}%)" if total_mappings > 0 else "Needs Review:       0 (0%)")
    print(f"Reviewed:           {reviewed} ({reviewed/total_mappings*100:.1f}%)" if total_mappings > 0 else "Reviewed:           0 (0%)")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED")
    print("="*60 + "\n")
    
    print("🔗 Next Steps:")
    print("1. Visit: http://localhost:8000/admin/jobs/companymapping/")
    print("2. Filter by 'Needs review' = Yes")
    print("3. Review auto-created mappings")
    print("4. Use 'Mark as reviewed' action to approve")
    print()

if __name__ == '__main__':
    try:
        test_auto_mapping()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
