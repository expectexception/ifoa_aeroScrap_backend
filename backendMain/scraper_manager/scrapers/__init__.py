"""
Scraper Factory
Import and instantiate scrapers for different aviation job sites
"""

from .signature_aviation import SignatureAviationScraper
from .flygosh_scraper import FlygoshScraper
from .aviationindeed_scraper import AviationIndeedScraper
from .aap_aviation_scraper import AAPAviationScraper
from .indigo_scraper import IndiGoScraper
from .aviationjobsearch_scraper import AviationJobSearchScraper
from .goose_scraper import GooseRecruitmentScraper
from .linkdin_scraper import LinkedInScraper
from .peopleclick_scraper import CargoluxPeopleClickScraper
from .airindia_scraper import AirIndiaScraper
from .aviationcv_scraper import AviationCVScraper
from .jsfirm_scraper import JSFirmScraper
from .allflyingjobs_scraper import AllFlyingJobsScraper
from .emirates_scraper import EmiratesScraper
from .boeing_scraper import BoeingScraper
from .airbus_scraper import AirbusScraper
from .pilots_global_scraper import PilotsGlobalScraper


# Available scrapers
SCRAPERS = {
    'signature': SignatureAviationScraper,
    'flygosh': FlygoshScraper,
    'aviationindeed': AviationIndeedScraper,
    'aap': AAPAviationScraper,
    'indigo': IndiGoScraper,
    'aviationjobsearch': AviationJobSearchScraper,
    'goose': GooseRecruitmentScraper,
    'linkedin': LinkedInScraper,
    'cargolux': CargoluxPeopleClickScraper,
    'airindia': AirIndiaScraper,
    'aviationcv': AviationCVScraper,
    'jsfirm': JSFirmScraper,
    'allflyingjobs': AllFlyingJobsScraper,
    'emirates': EmiratesScraper,
    'boeing': BoeingScraper,
    'airbus': AirbusScraper,
    'pilots_global': PilotsGlobalScraper,
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
