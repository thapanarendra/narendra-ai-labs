"""
Action item extraction for the Meeting Intelligence Agent.
Extracts tasks, deadlines, and assignments from meeting transcripts.
"""
import os
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


class Priority(Enum):
    """Action item priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionStatus(Enum):
    """Action item status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    BLOCKED = "blocked"


@dataclass
class ActionItem:
    """A task or action item extracted from a meeting."""
    id: str
    description: str
    assignee: Optional[str] = None
    deadline: Optional[datetime] = None
    priority: Priority = Priority.MEDIUM
    status: ActionStatus = ActionStatus.TODO
    source_quote: str = ""
    timestamp: float = 0.0
    meeting_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'description': self.description,
            'assignee': self.assignee,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'priority': self.priority.value,
            'status': self.status.value,
            'source_quote': self.source_quote,
            'timestamp': self.timestamp,
            'meeting_id': self.meeting_id,
            'created_at': self.created_at.isoformat(),
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            description=data['description'],
            assignee=data.get('assignee'),
            deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
            priority=Priority(data.get('priority', 'medium')),
            status=ActionStatus(data.get('status', 'todo')),
            source_quote=data.get('source_quote', ''),
            timestamp=data.get('timestamp', 0.0),
            meeting_id=data.get('meeting_id', ''),
            created_at=datetime.fromisoformat(data['created_at']) if 'created_at' in data else datetime.now(),
            tags=data.get('tags', [])
        )
    
    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        parts = [f"- [ ] **{self.description}**"]
        
        if self.assignee:
            parts.append(f"  - Assignee: {self.assignee}")
        if self.deadline:
            parts.append(f"  - Deadline: {self.deadline.strftime('%Y-%m-%d')}")
        if self.priority != Priority.MEDIUM:
            parts.append(f"  - Priority: {self.priority.value}")
        if self.source_quote:
            parts.append(f"  - Context: \"{self.source_quote[:100]}...\"")
        
        return "\n".join(parts)


class ActionExtractor:
    """
    Extracts action items from meeting transcripts using AI.
    """
    
    SYSTEM_PROMPT = """You are an expert at identifying action items, tasks, and commitments in meeting transcripts.

Extract ALL action items mentioned in the transcript. An action item is:
- A task someone commits to do
- A follow-up action discussed
- A deadline or timeline mentioned
- A decision that requires action
- Something someone says they "will", "should", "need to", or "have to" do

For each action item, identify:
1. Description: Clear, actionable description of the task
2. Assignee: Who is responsible (if mentioned, or "Unassigned")
3. Deadline: When it should be done (parse relative dates like "by Friday" to actual dates)
4. Priority: low, medium, high, or critical based on urgency language
5. Source quote: The exact quote where this was mentioned
6. Tags: Relevant categories or topics

Output as JSON array:
[
  {
    "description": "Task description",
    "assignee": "Person name or null",
    "deadline": "YYYY-MM-DD or null",
    "priority": "low|medium|high|critical",
    "source_quote": "Exact quote from transcript",
    "tags": ["tag1", "tag2"]
  }
]"""

    # Patterns for rule-based extraction (fallback)
    ACTION_PATTERNS = [
        r"(?:I'll|I will|I'm going to|Let me)\s+(.+?)(?:\.|$)",
        r"(?:need to|have to|should|must|gonna)\s+(.+?)(?:\.|$)",
        r"(?:action item[:\s]+)(.+?)(?:\.|$)",
        r"(?:TODO[:\s]+)(.+?)(?:\.|$)",
        r"(?:follow up on|follow-up[:\s]+)(.+?)(?:\.|$)",
        r"(?:by|before)\s+(monday|tuesday|wednesday|thursday|friday|tomorrow|next week).+?(?:\.|$)",
    ]
    
    DEADLINE_PATTERNS = [
        (r"by\s+tomorrow", 1),
        (r"by\s+end\s+of\s+day", 0),
        (r"by\s+end\s+of\s+week", None),  # Calculate to Friday
        (r"by\s+(monday|tuesday|wednesday|thursday|friday)", None),
        (r"by\s+(\d{1,2}/\d{1,2})", None),
        (r"in\s+(\d+)\s+days?", None),
        (r"next\s+week", 7),
    ]
    
    PRIORITY_KEYWORDS = {
        Priority.CRITICAL: ["urgent", "critical", "asap", "immediately", "right away", "emergency"],
        Priority.HIGH: ["important", "high priority", "soon", "priority", "crucial"],
        Priority.LOW: ["when you can", "low priority", "eventually", "sometime", "if possible"],
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        action_keywords: Optional[List[str]] = None
    ):
        """
        Initialize the action extractor.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
            action_keywords: Additional keywords that indicate action items
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.action_keywords = action_keywords or []
        
        self._client = None
        if HAS_OPENAI and self.api_key:
            self._client = OpenAI(api_key=self.api_key)
        
        self._action_count = 0
    
    def extract(
        self,
        transcript: str,
        meeting_id: str = "",
        participants: Optional[List[str]] = None,
        use_ai: bool = True
    ) -> List[ActionItem]:
        """
        Extract action items from transcript.
        
        Args:
            transcript: Meeting transcript text
            meeting_id: Meeting identifier
            participants: List of participant names for assignee matching
            use_ai: Whether to use AI extraction (falls back to rules if False)
            
        Returns:
            List of ActionItem objects
        """
        if use_ai and self._client:
            try:
                return self._extract_with_ai(transcript, meeting_id, participants)
            except Exception as e:
                logger.warning(f"AI extraction failed, falling back to rules: {e}")
        
        return self._extract_with_rules(transcript, meeting_id)
    
    def _extract_with_ai(
        self,
        transcript: str,
        meeting_id: str,
        participants: Optional[List[str]]
    ) -> List[ActionItem]:
        """Extract using AI."""
        # Build prompt
        prompt = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n\n"
        
        if participants:
            prompt += f"Meeting participants: {', '.join(participants)}\n\n"
        
        prompt += f"Transcript:\n{transcript}\n\nExtract all action items."
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2
        )
        
        # Parse response
        content = response.choices[0].message.content
        
        # Handle both array and object with 'actions' key
        result = json.loads(content)
        if isinstance(result, dict):
            items_data = result.get('actions', result.get('action_items', []))
        else:
            items_data = result
        
        actions = []
        for item in items_data:
            self._action_count += 1
            
            # Parse deadline
            deadline = None
            if item.get('deadline'):
                try:
                    deadline = datetime.fromisoformat(item['deadline'])
                except:
                    deadline = self._parse_deadline(item['deadline'])
            
            action = ActionItem(
                id=f"ACTION-{meeting_id}-{self._action_count:03d}",
                description=item.get('description', ''),
                assignee=item.get('assignee'),
                deadline=deadline,
                priority=Priority(item.get('priority', 'medium')),
                source_quote=item.get('source_quote', ''),
                meeting_id=meeting_id,
                tags=item.get('tags', [])
            )
            actions.append(action)
        
        logger.info(f"Extracted {len(actions)} action items")
        return actions
    
    def _extract_with_rules(
        self,
        transcript: str,
        meeting_id: str
    ) -> List[ActionItem]:
        """Extract using rule-based patterns."""
        actions = []
        
        # Normalize text
        text = transcript.lower()
        
        # Find matches for each pattern
        for pattern in self.ACTION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                self._action_count += 1
                
                # Get the matched text
                description = match.group(1).strip()
                if len(description) < 10:  # Skip very short matches
                    continue
                
                # Get context around match
                start = max(0, match.start() - 50)
                end = min(len(transcript), match.end() + 50)
                source_quote = transcript[start:end].strip()
                
                # Determine priority
                priority = self._determine_priority(source_quote)
                
                # Try to find deadline
                deadline = self._extract_deadline(source_quote)
                
                action = ActionItem(
                    id=f"ACTION-{meeting_id}-{self._action_count:03d}",
                    description=description.capitalize(),
                    priority=priority,
                    deadline=deadline,
                    source_quote=source_quote,
                    meeting_id=meeting_id
                )
                actions.append(action)
        
        # Deduplicate similar actions
        actions = self._deduplicate_actions(actions)
        
        return actions
    
    def _determine_priority(self, text: str) -> Priority:
        """Determine priority based on keywords."""
        text_lower = text.lower()
        
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return priority
        
        return Priority.MEDIUM
    
    def _extract_deadline(self, text: str) -> Optional[datetime]:
        """Extract deadline from text."""
        text_lower = text.lower()
        today = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0)
        
        # Check patterns
        if "tomorrow" in text_lower:
            return today + timedelta(days=1)
        
        if "end of day" in text_lower or "eod" in text_lower:
            return today
        
        if "end of week" in text_lower or "eow" in text_lower:
            days_until_friday = (4 - today.weekday()) % 7
            return today + timedelta(days=days_until_friday)
        
        if "next week" in text_lower:
            days_until_monday = (7 - today.weekday()) % 7 + 7
            return today + timedelta(days=days_until_monday)
        
        # Check for day names
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for i, day in enumerate(days):
            if day in text_lower:
                days_ahead = (i - today.weekday()) % 7
                if days_ahead == 0:
                    days_ahead = 7
                return today + timedelta(days=days_ahead)
        
        # Try to parse "in X days"
        match = re.search(r"in\s+(\d+)\s+days?", text_lower)
        if match:
            days = int(match.group(1))
            return today + timedelta(days=days)
        
        return None
    
    def _parse_deadline(self, deadline_str: str) -> Optional[datetime]:
        """Parse a deadline string."""
        if not deadline_str:
            return None
        
        # Try ISO format
        try:
            return datetime.fromisoformat(deadline_str)
        except:
            pass
        
        # Try common formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]
        for fmt in formats:
            try:
                return datetime.strptime(deadline_str, fmt)
            except:
                continue
        
        # Try relative dates
        return self._extract_deadline(deadline_str)
    
    def _deduplicate_actions(self, actions: List[ActionItem]) -> List[ActionItem]:
        """Remove duplicate or very similar actions."""
        if len(actions) <= 1:
            return actions
        
        unique = []
        seen_descriptions = set()
        
        for action in actions:
            # Normalize description for comparison
            normalized = action.description.lower().strip()
            
            # Check if similar exists
            is_duplicate = False
            for seen in seen_descriptions:
                if self._is_similar(normalized, seen):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(action)
                seen_descriptions.add(normalized)
        
        return unique
    
    @staticmethod
    def _is_similar(text1: str, text2: str, threshold: float = 0.8) -> bool:
        """Check if two texts are similar."""
        # Simple word overlap similarity
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return False
        
        intersection = words1 & words2
        union = words1 | words2
        
        similarity = len(intersection) / len(union)
        return similarity >= threshold
    
    def extract_from_segment(
        self,
        text: str,
        speaker: Optional[str],
        timestamp: float,
        meeting_id: str
    ) -> List[ActionItem]:
        """
        Extract action items from a single transcript segment.
        Useful for real-time extraction.
        
        Args:
            text: Segment text
            speaker: Speaker name
            timestamp: Segment timestamp
            meeting_id: Meeting ID
            
        Returns:
            List of ActionItem objects
        """
        # Quick check for action keywords
        text_lower = text.lower()
        has_action_keyword = any(
            kw in text_lower for kw in [
                "will", "going to", "need to", "have to", "should",
                "action", "todo", "follow up", "deadline", "by tomorrow"
            ]
        )
        
        if not has_action_keyword:
            return []
        
        actions = self._extract_with_rules(text, meeting_id)
        
        # Update with segment info
        for action in actions:
            action.timestamp = timestamp
            if speaker and not action.assignee:
                # Assume speaker is taking the action if they said "I will..."
                if any(phrase in text_lower for phrase in ["i'll", "i will", "i'm going to", "let me"]):
                    action.assignee = speaker
        
        return actions


class ActionTracker:
    """
    Tracks action items across meetings.
    Provides methods for updating status and querying.
    """
    
    def __init__(self):
        """Initialize the action tracker."""
        self._actions: Dict[str, ActionItem] = {}
    
    def add(self, action: ActionItem) -> None:
        """Add an action item."""
        self._actions[action.id] = action
    
    def add_many(self, actions: List[ActionItem]) -> None:
        """Add multiple action items."""
        for action in actions:
            self.add(action)
    
    def update_status(self, action_id: str, status: ActionStatus) -> bool:
        """Update action status."""
        if action_id in self._actions:
            self._actions[action_id].status = status
            return True
        return False
    
    def get(self, action_id: str) -> Optional[ActionItem]:
        """Get an action by ID."""
        return self._actions.get(action_id)
    
    def get_by_meeting(self, meeting_id: str) -> List[ActionItem]:
        """Get all actions for a meeting."""
        return [a for a in self._actions.values() if a.meeting_id == meeting_id]
    
    def get_by_assignee(self, assignee: str) -> List[ActionItem]:
        """Get all actions for an assignee."""
        return [a for a in self._actions.values() if a.assignee == assignee]
    
    def get_overdue(self) -> List[ActionItem]:
        """Get overdue action items."""
        now = datetime.now()
        return [
            a for a in self._actions.values()
            if a.deadline and a.deadline < now and a.status == ActionStatus.TODO
        ]
    
    def get_upcoming(self, days: int = 7) -> List[ActionItem]:
        """Get upcoming action items within specified days."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        return [
            a for a in self._actions.values()
            if a.deadline and now <= a.deadline <= cutoff and a.status == ActionStatus.TODO
        ]
    
    def get_all(self, status: Optional[ActionStatus] = None) -> List[ActionItem]:
        """Get all actions, optionally filtered by status."""
        if status:
            return [a for a in self._actions.values() if a.status == status]
        return list(self._actions.values())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all actions to dictionary."""
        return {
            action_id: action.to_dict()
            for action_id, action in self._actions.items()
        }
    
    def from_dict(self, data: Dict[str, Any]) -> None:
        """Load actions from dictionary."""
        for action_id, action_data in data.items():
            self._actions[action_id] = ActionItem.from_dict(action_data)
