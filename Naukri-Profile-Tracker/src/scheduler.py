"""
Scheduler - Handles automated task scheduling.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from .config import Settings, get_settings
from .naukri_agent import NaukriAgent


class Scheduler:
    """
    Task scheduler for Naukri Profile Tracker.
    
    Schedules:
    - Resume updates (every 2 days)
    - Recruiter activity checks (every 6 hours)
    - Job recommendations (daily)
    - Profile health checks (weekly)
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        Initialize Scheduler.
        
        Args:
            settings: Application settings
        """
        self.settings = settings or get_settings()
        self.scheduler = AsyncIOScheduler()
        self.agent: Optional[NaukriAgent] = None
        self._running = False
        
        logger.info("Scheduler initialized")
    
    def setup_jobs(self) -> None:
        """Configure all scheduled jobs."""
        
        # Resume update - every N days (default: 2)
        self.scheduler.add_job(
            self._run_resume_update,
            IntervalTrigger(days=self.settings.update_frequency_days),
            id="resume_update",
            name="Resume Update",
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(minutes=5)  # First run in 5 mins
        )
        
        # Recruiter activity check - every N hours (default: 6)
        self.scheduler.add_job(
            self._run_recruiter_check,
            IntervalTrigger(hours=self.settings.recruiter_check_hours),
            id="recruiter_check",
            name="Recruiter Activity Check",
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(minutes=10)
        )
        
        # Job recommendations - daily at 9 AM
        self.scheduler.add_job(
            self._run_job_recommendations,
            CronTrigger(hour=9, minute=0),
            id="job_recommendations",
            name="Job Recommendations",
            replace_existing=True
        )
        
        # Full profile check - daily at 8 PM
        self.scheduler.add_job(
            self._run_full_check,
            CronTrigger(hour=20, minute=0),
            id="full_check",
            name="Full Profile Check",
            replace_existing=True
        )
        
        # Daily summary email - at 9 PM
        self.scheduler.add_job(
            self._send_daily_summary,
            CronTrigger(hour=21, minute=0),
            id="daily_summary",
            name="Daily Summary",
            replace_existing=True
        )
        
        # Profile health check - weekly on Sunday at 10 AM
        self.scheduler.add_job(
            self._run_profile_health_check,
            CronTrigger(day_of_week='sun', hour=10, minute=0),
            id="profile_health",
            name="Profile Health Check",
            replace_existing=True
        )
        
        logger.info("Scheduled jobs configured")
        self._log_scheduled_jobs()
    
    def _log_scheduled_jobs(self) -> None:
        """Log all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        logger.info(f"Scheduled {len(jobs)} jobs:")
        for job in jobs:
            logger.info(f"  - {job.name}: Next run at {job.next_run_time}")
    
    async def start(self) -> None:
        """Start the scheduler."""
        if self._running:
            logger.warning("Scheduler already running")
            return
        
        logger.info("Starting Naukri Profile Tracker scheduler...")
        
        # Initialize agent
        self.agent = NaukriAgent(self.settings)
        await self.agent.start()
        
        # Login
        login_success = await self.agent.login()
        if not login_success:
            logger.error("Failed to login. Scheduler will retry on next job execution.")
        
        # Setup and start scheduler
        self.setup_jobs()
        self.scheduler.start()
        self._running = True
        
        logger.info("Scheduler started successfully")
    
    async def stop(self) -> None:
        """Stop the scheduler."""
        if not self._running:
            return
        
        logger.info("Stopping scheduler...")
        
        self.scheduler.shutdown(wait=True)
        
        if self.agent:
            await self.agent.close()
        
        self._running = False
        logger.info("Scheduler stopped")
    
    async def _ensure_logged_in(self) -> bool:
        """Ensure agent is logged in before running tasks."""
        if not self.agent:
            self.agent = NaukriAgent(self.settings)
            await self.agent.start()
        
        if not self.agent.is_logged_in:
            return await self.agent.login()
        
        return True
    
    async def _run_resume_update(self) -> None:
        """Run resume update task."""
        logger.info("Running scheduled resume update...")
        
        try:
            if not await self._ensure_logged_in():
                logger.error("Cannot run resume update - not logged in")
                return
            
            success = await self.agent.update_resume()
            
            if success:
                logger.info("Scheduled resume update completed successfully")
            else:
                logger.warning("Scheduled resume update may have failed")
                
        except Exception as e:
            logger.error(f"Error in scheduled resume update: {e}")
    
    async def _run_recruiter_check(self) -> None:
        """Run recruiter activity check task."""
        logger.info("Running scheduled recruiter check...")
        
        try:
            if not await self._ensure_logged_in():
                logger.error("Cannot run recruiter check - not logged in")
                return
            
            activity = await self.agent.check_recruiter_activity()
            logger.info(f"Recruiter check complete: {activity}")
            
        except Exception as e:
            logger.error(f"Error in scheduled recruiter check: {e}")
    
    async def _run_job_recommendations(self) -> None:
        """Run job recommendations fetch task."""
        logger.info("Running scheduled job recommendations fetch...")
        
        try:
            if not await self._ensure_logged_in():
                logger.error("Cannot fetch jobs - not logged in")
                return
            
            jobs = await self.agent.get_job_recommendations(20)
            logger.info(f"Fetched {len(jobs)} job recommendations")
            
        except Exception as e:
            logger.error(f"Error in scheduled job recommendations: {e}")
    
    async def _run_full_check(self) -> None:
        """Run full profile check task."""
        logger.info("Running scheduled full profile check...")
        
        try:
            if not await self._ensure_logged_in():
                logger.error("Cannot run full check - not logged in")
                return
            
            summary = await self.agent.run_full_check()
            logger.info(f"Full check complete: {summary}")
            
        except Exception as e:
            logger.error(f"Error in scheduled full check: {e}")
    
    async def _send_daily_summary(self) -> None:
        """Send daily summary notification."""
        logger.info("Sending daily summary...")
        
        try:
            if not self.agent:
                logger.warning("Agent not initialized for daily summary")
                return
            
            # Get summary data from database
            summary = {
                "profile_views": 0,
                "new_messages": 0,
                "interview_requests": 0,
                "jobs_recommended": 0,
                "resume_updated": False,
                "applications": [],
            }
            
            # Get recent activities
            activities = self.agent.db.get_recent_activities(50)
            
            # Count activities by type
            for activity in activities:
                if activity.get("activity_type") == "resume_update":
                    summary["resume_updated"] = True
            
            # Get application stats
            app_stats = self.agent.db.get_application_stats()
            summary["applications_total"] = app_stats.get("total", 0)
            
            await self.agent.notifier.send_daily_summary(summary)
            logger.info("Daily summary sent")
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    async def _run_profile_health_check(self) -> None:
        """Run weekly profile health check."""
        logger.info("Running scheduled profile health check...")
        
        try:
            if not await self._ensure_logged_in():
                logger.error("Cannot run health check - not logged in")
                return
            
            performance = await self.agent.get_profile_performance()
            logger.info(f"Profile health: {performance}")
            
        except Exception as e:
            logger.error(f"Error in scheduled health check: {e}")
    
    def add_custom_job(
        self,
        func: Callable,
        trigger: str,
        job_id: str,
        **trigger_args
    ) -> None:
        """
        Add a custom job to the scheduler.
        
        Args:
            func: Function to execute
            trigger: Trigger type ('interval', 'cron', 'date')
            job_id: Unique job identifier
            **trigger_args: Trigger-specific arguments
        """
        if trigger == "interval":
            trigger_obj = IntervalTrigger(**trigger_args)
        elif trigger == "cron":
            trigger_obj = CronTrigger(**trigger_args)
        else:
            raise ValueError(f"Unsupported trigger type: {trigger}")
        
        self.scheduler.add_job(
            func,
            trigger_obj,
            id=job_id,
            replace_existing=True
        )
        logger.info(f"Added custom job: {job_id}")
    
    def remove_job(self, job_id: str) -> None:
        """Remove a scheduled job."""
        self.scheduler.remove_job(job_id)
        logger.info(f"Removed job: {job_id}")
    
    def get_job_status(self) -> list[dict]:
        """Get status of all scheduled jobs."""
        jobs = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in jobs
        ]


async def run_scheduler() -> None:
    """Run the scheduler as a daemon."""
    scheduler = Scheduler()
    
    try:
        await scheduler.start()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await scheduler.stop()
