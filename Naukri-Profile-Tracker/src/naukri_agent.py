"""
Main Naukri Agent - Orchestrates all automation tasks.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from loguru import logger
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from .config import NaukriSelectors, NaukriURLs, Settings, get_settings
from .database import Database
from .job_tracker import JobTracker
from .notifier import Notifier
from .recruiter_tracker import RecruiterTracker
from .resume_manager import ResumeManager


class NaukriAgent:
    """
    Main agent class for Naukri.com automation.
    
    Handles browser automation, profile management, and activity tracking.
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """Initialize the Naukri Agent."""
        self.settings = settings or get_settings()
        self.settings.ensure_directories()
        
        self._setup_logging()
        
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.is_logged_in = False
        
        # Initialize components
        self.db = Database(self.settings.database_path)
        self.notifier = Notifier(self.settings)
        self.resume_manager: Optional[ResumeManager] = None
        self.recruiter_tracker: Optional[RecruiterTracker] = None
        self.job_tracker: Optional[JobTracker] = None
        
        logger.info("Naukri Agent initialized")
    
    def _setup_logging(self) -> None:
        """Configure logging with loguru."""
        log_file = self.settings.logs_dir / "naukri_agent.log"
        
        logger.add(
            log_file,
            rotation="10 MB",
            retention="30 days",
            level=self.settings.log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )
    
    async def start(self) -> None:
        """Start the browser and initialize components."""
        logger.info("Starting Naukri Agent browser...")
        
        playwright = await async_playwright().start()
        
        self.browser = await playwright.chromium.launch(
            headless=self.settings.headless_mode,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ]
        )
        
        # Create context with persistent storage for session management
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            storage_state=self._get_storage_state_path(),
        )
        
        # Block unnecessary resources for faster loading
        await self.context.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2}", lambda route: route.abort())
        
        self.page = await self.context.new_page()
        
        # Initialize component managers with page reference
        self.resume_manager = ResumeManager(self.page, self.settings, self.db)
        self.recruiter_tracker = RecruiterTracker(self.page, self.settings, self.db)
        self.job_tracker = JobTracker(self.page, self.settings, self.db)
        
        logger.info("Browser started successfully")
    
    def _get_storage_state_path(self) -> Optional[str]:
        """Get storage state path if it exists."""
        state_path = self.settings.browser_state_path / "state.json"
        if state_path.exists():
            return str(state_path)
        return None
    
    async def _save_storage_state(self) -> None:
        """Save browser storage state for session persistence."""
        state_path = self.settings.browser_state_path / "state.json"
        self.settings.browser_state_path.mkdir(parents=True, exist_ok=True)
        await self.context.storage_state(path=str(state_path))
        logger.debug("Browser state saved")
    
    async def login(self) -> bool:
        """
        Login to Naukri.com.
        
        Returns:
            bool: True if login successful, False otherwise.
        """
        logger.info("Attempting to login to Naukri.com...")
        
        try:
            await self.page.goto(NaukriURLs.LOGIN, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Check if already logged in
            if await self._check_if_logged_in():
                logger.info("Already logged in (session restored)")
                self.is_logged_in = True
                return True
            
            # Fill login credentials
            email_input = self.page.locator(NaukriSelectors.LOGIN_EMAIL_INPUT)
            password_input = self.page.locator(NaukriSelectors.LOGIN_PASSWORD_INPUT)
            
            await email_input.fill(self.settings.naukri_email)
            await asyncio.sleep(0.5)
            await password_input.fill(self.settings.naukri_password.get_secret_value())
            await asyncio.sleep(0.5)
            
            # Click login button
            login_button = self.page.locator(NaukriSelectors.LOGIN_SUBMIT_BUTTON)
            await login_button.click()
            
            # Wait for navigation
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # Verify login success
            if await self._check_if_logged_in():
                logger.info("Login successful!")
                self.is_logged_in = True
                await self._save_storage_state()
                
                # Log activity
                self.db.log_activity("login", {"timestamp": datetime.now().isoformat()})
                
                return True
            else:
                # Check for error message
                error = await self.page.locator(NaukriSelectors.LOGIN_ERROR_MESSAGE).text_content()
                logger.error(f"Login failed: {error}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            await self._take_screenshot("login_error")
            return False
    
    async def _check_if_logged_in(self) -> bool:
        """Check if currently logged into Naukri."""
        try:
            # Check for profile menu or user name element
            user_element = self.page.locator(NaukriSelectors.USER_NAME)
            return await user_element.count() > 0
        except:
            return False
    
    async def _take_screenshot(self, name: str) -> None:
        """Take screenshot for debugging."""
        screenshot_path = self.settings.logs_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=str(screenshot_path))
        logger.debug(f"Screenshot saved: {screenshot_path}")
    
    async def update_resume(self, method: str = "upload") -> bool:
        """
        Update resume on Naukri.com.
        
        Args:
            method: 'upload' to re-upload resume file, 'headline' to update headline
        
        Returns:
            bool: True if update successful
        """
        if not self.is_logged_in:
            logger.warning("Not logged in. Please login first.")
            return False
        
        if method == "upload":
            success = await self.resume_manager.upload_resume()
        elif method == "headline":
            success = await self.resume_manager.update_headline()
        else:
            # Alternate between methods for variety
            last_method = self.db.get_last_resume_update_method()
            if last_method == "upload":
                success = await self.resume_manager.update_headline()
            else:
                success = await self.resume_manager.upload_resume()
        
        if success:
            await self.notifier.send_notification(
                "Resume Updated",
                f"Your Naukri resume was successfully updated at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
        
        return success
    
    async def check_recruiter_activity(self) -> dict[str, Any]:
        """
        Check for recruiter activities.
        
        Returns:
            dict: Summary of recruiter activities
        """
        if not self.is_logged_in:
            logger.warning("Not logged in. Please login first.")
            return {}
        
        activity = await self.recruiter_tracker.get_activity_summary()
        
        # Check for new activities and notify
        new_views = activity.get("new_profile_views", 0)
        new_messages = activity.get("new_messages", 0)
        new_interview_requests = activity.get("new_interview_requests", 0)
        
        if new_views > 0 or new_messages > 0 or new_interview_requests > 0:
            await self.notifier.send_notification(
                "Recruiter Activity Alert!",
                f"New Profile Views: {new_views}\n"
                f"New Messages: {new_messages}\n"
                f"New Interview Requests: {new_interview_requests}"
            )
        
        return activity
    
    async def get_job_recommendations(self, limit: int = 20) -> list[dict]:
        """
        Get job recommendations based on profile.
        
        Args:
            limit: Maximum number of recommendations to fetch
        
        Returns:
            list: List of job recommendation dictionaries
        """
        if not self.is_logged_in:
            logger.warning("Not logged in. Please login first.")
            return []
        
        return await self.job_tracker.get_recommendations(limit)
    
    async def get_application_status(self) -> list[dict]:
        """
        Get status of all job applications.
        
        Returns:
            list: List of application status dictionaries
        """
        if not self.is_logged_in:
            logger.warning("Not logged in. Please login first.")
            return []
        
        return await self.job_tracker.get_applications()
    
    async def get_profile_performance(self) -> dict[str, Any]:
        """
        Get profile performance metrics.
        
        Returns:
            dict: Profile performance statistics
        """
        if not self.is_logged_in:
            logger.warning("Not logged in. Please login first.")
            return {}
        
        try:
            await self.page.goto(NaukriURLs.PROFILE_PERFORMANCE, wait_until="networkidle")
            await asyncio.sleep(2)
            
            performance = {
                "timestamp": datetime.now().isoformat(),
                "profile_views": await self._get_stat_value(NaukriSelectors.PROFILE_VIEWS_STAT),
                "search_appearances": await self._get_stat_value(NaukriSelectors.SEARCH_APPEARANCES),
                "recruiter_actions": await self._get_stat_value(NaukriSelectors.RECRUITER_ACTIONS),
            }
            
            # Store in database
            self.db.store_performance_metrics(performance)
            
            logger.info(f"Profile performance: {performance}")
            return performance
            
        except Exception as e:
            logger.error(f"Error getting profile performance: {e}")
            return {}
    
    async def _get_stat_value(self, selector: str) -> int:
        """Extract numeric stat value from element."""
        try:
            element = self.page.locator(selector)
            if await element.count() > 0:
                text = await element.first.text_content()
                # Extract number from text
                import re
                numbers = re.findall(r'\d+', text or "")
                return int(numbers[0]) if numbers else 0
        except:
            pass
        return 0
    
    async def run_full_check(self) -> dict[str, Any]:
        """
        Run a complete profile check including all activities.
        
        Returns:
            dict: Complete activity summary
        """
        logger.info("Running full profile check...")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "login_status": self.is_logged_in,
        }
        
        if not self.is_logged_in:
            login_success = await self.login()
            summary["login_status"] = login_success
            if not login_success:
                return summary
        
        # Get recruiter activity
        summary["recruiter_activity"] = await self.check_recruiter_activity()
        
        # Get profile performance
        summary["profile_performance"] = await self.get_profile_performance()
        
        # Get job recommendations
        summary["job_recommendations_count"] = len(await self.get_job_recommendations(10))
        
        # Get application status
        summary["applications"] = await self.get_application_status()
        
        logger.info(f"Full check complete: {summary}")
        
        return summary
    
    async def close(self) -> None:
        """Close browser and cleanup resources."""
        logger.info("Closing Naukri Agent...")
        
        if self.context:
            await self._save_storage_state()
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        self.db.close()
        
        logger.info("Naukri Agent closed")


async def run_agent_task(task: str = "full-check") -> dict[str, Any]:
    """
    Run a specific agent task.
    
    Args:
        task: Task to run ('resume-update', 'recruiter-check', 
              'job-recommendations', 'full-check')
    
    Returns:
        dict: Task result
    """
    agent = NaukriAgent()
    result = {}
    
    try:
        await agent.start()
        login_success = await agent.login()
        
        if not login_success:
            return {"error": "Login failed"}
        
        if task == "resume-update":
            result["resume_updated"] = await agent.update_resume()
        elif task == "recruiter-check":
            result["recruiter_activity"] = await agent.check_recruiter_activity()
        elif task == "job-recommendations":
            result["recommendations"] = await agent.get_job_recommendations()
        elif task == "full-check":
            result = await agent.run_full_check()
        else:
            result["error"] = f"Unknown task: {task}"
        
    finally:
        await agent.close()
    
    return result
