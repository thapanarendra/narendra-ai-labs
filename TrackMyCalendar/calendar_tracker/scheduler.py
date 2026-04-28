"""
Calendar Scheduler module
Monitors calendars and triggers reminders at specified times
"""

import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
import logging

import pytz

from .models import CalendarEvent, CalendarSource
from .google_calendar import GoogleCalendarClient
from .outlook_calendar import OutlookCalendarClient
from .icalendar_reader import ICalendarClient
from .notification import NotificationManager

logger = logging.getLogger(__name__)


class CalendarScheduler:
    """
    Main scheduler that monitors calendars and sends reminders
    """

    def __init__(
        self,
        reminder_times: List[int] = None,
        check_interval: int = 30,
        timezone: str = "UTC",
    ):
        """
        Initialize the calendar scheduler

        Args:
            reminder_times: List of minutes before meeting to send reminders
            check_interval: How often to check for upcoming meetings (seconds)
            timezone: Timezone for calculations
        """
        self.reminder_times = sorted(reminder_times or [10, 5, 0], reverse=True)
        self.check_interval = check_interval
        self.timezone = pytz.timezone(timezone)

        # Calendar clients
        self.google_client: Optional[GoogleCalendarClient] = None
        self.outlook_client: Optional[OutlookCalendarClient] = None
        self.icalendar_client: Optional[ICalendarClient] = None

        # Notification manager
        self.notification_manager: Optional[NotificationManager] = None

        # Track sent reminders to avoid duplicates
        # Key: (event_id, source, minutes_before)
        self._sent_reminders: Set[tuple] = set()

        # Running state
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Events cache
        self._events_cache: List[CalendarEvent] = []
        self._last_fetch = None
        self._fetch_interval = 300  # Fetch new events every 5 minutes

    def setup_google_calendar(
        self, credentials_path: str, token_path: str
    ) -> bool:
        """
        Set up Google Calendar integration

        Args:
            credentials_path: Path to credentials.json
            token_path: Path to store token.json

        Returns:
            True if setup successful
        """
        try:
            self.google_client = GoogleCalendarClient(
                credentials_path=credentials_path,
                token_path=token_path,
                timezone=self.timezone.zone,
            )
            if self.google_client.authenticate():
                logger.info("✅ Google Calendar connected")
                return True
            else:
                logger.error("❌ Google Calendar authentication failed")
                return False
        except Exception as e:
            logger.error(f"Google Calendar setup error: {e}")
            return False

    def setup_outlook_calendar(
        self,
        client_id: str,
        client_secret: str = "",
        tenant_id: str = "common",
    ) -> bool:
        """
        Set up Outlook Calendar integration

        Args:
            client_id: Azure AD application client ID
            client_secret: Azure AD application client secret
            tenant_id: Azure AD tenant ID

        Returns:
            True if setup successful
        """
        try:
            self.outlook_client = OutlookCalendarClient(
                client_id=client_id,
                client_secret=client_secret,
                tenant_id=tenant_id,
                timezone=self.timezone.zone,
            )
            if self.outlook_client.authenticate():
                logger.info("✅ Outlook Calendar connected")
                return True
            else:
                logger.error("❌ Outlook Calendar authentication failed")
                return False
        except Exception as e:
            logger.error(f"Outlook Calendar setup error: {e}")
            return False

    def setup_icalendar(self, sources: List[str]) -> bool:
        """
        Set up iCalendar integration

        Args:
            sources: List of .ics file paths or URLs

        Returns:
            True if setup successful
        """
        try:
            self.icalendar_client = ICalendarClient(
                sources=sources,
                timezone=self.timezone.zone,
            )
            logger.info(f"✅ iCalendar configured with {len(sources)} source(s)")
            return True
        except Exception as e:
            logger.error(f"iCalendar setup error: {e}")
            return False

    def setup_notifications(
        self,
        enable_desktop: bool = True,
        enable_sms: bool = False,
        enable_pushbullet: bool = False,
        enable_sound: bool = True,
        twilio_config: Optional[dict] = None,
        pushbullet_api_key: Optional[str] = None,
    ):
        """
        Set up notification channels

        Args:
            enable_desktop: Enable desktop notifications
            enable_sms: Enable SMS notifications
            enable_pushbullet: Enable Pushbullet notifications
            enable_sound: Enable sound alerts
            twilio_config: Twilio configuration dict
            pushbullet_api_key: Pushbullet API key
        """
        self.notification_manager = NotificationManager(
            enable_desktop=enable_desktop,
            enable_sms=enable_sms,
            enable_pushbullet=enable_pushbullet,
            enable_sound=enable_sound,
            twilio_config=twilio_config,
            pushbullet_api_key=pushbullet_api_key,
        )
        logger.info("✅ Notification manager configured")

    def fetch_all_events(self, hours_ahead: int = 24) -> List[CalendarEvent]:
        """
        Fetch events from all configured calendars

        Args:
            hours_ahead: How many hours ahead to look

        Returns:
            Combined list of events from all sources
        """
        all_events = []

        # Google Calendar
        if self.google_client and self.google_client.is_authenticated():
            try:
                events = self.google_client.get_upcoming_events(hours_ahead)
                all_events.extend(events)
                logger.debug(f"Fetched {len(events)} events from Google Calendar")
            except Exception as e:
                logger.error(f"Error fetching Google events: {e}")

        # Outlook Calendar
        if self.outlook_client and self.outlook_client.is_authenticated():
            try:
                events = self.outlook_client.get_upcoming_events(hours_ahead)
                all_events.extend(events)
                logger.debug(f"Fetched {len(events)} events from Outlook Calendar")
            except Exception as e:
                logger.error(f"Error fetching Outlook events: {e}")

        # iCalendar
        if self.icalendar_client:
            try:
                events = self.icalendar_client.get_upcoming_events(hours_ahead)
                all_events.extend(events)
                logger.debug(f"Fetched {len(events)} events from iCalendar")
            except Exception as e:
                logger.error(f"Error fetching iCalendar events: {e}")

        # Sort by start time
        all_events.sort(key=lambda e: e.start_time)

        # Update cache
        self._events_cache = all_events
        self._last_fetch = datetime.now(self.timezone)

        return all_events

    def check_and_send_reminders(self):
        """
        Check for upcoming events and send reminders as needed
        """
        now = datetime.now(self.timezone)

        # Refresh events if needed
        if (
            self._last_fetch is None
            or (now - self._last_fetch).total_seconds() > self._fetch_interval
        ):
            self.fetch_all_events()

        for event in self._events_cache:
            # Skip all-day events
            if event.is_all_day:
                continue

            # Calculate minutes until event
            time_diff = event.start_time - now
            minutes_until = time_diff.total_seconds() / 60

            # Check each reminder time
            for reminder_minutes in self.reminder_times:
                # Create unique key for this reminder
                reminder_key = (
                    event.id,
                    event.source.value,
                    event.start_time.isoformat(),
                    reminder_minutes,
                )

                # Skip if already sent
                if reminder_key in self._sent_reminders:
                    continue

                # Check if it's time to send this reminder
                # We send the reminder if we're within the window
                # (reminder_minutes - 1) to (reminder_minutes + 0.5)
                if reminder_minutes - 1 <= minutes_until <= reminder_minutes + 0.5:
                    if self._send_reminder(event, reminder_minutes):
                        self._sent_reminders.add(reminder_key)

                # Also trigger if we missed the window but event hasn't started
                # and this reminder hasn't been sent
                elif minutes_until < reminder_minutes and minutes_until > -1:
                    # Check if any later reminder was already sent
                    later_sent = any(
                        (event.id, event.source.value, event.start_time.isoformat(), m)
                        in self._sent_reminders
                        for m in self.reminder_times
                        if m < reminder_minutes
                    )
                    if not later_sent:
                        if self._send_reminder(event, int(minutes_until)):
                            self._sent_reminders.add(reminder_key)

        # Clean up old reminders (events that have passed)
        self._cleanup_old_reminders()

    def _send_reminder(self, event: CalendarEvent, minutes_until: int) -> bool:
        """
        Send a reminder for an event

        Args:
            event: The calendar event
            minutes_until: Minutes until the event

        Returns:
            True if reminder sent successfully
        """
        if not self.notification_manager:
            logger.error("Notification manager not configured")
            return False

        # Determine reminder type
        if minutes_until <= 0:
            reminder_type = "started"
        elif minutes_until <= 2:
            reminder_type = "starting"
        else:
            reminder_type = "upcoming"

        return self.notification_manager.send_reminder(
            event=event,
            minutes_until=max(0, minutes_until),
            reminder_type=reminder_type,
        )

    def _cleanup_old_reminders(self):
        """Remove reminders for past events"""
        now = datetime.now(self.timezone)
        cutoff = now - timedelta(hours=1)

        # Get current event IDs
        current_event_ids = {
            (e.id, e.source.value, e.start_time.isoformat())
            for e in self._events_cache
            if e.start_time > cutoff
        }

        # Filter sent reminders
        self._sent_reminders = {
            r for r in self._sent_reminders
            if (r[0], r[1], r[2]) in current_event_ids
        }

    def start(self, blocking: bool = True):
        """
        Start the scheduler

        Args:
            blocking: If True, blocks the main thread. If False, runs in background.
        """
        if self._running:
            logger.warning("Scheduler is already running")
            return

        if not self.notification_manager:
            raise ValueError("Notification manager not configured. Call setup_notifications() first.")

        has_calendar = any([
            self.google_client and self.google_client.is_authenticated(),
            self.outlook_client and self.outlook_client.is_authenticated(),
            self.icalendar_client,
        ])

        if not has_calendar:
            raise ValueError("No calendar sources configured. Set up at least one calendar.")

        self._running = True
        logger.info("🚀 Calendar scheduler started")
        print("\n" + "=" * 50)
        print("📅 TrackMyCalendar is now running!")
        print(f"⏰ Checking every {self.check_interval} seconds")
        print(f"🔔 Reminders at: {self.reminder_times} minutes before")
        print("=" * 50)
        print("\nPress Ctrl+C to stop\n")

        if blocking:
            self._run_loop()
        else:
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def _run_loop(self):
        """Main scheduler loop"""
        try:
            # Initial fetch
            events = self.fetch_all_events()
            print(f"📆 Found {len(events)} upcoming events")

            if events:
                print("\nUpcoming events:")
                for event in events[:5]:  # Show first 5
                    print(f"  • {event.title} - {event.display_time}")
                if len(events) > 5:
                    print(f"  ... and {len(events) - 5} more")
            print()

            while self._running:
                try:
                    self.check_and_send_reminders()
                except Exception as e:
                    logger.error(f"Error in check loop: {e}")

                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n👋 Stopping scheduler...")
        finally:
            self._running = False
            logger.info("Scheduler stopped")

    def stop(self):
        """Stop the scheduler"""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """
        Get list of upcoming events

        Args:
            hours: How many hours ahead to look

        Returns:
            List of upcoming events
        """
        return self.fetch_all_events(hours)

    def print_status(self):
        """Print current scheduler status"""
        print("\n📊 Scheduler Status")
        print("=" * 40)
        print(f"Running: {'✅ Yes' if self._running else '❌ No'}")
        print(f"Check interval: {self.check_interval} seconds")
        print(f"Reminder times: {self.reminder_times} minutes")
        print(f"Timezone: {self.timezone.zone}")

        print("\n📆 Calendar Sources:")
        print(f"  Google: {'✅ Connected' if self.google_client and self.google_client.is_authenticated() else '❌ Not connected'}")
        print(f"  Outlook: {'✅ Connected' if self.outlook_client and self.outlook_client.is_authenticated() else '❌ Not connected'}")
        print(f"  iCalendar: {'✅ Configured' if self.icalendar_client else '❌ Not configured'}")

        print(f"\n📬 Cached events: {len(self._events_cache)}")
        print(f"🔔 Reminders sent: {len(self._sent_reminders)}")
        print("=" * 40)
