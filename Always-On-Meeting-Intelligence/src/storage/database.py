"""
Database storage for the Meeting Intelligence Agent.
Stores meetings, transcripts, action items, and metadata.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

try:
    from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

Base = declarative_base() if HAS_SQLALCHEMY else None


if HAS_SQLALCHEMY:
    class MeetingModel(Base):
        """SQLAlchemy model for meetings."""
        __tablename__ = 'meetings'
        
        id = Column(String, primary_key=True)
        title = Column(String, nullable=True)
        start_time = Column(DateTime, nullable=False)
        end_time = Column(DateTime, nullable=True)
        duration = Column(Float, default=0.0)
        recording_path = Column(String, nullable=True)
        transcript_text = Column(Text, nullable=True)
        summary = Column(Text, nullable=True)
        language = Column(String, nullable=True)
        participants = Column(Text, nullable=True)  # JSON array
        key_points = Column(Text, nullable=True)  # JSON array
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
        
        # Relationships
        segments = relationship("TranscriptSegmentModel", back_populates="meeting", cascade="all, delete-orphan")
        action_items = relationship("ActionItemModel", back_populates="meeting", cascade="all, delete-orphan")
        speakers = relationship("SpeakerModel", back_populates="meeting", cascade="all, delete-orphan")
    
    
    class TranscriptSegmentModel(Base):
        """SQLAlchemy model for transcript segments."""
        __tablename__ = 'transcript_segments'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
        segment_index = Column(Integer, nullable=False)
        text = Column(Text, nullable=False)
        start_time = Column(Float, nullable=False)
        end_time = Column(Float, nullable=False)
        speaker_id = Column(String, nullable=True)
        confidence = Column(Float, default=1.0)
        
        meeting = relationship("MeetingModel", back_populates="segments")
    
    
    class ActionItemModel(Base):
        """SQLAlchemy model for action items."""
        __tablename__ = 'action_items'
        
        id = Column(String, primary_key=True)
        meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
        description = Column(Text, nullable=False)
        assignee = Column(String, nullable=True)
        deadline = Column(DateTime, nullable=True)
        priority = Column(String, default='medium')
        status = Column(String, default='todo')
        source_quote = Column(Text, nullable=True)
        timestamp = Column(Float, default=0.0)
        tags = Column(Text, nullable=True)  # JSON array
        created_at = Column(DateTime, default=datetime.now)
        updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
        external_id = Column(String, nullable=True)  # Jira/Asana ticket ID
        
        meeting = relationship("MeetingModel", back_populates="action_items")
    
    
    class SpeakerModel(Base):
        """SQLAlchemy model for speakers."""
        __tablename__ = 'speakers'
        
        id = Column(Integer, primary_key=True, autoincrement=True)
        meeting_id = Column(String, ForeignKey('meetings.id'), nullable=False)
        speaker_id = Column(String, nullable=False)
        name = Column(String, nullable=True)
        total_speaking_time = Column(Float, default=0.0)
        segment_count = Column(Integer, default=0)
        
        meeting = relationship("MeetingModel", back_populates="speakers")


@dataclass
class Meeting:
    """Data class for a meeting."""
    id: str
    title: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    recording_path: Optional[str] = None
    transcript_text: Optional[str] = None
    summary: Optional[str] = None
    language: Optional[str] = None
    participants: List[str] = None
    key_points: List[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = []
        if self.key_points is None:
            self.key_points = []
        if self.created_at is None:
            self.created_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'recording_path': self.recording_path,
            'transcript_text': self.transcript_text,
            'summary': self.summary,
            'language': self.language,
            'participants': self.participants,
            'key_points': self.key_points,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Meeting':
        """Create from dictionary."""
        return cls(
            id=data['id'],
            title=data.get('title', ''),
            start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else datetime.now(),
            end_time=datetime.fromisoformat(data['end_time']) if data.get('end_time') else None,
            duration=data.get('duration', 0.0),
            recording_path=data.get('recording_path'),
            transcript_text=data.get('transcript_text'),
            summary=data.get('summary'),
            language=data.get('language'),
            participants=data.get('participants', []),
            key_points=data.get('key_points', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


class MeetingDatabase:
    """
    Database for storing meeting data.
    Uses SQLite with SQLAlchemy ORM.
    """
    
    def __init__(self, database_path: str = "./data/meetings.db"):
        """
        Initialize the database.
        
        Args:
            database_path: Path to SQLite database file
        """
        if not HAS_SQLALCHEMY:
            raise ImportError("sqlalchemy is required for database storage")
        
        self.database_path = database_path
        
        # Create directory if needed
        Path(database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine and session
        self._engine = create_engine(f"sqlite:///{database_path}", echo=False)
        self._Session = sessionmaker(bind=self._engine)
        
        # Create tables
        Base.metadata.create_all(self._engine)
        
        logger.info(f"Database initialized: {database_path}")
    
    def _get_session(self):
        """Get a new database session."""
        return self._Session()
    
    # Meeting operations
    
    def save_meeting(self, meeting: Meeting) -> bool:
        """Save a meeting to the database."""
        session = self._get_session()
        try:
            # Check if exists
            existing = session.query(MeetingModel).filter_by(id=meeting.id).first()
            
            if existing:
                # Update
                existing.title = meeting.title
                existing.start_time = meeting.start_time
                existing.end_time = meeting.end_time
                existing.duration = meeting.duration
                existing.recording_path = meeting.recording_path
                existing.transcript_text = meeting.transcript_text
                existing.summary = meeting.summary
                existing.language = meeting.language
                existing.participants = json.dumps(meeting.participants)
                existing.key_points = json.dumps(meeting.key_points)
                existing.updated_at = datetime.now()
            else:
                # Insert
                model = MeetingModel(
                    id=meeting.id,
                    title=meeting.title,
                    start_time=meeting.start_time,
                    end_time=meeting.end_time,
                    duration=meeting.duration,
                    recording_path=meeting.recording_path,
                    transcript_text=meeting.transcript_text,
                    summary=meeting.summary,
                    language=meeting.language,
                    participants=json.dumps(meeting.participants),
                    key_points=json.dumps(meeting.key_points),
                    created_at=meeting.created_at
                )
                session.add(model)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving meeting: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a meeting by ID."""
        session = self._get_session()
        try:
            model = session.query(MeetingModel).filter_by(id=meeting_id).first()
            if model:
                return self._model_to_meeting(model)
            return None
        finally:
            session.close()
    
    def get_all_meetings(
        self,
        limit: int = 100,
        offset: int = 0,
        order_by: str = "start_time",
        descending: bool = True
    ) -> List[Meeting]:
        """Get all meetings with pagination."""
        session = self._get_session()
        try:
            query = session.query(MeetingModel)
            
            # Order
            order_col = getattr(MeetingModel, order_by, MeetingModel.start_time)
            if descending:
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col)
            
            # Pagination
            query = query.offset(offset).limit(limit)
            
            return [self._model_to_meeting(m) for m in query.all()]
        finally:
            session.close()
    
    def search_meetings(
        self,
        query: str,
        limit: int = 20
    ) -> List[Meeting]:
        """Search meetings by text."""
        session = self._get_session()
        try:
            search_term = f"%{query}%"
            results = session.query(MeetingModel).filter(
                (MeetingModel.title.like(search_term)) |
                (MeetingModel.transcript_text.like(search_term)) |
                (MeetingModel.summary.like(search_term))
            ).order_by(MeetingModel.start_time.desc()).limit(limit).all()
            
            return [self._model_to_meeting(m) for m in results]
        finally:
            session.close()
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete a meeting and all related data."""
        session = self._get_session()
        try:
            meeting = session.query(MeetingModel).filter_by(id=meeting_id).first()
            if meeting:
                session.delete(meeting)
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting meeting: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def _model_to_meeting(self, model: 'MeetingModel') -> Meeting:
        """Convert model to Meeting dataclass."""
        return Meeting(
            id=model.id,
            title=model.title or "",
            start_time=model.start_time,
            end_time=model.end_time,
            duration=model.duration,
            recording_path=model.recording_path,
            transcript_text=model.transcript_text,
            summary=model.summary,
            language=model.language,
            participants=json.loads(model.participants) if model.participants else [],
            key_points=json.loads(model.key_points) if model.key_points else [],
            created_at=model.created_at
        )
    
    # Transcript segment operations
    
    def save_segments(self, meeting_id: str, segments: List[Dict[str, Any]]) -> bool:
        """Save transcript segments."""
        session = self._get_session()
        try:
            # Delete existing segments
            session.query(TranscriptSegmentModel).filter_by(meeting_id=meeting_id).delete()
            
            # Add new segments
            for i, seg in enumerate(segments):
                model = TranscriptSegmentModel(
                    meeting_id=meeting_id,
                    segment_index=i,
                    text=seg.get('text', ''),
                    start_time=seg.get('start_time', 0.0),
                    end_time=seg.get('end_time', 0.0),
                    speaker_id=seg.get('speaker'),
                    confidence=seg.get('confidence', 1.0)
                )
                session.add(model)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving segments: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_segments(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Get transcript segments for a meeting."""
        session = self._get_session()
        try:
            segments = session.query(TranscriptSegmentModel).filter_by(
                meeting_id=meeting_id
            ).order_by(TranscriptSegmentModel.segment_index).all()
            
            return [
                {
                    'text': s.text,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                    'speaker': s.speaker_id,
                    'confidence': s.confidence
                }
                for s in segments
            ]
        finally:
            session.close()
    
    # Action item operations
    
    def save_action_item(self, action: Dict[str, Any]) -> bool:
        """Save an action item."""
        session = self._get_session()
        try:
            existing = session.query(ActionItemModel).filter_by(id=action['id']).first()
            
            deadline = action.get('deadline')
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline)
            
            if existing:
                existing.description = action.get('description', existing.description)
                existing.assignee = action.get('assignee')
                existing.deadline = deadline
                existing.priority = action.get('priority', 'medium')
                existing.status = action.get('status', 'todo')
                existing.source_quote = action.get('source_quote')
                existing.tags = json.dumps(action.get('tags', []))
                existing.external_id = action.get('external_id')
                existing.updated_at = datetime.now()
            else:
                model = ActionItemModel(
                    id=action['id'],
                    meeting_id=action.get('meeting_id', ''),
                    description=action.get('description', ''),
                    assignee=action.get('assignee'),
                    deadline=deadline,
                    priority=action.get('priority', 'medium'),
                    status=action.get('status', 'todo'),
                    source_quote=action.get('source_quote'),
                    timestamp=action.get('timestamp', 0.0),
                    tags=json.dumps(action.get('tags', [])),
                    external_id=action.get('external_id')
                )
                session.add(model)
            
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error saving action item: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def get_action_items(
        self,
        meeting_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get action items with optional filters."""
        session = self._get_session()
        try:
            query = session.query(ActionItemModel)
            
            if meeting_id:
                query = query.filter_by(meeting_id=meeting_id)
            if status:
                query = query.filter_by(status=status)
            if assignee:
                query = query.filter_by(assignee=assignee)
            
            query = query.order_by(ActionItemModel.created_at.desc())
            
            return [
                {
                    'id': a.id,
                    'meeting_id': a.meeting_id,
                    'description': a.description,
                    'assignee': a.assignee,
                    'deadline': a.deadline.isoformat() if a.deadline else None,
                    'priority': a.priority,
                    'status': a.status,
                    'source_quote': a.source_quote,
                    'timestamp': a.timestamp,
                    'tags': json.loads(a.tags) if a.tags else [],
                    'external_id': a.external_id,
                    'created_at': a.created_at.isoformat()
                }
                for a in query.all()
            ]
        finally:
            session.close()
    
    def update_action_status(self, action_id: str, status: str) -> bool:
        """Update action item status."""
        session = self._get_session()
        try:
            action = session.query(ActionItemModel).filter_by(id=action_id).first()
            if action:
                action.status = status
                action.updated_at = datetime.now()
                session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating action status: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    # Statistics
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        session = self._get_session()
        try:
            meeting_count = session.query(MeetingModel).count()
            action_count = session.query(ActionItemModel).count()
            todo_count = session.query(ActionItemModel).filter_by(status='todo').count()
            
            # Total meeting time
            from sqlalchemy import func
            total_duration = session.query(func.sum(MeetingModel.duration)).scalar() or 0
            
            return {
                'total_meetings': meeting_count,
                'total_action_items': action_count,
                'pending_actions': todo_count,
                'total_meeting_hours': round(total_duration / 3600, 2)
            }
        finally:
            session.close()


class SimpleFileStorage:
    """
    Simple file-based storage as fallback.
    Uses JSON files for persistence.
    """
    
    def __init__(self, storage_path: str = "./data"):
        """Initialize file storage."""
        self.storage_path = Path(storage_path)
        self.meetings_path = self.storage_path / "meetings"
        self.actions_path = self.storage_path / "actions"
        
        # Create directories
        self.meetings_path.mkdir(parents=True, exist_ok=True)
        self.actions_path.mkdir(parents=True, exist_ok=True)
    
    def save_meeting(self, meeting: Meeting) -> bool:
        """Save meeting to JSON file."""
        try:
            file_path = self.meetings_path / f"{meeting.id}.json"
            with open(file_path, 'w') as f:
                json.dump(meeting.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving meeting: {e}")
            return False
    
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get meeting from JSON file."""
        file_path = self.meetings_path / f"{meeting_id}.json"
        if not file_path.exists():
            return None
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return Meeting.from_dict(data)
        except Exception as e:
            logger.error(f"Error loading meeting: {e}")
            return None
    
    def get_all_meetings(self) -> List[Meeting]:
        """Get all meetings."""
        meetings = []
        for file_path in self.meetings_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                meetings.append(Meeting.from_dict(data))
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        return sorted(meetings, key=lambda m: m.start_time, reverse=True)
    
    def delete_meeting(self, meeting_id: str) -> bool:
        """Delete meeting file."""
        file_path = self.meetings_path / f"{meeting_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
    
    def save_action_items(self, meeting_id: str, actions: List[Dict[str, Any]]) -> bool:
        """Save action items to JSON file."""
        try:
            file_path = self.actions_path / f"{meeting_id}.json"
            with open(file_path, 'w') as f:
                json.dump(actions, f, indent=2, default=str)
            return True
        except Exception as e:
            logger.error(f"Error saving actions: {e}")
            return False
    
    def get_action_items(self, meeting_id: str) -> List[Dict[str, Any]]:
        """Get action items from JSON file."""
        file_path = self.actions_path / f"{meeting_id}.json"
        if not file_path.exists():
            return []
        
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading actions: {e}")
            return []


def get_storage(database_path: str = "./data/meetings.db"):
    """Get storage instance (database or file-based)."""
    if HAS_SQLALCHEMY:
        return MeetingDatabase(database_path)
    else:
        logger.warning("SQLAlchemy not available, using file storage")
        return SimpleFileStorage(Path(database_path).parent)
