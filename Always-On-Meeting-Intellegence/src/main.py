#!/usr/bin/env python3
"""
Main orchestrator for the Always-On Meeting Intelligence Agent.
Coordinates all components for real-time meeting capture and analysis.
"""
import os
import sys
import signal
import threading
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
import json

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.settings import get_settings, Settings
from src.audio.detector import AudioActivityMonitor, VoiceActivityState
from src.audio.recorder import AudioRecorder, StreamingRecorder
from src.transcription.transcriber import WhisperTranscriber, StreamingTranscriber, Transcript, TranscriptSegment
from src.transcription.speaker_diarization import SpeakerDiarizer, get_diarizer, DiarizationResult
from src.intelligence.notes_generator import NotesGenerator, IncrementalNotesGenerator, MeetingNotes
from src.intelligence.action_extractor import ActionExtractor, ActionItem, ActionTracker
from src.intelligence.query_engine import MeetingIndex, MeetingQueryEngine, SimpleQueryEngine
from src.storage.database import MeetingDatabase, Meeting, get_storage
from src.integrations.jira_integration import get_jira_integration
from src.integrations.asana_integration import get_asana_integration

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


@dataclass
class MeetingSession:
    """Active meeting session data."""
    id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    recording_path: Optional[str] = None
    transcript: List[TranscriptSegment] = field(default_factory=list)
    speakers: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[MeetingNotes] = None
    action_items: List[ActionItem] = field(default_factory=list)
    is_active: bool = True


class MeetingIntelligenceAgent:
    """
    Main agent that orchestrates all meeting intelligence components.
    """
    
    def __init__(
        self,
        config_path: str = "config.yaml",
        settings: Optional[Settings] = None
    ):
        """
        Initialize the meeting intelligence agent.
        
        Args:
            config_path: Path to configuration file
            settings: Optional pre-loaded settings
        """
        # Load settings
        self.settings = settings or get_settings(config_path)
        
        # Initialize components
        self._init_components()
        
        # State
        self._running = False
        self._current_session: Optional[MeetingSession] = None
        self._sessions: Dict[str, MeetingSession] = {}
        
        # Callbacks
        self._on_meeting_start: List[Callable] = []
        self._on_meeting_end: List[Callable] = []
        self._on_transcript_update: List[Callable] = []
        self._on_action_item: List[Callable] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info("Meeting Intelligence Agent initialized")
    
    def _init_components(self):
        """Initialize all agent components."""
        settings = self.settings
        
        # Audio monitoring and recording
        self._audio_monitor = AudioActivityMonitor(
            sample_rate=settings.audio.sample_rate,
            sensitivity=settings.audio.sensitivity,
            silence_threshold=settings.audio.silence_threshold,
            min_speech_duration=settings.detection.min_voice_duration
        )
        
        self._recorder = AudioRecorder(
            sample_rate=settings.audio.sample_rate,
            recordings_path=settings.storage.recordings_path,
            format=settings.audio.recording_format
        )
        
        # Transcription
        self._transcriber = None
        self._streaming_transcriber = None
        
        # Notes and actions
        self._notes_generator = None
        self._incremental_notes = None
        self._action_extractor = None
        self._action_tracker = ActionTracker()
        
        # Query engine
        self._query_engine = None
        self._meeting_index = None
        
        # Storage
        self._database = get_storage(settings.storage.database_path)
        
        # Integrations
        self._jira = None
        self._asana = None
        
        # Lazy initialization flags
        self._ai_initialized = False
    
    def _init_ai_components(self):
        """Initialize AI components (lazy loading)."""
        if self._ai_initialized:
            return
        
        settings = self.settings
        
        try:
            # Transcriber
            self._transcriber = WhisperTranscriber(
                model_name=settings.ai.whisper_model,
                use_local=settings.ai.whisper_local,
                api_key=settings.ai.openai_api_key
            )
            
            # Notes generator
            if settings.ai.openai_api_key:
                self._notes_generator = NotesGenerator(
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.model,
                    style=settings.notes.summary_style
                )
                
                self._incremental_notes = IncrementalNotesGenerator(
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.model
                )
                
                self._action_extractor = ActionExtractor(
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.model,
                    action_keywords=settings.actions.action_keywords
                )
            
            # Query engine
            try:
                self._meeting_index = MeetingIndex(
                    embedding_model=settings.ai.embedding_model,
                    persist_path=settings.storage.vector_db_path
                )
                
                self._query_engine = MeetingQueryEngine(
                    index=self._meeting_index,
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.model
                )
            except Exception as e:
                logger.warning(f"Vector search not available: {e}")
                self._query_engine = SimpleQueryEngine(
                    api_key=settings.ai.openai_api_key,
                    model=settings.ai.model
                )
            
            self._ai_initialized = True
            logger.info("AI components initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize AI components: {e}")
    
    def _init_integrations(self):
        """Initialize external integrations."""
        settings = self.settings
        
        # Jira
        if settings.integrations.jira.enabled:
            self._jira = get_jira_integration(
                url=settings.integrations.jira.url,
                email=settings.integrations.jira.email,
                api_token=settings.integrations.jira.api_token,
                project_key=settings.integrations.jira.project_key
            )
        
        # Asana
        if settings.integrations.asana.enabled:
            self._asana = get_asana_integration(
                api_token=settings.integrations.asana.api_token,
                workspace_gid=settings.integrations.asana.workspace_gid,
                project_gid=settings.integrations.asana.project_gid
            )
    
    def start(self):
        """Start the always-on meeting intelligence agent."""
        if self._running:
            logger.warning("Agent already running")
            return
        
        self._running = True
        
        # Setup audio callbacks
        self._audio_monitor.on_meeting_start(self._handle_meeting_start)
        self._audio_monitor.on_meeting_end(self._handle_meeting_end)
        self._audio_monitor.on_audio_data(self._handle_audio_data)
        
        # Start audio monitoring
        self._audio_monitor.start()
        
        logger.info("Meeting Intelligence Agent started - listening for meetings...")
        console.print("[green]✓ Agent started - listening for voice activity...[/green]")
    
    def stop(self):
        """Stop the agent."""
        if not self._running:
            return
        
        self._running = False
        
        # Stop audio monitoring
        self._audio_monitor.stop()
        
        # End any active session
        if self._current_session:
            self._end_session()
        
        logger.info("Meeting Intelligence Agent stopped")
        console.print("[yellow]Agent stopped[/yellow]")
    
    def _handle_meeting_start(self):
        """Handle meeting start event."""
        with self._lock:
            # Initialize AI components if needed
            self._init_ai_components()
            
            # Create new session
            session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self._current_session = MeetingSession(
                id=session_id,
                start_time=datetime.now()
            )
            
            # Start recording
            self._recorder.start_recording(session_id)
            self._current_session.recording_path = str(
                self._recorder.recordings_path / f"{session_id}.{self.settings.audio.recording_format}"
            )
            
            # Notify
            logger.info(f"Meeting started: {session_id}")
            console.print(f"[green]🎙️ Meeting started: {session_id}[/green]")
            
            if self.settings.notifications.on_meeting_start:
                self._send_notification("Meeting Started", "Recording and transcription active")
            
            # Trigger callbacks
            for callback in self._on_meeting_start:
                try:
                    callback(session_id)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
    
    def _handle_meeting_end(self, duration: float):
        """Handle meeting end event."""
        with self._lock:
            if not self._current_session:
                return
            
            session = self._current_session
            session.is_active = False
            session.end_time = datetime.now()
            
            # Stop recording
            recording_meta = self._recorder.stop_recording(save=True)
            
            # Check minimum duration
            if duration < self.settings.audio.min_meeting_duration:
                logger.info(f"Meeting too short ({duration:.1f}s), discarding")
                self._current_session = None
                return
            
            console.print(f"[yellow]Meeting ended ({duration/60:.1f} min)[/yellow]")
            
            # Process meeting
            self._process_meeting(session)
            
            # Store session
            self._sessions[session.id] = session
            self._current_session = None
    
    def _handle_audio_data(self, audio_data):
        """Handle incoming audio data."""
        if not self._current_session:
            return
        
        # Forward to recorder
        self._recorder.add_audio_data(audio_data)
    
    def _process_meeting(self, session: MeetingSession):
        """Process a completed meeting."""
        console.print("[cyan]Processing meeting...[/cyan]")
        
        try:
            # Transcribe
            if session.recording_path and Path(session.recording_path).exists():
                console.print("  Transcribing audio...")
                transcript = self._transcriber.transcribe(session.recording_path)
                session.transcript = transcript.segments
                
                # Speaker diarization
                console.print("  Identifying speakers...")
                try:
                    diarizer = get_diarizer(use_pyannote=True)
                    diarization = diarizer.diarize(session.recording_path)
                    session.speakers = diarization.get_speaker_stats()
                    
                    # Assign speakers to segments
                    for seg in session.transcript:
                        speaker = diarization.get_speaker_at_time(seg.start_time)
                        if speaker:
                            seg.speaker = speaker
                except Exception as e:
                    logger.warning(f"Speaker diarization failed: {e}")
            
            # Generate notes
            if self._notes_generator and session.transcript:
                console.print("  Generating meeting notes...")
                transcript_text = " ".join(seg.text for seg in session.transcript)
                session.notes = self._notes_generator.generate(
                    transcript=transcript_text,
                    meeting_id=session.id,
                    speakers=list(session.speakers.keys())
                )
            
            # Extract action items
            if self._action_extractor and session.transcript:
                console.print("  Extracting action items...")
                transcript_text = " ".join(seg.text for seg in session.transcript)
                session.action_items = self._action_extractor.extract(
                    transcript=transcript_text,
                    meeting_id=session.id,
                    participants=list(session.speakers.keys())
                )
                
                # Track actions
                for action in session.action_items:
                    self._action_tracker.add(action)
            
            # Save to database
            self._save_meeting(session)
            
            # Index for search
            if self._meeting_index:
                self._meeting_index.add_meeting(
                    meeting_id=session.id,
                    transcript=" ".join(seg.text for seg in session.transcript),
                    segments=[seg.to_dict() for seg in session.transcript],
                    metadata={
                        'title': session.notes.title if session.notes else f"Meeting {session.id}",
                        'date': session.start_time.isoformat()
                    }
                )
            
            # Create tickets
            if session.action_items:
                self._create_tickets(session)
            
            # Print summary
            self._print_meeting_summary(session)
            
            # Notify
            if self.settings.notifications.on_meeting_end:
                self._send_notification(
                    "Meeting Ended",
                    f"Duration: {(session.end_time - session.start_time).seconds // 60} min, "
                    f"Actions: {len(session.action_items)}"
                )
            
        except Exception as e:
            logger.error(f"Error processing meeting: {e}")
            console.print(f"[red]Error processing meeting: {e}[/red]")
    
    def _save_meeting(self, session: MeetingSession):
        """Save meeting to database."""
        meeting = Meeting(
            id=session.id,
            title=session.notes.title if session.notes else f"Meeting {session.id}",
            start_time=session.start_time,
            end_time=session.end_time,
            duration=(session.end_time - session.start_time).total_seconds() if session.end_time else 0,
            recording_path=session.recording_path,
            transcript_text=" ".join(seg.text for seg in session.transcript),
            summary=session.notes.summary if session.notes else None,
            participants=list(session.speakers.keys()),
            key_points=session.notes.key_points if session.notes else []
        )
        
        self._database.save_meeting(meeting)
        
        # Save segments
        if session.transcript:
            self._database.save_segments(
                session.id,
                [seg.to_dict() for seg in session.transcript]
            )
        
        # Save action items
        for action in session.action_items:
            self._database.save_action_item(action.to_dict())
        
        logger.info(f"Meeting {session.id} saved to database")
    
    def _create_tickets(self, session: MeetingSession):
        """Create tickets from action items."""
        if not session.action_items:
            return
        
        meeting_title = session.notes.title if session.notes else f"Meeting {session.id}"
        
        # Jira
        if self._jira:
            console.print("  Creating Jira tickets...")
            issues = self._jira.create_batch(
                [a.to_dict() for a in session.action_items],
                meeting_title=meeting_title
            )
            console.print(f"    Created {len(issues)} Jira issues")
        
        # Asana
        if self._asana:
            console.print("  Creating Asana tasks...")
            tasks = self._asana.create_batch(
                [a.to_dict() for a in session.action_items],
                meeting_title=meeting_title
            )
            console.print(f"    Created {len(tasks)} Asana tasks")
    
    def _print_meeting_summary(self, session: MeetingSession):
        """Print meeting summary to console."""
        console.print()
        
        # Header
        title = session.notes.title if session.notes else f"Meeting {session.id}"
        console.print(Panel(f"[bold]{title}[/bold]", style="cyan"))
        
        # Duration
        if session.end_time:
            duration = (session.end_time - session.start_time).total_seconds()
            console.print(f"Duration: {duration/60:.1f} minutes")
        
        # Speakers
        if session.speakers:
            console.print(f"Speakers: {', '.join(session.speakers.keys())}")
        
        # Summary
        if session.notes and session.notes.summary:
            console.print("\n[bold]Summary:[/bold]")
            console.print(session.notes.summary)
        
        # Key points
        if session.notes and session.notes.key_points:
            console.print("\n[bold]Key Points:[/bold]")
            for point in session.notes.key_points[:5]:
                console.print(f"  • {point}")
        
        # Action items
        if session.action_items:
            console.print(f"\n[bold]Action Items ({len(session.action_items)}):[/bold]")
            for action in session.action_items[:5]:
                assignee = f"[{action.assignee}]" if action.assignee else ""
                deadline = f"(by {action.deadline.strftime('%Y-%m-%d')})" if action.deadline else ""
                console.print(f"  • {action.description} {assignee} {deadline}")
            if len(session.action_items) > 5:
                console.print(f"  ... and {len(session.action_items) - 5} more")
        
        console.print()
    
    def _send_notification(self, title: str, message: str):
        """Send desktop notification."""
        if not self.settings.notifications.desktop:
            return
        
        try:
            import subprocess
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], capture_output=True)
        except Exception:
            pass  # Ignore notification errors
    
    # Public API
    
    def query(self, question: str, meeting_id: Optional[str] = None) -> str:
        """
        Ask a question about past meetings.
        
        Args:
            question: Question to ask
            meeting_id: Optionally limit to specific meeting
            
        Returns:
            Answer string
        """
        self._init_ai_components()
        
        if not self._query_engine:
            return "Query engine not available."
        
        result = self._query_engine.query(question, meeting_id=meeting_id)
        return result.format_answer() if hasattr(result, 'format_answer') else str(result)
    
    def get_meetings(self, limit: int = 10) -> List[Meeting]:
        """Get recent meetings."""
        return self._database.get_all_meetings(limit=limit)
    
    def get_meeting(self, meeting_id: str) -> Optional[Meeting]:
        """Get a specific meeting."""
        return self._database.get_meeting(meeting_id)
    
    def get_action_items(
        self,
        meeting_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get action items."""
        return self._database.get_action_items(
            meeting_id=meeting_id,
            status=status
        )
    
    def export_notes(self, meeting_id: str, format: str = "markdown") -> str:
        """Export meeting notes."""
        meeting = self._database.get_meeting(meeting_id)
        if not meeting:
            return ""
        
        segments = self._database.get_segments(meeting_id)
        actions = self._database.get_action_items(meeting_id=meeting_id)
        
        if format == "markdown":
            return self._format_markdown(meeting, segments, actions)
        elif format == "json":
            return json.dumps({
                'meeting': meeting.to_dict(),
                'segments': segments,
                'actions': actions
            }, indent=2)
        else:
            return meeting.transcript_text or ""
    
    def _format_markdown(
        self,
        meeting: Meeting,
        segments: List[Dict[str, Any]],
        actions: List[Dict[str, Any]]
    ) -> str:
        """Format meeting as Markdown."""
        md = []
        
        md.append(f"# {meeting.title}")
        md.append(f"\n*Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}*")
        md.append(f"\n*Duration: {meeting.duration/60:.1f} minutes*")
        
        if meeting.participants:
            md.append(f"\n## Participants\n")
            for p in meeting.participants:
                md.append(f"- {p}")
        
        if meeting.summary:
            md.append(f"\n## Summary\n\n{meeting.summary}")
        
        if meeting.key_points:
            md.append("\n## Key Points\n")
            for point in meeting.key_points:
                md.append(f"- {point}")
        
        if actions:
            md.append("\n## Action Items\n")
            for action in actions:
                assignee = f" @{action['assignee']}" if action.get('assignee') else ""
                deadline = f" (due: {action['deadline'][:10]})" if action.get('deadline') else ""
                md.append(f"- [ ] {action['description']}{assignee}{deadline}")
        
        if segments:
            md.append("\n## Transcript\n")
            current_speaker = None
            for seg in segments:
                if seg.get('speaker') != current_speaker:
                    current_speaker = seg.get('speaker')
                    if current_speaker:
                        md.append(f"\n**{current_speaker}:**")
                md.append(seg.get('text', ''))
        
        return "\n".join(md)
    
    def on_meeting_start(self, callback: Callable):
        """Register callback for meeting start."""
        self._on_meeting_start.append(callback)
    
    def on_meeting_end(self, callback: Callable):
        """Register callback for meeting end."""
        self._on_meeting_end.append(callback)


# CLI Commands

@click.group()
@click.option('--config', '-c', default='config.yaml', help='Config file path')
@click.pass_context
def cli(ctx, config):
    """Always-On Meeting Intelligence Agent"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config


@cli.command()
@click.option('--input', '-i', type=click.Choice(['microphone', 'system', 'both']), default='both')
@click.option('--sensitivity', '-s', type=float, default=0.3)
@click.option('--debug', is_flag=True)
@click.pass_context
def start(ctx, input, sensitivity, debug):
    """Start the meeting intelligence agent."""
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    console.print(Panel.fit(
        "[bold cyan]Always-On Meeting Intelligence Agent[/bold cyan]\n"
        "Listening for voice activity to automatically capture meetings.",
        border_style="cyan"
    ))
    
    # Create agent
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    
    # Handle shutdown
    def signal_handler(sig, frame):
        console.print("\n[yellow]Shutting down...[/yellow]")
        agent.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start agent
    agent.start()
    
    # Keep running
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    while True:
        time.sleep(1)


@cli.command()
@click.argument('question')
@click.option('--meeting', '-m', help='Limit to specific meeting ID')
@click.pass_context
def query(ctx, question, meeting):
    """Ask a question about past meetings."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    
    with console.status("Searching meetings..."):
        answer = agent.query(question, meeting_id=meeting)
    
    console.print(Panel(answer, title="Answer", border_style="green"))


@cli.command('list-meetings')
@click.option('--limit', '-n', default=10, help='Number of meetings to show')
@click.pass_context
def list_meetings(ctx, limit):
    """List recent meetings."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    meetings = agent.get_meetings(limit=limit)
    
    if not meetings:
        console.print("[yellow]No meetings found[/yellow]")
        return
    
    table = Table(title="Recent Meetings")
    table.add_column("ID", style="cyan")
    table.add_column("Title")
    table.add_column("Date")
    table.add_column("Duration")
    table.add_column("Actions")
    
    for m in meetings:
        duration = f"{m.duration/60:.1f} min" if m.duration else "-"
        actions = len(agent.get_action_items(meeting_id=m.id))
        table.add_row(
            m.id,
            m.title[:40],
            m.start_time.strftime("%Y-%m-%d %H:%M"),
            duration,
            str(actions)
        )
    
    console.print(table)


@cli.command('show-meeting')
@click.argument('meeting_id')
@click.pass_context
def show_meeting(ctx, meeting_id):
    """Show details of a specific meeting."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    meeting = agent.get_meeting(meeting_id)
    
    if not meeting:
        console.print(f"[red]Meeting {meeting_id} not found[/red]")
        return
    
    console.print(Panel(f"[bold]{meeting.title}[/bold]", style="cyan"))
    console.print(f"Date: {meeting.start_time.strftime('%Y-%m-%d %H:%M')}")
    console.print(f"Duration: {meeting.duration/60:.1f} minutes")
    
    if meeting.participants:
        console.print(f"Participants: {', '.join(meeting.participants)}")
    
    if meeting.summary:
        console.print("\n[bold]Summary:[/bold]")
        console.print(meeting.summary)
    
    actions = agent.get_action_items(meeting_id=meeting_id)
    if actions:
        console.print(f"\n[bold]Action Items ({len(actions)}):[/bold]")
        for a in actions:
            status = "✓" if a['status'] == 'done' else "○"
            console.print(f"  {status} {a['description']}")


@cli.command('list-actions')
@click.option('--status', '-s', type=click.Choice(['todo', 'in_progress', 'done']))
@click.option('--meeting', '-m', help='Filter by meeting ID')
@click.pass_context
def list_actions(ctx, status, meeting):
    """List action items."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    actions = agent.get_action_items(meeting_id=meeting, status=status)
    
    if not actions:
        console.print("[yellow]No action items found[/yellow]")
        return
    
    table = Table(title="Action Items")
    table.add_column("ID", style="cyan")
    table.add_column("Description")
    table.add_column("Assignee")
    table.add_column("Deadline")
    table.add_column("Status")
    
    for a in actions:
        deadline = a.get('deadline', '-')
        if deadline and deadline != '-':
            deadline = deadline[:10]
        
        table.add_row(
            a['id'][:15],
            a['description'][:50],
            a.get('assignee', '-') or '-',
            deadline,
            a.get('status', 'todo')
        )
    
    console.print(table)


@cli.command()
@click.argument('meeting_id')
@click.option('--format', '-f', type=click.Choice(['markdown', 'json', 'text']), default='markdown')
@click.option('--output', '-o', help='Output file path')
@click.pass_context
def export(ctx, meeting_id, format, output):
    """Export meeting notes."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    
    content = agent.export_notes(meeting_id, format=format)
    
    if not content:
        console.print(f"[red]Meeting {meeting_id} not found[/red]")
        return
    
    if output:
        Path(output).write_text(content)
        console.print(f"[green]Exported to {output}[/green]")
    else:
        console.print(content)


@cli.command('export-actions')
@click.argument('meeting_id')
@click.option('--target', '-t', type=click.Choice(['jira', 'asana']), required=True)
@click.pass_context
def export_actions(ctx, meeting_id, target):
    """Export action items to Jira or Asana."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    agent._init_integrations()
    
    actions = agent.get_action_items(meeting_id=meeting_id)
    if not actions:
        console.print("[yellow]No action items found[/yellow]")
        return
    
    meeting = agent.get_meeting(meeting_id)
    meeting_title = meeting.title if meeting else meeting_id
    
    if target == 'jira':
        if not agent._jira:
            console.print("[red]Jira integration not configured[/red]")
            return
        
        with console.status("Creating Jira issues..."):
            issues = agent._jira.create_batch(actions, meeting_title=meeting_title)
        
        console.print(f"[green]Created {len(issues)} Jira issues[/green]")
        for issue in issues:
            console.print(f"  {issue.key}: {issue.url}")
    
    elif target == 'asana':
        if not agent._asana:
            console.print("[red]Asana integration not configured[/red]")
            return
        
        with console.status("Creating Asana tasks..."):
            tasks = agent._asana.create_batch(actions, meeting_title=meeting_title)
        
        console.print(f"[green]Created {len(tasks)} Asana tasks[/green]")


@cli.command()
@click.pass_context
def stats(ctx):
    """Show agent statistics."""
    agent = MeetingIntelligenceAgent(config_path=ctx.obj['config'])
    stats = agent._database.get_stats()
    
    console.print(Panel.fit(
        f"[bold]Meeting Intelligence Stats[/bold]\n\n"
        f"Total Meetings: {stats['total_meetings']}\n"
        f"Total Action Items: {stats['total_action_items']}\n"
        f"Pending Actions: {stats['pending_actions']}\n"
        f"Total Meeting Hours: {stats['total_meeting_hours']}",
        border_style="cyan"
    ))


@cli.command()
@click.pass_context
def devices(ctx):
    """List available audio input devices."""
    from src.audio.detector import AudioActivityMonitor
    
    devices = AudioActivityMonitor.list_input_devices()
    
    if not devices:
        console.print("[yellow]No audio input devices found[/yellow]")
        return
    
    table = Table(title="Audio Input Devices")
    table.add_column("Index", style="cyan")
    table.add_column("Name")
    table.add_column("Channels")
    table.add_column("Sample Rate")
    
    for d in devices:
        table.add_row(
            str(d['index']),
            d['name'],
            str(d['channels']),
            str(int(d['sample_rate']))
        )
    
    console.print(table)


if __name__ == "__main__":
    cli()
