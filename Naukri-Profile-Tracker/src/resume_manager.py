"""
Resume Manager - Handles resume upload and update operations.
"""

import asyncio
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from playwright.async_api import Page

from .config import NaukriSelectors, NaukriURLs, Settings
from .database import Database


class ResumeManager:
    """
    Manages resume operations on Naukri.com.
    
    Supports:
    - Resume file upload
    - Resume headline updates
    - Profile refresh techniques
    """
    
    # Headlines that can be used to refresh profile
    HEADLINE_VARIATIONS = [
        "Experienced {role} | {skills} | Open to New Opportunities",
        "{role} with {experience}+ Years | {skills} | Actively Seeking",
        "Passionate {role} | Expert in {skills} | Looking for Challenges",
        "{role} | {skills} | Available for Immediate Joining",
        "Results-Driven {role} | {skills} Specialist | Ready for Growth",
    ]
    
    def __init__(self, page: Page, settings: Settings, db: Database):
        """
        Initialize Resume Manager.
        
        Args:
            page: Playwright page instance
            settings: Application settings
            db: Database instance
        """
        self.page = page
        self.settings = settings
        self.db = db
    
    async def upload_resume(self) -> bool:
        """
        Upload resume file to Naukri.
        
        This refreshes the profile and increases visibility to recruiters.
        
        Returns:
            bool: True if upload successful
        """
        logger.info("Starting resume upload...")
        
        try:
            # Navigate to resume section
            await self.page.goto(NaukriURLs.RESUME, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Check if resume path exists
            resume_path = self.settings.resume_path
            if not resume_path.exists():
                logger.error(f"Resume file not found: {resume_path}")
                return False
            
            # Find file upload input
            file_input = self.page.locator(NaukriSelectors.RESUME_UPLOAD_INPUT)
            
            if await file_input.count() == 0:
                # Try alternative selector
                file_input = self.page.locator('input[type="file"]')
            
            if await file_input.count() > 0:
                # Upload the file
                await file_input.set_input_files(str(resume_path))
                logger.info(f"Resume file selected: {resume_path}")
                
                # Wait for upload to complete
                await asyncio.sleep(5)
                
                # Check for success message or confirmation
                success = await self._check_upload_success()
                
                if success:
                    logger.info("Resume uploaded successfully!")
                    self.db.log_activity(
                        "resume_update",
                        {
                            "method": "upload",
                            "file": str(resume_path),
                            "timestamp": datetime.now().isoformat()
                        }
                    )
                    return True
                else:
                    logger.warning("Resume upload may have failed - no confirmation detected")
                    return False
            else:
                logger.error("Could not find file upload input")
                return False
                
        except Exception as e:
            logger.error(f"Resume upload error: {e}")
            return False
    
    async def _check_upload_success(self) -> bool:
        """Check if resume upload was successful."""
        try:
            # Look for success message
            success_selectors = [
                NaukriSelectors.RESUME_UPDATE_SUCCESS,
                ".success-msg",
                ".upload-success",
                "[class*='success']"
            ]
            
            for selector in success_selectors:
                element = self.page.locator(selector)
                if await element.count() > 0:
                    return True
            
            # Check if page shows updated resume info
            await self.page.wait_for_timeout(2000)
            
            # Alternative: check if resume section shows recent update
            updated_text = await self.page.locator("text=/updated|uploaded/i").count()
            return updated_text > 0
            
        except:
            return False
    
    async def update_headline(self, headline: Optional[str] = None) -> bool:
        """
        Update resume headline to refresh profile.
        
        A small change to headline counts as a profile update.
        
        Args:
            headline: Custom headline text (optional)
        
        Returns:
            bool: True if update successful
        """
        logger.info("Starting headline update...")
        
        try:
            # Navigate to profile/headline section
            await self.page.goto(NaukriURLs.UPDATE_HEADLINE, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Click edit button for headline
            edit_button = self.page.locator(NaukriSelectors.RESUME_HEADLINE_EDIT)
            if await edit_button.count() > 0:
                await edit_button.click()
                await asyncio.sleep(1)
            
            # Find headline textarea
            headline_input = self.page.locator(NaukriSelectors.RESUME_HEADLINE_INPUT)
            
            if await headline_input.count() == 0:
                # Try alternatives
                headline_input = self.page.locator("textarea")
            
            if await headline_input.count() > 0:
                # Get current headline
                current_headline = await headline_input.input_value()
                logger.debug(f"Current headline: {current_headline}")
                
                # Generate new headline or use provided
                if headline:
                    new_headline = headline
                else:
                    new_headline = self._generate_refreshed_headline(current_headline)
                
                # Clear and enter new headline
                await headline_input.clear()
                await asyncio.sleep(0.5)
                await headline_input.fill(new_headline)
                await asyncio.sleep(0.5)
                
                # Save changes
                save_button = self.page.locator(NaukriSelectors.RESUME_HEADLINE_SAVE)
                if await save_button.count() > 0:
                    await save_button.click()
                else:
                    # Try generic save button
                    await self.page.locator("button[type='submit'], .save-btn").click()
                
                await asyncio.sleep(2)
                
                logger.info(f"Headline updated: {new_headline}")
                self.db.log_activity(
                    "resume_update",
                    {
                        "method": "headline",
                        "old_headline": current_headline,
                        "new_headline": new_headline,
                        "timestamp": datetime.now().isoformat()
                    }
                )
                return True
            else:
                logger.error("Could not find headline input")
                return False
                
        except Exception as e:
            logger.error(f"Headline update error: {e}")
            return False
    
    def _generate_refreshed_headline(self, current_headline: str) -> str:
        """
        Generate a slightly modified headline to refresh profile.
        
        Args:
            current_headline: Current headline text
        
        Returns:
            str: Modified headline
        """
        # Simple technique: Add/remove a period or adjust spacing
        current_headline = current_headline.strip()
        
        if current_headline.endswith("."):
            return current_headline[:-1]
        elif current_headline.endswith(" "):
            return current_headline.strip()
        else:
            # Add a trailing space or period
            return f"{current_headline}."
    
    async def get_resume_info(self) -> dict:
        """
        Get current resume information.
        
        Returns:
            dict: Resume details including last update time
        """
        try:
            await self.page.goto(NaukriURLs.RESUME, wait_until="networkidle")
            await asyncio.sleep(2)
            
            info = {
                "timestamp": datetime.now().isoformat(),
                "last_updated": None,
                "filename": None,
            }
            
            # Try to find resume info
            resume_section = self.page.locator(NaukriSelectors.RESUME_UPLOAD_SECTION)
            if await resume_section.count() > 0:
                text = await resume_section.text_content()
                # Parse the text for date and filename info
                info["raw_text"] = text
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting resume info: {e}")
            return {}
    
    async def update_with_modification(self) -> bool:
        """
        Update resume by making a slight modification to the file.
        
        This creates a new upload without changing actual content.
        
        Returns:
            bool: True if update successful
        """
        # This method modifies resume metadata for a "new" upload
        # Implementation depends on resume file format
        
        logger.info("Updating resume with modification...")
        
        # For PDF: We'll re-upload the same file as Naukri counts re-uploads
        # as profile updates
        return await self.upload_resume()
