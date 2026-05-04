"""
Database - SQLite database for storing agent data.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

from loguru import logger


class Database:
    """
    SQLite database handler for Naukri Profile Tracker.
    
    Stores:
    - Activity logs
    - Recruiter activities
    - Job recommendations
    - Application status
    - Performance metrics
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
        logger.info(f"Database initialized: {db_path}")
    
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Activity log table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recruiter activities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiter_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recruiter_name TEXT,
                company TEXT,
                activity_type TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Job recommendations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                experience TEXT,
                url TEXT,
                status TEXT DEFAULT 'new',
                data TEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_title TEXT,
                company TEXT,
                status TEXT,
                applied_date TEXT,
                last_status TEXT,
                data TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Performance metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_views INTEGER,
                search_appearances INTEGER,
                recruiter_actions INTEGER,
                data TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Recruiter summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiter_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Resume updates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resume_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def log_activity(self, activity_type: str, data: dict) -> None:
        """
        Log an activity to the database.
        
        Args:
            activity_type: Type of activity
            data: Activity data dictionary
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO activity_log (activity_type, data) VALUES (?, ?)",
            (activity_type, json.dumps(data))
        )
        self.conn.commit()
        logger.debug(f"Logged activity: {activity_type}")
    
    def get_last_resume_update_method(self) -> Optional[str]:
        """Get the method used for the last resume update."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT method FROM resume_updates ORDER BY created_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        return row["method"] if row else None
    
    def store_recruiter_summary(self, summary: dict) -> None:
        """Store recruiter activity summary."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO recruiter_summary (data) VALUES (?)",
            (json.dumps(summary),)
        )
        self.conn.commit()
    
    def get_last_recruiter_summary(self) -> Optional[dict]:
        """Get the last recruiter summary."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT data FROM recruiter_summary ORDER BY created_at DESC LIMIT 1 OFFSET 1"
        )
        row = cursor.fetchone()
        return json.loads(row["data"]) if row else None
    
    def store_job_recommendation(self, job: dict) -> None:
        """Store a job recommendation."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO job_recommendations 
                (job_id, title, company, location, salary, experience, url, status, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.get("id"),
                job.get("title"),
                job.get("company"),
                job.get("location"),
                job.get("salary"),
                job.get("experience"),
                job.get("url"),
                job.get("status", "new"),
                json.dumps(job)
            ))
            self.conn.commit()
        except sqlite3.IntegrityError:
            pass  # Job already exists
    
    def update_application_status(self, application: dict) -> None:
        """Update application status in database."""
        cursor = self.conn.cursor()
        
        # Check if application exists
        cursor.execute(
            "SELECT status FROM applications WHERE job_title = ? AND company = ?",
            (application.get("title"), application.get("company"))
        )
        row = cursor.fetchone()
        
        if row:
            # Update existing
            last_status = row["status"]
            cursor.execute("""
                UPDATE applications 
                SET status = ?, last_status = ?, data = ?, updated_at = CURRENT_TIMESTAMP
                WHERE job_title = ? AND company = ?
            """, (
                application.get("status"),
                last_status,
                json.dumps(application),
                application.get("title"),
                application.get("company")
            ))
        else:
            # Insert new
            cursor.execute("""
                INSERT INTO applications (job_title, company, status, applied_date, data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                application.get("title"),
                application.get("company"),
                application.get("status"),
                application.get("applied_date"),
                json.dumps(application)
            ))
        
        self.conn.commit()
    
    def get_application_status_changes(self) -> list[dict]:
        """Get applications with recent status changes."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM applications 
            WHERE status != last_status AND last_status IS NOT NULL
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def store_performance_metrics(self, metrics: dict) -> None:
        """Store profile performance metrics."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO performance_metrics 
            (profile_views, search_appearances, recruiter_actions, data)
            VALUES (?, ?, ?, ?)
        """, (
            metrics.get("profile_views", 0),
            metrics.get("search_appearances", 0),
            metrics.get("recruiter_actions", 0),
            json.dumps(metrics)
        ))
        self.conn.commit()
    
    def get_recruiter_info(self, recruiter_name: str) -> Optional[dict]:
        """Get info about a specific recruiter."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM recruiter_activities WHERE recruiter_name = ? ORDER BY created_at DESC LIMIT 1",
            (recruiter_name,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_activity_trend(self, days: int = 7) -> list[dict]:
        """Get activity trend for specified days."""
        cursor = self.conn.cursor()
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count, activity_type
            FROM activity_log
            WHERE created_at >= ?
            GROUP BY DATE(created_at), activity_type
            ORDER BY date DESC
        """, (start_date,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def search_jobs(self, criteria: dict) -> list[dict]:
        """Search stored jobs by criteria."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM job_recommendations WHERE 1=1"
        params = []
        
        if criteria.get("title"):
            query += " AND title LIKE ?"
            params.append(f"%{criteria['title']}%")
        
        if criteria.get("company"):
            query += " AND company LIKE ?"
            params.append(f"%{criteria['company']}%")
        
        if criteria.get("location"):
            query += " AND location LIKE ?"
            params.append(f"%{criteria['location']}%")
        
        query += " ORDER BY fetched_at DESC LIMIT 50"
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_application_stats(self) -> dict:
        """Get application statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM applications")
        total = cursor.fetchone()["total"]
        
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM applications 
            GROUP BY status
        """)
        by_status = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        return {
            "total": total,
            "by_status": by_status
        }
    
    def get_recent_activities(self, limit: int = 20) -> list[dict]:
        """Get recent activities."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM activity_log ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
        logger.debug("Database connection closed")
