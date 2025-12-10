from difflib import SequenceMatcher
from typing import Optional
import re

# Keywords and tokens - Comprehensive list from worksheet (Section 2)
# Core Operational Control-Level Titles (20+)
KEYWORDS = [
    # Core operational roles
    "flight operations officer", "foo", "aircraft dispatcher", "flight dispatcher",
    "flight operations controller", "operations controller", "operations control centre officer",
    "occ officer", "network operations controller", "network operations officer",
    "scheduler", "flight scheduler", "load controller", "load control officer",
    "crew controller", "crew control officer", "integrated operations controller",
    "schedule control officer", "disruption manager", "disruption controller",
    "on-wing operations controller", "operations duty officer", "mission control officer",
    "flight operations coordinator", "operations support controller", "dispatch coordinator",
    "flight watch officer",
    
    # Supervisory titles
    "senior flight operations officer", "senior aircraft dispatcher", "senior flight dispatcher",
    "senior operations controller", "senior operations control centre officer",
    "supervisor operations control", "supervisor operations control centre",
    "supervisor dispatch", "crew control supervisor", "load control supervisor",
    "network operations supervisor", "senior scheduler",
    
    # Management / Superintendent titles
    "manager operations control centre", "occ manager", "manager flight operations control",
    "manager network operations centre", "noc manager", "head of operations control",
    "head of operations control centre", "director operations control",
    "director flight operations control", "superintendent operations control",
    "superintendent flight dispatch", "superintendent network control centre",
    "senior manager operations control", "director network operations control",
    "vice president operations control", "vp operations control",
    
    # Alternative title variants / regional differences
    "movement controller", "dispatch officer", "dispatch supervisor",
    "flight operations specialist", "operations planning controller",
    "occ coordinator", "noc coordinator", "ioc controller",
    "soc controller", "goc controller", "system operations controller",
    "global operations controller", "integrated operations centre controller",
    
    # Common abbreviations and variations
    "operations control", "flight operations", "flight dispatch", "network operations",
    "crew control", "operations centre", "dispatch", "operations coordination"
]

SENIOR_TOKENS = [
    "manager", "head", "director", "senior", "vp", "vice president",
    "superintendent", "lead", "chief", "principal", "supervisor",
    "sr", "sr.", "head of"
]


def is_operational_title(title: str) -> bool:
    """
    Check if job title matches operational control role keywords.
    Uses comprehensive keyword list from worksheet Section 2.
    """
    if not title:
        return False
    title_lower = title.lower()
    
    # Primary: Exact or substring match from keyword list
    if any(k in title_lower for k in KEYWORDS):
        return True
    
    # Secondary: Token-based matching for common terms
    # Require at least 2 operational tokens for better accuracy
    operational_tokens = ['dispatch', 'operations', 'occ', 'noc', 'controller', 
                          'coordinator', 'crew', 'flight', 'network', 'control']
    matches = sum(1 for token in operational_tokens if token in title_lower)
    
    if matches >= 2:
        return True
    
    # Tertiary: Check for specific combinations
    if ('operations' in title_lower or 'operational' in title_lower) and \
       ('control' in title_lower or 'centre' in title_lower or 'center' in title_lower):
        return True
    
    return False


def is_senior(title: str) -> bool:
    if not title:
        return False
    tl = title.lower()
    # quick check
    if any(tok in tl for tok in SENIOR_TOKENS):
        return True
    # regex-level precision for common abbreviations and phrases
    patterns = [
        r"\bsenior\b",
        r"\bsr\.?\b",
        r"\b(head|lead|principal|chief|director|manager|superintendent|supervisor)\b",
        r"\bvice\s+president\b",
    ]
    return any(re.search(p, tl) for p in patterns)


def classify_company_by_name(name: Optional[str]) -> Optional[str]:
    """Heuristic company -> operation_type mapping."""
    if not name:
        return None
    n = name.lower()
    if 'cargo' in n or 'freight' in n:
        return 'cargo'
    if 'charter' in n or 'ad-hoc' in n or 'ad hoc' in n:
        return 'ad_hoc_charter'
    if 'fbo' in n or 'business' in n or 'corporate' in n:
        return 'business'
    # low_cost operators often include 'low cost' or 'budget'
    if 'low cost' in n or 'budget' in n:
        return 'low_cost'
    # scheduled airlines often include 'airlines' or 'airways'
    if 'airlines' in n or 'airways' in n or re.search(r'\bair\b', n):
        return 'scheduled'
    return None


def fuzzy_title_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def is_duplicate(existing_title: str, existing_company: str, existing_date, new_title: str, new_company: str, new_date) -> bool:
    """Apply secondary and tertiary dedupe heuristics.
    - exact title+company+date
    - fuzzy title + same company and date within few days
    """
    # exact
    if existing_title and new_title and existing_title.strip().lower() == new_title.strip().lower():
        if existing_company and new_company and existing_company.strip().lower() == new_company.strip().lower():
            if existing_date == new_date:
                return True

    # fuzzy title check (threshold 0.9) and company equals and date equal
    score = fuzzy_title_similarity(existing_title or '', new_title or '')
    if score >= 0.90:
        if existing_company and new_company and existing_company.strip().lower() == new_company.strip().lower():
            # date check: exact or None
            if existing_date == new_date:
                return True
    return False
