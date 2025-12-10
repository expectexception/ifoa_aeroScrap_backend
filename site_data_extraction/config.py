"""
Configuration for Aviation Job Scraper
Edit these settings to control scraper behavior for different sites
"""

# Global Scraper Settings
SCRAPER_SETTINGS = {
    # Number of concurrent browser pages for description extraction
    'batch_size': 3,  # Reduced from 5 to be less aggressive
    
    # Output directory
    'output_dir': 'output',
    
    # Anti-Detection Settings
    'stealth_mode': True,
    'request_delay_min': 2,  # Minimum delay between requests (seconds)
    'request_delay_max': 5,  # Maximum delay between requests (seconds)
    'page_load_delay': 3,    # Extra delay after page load (seconds)
    'random_scroll': True,   # Simulate human scrolling
    'random_mouse': True,    # Simulate mouse movements
    
    # User-Agent Rotation
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
    ],
    
    # Proxy Settings (optional - add your proxies here)
    'proxy_list': [],  # Example: ['http://user:pass@proxy1.com:8080', 'http://proxy2.com:8080']
    'rotate_proxy': False,
    
    # Title Filtering Settings
    'use_filter': True,  # Enable/disable title keyword filtering
    'filter_file': 'filter_title.json',  # Path to filter configuration
    'filter_before_scrape': True,  # Filter before fetching descriptions (saves time)
}

# Per-Site Scraper Limits
SCRAPERS = {
    'signature': {
        'max_jobs': 20,  # None = extract all jobs
        'max_pages': None,  # None = no page limit
    },
    'flygosh': {
        'max_jobs': 20,   # Set to 50 to limit to 50 jobs
        'max_pages': None,  # Not applicable for listing-based scrapers
    },
    'aviationindeed': {
        'max_jobs': 20,   # Limit for testing
        'max_pages': None,
    },
    'aap': {
        'max_jobs': 20,   # Limit for testing
        'max_pages': None,
    },
    'indigo': {
        'max_jobs': 20,   # Limit for testing
        'max_pages': None,
    },
    'aviationjobsearch': {
        'max_jobs': 20,   # Increased to find matching jobs
        'max_pages': None,
    },
    'goose': {
        'max_jobs': 20,   # Limit for testing
        'max_pages': None,
    },
}

# Site Configurations
SITES = {
    'signature': {
        'name': 'Signature Aviation',
        'enabled': True,
        'api_url': 'https://hdbt.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions',
        'site_number': 'CX_1',
        'base_url': 'https://jobs.signatureaviation.com',
        'description': 'Oracle Cloud HCM-based job board',
    },
    'flygosh': {
        'name': 'Flygosh Jobs',
        'enabled': True,
        'base_url': 'https://flygoshjobs.com',
        'jobs_url': 'https://flygoshjobs.com/jobs/all/all-region/',
        'description': 'Aviation jobs listing page',
    },
    # NOT WORKING YET - CEIPAL iframe requires special handling 
    'aviationindeed': {
        'name': 'Aviation Indeed',
        'enabled': False, # Site has loading issues - needs investigation
        'base_url': 'https://www.aviationindeed.com',
        'ceipal_url': 'https://www.aviationindeed.com/ceipal/',
        'description': 'CEIPAL iframe-based job board',
    },
    'aap': {
        'name': 'AAP Aviation',
        'enabled': True,
        'base_url': 'https://jobs.aapaviation.com',
        'jobs_url': 'https://jobs.aapaviation.com/jobs',
        'description': 'AAP Aviation job board',
    },
    'indigo': {
        'name': 'IndiGo Airlines',
        'enabled': False,  # Site has loading issues - disabled
        'base_url': 'https://www.goindigo.in',
        'jobs_url': 'https://www.goindigo.in/careers/job-search.html?type=&location=&department=',
        'description': 'IndiGo Airlines careers page (currently under development)',
    },
    'aviationjobsearch': {
        'name': 'Aviation Job Search',
        'enabled': True,
        'base_url': 'https://www.aviationjobsearch.com',
        'jobs_url': 'https://www.aviationjobsearch.com/en-GB/jobs',
        'description': 'Aviation Job Search - comprehensive aviation job listings',
    },
    'goose': {
        'name': 'GOOSE Recruitment',
        'enabled': True,
        'base_url': 'https://www.goose-recruitment.com',
        'jobs_url': 'https://www.goose-recruitment.com/jobs',
        'description': 'GOOSE Recruitment - aviation and aerospace jobs',
    },
}

# Build complete config (used by scrapers)
CONFIG = {
    'scraper_settings': SCRAPER_SETTINGS,
    'scrapers': SCRAPERS,
    'sites': SITES,
}
