# Next Steps - Running Fresh Scrape Cycle

## Quick Start

To test all the fixes and see the improvements in action:

### Step 1: Navigate to Backend Directory
```bash
cd "/home/rajat/Desktop/AeroOps Intel/aeroScrap_backend/backendMain"
```

### Step 2: Run Fresh Scrape
```bash
# Run all scrapers
python manage.py scrape_all

# Or run specific scrapers to test:
python manage.py scrape_indigo      # Test Indigo description extraction
python manage.py scrape_aap         # Test AAP error handling
```

### Step 3: Monitor Progress
The scraper will output progress like:
```
Scraping Indigo Airlines...
✓ Extracted 10 jobs from listing
Fetching detailed descriptions for 10 jobs...
  Processed 10/10 jobs
✓ Successfully extracted 9/10 descriptions  <-- SHOULD BE HIGH NOW (was 0)
```

### Step 4: Verify Results
```bash
# Check database for improvements
python manage.py shell

# Inside Django shell:
from scraper_manager.models import ScrapedURL

# Check Indigo descriptions
indigo_urls = ScrapedURL.objects.filter(source='indigo')
with_desc = indigo_urls.filter(description__length__gt=0).count()
print(f"Indigo: {with_desc}/{indigo_urls.count()} have descriptions")
# Expected: 8-10/10

# Check by source
from django.db.models import Count, Q
stats = ScrapedURL.objects.values('source').annotate(
    total=Count('id'),
    with_desc=Count('description', filter=Q(description__gt=''))
)
for stat in stats:
    pct = (stat['with_desc'] / stat['total'] * 100) if stat['total'] > 0 else 0
    print(f"{stat['source']}: {pct:.0f}% descriptions")
```

## Expected Improvements

### Immediate (After This Scrape)
- ✅ **Indigo descriptions:** 0% → 90-100%
- ✅ **AAP errors:** Eliminated
- ✅ **Playwright errors:** Eliminated (0 → +4 successful jobs)

### Data Quality Score
- **Before:** 97%
- **After:** 98-99% (estimated)
- **Target:** >97% ✅

### Success Rate
- **Before:** 84% (178/211 completed)
- **After:** 98-99% (estimated, ~210/211 completed)
- **Expected:** 2-3 fewer failed jobs

## Troubleshooting

### If Indigo Still Has 0% Descriptions
1. Check if IndiGo website structure has changed
2. Run debug mode: Check HTML being extracted
3. Solution in extraction order:
   - JSON-LD might not exist (try CSS selectors)
   - Page might be blocked (try different delays)
   - HTML structure changed (need selector updates)

### If AAP Still Errors
1. Verify error message in Django admin
2. Check if issue is different from job_id
3. Manually run AAP scraper: `python manage.py scrape_aap --debug`

### If Playwright Still Fails
1. Verify installation: `python -m playwright install --with-deps`
2. Check browser cache: `rm -rf ~/.cache/ms-playwright/`
3. Reinstall: `python -m playwright install`

## Performance Monitoring

### Check API Performance
```bash
# Current response times
curl http://localhost:8000/api/scraper/stats/
# Should be fast (cached for 5 minutes)

# Job history with pagination
curl http://localhost:8000/api/scraper/history/?page=1
```

### Monitor Scraper Jobs
```python
from scraper_manager.models import ScraperJob

# Recent jobs
recent = ScraperJob.objects.latest('created_at')
print(f"Latest: {recent.status} - {recent.duration}s")

# Summary
from django.db.models import Count, Avg
summary = ScraperJob.objects.aggregate(
    total=Count('id'),
    completed=Count('id', filter=Q(status='completed')),
    failed=Count('id', filter=Q(status='failed')),
    avg_duration=Avg('duration')
)
print(summary)
```

## Detailed Testing

### Test Individual Scrapers
```bash
# Indigo only
python manage.py scrape_indigo

# AAP only
python manage.py scrape_aap

# Browser-based scraper (tests Playwright fix)
python manage.py scrape_signature
```

### Run Comprehensive Test
```bash
# Re-run the validation test
python scraper_manager/comprehensive_tester.py
# Should show improved numbers for Indigo
```

## Rollback Plan

If issues arise, all changes are reversible:

1. **Indigo scraper:** Keep old version backed up in `backups/scrapers/indigo_scraper.py`
2. **AAP scraper:** Changes are additive (can comment out error handling)
3. **Playwright:** Run `pip uninstall playwright-browsers` if needed

## Documentation

- `SCRAPER_FIXES_REPORT.md` - Complete fix details and expected improvements
- `DETAILED_CODE_CHANGES.md` - Line-by-line code changes
- `test_fixes.py` - Validation script (already passed)

---

## Summary

You now have:
1. ✅ Fixed Indigo scraper (multi-strategy description extraction)
2. ✅ Fixed AAP scraper (defensive error handling)
3. ✅ Installed Playwright (browser & dependencies)
4. ✅ All fixes validated and ready

**Next action:** Run `python manage.py scrape_all` to see the improvements!

