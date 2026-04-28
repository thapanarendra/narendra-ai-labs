#!/usr/bin/env python3
"""
Quick setup script for TrackMyCalendar
Guides user through initial configuration
"""

import os
import shutil
from pathlib import Path


def main():
    print("\n" + "=" * 60)
    print("  🚀 TrackMyCalendar Setup Wizard")
    print("=" * 60)

    base_dir = Path(__file__).parent

    # Create .env if not exists
    env_file = base_dir / ".env"
    env_example = base_dir / ".env.example"

    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("\n✅ Created .env file from .env.example")

    print("\n📋 Setup Checklist:\n")

    # Check Python dependencies
    print("1️⃣  Python Dependencies")
    try:
        import google.oauth2
        import msal
        import icalendar
        import plyer
        print("   ✅ Core dependencies installed")
    except ImportError as e:
        print(f"   ❌ Missing dependencies. Run: pip install -r requirements.txt")

    # Check Google Calendar
    print("\n2️⃣  Google Calendar")
    creds_path = base_dir / "credentials.json"
    if creds_path.exists():
        print("   ✅ credentials.json found")
    else:
        print("   ⚠️  credentials.json not found")
        print("      → Download from Google Cloud Console")
        print("      → https://console.cloud.google.com/apis/credentials")

    # Check .env configuration
    print("\n3️⃣  Configuration (.env)")
    if env_file.exists():
        print("   ✅ .env file exists")

        # Read and check key settings
        with open(env_file) as f:
            content = f.read()

        checks = [
            ("ENABLE_DESKTOP_NOTIFICATIONS=true", "Desktop notifications"),
            ("OUTLOOK_CLIENT_ID=", "Outlook (optional)"),
            ("TWILIO_ACCOUNT_SID=", "SMS via Twilio (optional)"),
        ]

        for pattern, name in checks:
            if pattern in content and not content.split(pattern)[1].startswith("your_"):
                print(f"   ✅ {name} configured")
    else:
        print("   ❌ .env file not found")

    # Test commands
    print("\n4️⃣  Available Commands")
    print("   • python main.py --status    Check configuration")
    print("   • python main.py --test      Test notifications")
    print("   • python main.py --events    Show upcoming events")
    print("   • python main.py             Start the tracker")

    print("\n" + "=" * 60)
    print("  📖 See README.md for detailed setup instructions")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
