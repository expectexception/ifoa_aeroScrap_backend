"""
Database Manager for Job URL Tracking
Prevents duplicate scraping and maintains job history
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Set
from contextlib import contextmanager


class JobDatabaseManager:
    """Manages job URL tracking and prevents duplicate scraping"""
    
    def __init__(self, db_path: str = 'jobs.db'):
        """Initialize database manager"""
        self.db_path = Path(db_path)
        self.init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def init_database(self):
        """Initialize database tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    title TEXT,
                    company TEXT,
                    source TEXT NOT NULL,
                    location TEXT,
                    first_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    scrape_count INTEGER DEFAULT 1,
                    is_active BOOLEAN DEFAULT 1,
                    job_data TEXT
                )
            """)
            
            # Create indexes for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_url ON jobs(url)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_id ON jobs(job_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_active ON jobs(is_active)
            """)
            
            # Create scrape_history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    scrape_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    jobs_found INTEGER,
                    jobs_new INTEGER,
                    jobs_updated INTEGER,
                    jobs_duplicate INTEGER,
                    duration_seconds REAL
                )
            """)
            
            conn.commit()
    
    def is_url_scraped(self, url: str) -> bool:
        """Check if URL has been scraped before"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM jobs WHERE url = ?", (url,))
            return cursor.fetchone() is not None
    
    def get_scraped_urls(self, source: Optional[str] = None) -> Set[str]:
        """Get set of all scraped URLs, optionally filtered by source"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if source:
                cursor.execute("SELECT url FROM jobs WHERE source = ?", (source,))
            else:
                cursor.execute("SELECT url FROM jobs")
            return {row['url'] for row in cursor.fetchall()}
    
    def add_or_update_job(self, job_data: Dict) -> tuple[bool, str]:
        """
        Add new job or update existing one
        Returns: (is_new, message)
        """
        url = job_data.get('url')
        job_id = job_data.get('job_id')
        
        if not url or not job_id:
            return False, "Missing required fields: url or job_id"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if job exists
            cursor.execute("SELECT id, scrape_count FROM jobs WHERE url = ?", (url,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing job
                cursor.execute("""
                    UPDATE jobs SET
                        last_scraped_at = CURRENT_TIMESTAMP,
                        scrape_count = scrape_count + 1,
                        title = ?,
                        company = ?,
                        location = ?,
                        job_data = ?
                    WHERE url = ?
                """, (
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('location'),
                    json.dumps(job_data),
                    url
                ))
                return False, f"Updated existing job (scraped {existing['scrape_count'] + 1} times)"
            else:
                # Insert new job
                cursor.execute("""
                    INSERT INTO jobs (
                        job_id, url, title, company, source, location, job_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    job_id,
                    url,
                    job_data.get('title'),
                    job_data.get('company'),
                    job_data.get('source'),
                    job_data.get('location'),
                    json.dumps(job_data)
                ))
                return True, "New job added"
    
    def add_jobs_batch(self, jobs: List[Dict], source: str) -> Dict[str, int]:
        """
        Add multiple jobs at once
        Returns: Statistics dictionary
        """
        stats = {
            'total': len(jobs),
            'new': 0,
            'updated': 0,
            'errors': 0
        }
        
        for job in jobs:
            try:
                is_new, _ = self.add_or_update_job(job)
                if is_new:
                    stats['new'] += 1
                else:
                    stats['updated'] += 1
            except Exception as e:
                stats['errors'] += 1
                print(f"Error adding job {job.get('job_id', 'unknown')}: {e}")
        
        stats['duplicate'] = stats['total'] - stats['new']
        return stats
    
    def log_scrape_session(self, source: str, stats: Dict, duration: float):
        """Log scraping session to history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_history (
                    source, jobs_found, jobs_new, jobs_updated, 
                    jobs_duplicate, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                source,
                stats.get('total', 0),
                stats.get('new', 0),
                stats.get('updated', 0),
                stats.get('duplicate', 0),
                duration
            ))
    
    def get_all_jobs(self, source: Optional[str] = None, active_only: bool = True) -> List[Dict]:
        """Get all jobs from database"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT job_data FROM jobs WHERE 1=1"
            params = []
            
            if source:
                query += " AND source = ?"
                params.append(source)
            
            if active_only:
                query += " AND is_active = 1"
            
            cursor.execute(query, params)
            
            jobs = []
            for row in cursor.fetchall():
                try:
                    job_data = json.loads(row['job_data'])
                    jobs.append(job_data)
                except json.JSONDecodeError:
                    continue
            
            return jobs
    
    def get_statistics(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total jobs
            cursor.execute("SELECT COUNT(*) as count FROM jobs")
            total_jobs = cursor.fetchone()['count']
            
            # Jobs by source
            cursor.execute("""
                SELECT source, COUNT(*) as count 
                FROM jobs 
                GROUP BY source 
                ORDER BY count DESC
            """)
            by_source = {row['source']: row['count'] for row in cursor.fetchall()}
            
            # Recent scraping sessions
            cursor.execute("""
                SELECT source, scrape_date, jobs_found, jobs_new, jobs_duplicate
                FROM scrape_history
                ORDER BY scrape_date DESC
                LIMIT 10
            """)
            recent_scrapes = [dict(row) for row in cursor.fetchall()]
            
            # Most scraped jobs
            cursor.execute("""
                SELECT url, title, company, scrape_count
                FROM jobs
                ORDER BY scrape_count DESC
                LIMIT 5
            """)
            most_scraped = [dict(row) for row in cursor.fetchall()]
            
            return {
                'total_jobs': total_jobs,
                'jobs_by_source': by_source,
                'recent_scrapes': recent_scrapes,
                'most_scraped': most_scraped
            }
    
    def mark_job_inactive(self, url: str):
        """Mark a job as inactive (no longer available)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET is_active = 0 WHERE url = ?", (url,))
    
    def export_to_json(self, output_path: str, source: Optional[str] = None):
        """Export all jobs to JSON file"""
        jobs = self.get_all_jobs(source=source)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, ensure_ascii=False, indent=2)
        
        return len(jobs), output_file
    
    def print_statistics(self):
        """Print database statistics"""
        stats = self.get_statistics()
        
        print("\n" + "=" * 70)
        print("📊 DATABASE STATISTICS")
        print("=" * 70)
        print(f"\nTotal Jobs in Database: {stats['total_jobs']}")
        
        print("\nJobs by Source:")
        for source, count in stats['jobs_by_source'].items():
            print(f"  • {source}: {count} jobs")
        
        if stats['most_scraped']:
            print("\nMost Frequently Scraped Jobs:")
            for job in stats['most_scraped']:
                print(f"  • {job['title']} at {job['company']} - {job['scrape_count']} times")
        
        if stats['recent_scrapes']:
            print("\nRecent Scraping Sessions:")
            for scrape in stats['recent_scrapes'][:5]:
                date = scrape['scrape_date'][:19]  # Trim to datetime
                print(f"  • {scrape['source']} ({date}): {scrape['jobs_new']} new, {scrape['jobs_duplicate']} duplicate")
        
        print("=" * 70)


if __name__ == '__main__':
    # Test database manager
    db = JobDatabaseManager()
    db.print_statistics()
