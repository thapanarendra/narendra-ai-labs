"""
Job Tracker - Handles job recommendations and application tracking.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

from loguru import logger
from playwright.async_api import Page

from .config import NaukriSelectors, NaukriURLs, Settings
from .database import Database


class JobTracker:
    """
    Tracks job recommendations and applications on Naukri.com.
    
    Features:
    - Fetch job recommendations
    - Track applied jobs
    - Monitor application status
    - Store matching jobs for review
    """
    
    def __init__(self, page: Page, settings: Settings, db: Database):
        """
        Initialize Job Tracker.
        
        Args:
            page: Playwright page instance
            settings: Application settings
            db: Database instance
        """
        self.page = page
        self.settings = settings
        self.db = db
    
    async def get_recommendations(self, limit: int = 20) -> list[dict]:
        """
        Get job recommendations based on profile.
        
        Args:
            limit: Maximum number of jobs to fetch
        
        Returns:
            list: List of job recommendation dictionaries
        """
        logger.info(f"Fetching job recommendations (limit: {limit})...")
        
        jobs = []
        
        try:
            await self.page.goto(NaukriURLs.JOB_RECOMMENDATIONS, wait_until="networkidle")
            await asyncio.sleep(3)
            
            # Scroll to load more jobs if needed
            await self._scroll_to_load_jobs(limit)
            
            # Get job cards
            job_cards = self.page.locator(NaukriSelectors.JOB_CARDS)
            count = await job_cards.count()
            
            logger.info(f"Found {count} job cards")
            
            for i in range(min(count, limit)):
                try:
                    job = await self._parse_job_card(job_cards.nth(i))
                    if job:
                        jobs.append(job)
                        # Store in database
                        self.db.store_job_recommendation(job)
                except Exception as e:
                    logger.debug(f"Error parsing job card {i}: {e}")
            
            logger.info(f"Fetched {len(jobs)} job recommendations")
            
            # Log activity
            self.db.log_activity(
                "job_recommendations_fetched",
                {"count": len(jobs), "timestamp": datetime.now().isoformat()}
            )
            
        except Exception as e:
            logger.error(f"Error fetching job recommendations: {e}")
        
        return jobs
    
    async def _scroll_to_load_jobs(self, target_count: int) -> None:
        """Scroll page to load more jobs."""
        try:
            for _ in range(min(target_count // 10, 5)):  # Max 5 scroll attempts
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(1)
        except:
            pass
    
    async def _parse_job_card(self, element) -> Optional[dict]:
        """Parse job card element to extract job details."""
        try:
            # Extract job details
            title_element = element.locator(NaukriSelectors.JOB_TITLE)
            company_element = element.locator(NaukriSelectors.JOB_COMPANY)
            location_element = element.locator(NaukriSelectors.JOB_LOCATION)
            salary_element = element.locator(NaukriSelectors.JOB_SALARY)
            experience_element = element.locator(NaukriSelectors.JOB_EXPERIENCE)
            
            job = {
                "id": f"job_{datetime.now().timestamp()}_{id(element)}",
                "title": await self._safe_get_text(title_element),
                "company": await self._safe_get_text(company_element),
                "location": await self._safe_get_text(location_element),
                "salary": await self._safe_get_text(salary_element),
                "experience": await self._safe_get_text(experience_element),
                "fetched_at": datetime.now().isoformat(),
                "status": "new",
            }
            
            # Try to get job link
            link_element = element.locator("a")
            if await link_element.count() > 0:
                job["url"] = await link_element.first.get_attribute("href")
            
            return job if job["title"] else None
            
        except Exception as e:
            logger.debug(f"Error parsing job card: {e}")
            return None
    
    async def _safe_get_text(self, element) -> str:
        """Safely get text content from element."""
        try:
            if await element.count() > 0:
                text = await element.first.text_content()
                return text.strip() if text else ""
        except:
            pass
        return ""
    
    async def get_applications(self) -> list[dict]:
        """
        Get list of applied jobs with their status.
        
        Returns:
            list: List of application dictionaries
        """
        logger.info("Fetching applied jobs...")
        
        applications = []
        
        try:
            await self.page.goto(NaukriURLs.APPLICATIONS, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Get application items
            app_items = self.page.locator(NaukriSelectors.APPLICATION_ITEMS)
            count = await app_items.count()
            
            for i in range(count):
                try:
                    app = await self._parse_application(app_items.nth(i))
                    if app:
                        applications.append(app)
                        # Update in database
                        self.db.update_application_status(app)
                except Exception as e:
                    logger.debug(f"Error parsing application {i}: {e}")
            
            logger.info(f"Found {len(applications)} applications")
            
            # Check for status changes and notify
            status_changes = self.db.get_application_status_changes()
            if status_changes:
                logger.info(f"Status changes detected: {len(status_changes)}")
            
        except Exception as e:
            logger.error(f"Error fetching applications: {e}")
        
        return applications
    
    async def _parse_application(self, element) -> Optional[dict]:
        """Parse application item element."""
        try:
            title_element = element.locator(NaukriSelectors.JOB_TITLE)
            company_element = element.locator(NaukriSelectors.JOB_COMPANY)
            status_element = element.locator(NaukriSelectors.APPLICATION_STATUS)
            date_element = element.locator(NaukriSelectors.APPLICATION_DATE)
            
            application = {
                "title": await self._safe_get_text(title_element),
                "company": await self._safe_get_text(company_element),
                "status": await self._safe_get_text(status_element),
                "applied_date": await self._safe_get_text(date_element),
                "last_checked": datetime.now().isoformat(),
            }
            
            return application if application["title"] else None
            
        except:
            return None
    
    async def apply_to_job(self, job_url: str) -> bool:
        """
        Apply to a specific job.
        
        Args:
            job_url: URL of the job to apply to
        
        Returns:
            bool: True if application successful
        """
        logger.info(f"Applying to job: {job_url}")
        
        try:
            await self.page.goto(job_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Find and click apply button
            apply_button = self.page.locator(NaukriSelectors.JOB_APPLY_BUTTON)
            
            if await apply_button.count() > 0:
                await apply_button.first.click()
                await asyncio.sleep(3)
                
                # Check if application was successful
                # This varies based on job posting type
                success = await self._check_application_success()
                
                if success:
                    logger.info("Job application submitted successfully!")
                    self.db.log_activity(
                        "job_application",
                        {"url": job_url, "timestamp": datetime.now().isoformat()}
                    )
                    return True
                else:
                    logger.warning("Application may require additional steps")
                    return False
            else:
                logger.warning("Apply button not found")
                return False
                
        except Exception as e:
            logger.error(f"Error applying to job: {e}")
            return False
    
    async def _check_application_success(self) -> bool:
        """Check if job application was successful."""
        try:
            success_indicators = [
                "text=/applied|success|submitted/i",
                ".success-message",
                ".application-success"
            ]
            
            for indicator in success_indicators:
                if await self.page.locator(indicator).count() > 0:
                    return True
            
            return False
        except:
            return False
    
    def get_matching_jobs(self, criteria: dict) -> list[dict]:
        """
        Get stored jobs matching specific criteria.
        
        Args:
            criteria: Filter criteria (title, company, location, etc.)
        
        Returns:
            list: Matching jobs from database
        """
        return self.db.search_jobs(criteria)
    
    def get_application_statistics(self) -> dict:
        """
        Get statistics about job applications.
        
        Returns:
            dict: Application statistics
        """
        return self.db.get_application_stats()
    
    async def get_saved_jobs(self) -> list[dict]:
        """
        Get jobs saved by the user on Naukri.
        
        Returns:
            list: List of saved jobs
        """
        logger.info("Fetching saved jobs...")
        
        saved_jobs = []
        
        try:
            # Navigate to saved jobs page
            await self.page.goto(f"{NaukriURLs.BASE}/mnjuser/savedjobs", wait_until="networkidle")
            await asyncio.sleep(2)
            
            job_cards = self.page.locator(NaukriSelectors.JOB_CARDS)
            count = await job_cards.count()
            
            for i in range(count):
                try:
                    job = await self._parse_job_card(job_cards.nth(i))
                    if job:
                        job["saved"] = True
                        saved_jobs.append(job)
                except:
                    pass
            
            logger.info(f"Found {len(saved_jobs)} saved jobs")
            
        except Exception as e:
            logger.error(f"Error fetching saved jobs: {e}")
        
        return saved_jobs
