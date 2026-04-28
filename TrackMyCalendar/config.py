"""
Configuration module for TrackMyCalendar
Loads settings from environment variables and .env file
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration loaded from environment variables"""

    # Base paths
    BASE_DIR = Path(__file__).parent

    # Google Calendar settings
    GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    GOOGLE_TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "token.json")

    # Microsoft Outlook settings
    OUTLOOK_CLIENT_ID = os.getenv("OUTLOOK_CLIENT_ID", "")
    OUTLOOK_CLIENT_SECRET = os.getenv("OUTLOOK_CLIENT_SECRET", "")
    OUTLOOK_TENANT_ID = os.getenv("OUTLOOK_TENANT_ID", "common")

    # iCalendar sources (comma-separated URLs or file paths)
    ICALENDAR_SOURCES = [
        s.strip()
        for s in os.getenv("ICALENDAR_SOURCES", "").split(",")
        if s.strip()
    ]

    # Notification settings
    ENABLE_DESKTOP_NOTIFICATIONS = os.getenv("ENABLE_DESKTOP_NOTIFICATIONS", "true").lower() == "true"
    ENABLE_SMS_NOTIFICATIONS = os.getenv("ENABLE_SMS_NOTIFICATIONS", "false").lower() == "true"
    ENABLE_PUSHBULLET_NOTIFICATIONS = os.getenv("ENABLE_PUSHBULLET_NOTIFICATIONS", "false").lower() == "true"
    ENABLE_SOUND_ALERTS = os.getenv("ENABLE_SOUND_ALERTS", "true").lower() == "true"

    # Twilio SMS settings
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_TO_NUMBER = os.getenv("TWILIO_TO_NUMBER", "")

    # Pushbullet settings
    PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY", "")

    # Reminder settings (minutes before meeting)
    REMINDER_TIMES = [
        int(t.strip())
        for t in os.getenv("REMINDER_TIMES", "10,5,0").split(",")
        if t.strip()
    ]

    # Check interval in seconds
    CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))

    # Timezone
    TIMEZONE = os.getenv("TIMEZONE", "UTC")

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        warnings = []

        # Check if at least one calendar source is configured
        has_google = Path(cls.GOOGLE_CREDENTIALS_PATH).exists()
        has_outlook = bool(cls.OUTLOOK_CLIENT_ID)
        has_icalendar = bool(cls.ICALENDAR_SOURCES)

        if not (has_google or has_outlook or has_icalendar):
            warnings.append(
                "No calendar sources configured. Please set up at least one calendar."
            )

        # Check if at least one notification method is enabled
        if not (
            cls.ENABLE_DESKTOP_NOTIFICATIONS
            or cls.ENABLE_SMS_NOTIFICATIONS
            or cls.ENABLE_PUSHBULLET_NOTIFICATIONS
        ):
            warnings.append(
                "No notification methods enabled. Enable at least one notification method."
            )

        # Check SMS configuration if enabled
        if cls.ENABLE_SMS_NOTIFICATIONS:
            if not all([cls.TWILIO_ACCOUNT_SID, cls.TWILIO_AUTH_TOKEN, cls.TWILIO_FROM_NUMBER, cls.TWILIO_TO_NUMBER]):
                warnings.append(
                    "SMS notifications enabled but Twilio credentials not fully configured."
                )

        # Check Pushbullet configuration if enabled
        if cls.ENABLE_PUSHBULLET_NOTIFICATIONS:
            if not cls.PUSHBULLET_API_KEY:
                warnings.append(
                    "Pushbullet notifications enabled but API key not configured."
                )

        return warnings

    @classmethod
    def print_status(cls):
        """Print configuration status"""
        print("\n📅 TrackMyCalendar Configuration Status")
        print("=" * 50)

        # Calendar sources
        print("\n📆 Calendar Sources:")
        print(f"  • Google Calendar: {'✅ Configured' if Path(cls.GOOGLE_CREDENTIALS_PATH).exists() else '❌ Not configured'}")
        print(f"  • Outlook Calendar: {'✅ Configured' if cls.OUTLOOK_CLIENT_ID else '❌ Not configured'}")
        print(f"  • iCalendar: {'✅ ' + str(len(cls.ICALENDAR_SOURCES)) + ' source(s)' if cls.ICALENDAR_SOURCES else '❌ Not configured'}")

        # Notification methods
        print("\n🔔 Notification Methods:")
        print(f"  • Desktop: {'✅ Enabled' if cls.ENABLE_DESKTOP_NOTIFICATIONS else '❌ Disabled'}")
        print(f"  • SMS (Twilio): {'✅ Enabled' if cls.ENABLE_SMS_NOTIFICATIONS else '❌ Disabled'}")
        print(f"  • Pushbullet: {'✅ Enabled' if cls.ENABLE_PUSHBULLET_NOTIFICATIONS else '❌ Disabled'}")
        print(f"  • Sound Alerts: {'✅ Enabled' if cls.ENABLE_SOUND_ALERTS else '❌ Disabled'}")

        # Reminder settings
        print("\n⏰ Reminder Settings:")
        print(f"  • Reminder times: {cls.REMINDER_TIMES} minutes before")
        print(f"  • Check interval: Every {cls.CHECK_INTERVAL} seconds")
        print(f"  • Timezone: {cls.TIMEZONE}")

        # Warnings
        warnings = cls.validate()
        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")

        print("=" * 50)
