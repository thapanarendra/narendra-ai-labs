"""
Google Calendar integration module
Handles authentication and event fetching from Google Calendar
"""

import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pytz

from .models import CalendarEvent, CalendarSource

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


class GoogleCalendarClient:
    """Client for fetching events from Google Calendar"""

    def __init__(self, credentials_path: str, token_path: str, timezone: str = "UTC"):
        """
        Initialize Google Calendar client

        Args:
            credentials_path: Path to OAuth2 credentials.json file
            token_path: Path to store/load token.json
            timezone: Timezone for date calculations
        """
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.timezone = pytz.timezone(timezone)
        self.service = None
        self._authenticated = False

    def authenticate(self) -> bool:
        """
        Authenticate with Google Calendar API

        Returns:
            True if authentication successful, False otherwise
        """
        creds = None

        # Load existing token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(self.token_path), SCOPES)
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")

        # Check if credentials are valid
        if creds and creds.valid:
            self._authenticated = True
        elif creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._authenticated = True
            except Exception as e:
                logger.warning(f"Failed to refresh token: {e}")
                creds = None

        # Need new credentials
        if not creds or not creds.valid:
            if not self.credentials_path.exists():
                logger.error(f"Credentials file not found: {self.credentials_path}")
                return False

            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.credentials_path), SCOPES
                )
                creds = flow.run_local_server(port=0)
                self._authenticated = True

                # Save the token
                with open(self.token_path, "w") as token:
                    token.write(creds.to_json())
                logger.info("Successfully authenticated with Google Calendar")
            except Exception as e:
                logger.error(f"Failed to authenticate: {e}")
                return False

        # Build the service
        try:
            self.service = build("calendar", "v3", credentials=creds)
            return True
        except Exception as e:
            logger.error(f"Failed to build service: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self._authenticated and self.service is not None

    def get_upcoming_events(
        self, hours_ahead: int = 24, max_results: int = 50
    ) -> List[CalendarEvent]:
        """
        Fetch upcoming events from Google Calendar

        Args:
            hours_ahead: How many hours ahead to look
            max_results: Maximum number of events to fetch

        Returns:
            List of CalendarEvent objects
        """
        if not self.is_authenticated():
            if not self.authenticate():
                logger.error("Not authenticated with Google Calendar")
                return []

        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(hours=hours_ahead)).isoformat() + "Z"

            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            return [self._parse_event(event) for event in events if event]

        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Google Calendar events: {e}")
            return []

    def _parse_event(self, event: dict) -> Optional[CalendarEvent]:
        """Parse a Google Calendar event into CalendarEvent"""
        try:
            event_id = event.get("id", "")
            title = event.get("summary", "No Title")

            # Parse start/end times
            start = event.get("start", {})
            end = event.get("end", {})

            is_all_day = "date" in start and "dateTime" not in start

            if is_all_day:
                start_time = datetime.strptime(start["date"], "%Y-%m-%d")
                end_time = datetime.strptime(end["date"], "%Y-%m-%d")
                start_time = self.timezone.localize(start_time)
                end_time = self.timezone.localize(end_time)
            else:
                start_time = datetime.fromisoformat(
                    start.get("dateTime", "").replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    end.get("dateTime", "").replace("Z", "+00:00")
                )
                start_time = start_time.astimezone(self.timezone)
                end_time = end_time.astimezone(self.timezone)

            # Extract meeting URL
            meeting_url = None
            if "hangoutLink" in event:
                meeting_url = event["hangoutLink"]
            elif "conferenceData" in event:
                entry_points = event["conferenceData"].get("entryPoints", [])
                for ep in entry_points:
                    if ep.get("entryPointType") == "video":
                        meeting_url = ep.get("uri")
                        break

            # Extract attendees
            attendees = [
                att.get("email", "")
                for att in event.get("attendees", [])
                if att.get("email")
            ]

            return CalendarEvent(
                id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                source=CalendarSource.GOOGLE,
                description=event.get("description"),
                location=event.get("location"),
                attendees=attendees,
                meeting_url=meeting_url,
                is_all_day=is_all_day,
            )
        except Exception as e:
            logger.error(f"Error parsing Google Calendar event: {e}")
            return None

    def get_calendars(self) -> List[dict]:
        """Get list of available calendars"""
        if not self.is_authenticated():
            if not self.authenticate():
                return []

        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get("items", [])
        except Exception as e:
            logger.error(f"Error fetching calendar list: {e}")
            return []
