# 🤖 Automatic Company Mapping Feature

## Overview

The Auto-Mapping feature automatically creates CompanyMapping entries when scrapers discover new company names. This eliminates manual mapping creation while maintaining quality through a review workflow.

## How It Works

### 1. **Automatic Discovery**
When a scraper finds a job with a new company name:
```python
# In scraper_manager/services.py
def _save_jobs_to_db(cls, scraper_name, jobs_data, ...):
    for job_data in jobs_data:
        new_job, created = Job.objects.update_or_create(...)
        if created:
            cls._auto_create_company_mapping(new_job)  # Auto-create mapping
```

### 2. **Auto-Creation Process**
```python
def _auto_create_company_mapping(cls, job):
    normalized = job.company.strip().lower()
    
    # Check if mapping already exists
    if CompanyMapping.objects.filter(normalized_name=normalized).exists():
        return
    
    # Create new mapping with review flags
    mapping = CompanyMapping.objects.create(
        company_name=job.company,
        normalized_name=normalized,
        operation_type=job.operation_type,  # Inherited from job
        country_code=job.country_code,      # Inherited from job
        auto_created=True,                  # Flag for tracking
        needs_review=True,                  # Requires approval
        notes=f'Auto-created from job: {job.title[:100]}'
    )
    mapping.update_statistics()
```

### 3. **Review Workflow**

#### Admin Interface Features:
- **⚠️ Review Status Badge**: Shows which mappings need review
- **🔍 Similar Companies Preview**: Identifies potential duplicates
- **✓ Bulk Approval Action**: Mark multiple mappings as reviewed

#### Review Process:
1. Navigate to **Admin → Company Mappings**
2. Filter by "Needs review" = Yes
3. Review auto-created mapping:
   - Check company name spelling
   - Verify operation_type is correct
   - Verify country_code is correct
   - Check for similar/duplicate companies
4. Edit if needed (correct typos, update classification)
5. Mark as reviewed:
   - Select mapping(s)
   - Choose "✓ Mark as reviewed" action
   - Click "Go"

### 4. **Visual Indicators**

#### List View:
```
⚠️ AUTO-CREATED - NEEDS REVIEW  → Not yet reviewed
✓ REVIEWED by admin            → Approved and verified
```

#### Detail View:
```
✅ Review Status
├── Needs Review: ✓ (Auto-created by scraper)
├── Auto Created: Yes
├── Reviewed By: admin
└── Reviewed At: 2025-11-24 11:00:00
```

## Database Schema

### New Fields in CompanyMapping:
```python
class CompanyMapping(models.Model):
    # Existing fields...
    
    # Review tracking fields
    auto_created = models.BooleanField(default=False, db_index=True)
    needs_review = models.BooleanField(default=True, db_index=True)
    reviewed_by = models.CharField(max_length=100, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    def mark_as_reviewed(self, username=None):
        """Mark mapping as reviewed and approved"""
        self.needs_review = False
        self.reviewed_by = username or 'admin'
        self.reviewed_at = timezone.now()
        self.save()
```

## Admin Methods

### 1. get_review_status(obj)
Displays review status badge in list view.

**Returns:**
- `⚠️ AUTO-CREATED - NEEDS REVIEW` - Auto-created, needs approval
- `⚠️ NEEDS REVIEW` - Manually created, needs review
- `✓ REVIEWED by [username]` - Approved and verified

### 2. get_unmapped_jobs_preview(obj)
Shows similar company names that might be duplicates.

**Features:**
- Uses difflib.SequenceMatcher for similarity detection
- 60% similarity threshold
- Shows top 10 matches with similarity percentages
- Displays job counts for each similar company

**Example Output:**
```
🔍 Found 3 potential matches:
┌──────────────────────────┬────────────┬─────────┐
│ IndiGo Airlines          │ 85% match  │ 15 jobs │
│ Indigo Airline           │ 80% match  │ 8 jobs  │
│ IndiGo Airways Limited   │ 75% match  │ 3 jobs  │
└──────────────────────────┴────────────┴─────────┘
```

### 3. mark_as_reviewed_action(request, queryset)
Bulk admin action to approve multiple mappings.

**Usage:**
1. Select one or more mappings
2. Choose "✓ Mark as reviewed" from Actions dropdown
3. Click "Go"

**Result:**
- Sets `needs_review = False`
- Records `reviewed_by = request.user.username`
- Sets `reviewed_at = current timestamp`

## Workflow Examples

### Example 1: New Airline Discovered
```
1. Scraper finds job from "Emirates Airline Group"
2. System auto-creates CompanyMapping:
   - company_name: "Emirates Airline Group"
   - operation_type: "scheduled" (from job)
   - country_code: "AE" (from job)
   - auto_created: True
   - needs_review: True

3. Admin reviews:
   - Notices it's similar to existing "Emirates"
   - Either: Updates job to use "Emirates"
   - Or: Approves new mapping as separate entity
   - Marks as reviewed
```

### Example 2: Typo in Company Name
```
1. Scraper finds "Air Inida" (typo)
2. System auto-creates mapping
3. Admin reviews:
   - Sees it's 90% similar to "Air India"
   - Directly edits company name in job: "Air Inida" → "Air India"
   - Deletes auto-created mapping (no longer needed)
   - Existing "Air India" mapping is used
```

### Example 3: Legitimate New Company
```
1. Scraper finds "Blue Dart Aviation" (new cargo airline)
2. System auto-creates mapping
3. Admin reviews:
   - No similar companies found
   - Operation type "cargo" is correct
   - Country code "IN" is correct
   - Marks as reviewed
4. Future jobs from "Blue Dart Aviation" use this mapping automatically
```

## Benefits

### ✅ Automation
- No manual mapping creation needed
- Reduces admin workload
- Faster scraping workflows

### ✅ Quality Control
- All auto-created mappings require review
- Similar company detection prevents duplicates
- Inherits operation_type and country_code from first job

### ✅ Traceability
- Track which mappings were auto-created
- Record who reviewed and when
- Audit trail for data quality

### ✅ Flexibility
- Easy to edit before approval
- Can delete if duplicate/incorrect
- Bulk approval for efficiency

## Filters & Search

### Admin List Filters:
- **Needs Review**: Yes/No
- **Auto Created**: Yes/No
- **Operation Type**: scheduled, cargo, charter, etc.
- **Country Code**: IN, AE, US, GB, etc.
- **Created At**: Date hierarchy
- **Reviewed At**: Filter by review date

### Search Fields:
- Company name
- Normalized name
- Notes
- Reviewed by username

## Best Practices

### For Admins:
1. **Regular Review**: Check "Needs review" filter daily after scraping
2. **Batch Processing**: Use bulk actions for similar/obvious cases
3. **Duplicate Check**: Always check "Similar Unmapped Companies" section
4. **Naming Consistency**: Update job company names to match existing mappings
5. **Notes**: Add notes about special cases or unusual companies

### For Developers:
1. **Inheritance**: Auto-created mappings inherit from first job - ensure job data is clean
2. **Logging**: Check logs for auto-creation events: `Auto-created company mapping: [name]`
3. **Statistics**: Auto-created mappings immediately update statistics
4. **Testing**: Test with various company name formats (typos, variations, etc.)

## Migration

Created in: `jobs/migrations/0009_add_company_mapping_review_fields.py`

**Added Fields:**
- `auto_created` (BooleanField, indexed)
- `needs_review` (BooleanField, indexed)
- `reviewed_by` (CharField, max_length=100)
- `reviewed_at` (DateTimeField)

## Related Documentation

- **API Reference**: `/documents/API_REFERENCE.md`
- **Admin Guide**: `/documents/ADMIN_GUIDE.md` (if exists)
- **Scraper Documentation**: `/backendMain/scrapers/README_UNIFIED_SCRAPER.md`

## Support

For issues or questions:
1. Check logs: `backendMain/logs/`
2. Django admin: http://localhost:8000/admin/
3. Database console: `python manage.py dbshell`

---

**Last Updated**: 2025-11-24  
**Feature Status**: ✅ Production Ready  
**Version**: 1.0
