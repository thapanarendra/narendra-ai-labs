"""
AI-powered meeting notes generator for the Meeting Intelligence Agent.
Generates structured summaries from transcripts.
"""
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging
import json

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class MeetingNotes:
    """Structured meeting notes."""
    meeting_id: str
    title: str
    summary: str
    key_points: List[str] = field(default_factory=list)
    decisions: List[str] = field(default_factory=list)
    discussion_topics: List[Dict[str, str]] = field(default_factory=list)
    participants: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'meeting_id': self.meeting_id,
            'title': self.title,
            'summary': self.summary,
            'key_points': self.key_points,
            'decisions': self.decisions,
            'discussion_topics': self.discussion_topics,
            'participants': self.participants,
            'created_at': self.created_at.isoformat()
        }
    
    def to_markdown(self) -> str:
        """Convert to Markdown format."""
        md = []
        
        # Title
        md.append(f"# {self.title}")
        md.append("")
        md.append(f"*Generated on {self.created_at.strftime('%Y-%m-%d %H:%M')}*")
        md.append("")
        
        # Participants
        if self.participants:
            md.append("## Participants")
            for p in self.participants:
                md.append(f"- {p}")
            md.append("")
        
        # Summary
        md.append("## Summary")
        md.append(self.summary)
        md.append("")
        
        # Key Points
        if self.key_points:
            md.append("## Key Points")
            for point in self.key_points:
                md.append(f"- {point}")
            md.append("")
        
        # Decisions
        if self.decisions:
            md.append("## Decisions Made")
            for decision in self.decisions:
                md.append(f"- {decision}")
            md.append("")
        
        # Discussion Topics
        if self.discussion_topics:
            md.append("## Discussion Topics")
            for topic in self.discussion_topics:
                md.append(f"### {topic.get('topic', 'Topic')}")
                md.append(topic.get('summary', ''))
                md.append("")
        
        return "\n".join(md)


class NotesGenerator:
    """
    Generates structured meeting notes from transcripts.
    Uses GPT-4 for intelligent summarization.
    """
    
    SYSTEM_PROMPT = """You are an expert meeting notes assistant. Your task is to analyze meeting transcripts and generate clear, structured notes.

Your notes should:
1. Be concise yet comprehensive
2. Capture all important points and decisions
3. Identify who said what when relevant
4. Highlight any action items or deadlines mentioned
5. Use professional language

Output your response as valid JSON with this structure:
{
    "title": "Brief descriptive title for the meeting",
    "summary": "2-3 paragraph executive summary",
    "key_points": ["Point 1", "Point 2", ...],
    "decisions": ["Decision 1", "Decision 2", ...],
    "discussion_topics": [
        {"topic": "Topic name", "summary": "Brief summary of discussion"}
    ],
    "participants": ["Participant 1", "Participant 2", ...]
}"""

    BRIEF_PROMPT = """Analyze this meeting transcript and provide:
- A short title
- A 1-paragraph summary
- 3-5 key points
- Any decisions made

Output as JSON."""

    DETAILED_PROMPT = """Analyze this meeting transcript thoroughly and provide:
- A descriptive title
- A comprehensive summary (2-3 paragraphs)
- All key points discussed
- All decisions made
- Major discussion topics with summaries
- List of participants identified

Output as JSON with structure: {title, summary, key_points, decisions, discussion_topics, participants}"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        style: str = "detailed",
        max_summary_length: int = 500
    ):
        """
        Initialize the notes generator.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
            style: Summary style ('brief', 'detailed', 'bullet')
            max_summary_length: Maximum summary length in words
        """
        if not HAS_OPENAI:
            raise ImportError("openai package is required for notes generation")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.style = style
        self.max_summary_length = max_summary_length
        
        self._client = OpenAI(api_key=self.api_key)
    
    def generate(
        self,
        transcript: str,
        meeting_id: str = "",
        speakers: Optional[List[str]] = None,
        context: Optional[str] = None
    ) -> MeetingNotes:
        """
        Generate meeting notes from transcript.
        
        Args:
            transcript: Meeting transcript text
            meeting_id: Meeting identifier
            speakers: List of speaker names
            context: Additional context about the meeting
            
        Returns:
            MeetingNotes object
        """
        # Build prompt
        prompt = self._build_prompt(transcript, speakers, context)
        
        # Call GPT
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000
        )
        
        # Parse response
        result = json.loads(response.choices[0].message.content)
        
        return MeetingNotes(
            meeting_id=meeting_id,
            title=result.get('title', 'Meeting Notes'),
            summary=result.get('summary', ''),
            key_points=result.get('key_points', []),
            decisions=result.get('decisions', []),
            discussion_topics=result.get('discussion_topics', []),
            participants=result.get('participants', speakers or [])
        )
    
    def _build_prompt(
        self,
        transcript: str,
        speakers: Optional[List[str]],
        context: Optional[str]
    ) -> str:
        """Build the prompt for GPT."""
        parts = []
        
        # Add style-specific instruction
        if self.style == "brief":
            parts.append(self.BRIEF_PROMPT)
        else:
            parts.append(self.DETAILED_PROMPT)
        
        # Add context if provided
        if context:
            parts.append(f"\nMeeting Context: {context}")
        
        # Add speakers if provided
        if speakers:
            parts.append(f"\nKnown Participants: {', '.join(speakers)}")
        
        # Add length constraint
        parts.append(f"\nLimit summary to approximately {self.max_summary_length} words.")
        
        # Add transcript
        parts.append(f"\n\n--- TRANSCRIPT ---\n{transcript}\n--- END TRANSCRIPT ---")
        
        return "\n".join(parts)
    
    def generate_streaming(
        self,
        transcript: str,
        meeting_id: str = "",
        on_chunk: Optional[callable] = None
    ) -> MeetingNotes:
        """
        Generate notes with streaming output.
        
        Args:
            transcript: Meeting transcript
            meeting_id: Meeting identifier
            on_chunk: Callback for streaming chunks
            
        Returns:
            MeetingNotes object
        """
        prompt = self._build_prompt(transcript, None, None)
        
        # Stream response
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2000,
            stream=True
        )
        
        full_response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content
                if on_chunk:
                    on_chunk(content)
        
        # Parse complete response
        result = json.loads(full_response)
        
        return MeetingNotes(
            meeting_id=meeting_id,
            title=result.get('title', 'Meeting Notes'),
            summary=result.get('summary', ''),
            key_points=result.get('key_points', []),
            decisions=result.get('decisions', []),
            discussion_topics=result.get('discussion_topics', []),
            participants=result.get('participants', [])
        )
    
    def enhance_notes(
        self,
        notes: MeetingNotes,
        additional_context: str
    ) -> MeetingNotes:
        """
        Enhance existing notes with additional context.
        
        Args:
            notes: Existing notes to enhance
            additional_context: New context or information
            
        Returns:
            Enhanced MeetingNotes
        """
        prompt = f"""Here are existing meeting notes:
        
Title: {notes.title}
Summary: {notes.summary}
Key Points: {json.dumps(notes.key_points)}
Decisions: {json.dumps(notes.decisions)}

Additional context/information:
{additional_context}

Please enhance these notes by incorporating the new information. Keep the same JSON structure."""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return MeetingNotes(
            meeting_id=notes.meeting_id,
            title=result.get('title', notes.title),
            summary=result.get('summary', notes.summary),
            key_points=result.get('key_points', notes.key_points),
            decisions=result.get('decisions', notes.decisions),
            discussion_topics=result.get('discussion_topics', notes.discussion_topics),
            participants=result.get('participants', notes.participants)
        )


class IncrementalNotesGenerator:
    """
    Generates notes incrementally as the meeting progresses.
    Updates notes in real-time.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        update_interval: int = 5  # minutes
    ):
        """
        Initialize incremental generator.
        
        Args:
            api_key: OpenAI API key
            model: GPT model to use
            update_interval: Minutes between updates
        """
        if not HAS_OPENAI:
            raise ImportError("openai package is required")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.update_interval = update_interval
        
        self._client = OpenAI(api_key=self.api_key)
        self._current_notes: Optional[MeetingNotes] = None
        self._processed_text = ""
    
    def update(
        self,
        new_transcript: str,
        meeting_id: str = ""
    ) -> MeetingNotes:
        """
        Update notes with new transcript content.
        
        Args:
            new_transcript: New transcript content since last update
            meeting_id: Meeting identifier
            
        Returns:
            Updated MeetingNotes
        """
        if not self._current_notes:
            # First update - generate initial notes
            self._current_notes = self._generate_initial(new_transcript, meeting_id)
        else:
            # Incremental update
            self._current_notes = self._update_notes(new_transcript)
        
        self._processed_text += new_transcript
        return self._current_notes
    
    def _generate_initial(self, transcript: str, meeting_id: str) -> MeetingNotes:
        """Generate initial notes."""
        prompt = f"""Generate initial meeting notes from this partial transcript. 
Note that the meeting is still in progress.

Transcript:
{transcript}

Output as JSON with: title, summary (brief), key_points (so far), decisions (if any)."""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Generate meeting notes in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return MeetingNotes(
            meeting_id=meeting_id,
            title=result.get('title', 'Meeting in Progress'),
            summary=result.get('summary', ''),
            key_points=result.get('key_points', []),
            decisions=result.get('decisions', [])
        )
    
    def _update_notes(self, new_content: str) -> MeetingNotes:
        """Update existing notes with new content."""
        prompt = f"""Current meeting notes:
Title: {self._current_notes.title}
Summary: {self._current_notes.summary}
Key Points: {json.dumps(self._current_notes.key_points)}
Decisions: {json.dumps(self._current_notes.decisions)}

New transcript content:
{new_content}

Update the notes to incorporate the new content. Keep them concise.
Output as JSON with the same structure."""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Update meeting notes in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return MeetingNotes(
            meeting_id=self._current_notes.meeting_id,
            title=result.get('title', self._current_notes.title),
            summary=result.get('summary', self._current_notes.summary),
            key_points=result.get('key_points', self._current_notes.key_points),
            decisions=result.get('decisions', self._current_notes.decisions),
            discussion_topics=result.get('discussion_topics', []),
            participants=result.get('participants', self._current_notes.participants)
        )
    
    def finalize(self) -> MeetingNotes:
        """Finalize notes at end of meeting."""
        if not self._current_notes:
            return MeetingNotes(meeting_id="", title="Empty Meeting", summary="No content.")
        
        prompt = f"""The meeting has ended. Here are the current notes:

Title: {self._current_notes.title}
Summary: {self._current_notes.summary}
Key Points: {json.dumps(self._current_notes.key_points)}
Decisions: {json.dumps(self._current_notes.decisions)}

Please polish and finalize these notes. Ensure the summary is comprehensive and all points are clear.
Output as JSON with: title, summary, key_points, decisions, discussion_topics, participants."""

        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Finalize and polish meeting notes in JSON format."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        
        final_notes = MeetingNotes(
            meeting_id=self._current_notes.meeting_id,
            title=result.get('title', self._current_notes.title),
            summary=result.get('summary', self._current_notes.summary),
            key_points=result.get('key_points', self._current_notes.key_points),
            decisions=result.get('decisions', self._current_notes.decisions),
            discussion_topics=result.get('discussion_topics', []),
            participants=result.get('participants', [])
        )
        
        # Reset state
        self._current_notes = None
        self._processed_text = ""
        
        return final_notes
