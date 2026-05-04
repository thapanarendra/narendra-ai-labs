"""
Recruiter Tracker - Monitors and tracks recruiter activities.
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

from loguru import logger
from playwright.async_api import Page

from .config import NaukriSelectors, NaukriURLs, Settings
from .database import Database


class RecruiterTracker:
    """
    Tracks recruiter activities on Naukri.com profile.
    
    Monitors:
    - Profile views by recruiters
    - Messages from recruiters
    - Interview requests
    - Connection requests
    """
    
    def __init__(self, page: Page, settings: Settings, db: Database):
        """
        Initialize Recruiter Tracker.
        
        Args:
            page: Playwright page instance
            settings: Application settings
            db: Database instance
        """
        self.page = page
        self.settings = settings
        self.db = db
    
    async def get_activity_summary(self) -> dict[str, Any]:
        """
        Get a complete summary of recruiter activities.
        
        Returns:
            dict: Activity summary with counts and details
        """
        logger.info("Fetching recruiter activity summary...")
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "profile_views": await self.get_profile_views(),
            "messages": await self.get_messages(),
            "interview_requests": await self.get_interview_requests(),
            "new_profile_views": 0,
            "new_messages": 0,
            "new_interview_requests": 0,
        }
        
        # Calculate new activities by comparing with last check
        last_summary = self.db.get_last_recruiter_summary()
        
        if last_summary:
            summary["new_profile_views"] = max(0, 
                summary["profile_views"].get("total", 0) - last_summary.get("profile_views", {}).get("total", 0)
            )
            summary["new_messages"] = max(0,
                summary["messages"].get("unread", 0) - last_summary.get("messages", {}).get("unread", 0)
            )
            summary["new_interview_requests"] = max(0,
                len(summary["interview_requests"].get("pending", [])) - len(last_summary.get("interview_requests", {}).get("pending", []))
            )
        
        # Store current summary
        self.db.store_recruiter_summary(summary)
        
        logger.info(f"Recruiter activity: Views={summary['profile_views'].get('total', 0)}, "
                   f"Messages={summary['messages'].get('unread', 0)}, "
                   f"Interview Requests={len(summary['interview_requests'].get('pending', []))}")
        
        return summary
    
    async def get_profile_views(self) -> dict[str, Any]:
        """
        Get profile view statistics.
        
        Returns:
            dict: Profile view details
        """
        views = {
            "total": 0,
            "today": 0,
            "this_week": 0,
            "recruiters": []
        }
        
        try:
            await self.page.goto(NaukriURLs.RECRUITER_ACTIVITY, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Get total views count
            view_count_element = self.page.locator(NaukriSelectors.RECRUITER_VIEW_COUNT)
            if await view_count_element.count() > 0:
                text = await view_count_element.first.text_content()
                views["total"] = self._extract_number(text)
            
            # Get list of recruiters who viewed
            recruiter_items = self.page.locator(NaukriSelectors.RECRUITER_VIEW_LIST)
            count = await recruiter_items.count()
            
            for i in range(min(count, 10)):  # Limit to 10 for performance
                try:
                    item = recruiter_items.nth(i)
                    recruiter_info = await self._parse_recruiter_view(item)
                    if recruiter_info:
                        views["recruiters"].append(recruiter_info)
                except Exception as e:
                    logger.debug(f"Error parsing recruiter view item: {e}")
            
            logger.info(f"Profile views: {views['total']} total")
            
        except Exception as e:
            logger.error(f"Error fetching profile views: {e}")
        
        return views
    
    async def _parse_recruiter_view(self, element) -> Optional[dict]:
        """Parse recruiter view item element."""
        try:
            name_element = element.locator(".recruiter-name, .name")
            company_element = element.locator(".company-name, .company")
            time_element = element.locator(".view-time, .time")
            
            return {
                "name": await name_element.text_content() if await name_element.count() > 0 else "Unknown",
                "company": await company_element.text_content() if await company_element.count() > 0 else "Unknown",
                "viewed_at": await time_element.text_content() if await time_element.count() > 0 else "Unknown",
            }
        except:
            return None
    
    async def get_messages(self) -> dict[str, Any]:
        """
        Get messages from recruiters.
        
        Returns:
            dict: Message statistics and recent messages
        """
        messages = {
            "total": 0,
            "unread": 0,
            "recent": []
        }
        
        try:
            await self.page.goto(NaukriURLs.MESSAGES, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Get message count
            message_count_element = self.page.locator(NaukriSelectors.RECRUITER_MESSAGE_COUNT)
            if await message_count_element.count() > 0:
                text = await message_count_element.first.text_content()
                messages["unread"] = self._extract_number(text)
            
            # Get recent messages
            message_items = self.page.locator(NaukriSelectors.RECRUITER_MESSAGES)
            count = await message_items.count()
            
            for i in range(min(count, 5)):  # Latest 5 messages
                try:
                    item = message_items.nth(i)
                    message_info = await self._parse_message(item)
                    if message_info:
                        messages["recent"].append(message_info)
                except Exception as e:
                    logger.debug(f"Error parsing message item: {e}")
            
            messages["total"] = count
            logger.info(f"Messages: {messages['unread']} unread")
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
        
        return messages
    
    async def _parse_message(self, element) -> Optional[dict]:
        """Parse message item element."""
        try:
            sender_element = element.locator(".sender-name, .from")
            subject_element = element.locator(".subject, .msg-subject")
            time_element = element.locator(".msg-time, .time")
            unread_element = element.locator(".unread, .new")
            
            return {
                "sender": await sender_element.text_content() if await sender_element.count() > 0 else "Unknown",
                "subject": await subject_element.text_content() if await subject_element.count() > 0 else "",
                "time": await time_element.text_content() if await time_element.count() > 0 else "",
                "is_unread": await unread_element.count() > 0,
            }
        except:
            return None
    
    async def get_interview_requests(self) -> dict[str, Any]:
        """
        Get interview requests from recruiters.
        
        Returns:
            dict: Interview request details
        """
        requests = {
            "pending": [],
            "responded": [],
            "total": 0
        }
        
        try:
            # Interview requests may be in messages or a separate section
            await self.page.goto(NaukriURLs.RECRUITER_ACTIVITY, wait_until="networkidle")
            await asyncio.sleep(2)
            
            interview_items = self.page.locator(NaukriSelectors.INTERVIEW_REQUESTS)
            count = await interview_items.count()
            
            for i in range(count):
                try:
                    item = interview_items.nth(i)
                    request_info = await self._parse_interview_request(item)
                    if request_info:
                        if request_info.get("status") == "pending":
                            requests["pending"].append(request_info)
                        else:
                            requests["responded"].append(request_info)
                except Exception as e:
                    logger.debug(f"Error parsing interview request: {e}")
            
            requests["total"] = len(requests["pending"]) + len(requests["responded"])
            logger.info(f"Interview requests: {len(requests['pending'])} pending")
            
        except Exception as e:
            logger.error(f"Error fetching interview requests: {e}")
        
        return requests
    
    async def _parse_interview_request(self, element) -> Optional[dict]:
        """Parse interview request element."""
        try:
            company_element = element.locator(".company-name, .company")
            role_element = element.locator(".job-title, .role")
            date_element = element.locator(".interview-date, .date")
            status_element = element.locator(".status")
            
            status_text = await status_element.text_content() if await status_element.count() > 0 else ""
            
            return {
                "company": await company_element.text_content() if await company_element.count() > 0 else "Unknown",
                "role": await role_element.text_content() if await role_element.count() > 0 else "Unknown",
                "date": await date_element.text_content() if await date_element.count() > 0 else "",
                "status": "pending" if "pending" in status_text.lower() else "responded",
            }
        except:
            return None
    
    def _extract_number(self, text: str) -> int:
        """Extract number from text string."""
        import re
        if not text:
            return 0
        numbers = re.findall(r'\d+', text)
        return int(numbers[0]) if numbers else 0
    
    async def get_recruiter_details(self, recruiter_name: str) -> Optional[dict]:
        """
        Get details about a specific recruiter.
        
        Args:
            recruiter_name: Name of the recruiter
        
        Returns:
            dict: Recruiter details if found
        """
        # This would navigate to recruiter profile if available
        # For now, return from stored data
        return self.db.get_recruiter_info(recruiter_name)
    
    async def get_activity_trend(self, days: int = 7) -> list[dict]:
        """
        Get activity trend over specified days.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            list: Daily activity breakdown
        """
        return self.db.get_activity_trend(days)
