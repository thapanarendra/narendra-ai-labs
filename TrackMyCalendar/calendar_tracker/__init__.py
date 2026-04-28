"""
TrackMyCalendar - Calendar Tracking Agent
Monitors Google, Outlook, and iCalendar for upcoming meetings
and sends reminders via multiple notification channels.
"""

__version__ = "1.0.0"
__author__ = "TrackMyCalendar"

from .scheduler import CalendarScheduler
from .notification import NotificationManager

__all__ = ["CalendarScheduler", "NotificationManager"]
