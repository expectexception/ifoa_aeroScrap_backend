import json
import logging
import os
import re
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, List, Optional, Union

import pdfplumber
from dateutil import parser as dateparser
from dateutil.relativedelta import relativedelta

class ResumeParserException(Exception):
    """Base exception for resume parser errors."""
    pass

class ResumeParser:
    """Parser for extracting structured information from resumes."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize parser with optional config path."""
        self.config = self._load_config(config_path) if config_path else {}
        self._setup_logging()
        
        # Compile regex patterns
        self.EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.PHONE_RE = re.compile(r"(\+?\d{1,3}[\s-]?)?(?:\(\d{2,4}\)|\d{2,4})[\s-]?\d{3,4}[\s-]?\d{3,4}")
        self.DATE_RANGE_RE = re.compile(
            r"(?P<start>(?:[A-Za-z]{3,9}\.?\s*\d{4}|\d{4}))\s*(?:-|–|—|to)\s*(?P<end>(?:present|now|current|[A-Za-z]{3,9}\.?\s*\d{4}|\d{4}))",
            flags=re.IGNORECASE,
        )
    
    def _setup_logging(self):
        """Setup logging configuration."""
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _load_config(self, path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise ResumeParserException(f"Failed to load config from {path}: {str(e)}")
    
    def extract_text(self, file_path: Union[str, Path]) -> str:
        """Extract text from PDF or text file."""
        file_path = str(file_path)
        text = ""
        
        try:
            if file_path.lower().endswith('.pdf'):
                with pdfplumber.open(file_path) as pdf:
                    text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
            else:
                # Try reading as text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
            
            return text
        except Exception as e:
            raise ResumeParserException(f"Failed to extract text from {file_path}: {str(e)}")
    
    def extract_contact_info(self, text: str) -> dict:
        """Extract email addresses and phone numbers."""
        emails = list({m.group(0) for m in self.EMAIL_RE.finditer(text)})
        phones = list({m.group(0) for m in self.PHONE_RE.finditer(text)})
        return {"emails": emails, "phones": phones}
    
    def extract_skills(self, text: str) -> dict:
        """Extract skills based on config and compute score."""
        skills_config = self.config.get("skills", {})
        lowered = text.lower()
        matched = {}
        total_score = 0
        
        for skill, weight in skills_config.items():
            if skill.lower() in lowered:
                matched[skill] = weight
                total_score += weight
        
        return {"matched": matched, "score": total_score}
    
    def extract_aviation_info(self, text: str) -> dict:
        """Extract aviation-specific information."""
        av_cfg = self.config.get("aviation", {})
        certs = []
        aircraft = []
        hours = {}
        license_ids = []
        lowered = text.lower()
        
        # Find certifications
        for cert in av_cfg.get("certifications", []):
            if cert.lower() in lowered:
                certs.append(cert)
        
        # Find aircraft types
        for ac in av_cfg.get("aircraft_types", []):
            if ac.lower() in lowered:
                aircraft.append(ac)
        
        # Extract flight hours
        hours_regex = av_cfg.get("hours_regex")
        if hours_regex:
            try:
                m = re.search(hours_regex, text)
                if m and m.group(1):
                    try:
                        h = int(m.group(1).replace(',', ''))
                        hours["total_hours"] = h
                    except ValueError:
                        pass
            except re.error:
                self.logger.warning("Invalid hours regex in config")
        
        # Find license numbers
        lic_re = re.compile(r"(?i)\b(ATPL|CPL|PPL|Licence|License)[\s:]*([A-Z0-9\-\/]+)\b")
        for m in lic_re.finditer(text):
            license_ids.append({"type": m.group(1), "id": m.group(2)})
        
        # Compute aviation score
        weights = av_cfg.get("weights", {})
        score = 0
        score += len(certs) * weights.get("certification", 5)
        score += len(aircraft) * weights.get("aircraft_type", 2)
        if "total_hours" in hours:
            score += (hours["total_hours"] // 100) * weights.get("per_100_hours", 1)
        
        return {
            "certifications": certs,
            "aircraft_types": aircraft,
            "hours": hours,
            "licenses": license_ids,
            "score": score
        }
    
    def parse_date(self, text: str) -> Optional[datetime]:
        """Parse date from text, handling 'present' and similar terms."""
        text = text.strip()
        if re.search(r"present|now|current", text, re.IGNORECASE):
            return datetime.now(UTC)
        try:
            dt = dateparser.parse(text, default=datetime(1, 1, 1))
            return dt
        except Exception:
            # fallback year-only
            m = re.search(r"(\d{4})", text)
            if m:
                year = int(m.group(1))
                return datetime(year, 1, 1)
        return None
    
    def extract_experience(self, text: str) -> dict:
        """Extract and analyze work experience dates."""
        experiences = []
        
        # Find all date ranges with context
        for m in self.DATE_RANGE_RE.finditer(text):
            start_raw = m.group("start")
            end_raw = m.group("end")
            start = self.parse_date(start_raw)
            end = self.parse_date(end_raw)
            
            # Capture surrounding context
            span_start = max(0, m.start() - 200)
            span_end = min(len(text), m.end() + 200)
            snippet = text[span_start:span_end].strip()
            
            experiences.append({
                "start_raw": start_raw,
                "end_raw": end_raw,
                "start": start.date().isoformat() if start else None,
                "end": end.date().isoformat() if end else None,
                "snippet": snippet
            })
        
        if not experiences:
            return {"items": [], "summary": None}
        
        # Analyze gaps and continuity
        intervals = []
        for exp in experiences:
            try:
                s = datetime.fromisoformat(exp["start"]) if exp["start"] else None
                e = datetime.fromisoformat(exp["end"]) if exp["end"] else datetime.now(UTC)
                if s:
                    intervals.append((s.date(), e.date()))
            except Exception:
                continue
        
        if not intervals:
            return {"items": experiences, "summary": None}
        
        # Sort and merge overlapping intervals
        intervals.sort()
        merged = []
        for s, e in intervals:
            if not merged:
                merged.append([s, e])
            else:
                last = merged[-1]
                if s <= last[1] + relativedelta(days=1):
                    if e > last[1]:
                        last[1] = e
                else:
                    merged.append([s, e])
        
        # Calculate total experience and gaps
        total_months = sum(
            ((e.year - s.year) * 12 + e.month - s.month + (1 if e.day >= s.day else 0))
            for s, e in merged
        )
        
        gaps = []
        continuous = True
        gap_threshold = self.config.get("gap_months_threshold", 3)
        
        for i in range(1, len(merged)):
            prev_end = merged[i-1][1]
            this_start = merged[i][0]
            gap_months = (
                (this_start.year - prev_end.year) * 12 
                + this_start.month - prev_end.month 
                + (1 if this_start.day > prev_end.day else 0)
            )
            
            if gap_months >= gap_threshold:
                gaps.append({
                    "from": prev_end.isoformat(),
                    "to": this_start.isoformat(),
                    "months": gap_months
                })
                continuous = False
        
        summary = {
            "total_months": total_months,
            "total_years": round(total_months / 12, 2),
            "continuous": continuous,
            "gaps": gaps,
            "merged_periods": [[s.isoformat(), e.isoformat()] for s, e in merged]
        }
        
        return {"items": experiences, "summary": summary}
    
    def guess_name(self, text: str) -> Optional[str]:
        """Attempt to extract candidate name from resume."""
        for line in text.splitlines():
            l = line.strip()
            if not l:
                continue
            # Skip lines with email or phone
            if self.EMAIL_RE.search(l) or self.PHONE_RE.search(l):
                continue
            # Look for 2-4 capitalized words
            words = l.split()
            if 1 < len(words) <= 4 and all(w[0].isupper() or w.isupper() for w in words if w):
                return l
        return None
    
    def parse(self, file_path: Union[str, Path]) -> dict:
        try:
            self.logger.info(f"Parsing resume: {file_path}")
            
            # Extract text
            text = self.extract_text(file_path)
            if not text.strip():
                raise ResumeParserException("No text could be extracted from file")
            
            # Extract all information
            contact_info = self.extract_contact_info(text)
            skills = self.extract_skills(text)
            aviation = self.extract_aviation_info(text)
            experience = self.extract_experience(text)
            name = self.guess_name(text) or Path(file_path).stem
            
            # Compute total score
            total_score = skills.get("score", 0) + aviation.get("score", 0)
            
            result = {
                "name": name,
                "emails": contact_info["emails"],
                "phones": contact_info["phones"],
                "skills": skills,
                "aviation": aviation,
                "experience_items": experience["items"],
                "experience_summary": experience["summary"],
                "total_score": total_score,
                "parsed_at": datetime.now(UTC).isoformat()
            }
            
            return result
            
        except Exception as e:
            raise ResumeParserException(f"Failed to parse resume: {str(e)}")

if __name__ == "__main__":
    # Convenience function for quick parsing
    def parse_resume(file_path: Union[str, Path], config_path: Optional[str] = None) -> dict:
        """Parse a resume file using default or provided configuration."""
        parser = ResumeParser(config_path)
        return parser.parse(file_path)