import json
import base64
import os
from datetime import datetime
from pathlib import Path
import logging

from django.conf import settings

logger = logging.getLogger('resume_api')

BASE_DIR = Path(settings.BASE_DIR)
RESUME_STORE_PATH = BASE_DIR / 'ResumeDataStore.json'


def load_resume_store() -> dict:
    if not RESUME_STORE_PATH.exists():
        return {"resumes": []}
    try:
        with open(RESUME_STORE_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading resume store: {e}")
        return {"resumes": []}


def save_resume_store(data: dict):
    try:
        with open(RESUME_STORE_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving resume store: {e}")


def add_resume_to_store(resume_data: dict) -> dict:
    store = load_resume_store()
    resume_id = str(len(store["resumes"]) + 1)
    resume_data["id"] = resume_id
    resume_data["stored_at"] = datetime.now().isoformat()
    store["resumes"].append(resume_data)
    save_resume_store(store)
    return resume_data


# Initialize parser if available
parser = None
try:
    from .resume_parser import ResumeParser
    
    # Try multiple config path locations
    config_paths = [
        BASE_DIR / 'resumes' / 'resumeParcerconfig.json',
        BASE_DIR / 'resumeParcerconfig.json',
        Path(__file__).parent / 'resumeParcerconfig.json',
    ]
    
    config_path = None
    for path in config_paths:
        if path.exists():
            config_path = str(path)
            logger.info(f"Found resume parser config at: {config_path}")
            break
    
    if config_path:
        parser = ResumeParser(config_path)
        logger.info("Resume parser initialized successfully")
    else:
        # Try without config (will use defaults)
        parser = ResumeParser()
        logger.warning("Resume parser initialized without config file")
        
except Exception as e:
    logger.error(f"Failed to initialize resume parser: {e}")
    parser = None


def format_resume_response(result: dict) -> dict:
    # A compact port of the formatting function from FastAPI app.
    name = result.get('name', 'Unknown')
    email = ''
    if isinstance(result.get('emails'), list):
        emails = result.get('emails', [])
        email = emails[0] if emails else ''
    else:
        email = result.get('email', '')

    phones = result.get('phones', []) or []

    raw_skills = result.get('skills', {}) or {}
    if isinstance(raw_skills, dict):
        skills_matched = raw_skills.get('matched', {})
        skill_score = raw_skills.get('score', 0)
        skills_list = list(skills_matched.keys())
    else:
        skills_list = list(raw_skills) if isinstance(raw_skills, list) else []
        skills_matched = {}
        skill_score = 0

    aviation_data = result.get('aviation') or {}
    aviation_score = aviation_data.get('score', 0)

    total_score = result.get('total_score')
    if total_score is None:
        total_score = min(round(((skill_score + aviation_score) / 200) * 100), 100)

    # Experience handling
    if 'experience' in result:
        exp_data = result['experience']
        experience_items = exp_data.get('items', [])
        exp_summary = exp_data.get('summary', {})
    else:
        experience_items = result.get('experience_items', [])
        exp_summary = result.get('experience_summary', {})

    if not exp_summary:
        exp_summary = {"total_months": 0, "continuous": True, "gaps": []}

    # Format gaps
    formatted_gaps = []
    for gap in exp_summary.get('gaps', []):
        months = gap.get('months', 0)
        if months:
            years = months // 12
            remaining_months = months % 12
            gap_text = ''
            if years:
                gap_text += f"{years} year{'s' if years>1 else ''}"
            if remaining_months:
                if gap_text:
                    gap_text += ' and '
                gap_text += f"{remaining_months} month{'s' if remaining_months>1 else ''}"
            formatted_gaps.append({
                'from': gap.get('from'),
                'to': gap.get('to'),
                'duration': gap_text
            })

    total_months = exp_summary.get('total_months', 0)
    total_experience = ''
    if total_months:
        years = total_months // 12
        remaining_months = total_months % 12
        if years:
            total_experience += f"{years} year{'s' if years>1 else ''}"
        if remaining_months:
            if total_experience:
                total_experience += ' and '
            total_experience += f"{remaining_months} month{'s' if remaining_months>1 else ''}"

    return {
        'id': result.get('id'),
        'filename': result.get('filename', ''),
        'name': name,
        'email': email,
        'phones': phones,
        'skills': skills_list,
        'skills_matched': skills_matched,
        'skill_score': skill_score,
        'aviation': {
            'certifications': aviation_data.get('certifications', []),
            'aircraft_types': aviation_data.get('aircraft_types', []),
            'hours': aviation_data.get('hours', {}),
            'licenses': aviation_data.get('licenses', []),
            'score': aviation_data.get('score', 0)
        },
        'aviation_score': aviation_data.get('score', 0),
        'experience_items': experience_items,
        'experience': {'items': experience_items, 'summary': exp_summary},
        'experience_summary': {
            **exp_summary,
            'formatted_gaps': formatted_gaps,
            'total_experience': total_experience,
            'experience_status': 'Continuous Experience' if exp_summary.get('continuous') else 'Has Employment Gaps',
        },
        'total_score': total_score,
        'score': total_score,
        'raw_text': result.get('raw_text', ''),
        'parsed_at': result.get('parsed_at')
    }
