"""
Microsoft Outlook Calendar integration module
Uses Microsoft Graph API to fetch calendar events
"""

import webbrowser
from datetime import datetime, timedelta
from typing import List, Optional
import logging

import msal
import requests
import pytz

from .models import CalendarEvent, CalendarSource

logger = logging.getLogger(__name__)

# Microsoft Graph API endpoints
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"
CALENDAR_EVENTS_ENDPOINT = f"{GRAPH_API_ENDPOINT}/me/calendar/events"

# Required scopes
SCOPES = ["Calendars.Read", "User.Read"]


class OutlookCalendarClient:
    """Client for fetching events from Microsoft Outlook Calendar"""

    def __init__(
        self,
        client_id: str,
        client_secret: str = "",
        tenant_id: str = "common",
        timezone: str = "UTC",
    ):
        """
        Initialize Outlook Calendar client

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret (optional for public clients)
            tenant_id: Azure AD tenant ID (use 'common' for multi-tenant)
            timezone: Timezone for date calculations
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id
        self.timezone = pytz.timezone(timezone)
        self.access_token = None
        self._token_expiry = None

        # Configure MSAL
        authority = f"https://login.microsoftonline.com/{tenant_id}"

        if client_secret:
            self.app = msal.ConfidentialClientApplication(
                client_id,
                authority=authority,
                client_credential=client_secret,
            )
        else:
            self.app = msal.PublicClientApplication(
                client_id,
                authority=authority,
            )

        self._token_cache_file = ".outlook_token_cache.json"

    def authenticate(self) -> bool:
        """
        Authenticate with Microsoft Graph API

        Returns:
            True if authentication successful, False otherwise
        """
        try:
            # Try to get token from cache
            accounts = self.app.get_accounts()
            if accounts:
                result = self.app.acquire_token_silent(SCOPES, account=accounts[0])
                if result and "access_token" in result:
                    self.access_token = result["access_token"]
                    logger.info("Acquired Outlook token from cache")
                    return True

            # Interactive authentication
            if isinstance(self.app, msal.PublicClientApplication):
                # Device code flow for better UX
                flow = self.app.initiate_device_flow(scopes=SCOPES)
                if "user_code" not in flow:
                    logger.error(f"Failed to create device flow: {flow}")
                    return False

                print(f"\n🔐 Outlook Authentication Required")
                print(f"Please visit: {flow['verification_uri']}")
                print(f"And enter code: {flow['user_code']}")
                print("Waiting for authentication...\n")

                # Open browser for user
                webbrowser.open(flow["verification_uri"])

                result = self.app.acquire_token_by_device_flow(flow)
            else:
                # Client credentials flow for confidential clients
                result = self.app.acquire_token_for_client(scopes=SCOPES)

            if result and "access_token" in result:
                self.access_token = result["access_token"]
                logger.info("Successfully authenticated with Outlook")
                return True
            else:
                error = result.get("error_description", "Unknown error")
                logger.error(f"Outlook authentication failed: {error}")
                return False

        except Exception as e:
            logger.error(f"Outlook authentication error: {e}")
            return False

    def is_authenticated(self) -> bool:
        """Check if client has valid access token"""
        return self.access_token is not None

    def get_upcoming_events(
        self, hours_ahead: int = 24, max_results: int = 50
    ) -> List[CalendarEvent]:
        """
        Fetch upcoming events from Outlook Calendar

        Args:
            hours_ahead: How many hours ahead to look
            max_results: Maximum number of events to fetch

        Returns:
            List of CalendarEvent objects
        """
        if not self.is_authenticated():
            if not self.authenticate():
                logger.error("Not authenticated with Outlook Calendar")
                return []

        try:
            now = datetime.utcnow()
            time_min = now.isoformat() + "Z"
            time_max = (now + timedelta(hours=hours_ahead)).isoformat() + "Z"

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json",
                "Prefer": f'outlook.timezone="{self.timezone.zone}"',
            }

            params = {
                "$filter": f"start/dateTime ge '{time_min}' and start/dateTime le '{time_max}'",
                "$orderby": "start/dateTime",
                "$top": max_results,
                "$select": "id,subject,start,end,location,bodyPreview,attendees,onlineMeeting,isAllDay,webLink",
            }

            response = requests.get(
                CALENDAR_EVENTS_ENDPOINT, headers=headers, params=params
            )

            if response.status_code == 401:
                # Token expired, try to re-authenticate
                self.access_token = None
                if self.authenticate():
                    return self.get_upcoming_events(hours_ahead, max_results)
                return []

            response.raise_for_status()
            data = response.json()
            events = data.get("value", [])

            return [
                event
                for event in (self._parse_event(e) for e in events)
                if event is not None
            ]

        except requests.exceptions.RequestException as e:
            logger.error(f"Outlook API request error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching Outlook events: {e}")
            return []

    def _parse_event(self, event: dict) -> Optional[CalendarEvent]:
        """Parse an Outlook Calendar event into CalendarEvent"""
        try:
            event_id = event.get("id", "")
            title = event.get("subject", "No Title")

            # Parse start/end times
            start = event.get("start", {})
            end = event.get("end", {})

            is_all_day = event.get("isAllDay", False)

            start_str = start.get("dateTime", "")
            end_str = end.get("dateTime", "")

            if is_all_day:
                start_time = datetime.fromisoformat(start_str.split("T")[0])
                end_time = datetime.fromisoformat(end_str.split("T")[0])
                start_time = self.timezone.localize(start_time)
                end_time = self.timezone.localize(end_time)
            else:
                # Handle timezone
                start_time = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
                end_time = datetime.fromisoformat(end_str.replace("Z", "+00:00"))

                # If timezone info provided in response
                if "timeZone" in start:
                    tz = pytz.timezone(start["timeZone"])
                    if start_time.tzinfo is None:
                        start_time = tz.localize(start_time)
                    if end_time.tzinfo is None:
                        end_time = tz.localize(end_time)

                start_time = start_time.astimezone(self.timezone)
                end_time = end_time.astimezone(self.timezone)

            # Extract meeting URL
            meeting_url = None
            online_meeting = event.get("onlineMeeting")
            if online_meeting:
                meeting_url = online_meeting.get("joinUrl")

            # Extract location
            location = None
            loc_data = event.get("location", {})
            if isinstance(loc_data, dict):
                location = loc_data.get("displayName")

            # Extract attendees
            attendees = [
                att.get("emailAddress", {}).get("address", "")
                for att in event.get("attendees", [])
                if att.get("emailAddress", {}).get("address")
            ]

            return CalendarEvent(
                id=event_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                source=CalendarSource.OUTLOOK,
                description=event.get("bodyPreview"),
                location=location,
                attendees=attendees,
                meeting_url=meeting_url,
                is_all_day=is_all_day,
            )
        except Exception as e:
            logger.error(f"Error parsing Outlook event: {e}")
            return None
