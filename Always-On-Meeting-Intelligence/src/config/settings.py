"""
Configuration settings for the Meeting Intelligence Agent.
"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AudioConfig:
    """Audio capture configuration."""
    input: str = "both"
    sensitivity: float = 0.3
    sample_rate: int = 16000
    chunk_duration: float = 0.5
    silence_threshold: float = 2.0
    min_meeting_duration: int = 30
    recording_format: str = "wav"


@dataclass
class AIConfig:
    """AI and transcription configuration."""
    openai_api_key: str = ""
    model: str = "gpt-4o"
    whisper_model: str = "base"
    whisper_local: bool = True
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    max_speakers: int = 10
    embedding_model: str = "all-MiniLM-L6-v2"
    
    def __post_init__(self):
        # Try to get API key from environment if not set
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY", "")


@dataclass
class StorageConfig:
    """Storage configuration."""
    recordings_path: str = "./data/recordings"
    transcripts_path: str = "./data/transcripts"
    database_path: str = "./data/meetings.db"
    vector_db_path: str = "./data/vector_db"
    retention_days: int = 90
    
    def __post_init__(self):
        # Create directories if they don't exist
        for path_attr in ['recordings_path', 'transcripts_path', 'vector_db_path']:
            path = Path(getattr(self, path_attr))
            path.mkdir(parents=True, exist_ok=True)
        
        # Create database directory
        db_dir = Path(self.database_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class DetectionConfig:
    """Meeting detection configuration."""
    auto_start: bool = True
    min_voice_duration: float = 3.0
    meeting_keywords: List[str] = field(default_factory=lambda: [
        "let's begin", "shall we start", "meeting", "call", "standup", "sync"
    ])


@dataclass
class NotesConfig:
    """Notes generation configuration."""
    auto_generate: bool = True
    summary_style: str = "detailed"
    include_speakers: bool = True
    max_summary_length: int = 500


@dataclass
class ActionsConfig:
    """Action item extraction configuration."""
    auto_extract: bool = True
    action_keywords: List[str] = field(default_factory=lambda: [
        "action item", "todo", "task", "need to", "should", "will do",
        "by tomorrow", "deadline", "assigned to", "take care of", "follow up"
    ])


@dataclass
class JiraConfig:
    """Jira integration configuration."""
    enabled: bool = False
    url: str = ""
    email: str = ""
    api_token: str = ""
    project_key: str = "MEET"
    default_issue_type: str = "Task"


@dataclass
class AsanaConfig:
    """Asana integration configuration."""
    enabled: bool = False
    api_token: str = ""
    workspace_gid: str = ""
    project_gid: str = ""


@dataclass
class IntegrationsConfig:
    """Integrations configuration."""
    jira: JiraConfig = field(default_factory=JiraConfig)
    asana: AsanaConfig = field(default_factory=AsanaConfig)


@dataclass
class QueryConfig:
    """Query interface configuration."""
    top_k: int = 5
    min_similarity: float = 0.5
    context_window: int = 200


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    file: str = "./data/logs/meeting_agent.log"
    max_size_mb: int = 50
    backup_count: int = 5
    
    def __post_init__(self):
        # Create log directory
        log_dir = Path(self.file).parent
        log_dir.mkdir(parents=True, exist_ok=True)


@dataclass
class NotificationsConfig:
    """Notifications configuration."""
    desktop: bool = True
    sound: bool = False
    on_meeting_start: bool = True
    on_meeting_end: bool = True
    on_action_items: bool = True


@dataclass
class Settings:
    """Main settings container."""
    audio: AudioConfig = field(default_factory=AudioConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    detection: DetectionConfig = field(default_factory=DetectionConfig)
    notes: NotesConfig = field(default_factory=NotesConfig)
    actions: ActionsConfig = field(default_factory=ActionsConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    query: QueryConfig = field(default_factory=QueryConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str = "config.yaml") -> "Settings":
        """Load settings from YAML file."""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # Return default settings if config doesn't exist
            return cls()
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}
        
        return cls._from_dict(config_data)
    
    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "Settings":
        """Create Settings from dictionary."""
        settings = cls()
        
        if 'audio' in data:
            settings.audio = AudioConfig(**data['audio'])
        
        if 'ai' in data:
            settings.ai = AIConfig(**data['ai'])
        
        if 'storage' in data:
            settings.storage = StorageConfig(**data['storage'])
        
        if 'detection' in data:
            settings.detection = DetectionConfig(**data['detection'])
        
        if 'notes' in data:
            settings.notes = NotesConfig(**data['notes'])
        
        if 'actions' in data:
            settings.actions = ActionsConfig(**data['actions'])
        
        if 'integrations' in data:
            int_data = data['integrations']
            jira = JiraConfig(**int_data.get('jira', {})) if 'jira' in int_data else JiraConfig()
            asana = AsanaConfig(**int_data.get('asana', {})) if 'asana' in int_data else AsanaConfig()
            settings.integrations = IntegrationsConfig(jira=jira, asana=asana)
        
        if 'query' in data:
            settings.query = QueryConfig(**data['query'])
        
        if 'logging' in data:
            settings.logging = LoggingConfig(**data['logging'])
        
        if 'notifications' in data:
            settings.notifications = NotificationsConfig(**data['notifications'])
        
        return settings
    
    def save(self, config_path: str = "config.yaml"):
        """Save settings to YAML file."""
        data = {
            'audio': self.audio.__dict__,
            'ai': {k: v for k, v in self.ai.__dict__.items() if k != 'openai_api_key'},
            'storage': self.storage.__dict__,
            'detection': self.detection.__dict__,
            'notes': self.notes.__dict__,
            'actions': self.actions.__dict__,
            'integrations': {
                'jira': self.integrations.jira.__dict__,
                'asana': self.integrations.asana.__dict__,
            },
            'query': self.query.__dict__,
            'logging': self.logging.__dict__,
            'notifications': self.notifications.__dict__,
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)


# Global settings instance
_settings: Optional[Settings] = None


def get_settings(config_path: str = "config.yaml") -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml(config_path)
    return _settings


def reload_settings(config_path: str = "config.yaml") -> Settings:
    """Reload settings from config file."""
    global _settings
    _settings = Settings.from_yaml(config_path)
    return _settings
