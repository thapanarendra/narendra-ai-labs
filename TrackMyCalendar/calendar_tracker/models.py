"""
Data models for calendar events
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum


class CalendarSource(Enum):
    """Enum representing calendar sources"""
    GOOGLE = "google"
    OUTLOOK = "outlook"
    ICALENDAR = "icalendar"


@dataclass
class CalendarEvent:
    """Represents a calendar event from any source"""
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    source: CalendarSource
    description: Optional[str] = None
    location: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    meeting_url: Optional[str] = None
    is_all_day: bool = False
    reminder_sent: dict = field(default_factory=dict)  # {minutes: bool}

    def __hash__(self):
        """Make event hashable for set operations"""
        return hash((self.id, self.source.value, self.start_time.isoformat()))

    def __eq__(self, other):
        """Compare events"""
        if not isinstance(other, CalendarEvent):
            return False
        return (
            self.id == other.id
            and self.source == other.source
            and self.start_time == other.start_time
        )

    @property
    def display_time(self) -> str:
        """Format start time for display"""
        if self.is_all_day:
            return self.start_time.strftime("%A, %B %d, %Y")
        return self.start_time.strftime("%I:%M %p on %A, %B %d")

    @property
    def source_icon(self) -> str:
        """Get icon for the calendar source"""
        icons = {
            CalendarSource.GOOGLE: "📅",
            CalendarSource.OUTLOOK: "📧",
            CalendarSource.ICALENDAR: "📆",
        }
        return icons.get(self.source, "📅")

    def to_dict(self) -> dict:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "source": self.source.value,
            "description": self.description,
            "location": self.location,
            "attendees": self.attendees,
            "meeting_url": self.meeting_url,
            "is_all_day": self.is_all_day,
        }
