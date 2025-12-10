# 🚀 Auto-Mapping Quick Reference

## One-Sentence Summary
Scrapers automatically create CompanyMapping entries for new companies, flagged for admin review.

## Visual Flow
```
Scraper finds job → Check if company mapping exists → No? → Auto-create mapping
  with new company                                           ├─ auto_created = True
                                                             ├─ needs_review = True
                                                             ├─ operation_type (inherited)
                                                             └─ country_code (inherited)
```

## Admin Workflow (3 Steps)
```
1. Filter: "Needs review" = Yes
2. Review: Check name, check duplicates, edit if needed
3. Approve: Select → "✓ Mark as reviewed" → Go
```

## Status Indicators
- ⚠️ AUTO-CREATED - NEEDS REVIEW = Not reviewed yet
- ⚠️ NEEDS REVIEW = Manually created, needs verification
- ✓ REVIEWED by [user] = Approved and ready

## Key URLs
- Admin: http://localhost:8000/admin/jobs/companymapping/
- Filter for review: Add `?needs_review__exact=1` to URL
- Filter auto-created: Add `?auto_created__exact=1` to URL

## Database Fields
```python
auto_created    # Boolean - Was it auto-created?
needs_review    # Boolean - Needs approval?
reviewed_by     # String - Who approved?
reviewed_at     # DateTime - When approved?
```

## Code Trigger Point
```python
# In scraper_manager/services.py
def _save_jobs_to_db(cls, ...):
    new_job, created = Job.objects.update_or_create(...)
    if created:
        cls._auto_create_company_mapping(new_job)  # ← HERE
```

## Test Command
```bash
cd backendMain
python test_auto_mapping.py
```

## Migration
```bash
python manage.py migrate jobs  # Already applied: 0009
```

## Logs to Watch
```bash
tail -f logs/scraper.log | grep "Auto-created"
```

## Common Tasks

### View all auto-created mappings:
```python
CompanyMapping.objects.filter(auto_created=True)
```

### View mappings needing review:
```python
CompanyMapping.objects.filter(needs_review=True)
```

### Manually mark as reviewed:
```python
mapping = CompanyMapping.objects.get(id=X)
mapping.mark_as_reviewed(username='admin')
```

### Find similar companies:
```python
from difflib import SequenceMatcher
SequenceMatcher(None, "Air India".lower(), "AirIndia".lower()).ratio()
# Returns: 0.90 (90% similar)
```

## Admin Actions
- ✓ Mark as reviewed - Bulk approve mappings
- 🔄 Refresh statistics - Update job counts
- 📊 Export as CSV - Download mappings
- 🤖 Auto-detect operation type - Infer from jobs
- 🔗 Apply to jobs - Link jobs to this mapping

## Filters Available
- Needs review (Yes/No)
- Auto created (Yes/No)
- Operation type
- Country code
- Created date
- Reviewed date

## Search Fields
- Company name
- Normalized name
- Notes
- Reviewed by

## Performance
- Auto-creation: ~50ms per company
- Similarity check: ~100ms for 200 companies
- Bulk approval: ~10ms per mapping

## Tips
✅ Review daily after scraping runs
✅ Use bulk actions for obvious cases
✅ Check "Unmapped Jobs" section for duplicates
✅ Edit company names in jobs to match existing mappings
✅ Delete unnecessary auto-created mappings

## Documentation
- Full guide: `/documents/AUTO_MAPPING_FEATURE.md`
- Implementation summary: `/documents/AUTO_MAPPING_IMPLEMENTATION_SUMMARY.md`
- API reference: `/documents/API_REFERENCE.md`
