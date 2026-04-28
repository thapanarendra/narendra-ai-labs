# TrackMyCalendar 📅

A powerful calendar tracking agent that monitors your **Google Calendar**, **Microsoft Outlook**, and **iCalendar** feeds, sending you timely reminders via desktop notifications, SMS, or Pushbullet.

## ✨ Features

- **Multi-Calendar Support**
  - Google Calendar (via Google Calendar API)
  - Microsoft Outlook (via Microsoft Graph API)
  - iCalendar (.ics files and remote feeds)

- **Smart Reminders**
  - Configurable reminder times (default: 10 min, 5 min, at start)
  - Avoids duplicate notifications
  - Handles recurring events

- **Multiple Notification Channels**
  - 🖥️ Desktop notifications (macOS, Windows, Linux)
  - 📱 SMS via Twilio
  - 📲 Pushbullet push notifications
  - 🔊 Sound alerts

- **Easy Configuration**
  - Environment variable based
  - Single `.env` file setup

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd TrackMyCalendar
pip install -r requirements.txt
```

### 2. Configure Your Calendars

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#configuration) below).

### 3. Run the Agent

```bash
python main.py
```

## 📋 Configuration

### Google Calendar Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Calendar API**
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` and place in project root

```env
GOOGLE_CREDENTIALS_PATH=credentials.json
GOOGLE_TOKEN_PATH=token.json
```

### Microsoft Outlook Setup

1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to **Azure Active Directory** → **App registrations**
3. Create a new registration
4. Add **Calendars.Read** permission under Microsoft Graph
5. Note the Application (client) ID

```env
OUTLOOK_CLIENT_ID=your_client_id
OUTLOOK_CLIENT_SECRET=your_secret  # Optional for public clients
OUTLOOK_TENANT_ID=common
```

### iCalendar Setup

Add URLs or file paths to your .ics calendars (comma-separated):

```env
ICALENDAR_SOURCES=https://calendar.google.com/calendar/ical/xxx/basic.ics,/path/to/local.ics
```

### Notification Settings

#### Desktop Notifications (Default)
```env
ENABLE_DESKTOP_NOTIFICATIONS=true
ENABLE_SOUND_ALERTS=true
```

#### SMS via Twilio
1. Create account at [Twilio](https://www.twilio.com/)
2. Get your Account SID, Auth Token, and phone numbers

```env
ENABLE_SMS_NOTIFICATIONS=true
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_TO_NUMBER=+1234567890
```

#### Pushbullet
1. Create account at [Pushbullet](https://www.pushbullet.com/)
2. Get your API key from Settings

```env
ENABLE_PUSHBULLET_NOTIFICATIONS=true
PUSHBULLET_API_KEY=your_api_key
```

### Reminder Settings

```env
# Minutes before meeting to send reminders
REMINDER_TIMES=10,5,0

# How often to check for new events (seconds)
CHECK_INTERVAL=30

# Your timezone
TIMEZONE=America/New_York
```

## 🔧 Commands

```bash
# Run the calendar tracker
python main.py

# Check configuration status
python main.py --status

# Test notification channels
python main.py --test

# List upcoming events
python main.py --events

# Enable verbose logging
python main.py -v
```

## 📁 Project Structure

```
TrackMyCalendar/
├── main.py                 # Main entry point
├── config.py               # Configuration loader
├── requirements.txt        # Python dependencies
├── .env.example           # Example configuration
├── .env                   # Your configuration (create this)
├── credentials.json       # Google OAuth credentials
└── calendar_tracker/
    ├── __init__.py
    ├── models.py          # Data models
    ├── google_calendar.py # Google Calendar client
    ├── outlook_calendar.py # Outlook Calendar client
    ├── icalendar_reader.py # iCalendar parser
    ├── notification.py    # Notification manager
    └── scheduler.py       # Main scheduler
```

## 🏃 Running as a Background Service

### macOS (launchd)

Create `~/Library/LaunchAgents/com.trackmycalendar.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trackmycalendar</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/TrackMyCalendar/main.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/path/to/TrackMyCalendar</string>
</dict>
</plist>
```

Load the service:
```bash
launchctl load ~/Library/LaunchAgents/com.trackmycalendar.plist
```

### Linux (systemd)

Create `/etc/systemd/user/trackmycalendar.service`:

```ini
[Unit]
Description=TrackMyCalendar - Calendar Reminder Agent
After=network.target

[Service]
Type=simple
WorkingDirectory=/path/to/TrackMyCalendar
ExecStart=/usr/bin/python3 /path/to/TrackMyCalendar/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

Enable and start:
```bash
systemctl --user enable trackmycalendar
systemctl --user start trackmycalendar
```

## 🔒 Security Notes

- Never commit your `.env` file or `credentials.json`
- Store API keys and tokens securely
- The app only requests read-only calendar access

## 📝 License

MIT License - Feel free to use and modify!

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.
