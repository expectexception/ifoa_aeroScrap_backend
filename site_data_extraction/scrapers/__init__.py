"""
Scraper Factory
Import and instantiate scrapers for different aviation job sites
"""

from scrapers.signature_aviation import SignatureAviationScraper
from scrapers.flygosh_scraper import FlygoshScraper
from scrapers.aviationindeed_scraper import AviationIndeedScraper
from scrapers.aap_aviation_scraper import AAPAviationScraper
from scrapers.indigo_scraper import IndiGoScraper
from scrapers.aviationjobsearch_scraper import AviationJobSearchScraper
from scrapers.goose_scraper import GooseRecruitmentScraper


# Available scrapers
SCRAPERS = {
    'signature': SignatureAviationScraper,
    'flygosh': FlygoshScraper,
    'aviationindeed': AviationIndeedScraper,
    'aap': AAPAviationScraper,
    'indigo': IndiGoScraper,
    'aviationjobsearch': AviationJobSearchScraper,
    'goose': GooseRecruitmentScraper,
}


def get_scraper(site_name: str, config: dict, db_manager=None):
    """
    Factory function to get scraper instance
    
    Args:
        site_name: Name of the site ('signature', 'flygosh', etc.)
        config: Configuration dictionary for the scraper
        db_manager: Optional database manager for URL tracking
    
    Returns:
        Scraper instance
    """
    if site_name not in SCRAPERS:
        raise ValueError(f"Unknown site: {site_name}. Available: {list(SCRAPERS.keys())}")
    
    scraper_class = SCRAPERS[site_name]
    return scraper_class(config, db_manager=db_manager)


def list_scrapers():
    """List all available scrapers"""
    return list(SCRAPERS.keys())
