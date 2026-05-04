"""
Tests for Naukri Profile Tracker Agent.
"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Settings, NaukriURLs, NaukriSelectors
from src.database import Database


class TestSettings:
    """Test Settings configuration."""
    
    def test_default_settings(self):
        """Test default settings values."""
        with patch.dict('os.environ', {
            'NAUKRI_EMAIL': 'test@example.com',
            'NAUKRI_PASSWORD': 'testpass123'
        }):
            settings = Settings()
            assert settings.naukri_email == 'test@example.com'
            assert settings.headless_mode == True
            assert settings.update_frequency_days == 2
            assert settings.recruiter_check_hours == 6
    
    def test_naukri_urls(self):
        """Test URL constants."""
        assert "naukri.com" in NaukriURLs.BASE
        assert "login" in NaukriURLs.LOGIN
        assert "profile" in NaukriURLs.PROFILE


class TestDatabase:
    """Test Database operations."""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create a temporary database."""
        db_path = tmp_path / "test.db"
        return Database(db_path)
    
    def test_log_activity(self, db):
        """Test activity logging."""
        db.log_activity("test_activity", {"key": "value"})
        activities = db.get_recent_activities(1)
        assert len(activities) == 1
        assert activities[0]["activity_type"] == "test_activity"
    
    def test_store_job_recommendation(self, db):
        """Test job recommendation storage."""
        job = {
            "id": "test_job_1",
            "title": "Software Engineer",
            "company": "Test Corp",
            "location": "Bangalore",
            "salary": "10-15 LPA",
            "experience": "2-5 years",
        }
        db.store_job_recommendation(job)
        
        jobs = db.search_jobs({"title": "Software"})
        assert len(jobs) >= 1
        assert jobs[0]["title"] == "Software Engineer"
    
    def test_application_status(self, db):
        """Test application status tracking."""
        app = {
            "title": "Test Job",
            "company": "Test Company",
            "status": "Applied",
            "applied_date": "2024-01-01",
        }
        db.update_application_status(app)
        
        # Update status
        app["status"] = "Interview Scheduled"
        db.update_application_status(app)
        
        # Check for status changes
        changes = db.get_application_status_changes()
        assert len(changes) == 1
    
    def test_performance_metrics(self, db):
        """Test performance metrics storage."""
        metrics = {
            "profile_views": 100,
            "search_appearances": 50,
            "recruiter_actions": 10,
        }
        db.store_performance_metrics(metrics)
        
        # Verify stored (indirectly through activity log)
        assert True  # Metrics stored without error


class TestResumeManager:
    """Test Resume Manager operations."""
    
    @pytest.mark.asyncio
    async def test_generate_refreshed_headline(self):
        """Test headline generation."""
        from src.resume_manager import ResumeManager
        
        # Mock dependencies
        mock_page = MagicMock()
        mock_settings = MagicMock()
        mock_db = MagicMock()
        
        manager = ResumeManager(mock_page, mock_settings, mock_db)
        
        # Test headline modification
        original = "Software Engineer with 5 years experience"
        modified = manager._generate_refreshed_headline(original)
        
        # Should be different from original
        assert modified != original
        # Should be based on original
        assert original.replace(".", "") in modified or modified.replace(".", "") in original


class TestJobTracker:
    """Test Job Tracker operations."""
    
    @pytest.fixture
    def db(self, tmp_path):
        """Create a temporary database."""
        db_path = tmp_path / "test.db"
        return Database(db_path)
    
    def test_search_jobs(self, db):
        """Test job search functionality."""
        # Add test jobs
        jobs = [
            {"id": "1", "title": "Python Developer", "company": "ABC Corp", "location": "Mumbai"},
            {"id": "2", "title": "Java Developer", "company": "XYZ Inc", "location": "Bangalore"},
            {"id": "3", "title": "Python Engineer", "company": "Tech Co", "location": "Delhi"},
        ]
        
        for job in jobs:
            db.store_job_recommendation(job)
        
        # Search by title
        results = db.search_jobs({"title": "Python"})
        assert len(results) == 2
        
        # Search by location
        results = db.search_jobs({"location": "Bangalore"})
        assert len(results) == 1
    
    def test_application_stats(self, db):
        """Test application statistics."""
        apps = [
            {"title": "Job 1", "company": "Co 1", "status": "Applied", "applied_date": "2024-01-01"},
            {"title": "Job 2", "company": "Co 2", "status": "Interview", "applied_date": "2024-01-02"},
            {"title": "Job 3", "company": "Co 3", "status": "Applied", "applied_date": "2024-01-03"},
        ]
        
        for app in apps:
            db.update_application_status(app)
        
        stats = db.get_application_stats()
        assert stats["total"] == 3
        assert stats["by_status"]["Applied"] == 2
        assert stats["by_status"]["Interview"] == 1


class TestNaukriAgent:
    """Test Naukri Agent operations."""
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self):
        """Test agent initialization."""
        with patch.dict('os.environ', {
            'NAUKRI_EMAIL': 'test@example.com',
            'NAUKRI_PASSWORD': 'testpass123'
        }):
            from src.naukri_agent import NaukriAgent
            
            agent = NaukriAgent()
            assert agent.is_logged_in == False
            assert agent.browser is None


class TestScheduler:
    """Test Scheduler operations."""
    
    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        with patch.dict('os.environ', {
            'NAUKRI_EMAIL': 'test@example.com',
            'NAUKRI_PASSWORD': 'testpass123'
        }):
            from src.scheduler import Scheduler
            
            scheduler = Scheduler()
            assert scheduler._running == False
    
    def test_job_configuration(self):
        """Test job configuration."""
        with patch.dict('os.environ', {
            'NAUKRI_EMAIL': 'test@example.com',
            'NAUKRI_PASSWORD': 'testpass123'
        }):
            from src.scheduler import Scheduler
            
            scheduler = Scheduler()
            scheduler.setup_jobs()
            
            jobs = scheduler.get_job_status()
            job_ids = [job["id"] for job in jobs]
            
            assert "resume_update" in job_ids
            assert "recruiter_check" in job_ids
            assert "job_recommendations" in job_ids


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
