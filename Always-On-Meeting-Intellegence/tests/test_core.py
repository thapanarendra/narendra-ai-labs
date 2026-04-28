"""
Tests for the audio detection module.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch


class TestVoiceActivityDetector:
    """Tests for VoiceActivityDetector class."""
    
    def test_calculate_rms(self):
        """Test RMS calculation."""
        from src.audio.audio_utils import calculate_rms
        
        # Test with known values
        audio = np.array([1.0, -1.0, 1.0, -1.0], dtype=np.float32)
        rms = calculate_rms(audio)
        assert rms == pytest.approx(1.0, rel=0.01)
        
        # Test with zeros
        audio = np.zeros(100, dtype=np.float32)
        rms = calculate_rms(audio)
        assert rms == 0.0
    
    def test_calculate_db(self):
        """Test decibel calculation."""
        from src.audio.audio_utils import calculate_db
        
        # Full scale signal
        audio = np.ones(100, dtype=np.float32)
        db = calculate_db(audio)
        assert db == pytest.approx(0.0, abs=0.1)
        
        # Silent signal
        audio = np.zeros(100, dtype=np.float32)
        db = calculate_db(audio)
        assert db == -100.0
    
    def test_normalize_audio(self):
        """Test audio normalization."""
        from src.audio.audio_utils import normalize_audio
        
        audio = np.array([0.5, -0.5, 0.25], dtype=np.float32)
        normalized = normalize_audio(audio)
        
        assert np.max(np.abs(normalized)) == pytest.approx(1.0)
    
    def test_split_audio_into_chunks(self):
        """Test audio chunking."""
        from src.audio.audio_utils import split_audio_into_chunks
        
        audio = np.arange(100, dtype=np.float32)
        chunks = split_audio_into_chunks(audio, chunk_size=10, overlap=0)
        
        assert len(chunks) == 10
        assert all(len(c) == 10 for c in chunks)


class TestAudioRecorder:
    """Tests for AudioRecorder class."""
    
    def test_audio_buffer(self):
        """Test AudioBuffer class."""
        from src.audio.recorder import AudioBuffer
        
        buffer = AudioBuffer(max_duration=1.0, sample_rate=16000)
        
        # Add some audio
        chunk = np.random.randn(1600).astype(np.float32)
        buffer.append(chunk)
        
        assert buffer.get_duration() == pytest.approx(0.1, abs=0.01)
        
        # Get all audio
        audio = buffer.get_all()
        assert len(audio) == 1600
        
        # Clear
        buffer.clear()
        assert buffer.get_duration() == 0.0
    
    def test_buffer_max_duration(self):
        """Test buffer respects max duration."""
        from src.audio.recorder import AudioBuffer
        
        buffer = AudioBuffer(max_duration=0.5, sample_rate=16000)
        
        # Add more than max duration
        for _ in range(10):
            chunk = np.random.randn(1600).astype(np.float32)
            buffer.append(chunk)
        
        # Should be limited to max duration
        assert buffer.get_duration() <= 0.6  # Some tolerance


class TestActionExtractor:
    """Tests for action item extraction."""
    
    def test_determine_priority(self):
        """Test priority determination from keywords."""
        from src.intelligence.action_extractor import ActionExtractor, Priority
        
        extractor = ActionExtractor(api_key="test")
        
        assert extractor._determine_priority("This is urgent!") == Priority.CRITICAL
        assert extractor._determine_priority("High priority task") == Priority.HIGH
        assert extractor._determine_priority("Do this when you can") == Priority.LOW
        assert extractor._determine_priority("Regular task") == Priority.MEDIUM
    
    def test_extract_deadline(self):
        """Test deadline extraction."""
        from src.intelligence.action_extractor import ActionExtractor
        from datetime import datetime, timedelta
        
        extractor = ActionExtractor(api_key="test")
        
        # Tomorrow
        deadline = extractor._extract_deadline("Please complete this by tomorrow")
        assert deadline is not None
        assert deadline.date() == (datetime.now() + timedelta(days=1)).date()
        
        # Next week
        deadline = extractor._extract_deadline("Do this next week")
        assert deadline is not None
    
    def test_deduplicate_actions(self):
        """Test action deduplication."""
        from src.intelligence.action_extractor import ActionExtractor, ActionItem
        
        extractor = ActionExtractor(api_key="test")
        
        actions = [
            ActionItem(id="1", description="Update the documentation"),
            ActionItem(id="2", description="Update documentation"),  # Similar
            ActionItem(id="3", description="Deploy to production"),
        ]
        
        deduplicated = extractor._deduplicate_actions(actions)
        assert len(deduplicated) == 2


class TestMeetingNotes:
    """Tests for meeting notes generation."""
    
    def test_meeting_notes_to_markdown(self):
        """Test Markdown export."""
        from src.intelligence.notes_generator import MeetingNotes
        
        notes = MeetingNotes(
            meeting_id="test123",
            title="Test Meeting",
            summary="This is a test meeting summary.",
            key_points=["Point 1", "Point 2"],
            decisions=["Decision A"],
            participants=["Alice", "Bob"]
        )
        
        md = notes.to_markdown()
        
        assert "# Test Meeting" in md
        assert "Point 1" in md
        assert "Decision A" in md
        assert "Alice" in md
    
    def test_meeting_notes_to_dict(self):
        """Test dictionary conversion."""
        from src.intelligence.notes_generator import MeetingNotes
        
        notes = MeetingNotes(
            meeting_id="test123",
            title="Test Meeting",
            summary="Summary here"
        )
        
        d = notes.to_dict()
        
        assert d['meeting_id'] == "test123"
        assert d['title'] == "Test Meeting"
        assert d['summary'] == "Summary here"


class TestDatabase:
    """Tests for database operations."""
    
    def test_meeting_dataclass(self):
        """Test Meeting dataclass."""
        from src.storage.database import Meeting
        from datetime import datetime
        
        meeting = Meeting(
            id="test123",
            title="Test Meeting",
            start_time=datetime.now()
        )
        
        assert meeting.id == "test123"
        assert meeting.participants == []
        
        # Test to_dict
        d = meeting.to_dict()
        assert d['id'] == "test123"
        
        # Test from_dict
        meeting2 = Meeting.from_dict(d)
        assert meeting2.id == meeting.id
        assert meeting2.title == meeting.title


class TestSearchResults:
    """Tests for search and query functionality."""
    
    def test_search_result_to_dict(self):
        """Test SearchResult conversion."""
        from src.intelligence.query_engine import SearchResult
        from datetime import datetime
        
        result = SearchResult(
            meeting_id="test123",
            text="This is the matched text",
            score=0.95,
            speaker="Alice"
        )
        
        d = result.to_dict()
        assert d['meeting_id'] == "test123"
        assert d['score'] == 0.95
    
    def test_query_answer_format(self):
        """Test QueryAnswer formatting."""
        from src.intelligence.query_engine import QueryAnswer, SearchResult
        
        answer = QueryAnswer(
            answer="The client expressed concerns about timeline.",
            confidence=0.9,
            sources=[
                SearchResult(
                    meeting_id="meet1",
                    text="I'm worried about the timeline",
                    score=0.95,
                    speaker="Client"
                )
            ]
        )
        
        formatted = answer.format_answer()
        assert "timeline" in formatted.lower()
        assert "Sources" in formatted


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
