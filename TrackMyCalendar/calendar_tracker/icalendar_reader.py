"""
iCalendar integration module
Handles parsing of .ics files and remote iCalendar feeds
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union
import logging
import hashlib

import requests
from icalendar import Calendar
from recurring_ical_events import of
import pytz

from .models import CalendarEvent, CalendarSource

logger = logging.getLogger(__name__)


class ICalendarClient:
    """Client for fetching events from iCalendar sources (.ics files)"""

    def __init__(self, sources: List[str], timezone: str = "UTC"):
        """
        Initialize iCalendar client

        Args:
            sources: List of .ics file paths or URLs
            timezone: Timezone for date calculations
        """
        self.sources = sources
        self.timezone = pytz.timezone(timezone)
        self._cached_calendars = {}
        self._cache_timeout = 300  # 5 minutes

    def get_upcoming_events(
        self, hours_ahead: int = 24, max_results: int = 50
    ) -> List[CalendarEvent]:
        """
        Fetch upcoming events from all iCalendar sources

        Args:
            hours_ahead: How many hours ahead to look
            max_results: Maximum number of events to fetch

        Returns:
            List of CalendarEvent objects
        """
        all_events = []

        for source in self.sources:
            try:
                events = self._get_events_from_source(source, hours_ahead)
                all_events.extend(events)
            except Exception as e:
                logger.error(f"Error fetching from {source}: {e}")

        # Sort by start time and limit results
        all_events.sort(key=lambda e: e.start_time)
        return all_events[:max_results]

    def _get_events_from_source(
        self, source: str, hours_ahead: int
    ) -> List[CalendarEvent]:
        """
        Fetch events from a single iCalendar source

        Args:
            source: File path or URL to .ics file
            hours_ahead: How many hours ahead to look

        Returns:
            List of CalendarEvent objects
        """
        # Load calendar data
        if source.startswith(("http://", "https://")):
            calendar_data = self._fetch_remote_calendar(source)
        else:
            calendar_data = self._load_local_calendar(source)

        if not calendar_data:
            return []

        # Parse calendar
        try:
            cal = Calendar.from_ical(calendar_data)
        except Exception as e:
            logger.error(f"Failed to parse iCalendar data from {source}: {e}")
            return []

        # Get events in time range
        now = datetime.now(self.timezone)
        end_time = now + timedelta(hours=hours_ahead)

        try:
            # Use recurring_ical_events to handle recurring events
            recurring_events = of(cal).between(now, end_time)
        except Exception as e:
            logger.warning(f"Error processing recurring events: {e}")
            recurring_events = []

        events = []
        for event in recurring_events:
            parsed = self._parse_event(event, source)
            if parsed:
                events.append(parsed)

        return events

    def _fetch_remote_calendar(self, url: str) -> Optional[bytes]:
        """
        Fetch calendar data from a remote URL

        Args:
            url: URL to the .ics file

        Returns:
            Calendar data as bytes, or None if fetch fails
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch remote calendar {url}: {e}")
            return None

    def _load_local_calendar(self, path: str) -> Optional[bytes]:
        """
        Load calendar data from a local file

        Args:
            path: Path to the .ics file

        Returns:
            Calendar data as bytes, or None if load fails
        """
        file_path = Path(path)
        if not file_path.exists():
            logger.error(f"Calendar file not found: {path}")
            return None

        try:
            return file_path.read_bytes()
        except Exception as e:
            logger.error(f"Failed to read calendar file {path}: {e}")
            return None

    def _parse_event(self, event, source: str) -> Optional[CalendarEvent]:
        """
        Parse an iCalendar event into CalendarEvent

        Args:
            event: icalendar Event object
            source: Source identifier for the calendar

        Returns:
            CalendarEvent object or None if parsing fails
        """
        try:
            # Get event properties
            uid = str(event.get("UID", ""))
            title = str(event.get("SUMMARY", "No Title"))
            description = str(event.get("DESCRIPTION", "")) if event.get("DESCRIPTION") else None
            location = str(event.get("LOCATION", "")) if event.get("LOCATION") else None

            # Generate unique ID using source hash
            source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
            event_id = f"{source_hash}_{uid}"

            # Parse times
            dtstart = event.get("DTSTART")
            dtend = event.get("DTEND")

            if not dtstart:
                return None

            start_dt = dtstart.dt
            end_dt = dtend.dt if dtend else start_dt

            # Check if all-day event (date without time)
            is_all_day = not hasattr(start_dt, "hour")

            if is_all_day:
                start_time = datetime.combine(start_dt, datetime.min.time())
                end_time = datetime.combine(end_dt, datetime.min.time())
                start_time = self.timezone.localize(start_time)
                end_time = self.timezone.localize(end_time)
            else:
                # Ensure timezone aware
                if start_dt.tzinfo is None:
                    start_time = self.timezone.localize(start_dt)
                else:
                    start_time = start_dt.astimezone(self.timezone)

                if end_dt.tzinfo is None:
                    end_time = self.timezone.localize(end_dt)
                else:
                    end_time = end_dt.astimezone(self.timezone)

            # Try to extract meeting URL from description or location
            meeting_url = None
            for text in [description, location]:
                if text:
                    # Look for common meeting URLs
                    for pattern in ["zoom.us", "meet.google.com", "teams.microsoft.com", "webex.com"]:
                        if pattern in text.lower():
                            # Extract URL
                            import re
                            urls = re.findall(r'https?://[^\s<>"]+', text)
                            for url in urls:
                                if pattern in url.lower():
                                    meeting_url = url
                                    break
                            if meeting_url:
                                break

            # Extract attendees
            attendees = []
            for attendee in event.get("ATTENDEE", []):
                if attendee:
                    email = str(attendee).replace("mailto:", "")
                    if "@" in email:
                        attendees.append(email)

            return CalendarEvent(
                id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                source=CalendarSource.ICALENDAR,
                description=description,
                location=location,
                attendees=attendees,
                meeting_url=meeting_url,
                is_all_day=is_all_day,
            )

        except Exception as e:
            logger.error(f"Error parsing iCalendar event: {e}")
            return None

    def add_source(self, source: str):
        """Add a new calendar source"""
        if source not in self.sources:
            self.sources.append(source)
            logger.info(f"Added iCalendar source: {source}")

    def remove_source(self, source: str):
        """Remove a calendar source"""
        if source in self.sources:
            self.sources.remove(source)
            logger.info(f"Removed iCalendar source: {source}")
