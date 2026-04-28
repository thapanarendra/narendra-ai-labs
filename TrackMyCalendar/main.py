#!/usr/bin/env python3
"""
TrackMyCalendar - Calendar Reminder Agent
Main entry point for running the calendar tracker

Usage:
    python main.py              # Run with default settings
    python main.py --test       # Test notification channels
    python main.py --status     # Show configuration status
    python main.py --events     # List upcoming events
"""

import argparse
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from calendar_tracker import CalendarScheduler, NotificationManager


def setup_logging(verbose: bool = False):
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_scheduler() -> CalendarScheduler:
    """Create and configure the calendar scheduler"""
    scheduler = CalendarScheduler(
        reminder_times=Config.REMINDER_TIMES,
        check_interval=Config.CHECK_INTERVAL,
        timezone=Config.TIMEZONE,
    )

    # Set up Google Calendar if configured
    if Path(Config.GOOGLE_CREDENTIALS_PATH).exists():
        print("🔄 Setting up Google Calendar...")
        scheduler.setup_google_calendar(
            credentials_path=Config.GOOGLE_CREDENTIALS_PATH,
            token_path=Config.GOOGLE_TOKEN_PATH,
        )

    # Set up Outlook Calendar if configured
    if Config.OUTLOOK_CLIENT_ID:
        print("🔄 Setting up Outlook Calendar...")
        scheduler.setup_outlook_calendar(
            client_id=Config.OUTLOOK_CLIENT_ID,
            client_secret=Config.OUTLOOK_CLIENT_SECRET,
            tenant_id=Config.OUTLOOK_TENANT_ID,
        )

    # Set up iCalendar if configured
    if Config.ICALENDAR_SOURCES:
        print("🔄 Setting up iCalendar sources...")
        scheduler.setup_icalendar(sources=Config.ICALENDAR_SOURCES)

    # Set up notifications
    twilio_config = None
    if Config.ENABLE_SMS_NOTIFICATIONS:
        twilio_config = {
            "account_sid": Config.TWILIO_ACCOUNT_SID,
            "auth_token": Config.TWILIO_AUTH_TOKEN,
            "from_number": Config.TWILIO_FROM_NUMBER,
            "to_number": Config.TWILIO_TO_NUMBER,
        }

    scheduler.setup_notifications(
        enable_desktop=Config.ENABLE_DESKTOP_NOTIFICATIONS,
        enable_sms=Config.ENABLE_SMS_NOTIFICATIONS,
        enable_pushbullet=Config.ENABLE_PUSHBULLET_NOTIFICATIONS,
        enable_sound=Config.ENABLE_SOUND_ALERTS,
        twilio_config=twilio_config,
        pushbullet_api_key=Config.PUSHBULLET_API_KEY,
    )

    return scheduler


def test_notifications():
    """Test all configured notification channels"""
    print("\n🧪 Testing Notification Channels\n")

    twilio_config = None
    if Config.ENABLE_SMS_NOTIFICATIONS:
        twilio_config = {
            "account_sid": Config.TWILIO_ACCOUNT_SID,
            "auth_token": Config.TWILIO_AUTH_TOKEN,
            "from_number": Config.TWILIO_FROM_NUMBER,
            "to_number": Config.TWILIO_TO_NUMBER,
        }

    manager = NotificationManager(
        enable_desktop=Config.ENABLE_DESKTOP_NOTIFICATIONS,
        enable_sms=Config.ENABLE_SMS_NOTIFICATIONS,
        enable_pushbullet=Config.ENABLE_PUSHBULLET_NOTIFICATIONS,
        enable_sound=Config.ENABLE_SOUND_ALERTS,
        twilio_config=twilio_config,
        pushbullet_api_key=Config.PUSHBULLET_API_KEY,
    )

    results = manager.test_notifications()

    print("\n📊 Test Results:")
    for channel, success in results.items():
        status = "✅ Passed" if success else "❌ Failed"
        print(f"  {channel}: {status}")


def show_events():
    """Show upcoming events from all calendars"""
    print("\n📆 Fetching Upcoming Events...\n")

    scheduler = create_scheduler()
    events = scheduler.get_upcoming_events(hours=24)

    if not events:
        print("No upcoming events in the next 24 hours.")
        return

    print(f"Found {len(events)} upcoming events:\n")

    for event in events:
        print(f"{event.source_icon} {event.title}")
        print(f"   📅 {event.display_time}")
        if event.location:
            print(f"   📍 {event.location}")
        if event.meeting_url:
            print(f"   🔗 {event.meeting_url}")
        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="TrackMyCalendar - Calendar Reminder Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py              Run the calendar tracker
  python main.py --test       Test notification channels
  python main.py --status     Show configuration status
  python main.py --events     List upcoming events
  python main.py -v           Run with verbose logging
        """,
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="Test notification channels",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show configuration status",
    )
    parser.add_argument(
        "--events",
        action="store_true",
        help="List upcoming events",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.verbose)

    # Handle different modes
    if args.status:
        Config.print_status()
        return

    if args.test:
        test_notifications()
        return

    if args.events:
        show_events()
        return

    # Run the scheduler
    print("\n" + "=" * 50)
    print("  📅 TrackMyCalendar - Calendar Reminder Agent")
    print("=" * 50)

    # Validate configuration
    warnings = Config.validate()
    if warnings:
        print("\n⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
        print()

    try:
        scheduler = create_scheduler()
        scheduler.start(blocking=True)
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nPlease configure at least one calendar source and notification method.")
        print("See .env.example for configuration options.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)


if __name__ == "__main__":
    main()
