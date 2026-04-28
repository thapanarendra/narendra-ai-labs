"""
Notification module for sending reminders through various channels
Supports desktop notifications, SMS (Twilio), and Pushbullet
"""

import subprocess
import sys
from typing import Optional
import logging

from .models import CalendarEvent

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages sending notifications through multiple channels"""

    def __init__(
        self,
        enable_desktop: bool = True,
        enable_sms: bool = False,
        enable_pushbullet: bool = False,
        enable_sound: bool = True,
        twilio_config: Optional[dict] = None,
        pushbullet_api_key: Optional[str] = None,
    ):
        """
        Initialize notification manager

        Args:
            enable_desktop: Enable desktop notifications
            enable_sms: Enable SMS notifications via Twilio
            enable_pushbullet: Enable Pushbullet notifications
            enable_sound: Enable sound alerts
            twilio_config: Dict with account_sid, auth_token, from_number, to_number
            pushbullet_api_key: Pushbullet API key
        """
        self.enable_desktop = enable_desktop
        self.enable_sms = enable_sms
        self.enable_pushbullet = enable_pushbullet
        self.enable_sound = enable_sound
        self.twilio_config = twilio_config or {}
        self.pushbullet_api_key = pushbullet_api_key

        # Initialize notification clients
        self._init_clients()

    def _init_clients(self):
        """Initialize notification service clients"""
        # Desktop notifications
        if self.enable_desktop:
            try:
                from plyer import notification as desktop_notifier
                self._desktop_notifier = desktop_notifier
            except ImportError:
                logger.warning("plyer not installed, desktop notifications disabled")
                self.enable_desktop = False
                self._desktop_notifier = None

        # Twilio SMS
        if self.enable_sms:
            try:
                from twilio.rest import Client as TwilioClient
                if all(self.twilio_config.get(k) for k in ["account_sid", "auth_token"]):
                    self._twilio_client = TwilioClient(
                        self.twilio_config["account_sid"],
                        self.twilio_config["auth_token"],
                    )
                else:
                    logger.warning("Twilio credentials not configured")
                    self.enable_sms = False
                    self._twilio_client = None
            except ImportError:
                logger.warning("twilio not installed, SMS notifications disabled")
                self.enable_sms = False
                self._twilio_client = None

        # Pushbullet
        if self.enable_pushbullet:
            try:
                from pushbullet import Pushbullet
                if self.pushbullet_api_key:
                    self._pushbullet = Pushbullet(self.pushbullet_api_key)
                else:
                    logger.warning("Pushbullet API key not configured")
                    self.enable_pushbullet = False
                    self._pushbullet = None
            except ImportError:
                logger.warning("pushbullet.py not installed, Pushbullet notifications disabled")
                self.enable_pushbullet = False
                self._pushbullet = None

    def send_reminder(
        self,
        event: CalendarEvent,
        minutes_until: int,
        reminder_type: str = "upcoming",
    ) -> bool:
        """
        Send reminder notification for an event

        Args:
            event: The calendar event
            minutes_until: Minutes until the event starts
            reminder_type: Type of reminder (upcoming, starting, started)

        Returns:
            True if at least one notification was sent successfully
        """
        # Build notification content
        title, message = self._build_notification_content(event, minutes_until, reminder_type)

        success = False

        # Send through all enabled channels
        if self.enable_desktop:
            if self._send_desktop_notification(title, message, event):
                success = True

        if self.enable_sms:
            if self._send_sms_notification(title, message, event):
                success = True

        if self.enable_pushbullet:
            if self._send_pushbullet_notification(title, message, event):
                success = True

        if self.enable_sound:
            self._play_sound_alert(minutes_until)

        if success:
            logger.info(f"Sent reminder for: {event.title} ({minutes_until} min)")
        else:
            logger.warning(f"Failed to send any reminder for: {event.title}")

        return success

    def _build_notification_content(
        self, event: CalendarEvent, minutes_until: int, reminder_type: str
    ) -> tuple:
        """Build notification title and message"""
        source_icon = event.source_icon

        if minutes_until == 0:
            title = f"🔔 Meeting Starting Now!"
            time_text = "starting now"
        elif minutes_until == 1:
            title = f"⏰ Meeting in 1 minute"
            time_text = "in 1 minute"
        else:
            title = f"⏰ Meeting in {minutes_until} minutes"
            time_text = f"in {minutes_until} minutes"

        # Build message
        message_parts = [f"{source_icon} {event.title}"]
        message_parts.append(f"📅 {event.display_time}")

        if event.location:
            message_parts.append(f"📍 {event.location}")

        if event.meeting_url:
            message_parts.append(f"🔗 Join: {event.meeting_url}")

        message = "\n".join(message_parts)

        return title, message

    def _send_desktop_notification(
        self, title: str, message: str, event: CalendarEvent
    ) -> bool:
        """Send desktop notification"""
        try:
            # Use macOS native notification for better experience
            if sys.platform == "darwin":
                return self._send_macos_notification(title, message, event)

            # Fallback to plyer for other platforms
            if self._desktop_notifier:
                self._desktop_notifier.notify(
                    title=title,
                    message=message,
                    app_name="TrackMyCalendar",
                    timeout=10,
                )
                return True
        except Exception as e:
            logger.error(f"Desktop notification error: {e}")
        return False

    def _send_macos_notification(
        self, title: str, message: str, event: CalendarEvent
    ) -> bool:
        """Send notification using macOS native notification center"""
        try:
            # Use AppleScript for rich notifications
            script = f'''
            display notification "{message.replace('"', '\\"').replace(chr(10), ' ')}" with title "{title.replace('"', '\\"')}" sound name "Glass"
            '''

            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True,
            )
            return True
        except Exception as e:
            logger.error(f"macOS notification error: {e}")
            # Fallback to plyer
            if self._desktop_notifier:
                try:
                    self._desktop_notifier.notify(
                        title=title,
                        message=message,
                        app_name="TrackMyCalendar",
                        timeout=10,
                    )
                    return True
                except:
                    pass
        return False

    def _send_sms_notification(
        self, title: str, message: str, event: CalendarEvent
    ) -> bool:
        """Send SMS notification via Twilio"""
        if not self._twilio_client:
            return False

        try:
            from_number = self.twilio_config.get("from_number")
            to_number = self.twilio_config.get("to_number")

            if not from_number or not to_number:
                logger.error("Twilio phone numbers not configured")
                return False

            # Build SMS message (shorter format)
            sms_message = f"{title}\n{event.title}\n{event.display_time}"
            if event.meeting_url:
                sms_message += f"\nJoin: {event.meeting_url}"

            self._twilio_client.messages.create(
                body=sms_message[:1600],  # SMS limit
                from_=from_number,
                to=to_number,
            )
            logger.info(f"SMS sent to {to_number}")
            return True
        except Exception as e:
            logger.error(f"SMS notification error: {e}")
        return False

    def _send_pushbullet_notification(
        self, title: str, message: str, event: CalendarEvent
    ) -> bool:
        """Send Pushbullet notification"""
        if not self._pushbullet:
            return False

        try:
            # Send as link if meeting URL available, otherwise as note
            if event.meeting_url:
                self._pushbullet.push_link(
                    title=title,
                    url=event.meeting_url,
                    body=message,
                )
            else:
                self._pushbullet.push_note(title=title, body=message)
            return True
        except Exception as e:
            logger.error(f"Pushbullet notification error: {e}")
        return False

    def _play_sound_alert(self, minutes_until: int):
        """Play a sound alert"""
        try:
            if sys.platform == "darwin":
                # Use macOS system sounds
                if minutes_until == 0:
                    sound = "Sosumi"  # More urgent for meeting start
                else:
                    sound = "Glass"  # Gentle for reminders

                subprocess.run(
                    ["afplay", f"/System/Library/Sounds/{sound}.aiff"],
                    capture_output=True,
                )
            elif sys.platform == "win32":
                import winsound
                winsound.MessageBeep()
            else:
                # Linux - try to use paplay or aplay
                subprocess.run(
                    ["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"],
                    capture_output=True,
                )
        except Exception as e:
            logger.debug(f"Sound alert error: {e}")

    def test_notifications(self) -> dict:
        """
        Test all enabled notification channels

        Returns:
            Dict with test results for each channel
        """
        results = {}

        # Create a test event
        from datetime import datetime
        import pytz

        test_event = CalendarEvent(
            id="test",
            title="Test Meeting",
            start_time=datetime.now(pytz.UTC),
            end_time=datetime.now(pytz.UTC),
            source=CalendarEvent.__module__,
            description="This is a test notification",
        )
        # Fix the source
        from .models import CalendarSource
        test_event.source = CalendarSource.GOOGLE

        print("\n🧪 Testing Notification Channels...")

        if self.enable_desktop:
            print("  Testing desktop notifications...")
            results["desktop"] = self._send_desktop_notification(
                "🧪 Test Notification",
                "If you see this, desktop notifications are working!",
                test_event,
            )
            print(f"  Desktop: {'✅ Working' if results['desktop'] else '❌ Failed'}")

        if self.enable_sms:
            print("  Testing SMS notifications...")
            results["sms"] = self._send_sms_notification(
                "🧪 Test SMS",
                "TrackMyCalendar SMS test",
                test_event,
            )
            print(f"  SMS: {'✅ Working' if results['sms'] else '❌ Failed'}")

        if self.enable_pushbullet:
            print("  Testing Pushbullet notifications...")
            results["pushbullet"] = self._send_pushbullet_notification(
                "🧪 Test Pushbullet",
                "TrackMyCalendar Pushbullet test",
                test_event,
            )
            print(f"  Pushbullet: {'✅ Working' if results['pushbullet'] else '❌ Failed'}")

        if self.enable_sound:
            print("  Testing sound alerts...")
            self._play_sound_alert(5)
            results["sound"] = True
            print("  Sound: ✅ Played (check if you heard it)")

        return results
