# 🗄️ Database Management System

## Overview

The aviation job scraper now includes a **SQLite database system** that:
- ✅ **Prevents duplicate scraping** of the same job URLs
- ✅ **Tracks scraping history** and statistics
- ✅ **Generates consolidated output** (`job_output.json`)
- ✅ **Monitors job activity** across multiple sources

## Quick Start

### Run All Scrapers with Database Tracking
\`\`\`bash
python run_all_scrapers.py all
\`\`\`

### Run Specific Scrapers
\`\`\`bash
python run_all_scrapers.py aviationjobsearch flygosh
\`\`\`

### View Statistics
\`\`\`bash
python run_all_scrapers.py stats
\`\`\`

### Export to JSON
\`\`\`bash
python run_all_scrapers.py export [filename]
\`\`\`

## How It Works

### 1. First Run
- Scrapes jobs from all enabled sites
- Saves each job to database with URL as unique identifier
- Generates \`job_output.json\` with all jobs

### 2. Subsequent Runs
- Checks each job URL against database
- **Skips duplicates** - doesn't re-scrape same jobs
- **Updates existing** - refreshes job data if URL already exists
- **Adds new** - only processes genuinely new jobs

### 3. Database Tracking
- Records when each job was first/last scraped
- Counts how many times each job was encountered
- Logs each scraping session with statistics

## Database Schema

### jobs Table
\`\`\`sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    job_id TEXT UNIQUE,           -- Unique job identifier
    url TEXT UNIQUE,               -- Job URL (prevents duplicates)
    title TEXT,
    company TEXT,
    source TEXT,                   -- Which scraper found it
    location TEXT,
    first_scraped_at TIMESTAMP,   -- When first discovered
    last_scraped_at TIMESTAMP,    -- Last time seen
    scrape_count INTEGER,         -- Number of times scraped
    is_active BOOLEAN,            -- Job still available
    job_data TEXT                 -- Full JSON data
);
\`\`\`

### scrape_history Table
\`\`\`sql
CREATE TABLE scrape_history (
    id INTEGER PRIMARY KEY,
    source TEXT,                  -- Scraper name
    scrape_date TIMESTAMP,
    jobs_found INTEGER,           -- Total jobs found
    jobs_new INTEGER,             -- New jobs added
    jobs_updated INTEGER,         -- Existing jobs refreshed
    jobs_duplicate INTEGER,       -- Duplicates skipped
    duration_seconds REAL         -- How long it took
);
\`\`\`

## Example Output

### First Run
\`\`\`
💾 Saving to database...
  ✓ Database updated:
    - New jobs: 5
    - Updated jobs: 0
    - Duplicates skipped: 0

✓ Saved 5 jobs to output/aviation_job_search_jobs_20251125_135505.json
\`\`\`

### Second Run (Same Jobs)
\`\`\`
💾 Saving to database...
  ✓ Database updated:
    - New jobs: 0
    - Updated jobs: 5
    - Duplicates skipped: 5

✓ Saved 5 jobs to output/aviation_job_search_jobs_20251125_135600.json
\`\`\`

### Statistics View
\`\`\`
📊 DATABASE STATISTICS
======================================================================

Total Jobs in Database: 24

Jobs by Source:
  • aviationjobsearch: 5 jobs
  • flygosh: 5 jobs
  • goose: 5 jobs
  • signature: 5 jobs
  • aap: 4 jobs

Most Frequently Scraped Jobs:
  • Sheet Metal Worker at DCS Group - 3 times
  • First Officers at ZENON - 3 times

Recent Scraping Sessions:
  • goose (2025-11-25 08:29:07): 5 new, 0 duplicate
  • aviationjobsearch (2025-11-25 08:28:34): 0 new, 5 duplicate
\`\`\`

## Files Generated

| File | Description |
|------|-------------|
| \`jobs.db\` | SQLite database with all job data |
| \`job_output.json\` | Consolidated JSON with all jobs |
| \`output/*.json\` | Individual scraper outputs (timestamped) |

## Benefits

### 1. Prevents Duplicate Work
- Won't re-scrape same job URLs
- Saves time and bandwidth
- Reduces load on target websites

### 2. Tracks History
- See which jobs are most frequently posted
- Monitor scraping performance over time
- Identify popular job sources

### 3. Consolidated Output
- Single \`job_output.json\` with all jobs
- No need to merge multiple files
- Easy to import into other systems

### 4. Scraping Efficiency
- First run: Scrapes all jobs
- Second run: Only new jobs
- Result: Much faster subsequent runs

## Usage Examples

### Daily Scraping
\`\`\`bash
# Run daily to catch new jobs only
python run_all_scrapers.py all
\`\`\`

Output:
- Day 1: 24 new jobs
- Day 2: 3 new jobs, 21 duplicates skipped
- Day 3: 1 new job, 23 duplicates skipped

### Check What's New
\`\`\`bash
# View statistics to see latest additions
python run_all_scrapers.py stats
\`\`\`

### Export for Analysis
\`\`\`bash
# Export all jobs to JSON for data analysis
python run_all_scrapers.py export all_aviation_jobs.json
\`\`\`

## Database Management

### Direct Access
\`\`\`python
from db_manager import JobDatabaseManager

db = JobDatabaseManager('jobs.db')

# Get all jobs
all_jobs = db.get_all_jobs()

# Get jobs from specific source
signature_jobs = db.get_all_jobs(source='signature')

# Check if URL already scraped
is_scraped = db.is_url_scraped('https://example.com/job/123')

# Get statistics
stats = db.get_statistics()
print(f"Total jobs: {stats['total_jobs']}")

# Export to JSON
count, path = db.export_to_json('my_export.json')
\`\`\`

### Reset Database
\`\`\`bash
# Delete database to start fresh
rm jobs.db
python run_all_scrapers.py all
\`\`\`

## Key Features

### 1. URL-Based Deduplication
- Uses job URL as unique identifier
- Prevents duplicate scraping
- Updates existing records if job details change

### 2. Source Tracking
- Knows which scraper found each job
- Can filter by source
- Tracks performance per scraper

### 3. Temporal Tracking
- First scraped timestamp
- Last scraped timestamp
- Scrape count (how many times seen)

### 4. Session Logging
- Records each scraping run
- Tracks new vs duplicate jobs
- Monitors performance over time

## Configuration

### Enable/Disable Database
Database is **always enabled** in \`run_all_scrapers.py\`.

To run **without** database (old behavior):
\`\`\`bash
python run_scraper.py aviationjobsearch
\`\`\`

### Database Location
Default: \`jobs.db\` in project root

Change location:
\`\`\`python
db_manager = JobDatabaseManager('path/to/custom.db')
\`\`\`

## Best Practices

1. **Regular Runs**: Run daily/weekly to catch new jobs
2. **Check Stats**: Use \`stats\` command to monitor
3. **Export Regularly**: Backup with \`export\` command
4. **Clean Old Jobs**: Mark inactive jobs periodically
5. **Monitor Duplicates**: High duplicate count = site not updated

## Troubleshooting

### Database Locked
\`\`\`bash
# Another process is using the database
# Close other terminals and retry
\`\`\`

### Too Many Duplicates
- Site hasn't posted new jobs
- Increase \`max_jobs\` to see more listings
- Site may have updated but using same URLs

### Missing Jobs
- Check if scraper is enabled in \`config.py\`
- View individual scraper output in \`output/\` folder
- Run with \`stats\` to see what's in database

## Comparison: Old vs New

### Old System (run_scraper.py)
- ❌ No duplicate detection
- ❌ Re-scrapes same jobs every time
- ❌ Multiple separate JSON files
- ❌ No history tracking

### New System (run_all_scrapers.py)
- ✅ Automatic duplicate detection
- ✅ Only scrapes new jobs
- ✅ Single consolidated \`job_output.json\`
- ✅ Full history tracking
- ✅ Statistics dashboard
- ✅ Efficient repeated runs

## Performance

### First Run
- Duration: ~3-5 minutes for all scrapers
- Jobs found: 24+ jobs
- Database size: ~128 KB

### Second Run (Same Day)
- Duration: ~1-2 minutes (mostly duplicates)
- New jobs: 0-5 (depending on site updates)
- Duplicates skipped: 20-24

## Summary

The database system transforms the scraper from a simple extraction tool into a **comprehensive job monitoring system** that:

1. **Tracks all jobs** across multiple sources
2. **Prevents waste** by skipping duplicates
3. **Provides insights** through statistics
4. **Consolidates output** into single file
5. **Monitors history** over time

Use \`run_all_scrapers.py\` for production scraping with database benefits!
