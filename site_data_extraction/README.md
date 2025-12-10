# Aviation Job Scraper

Production-ready multi-site aviation job scraper with modular architecture.

## Features

✅ Multi-site support  
✅ Full job descriptions from detail pages  
✅ Configurable limits per site  
✅ JSON output only  
✅ Async processing with Playwright  

## Supported Sites

- **Signature Aviation** - Oracle Cloud HCM API + web scraping ✅
- **Flygosh Jobs** - JavaScript-rendered listings ✅
- **Aviation Indeed** - CEIPAL iframe-based job board ⚠️
- **AAP Aviation** - Deep job extraction ✅
- **IndiGo Airlines** - Careers page scraper (In Development) 🔄

## Quick Start

```bash
# Extract from specific site
python run_scraper.py signature
python run_scraper.py flygosh
python run_scraper.py aviationindeed
python run_scraper.py aap
python run_scraper.py indigo

# Extract from all sites
python run_scraper.py all
```

## Configuration

Edit `config.py`:

```python
SCRAPERS = {
    'signature': {'max_jobs': 50},   # Limit jobs
    'flygosh': {'max_jobs': None},   # All jobs
}
```

## Output

JSON files saved to: `output/{site}_jobs_TIMESTAMP.json`

Each job contains:
- `job_id`, `title`, `company`, `location`
- `job_type`, `posted_date`, `closing_date`
- **`description`** - Full job description from detail page
- `requirements`, `qualifications`
- `url`, `apply_url`

## Project Structure

```
├── scrapers/
│   ├── base_scraper.py             # Base class
│   ├── signature_aviation.py      # Signature scraper
│   ├── flygosh_scraper.py          # Flygosh scraper
│   ├── aviationindeed_scraper.py   # Aviation Indeed scraper
│   ├── aap_aviation_scraper.py     # AAP Aviation scraper
│   └── indigo_scraper.py           # IndiGo Airlines scraper
├── config.py                    # Configuration
├── run_scraper.py               # Runner
└── output/                      # JSON results
```

## Adding New Sites

1. Create `scrapers/newsite.py` (inherit from `BaseScraper`)
2. Add to `scrapers/__init__.py` factory
3. Add config to `config.py`
4. Run: `python run_scraper.py newsite`

## Module Usage

```python
from scrapers import get_scraper
from config import CONFIG
import asyncio

scraper = get_scraper('signature', CONFIG)
jobs = asyncio.run(scraper.run())
```
