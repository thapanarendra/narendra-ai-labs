"""
Speech-to-text transcription for the Meeting Intelligence Agent.
Uses OpenAI Whisper for accurate transcription.
"""
import numpy as np
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Union
from dataclasses import dataclass, field
import queue
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

# Import Whisper (local or API)
try:
    import whisper
    HAS_LOCAL_WHISPER = True
except ImportError:
    HAS_LOCAL_WHISPER = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False


@dataclass
class TranscriptSegment:
    """A segment of transcribed speech."""
    id: int
    text: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    speaker: Optional[str] = None
    language: Optional[str] = None
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds."""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'text': self.text,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'confidence': self.confidence,
            'speaker': self.speaker,
            'language': self.language
        }


@dataclass
class Transcript:
    """Complete meeting transcript."""
    meeting_id: str
    segments: List[TranscriptSegment] = field(default_factory=list)
    language: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    duration: float = 0.0
    
    @property
    def full_text(self) -> str:
        """Get full transcript text."""
        return " ".join(seg.text for seg in self.segments)
    
    def get_text_with_speakers(self) -> str:
        """Get transcript text with speaker labels."""
        lines = []
        current_speaker = None
        current_text = []
        
        for seg in self.segments:
            if seg.speaker != current_speaker:
                if current_text:
                    speaker_label = current_speaker or "Unknown"
                    lines.append(f"{speaker_label}: {' '.join(current_text)}")
                current_speaker = seg.speaker
                current_text = [seg.text]
            else:
                current_text.append(seg.text)
        
        if current_text:
            speaker_label = current_speaker or "Unknown"
            lines.append(f"{speaker_label}: {' '.join(current_text)}")
        
        return "\n".join(lines)
    
    def get_text_with_timestamps(self) -> str:
        """Get transcript with timestamps."""
        lines = []
        for seg in self.segments:
            timestamp = f"[{self._format_time(seg.start_time)} - {self._format_time(seg.end_time)}]"
            speaker = f"{seg.speaker}: " if seg.speaker else ""
            lines.append(f"{timestamp} {speaker}{seg.text}")
        return "\n".join(lines)
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS."""
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'meeting_id': self.meeting_id,
            'segments': [seg.to_dict() for seg in self.segments],
            'language': self.language,
            'created_at': self.created_at.isoformat(),
            'duration': self.duration,
            'full_text': self.full_text
        }


class WhisperTranscriber:
    """
    Transcribes audio using OpenAI Whisper.
    Supports both local model and API.
    """
    
    def __init__(
        self,
        model_name: str = "base",
        use_local: bool = True,
        api_key: Optional[str] = None,
        language: Optional[str] = None,
        device: str = "auto"
    ):
        """
        Initialize the transcriber.
        
        Args:
            model_name: Whisper model name (tiny, base, small, medium, large)
            use_local: Use local model (True) or OpenAI API (False)
            api_key: OpenAI API key (for API mode)
            language: Language code (e.g., 'en') or None for auto-detect
            device: Device for local model ('auto', 'cuda', 'cpu')
        """
        self.model_name = model_name
        self.use_local = use_local
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.language = language
        self.device = device
        
        self._model = None
        self._client = None
        self._lock = threading.Lock()
        
        # Load model/client
        self._initialize()
    
    def _initialize(self):
        """Initialize the model or API client."""
        if self.use_local:
            if not HAS_LOCAL_WHISPER:
                raise ImportError("whisper package is required for local transcription")
            
            logger.info(f"Loading Whisper model: {self.model_name}")
            
            # Determine device
            device = self.device
            if device == "auto":
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
            
            self._model = whisper.load_model(self.model_name, device=device)
            logger.info(f"Whisper model loaded on {device}")
        else:
            if not HAS_OPENAI:
                raise ImportError("openai package is required for API transcription")
            
            self._client = OpenAI(api_key=self.api_key)
            logger.info("Using OpenAI Whisper API")
    
    def transcribe(
        self,
        audio_data: Union[np.ndarray, str, Path],
        sample_rate: int = 16000,
        timestamps: bool = True
    ) -> Transcript:
        """
        Transcribe audio data.
        
        Args:
            audio_data: Audio as numpy array or path to audio file
            sample_rate: Sample rate (if audio_data is numpy array)
            timestamps: Whether to include word-level timestamps
            
        Returns:
            Transcript object
        """
        with self._lock:
            if isinstance(audio_data, (str, Path)):
                return self._transcribe_file(str(audio_data), timestamps)
            else:
                return self._transcribe_array(audio_data, sample_rate, timestamps)
    
    def _transcribe_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        timestamps: bool
    ) -> Transcript:
        """Transcribe numpy array."""
        # Ensure float32
        if audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        
        # Normalize if needed
        if np.max(np.abs(audio_data)) > 1.0:
            audio_data = audio_data / 32768.0
        
        if self.use_local:
            return self._transcribe_local_array(audio_data, sample_rate, timestamps)
        else:
            # Save to temp file for API
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                import soundfile as sf
                sf.write(f.name, audio_data, sample_rate)
                try:
                    return self._transcribe_api(f.name, timestamps)
                finally:
                    os.unlink(f.name)
    
    def _transcribe_file(self, file_path: str, timestamps: bool) -> Transcript:
        """Transcribe audio file."""
        if self.use_local:
            return self._transcribe_local_file(file_path, timestamps)
        else:
            return self._transcribe_api(file_path, timestamps)
    
    def _transcribe_local_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int,
        timestamps: bool
    ) -> Transcript:
        """Transcribe using local Whisper model."""
        # Resample to 16kHz if needed
        if sample_rate != 16000:
            from scipy import signal
            audio_data = signal.resample(
                audio_data, 
                int(len(audio_data) * 16000 / sample_rate)
            )
        
        # Run Whisper
        options = {}
        if self.language:
            options['language'] = self.language
        
        result = self._model.transcribe(audio_data, **options)
        
        return self._parse_whisper_result(result)
    
    def _transcribe_local_file(self, file_path: str, timestamps: bool) -> Transcript:
        """Transcribe file using local Whisper model."""
        options = {}
        if self.language:
            options['language'] = self.language
        
        result = self._model.transcribe(file_path, **options)
        
        return self._parse_whisper_result(result)
    
    def _transcribe_api(self, file_path: str, timestamps: bool) -> Transcript:
        """Transcribe using OpenAI Whisper API."""
        with open(file_path, 'rb') as audio_file:
            kwargs = {
                'model': 'whisper-1',
                'file': audio_file,
                'response_format': 'verbose_json' if timestamps else 'json'
            }
            if self.language:
                kwargs['language'] = self.language
            
            result = self._client.audio.transcriptions.create(**kwargs)
        
        return self._parse_api_result(result)
    
    def _parse_whisper_result(self, result: dict) -> Transcript:
        """Parse local Whisper result."""
        segments = []
        
        for i, seg in enumerate(result.get('segments', [])):
            segments.append(TranscriptSegment(
                id=i,
                text=seg['text'].strip(),
                start_time=seg['start'],
                end_time=seg['end'],
                confidence=seg.get('no_speech_prob', 0),
                language=result.get('language')
            ))
        
        # Calculate duration
        duration = segments[-1].end_time if segments else 0.0
        
        return Transcript(
            meeting_id="",  # Will be set later
            segments=segments,
            language=result.get('language'),
            duration=duration
        )
    
    def _parse_api_result(self, result) -> Transcript:
        """Parse OpenAI API result."""
        segments = []
        
        # Handle verbose JSON response
        if hasattr(result, 'segments'):
            for i, seg in enumerate(result.segments):
                segments.append(TranscriptSegment(
                    id=i,
                    text=seg.text.strip(),
                    start_time=seg.start,
                    end_time=seg.end,
                    language=result.language
                ))
        else:
            # Simple response - create single segment
            segments.append(TranscriptSegment(
                id=0,
                text=result.text.strip(),
                start_time=0.0,
                end_time=0.0
            ))
        
        duration = segments[-1].end_time if segments else 0.0
        
        return Transcript(
            meeting_id="",
            segments=segments,
            language=getattr(result, 'language', None),
            duration=duration
        )


class StreamingTranscriber:
    """
    Real-time streaming transcription.
    Processes audio chunks and emits partial transcripts.
    """
    
    def __init__(
        self,
        model_name: str = "base",
        sample_rate: int = 16000,
        chunk_duration: float = 5.0,
        overlap_duration: float = 0.5,
        on_partial: Optional[Callable[[str, float], None]] = None,
        on_final: Optional[Callable[[TranscriptSegment], None]] = None
    ):
        """
        Initialize streaming transcriber.
        
        Args:
            model_name: Whisper model name
            sample_rate: Audio sample rate
            chunk_duration: Duration of each transcription chunk
            overlap_duration: Overlap between chunks for continuity
            on_partial: Callback for partial transcripts (text, timestamp)
            on_final: Callback for final segments
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.overlap_duration = overlap_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.overlap_size = int(sample_rate * overlap_duration)
        
        self._on_partial = on_partial
        self._on_final = on_final
        
        # Initialize transcriber
        self._transcriber = WhisperTranscriber(
            model_name=model_name,
            use_local=True
        )
        
        # Buffer for audio
        self._buffer = np.array([], dtype=np.float32)
        self._segment_id = 0
        self._base_time = 0.0
        
        # Processing queue
        self._queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Lock
        self._lock = threading.Lock()
    
    def start(self):
        """Start streaming transcription."""
        self._running = True
        self._thread = threading.Thread(target=self._process_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop streaming transcription."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5.0)
        self._flush()
    
    def add_audio(self, audio_data: np.ndarray, timestamp: float):
        """Add audio data for transcription."""
        with self._lock:
            self._buffer = np.concatenate([self._buffer, audio_data])
            
            # Check if we have enough for a chunk
            while len(self._buffer) >= self.chunk_size:
                chunk = self._buffer[:self.chunk_size].copy()
                self._buffer = self._buffer[self.chunk_size - self.overlap_size:]
                
                self._queue.put((chunk, self._base_time))
                self._base_time += self.chunk_duration - self.overlap_duration
    
    def _process_loop(self):
        """Process audio chunks in background."""
        while self._running:
            try:
                chunk, base_time = self._queue.get(timeout=0.5)
                self._transcribe_chunk(chunk, base_time)
            except queue.Empty:
                continue
    
    def _transcribe_chunk(self, chunk: np.ndarray, base_time: float):
        """Transcribe a single chunk."""
        try:
            transcript = self._transcriber.transcribe(chunk, self.sample_rate)
            
            for seg in transcript.segments:
                # Adjust timestamps
                seg.start_time += base_time
                seg.end_time += base_time
                seg.id = self._segment_id
                self._segment_id += 1
                
                # Emit partial
                if self._on_partial:
                    self._on_partial(seg.text, seg.start_time)
                
                # Emit final
                if self._on_final:
                    self._on_final(seg)
                    
        except Exception as e:
            logger.error(f"Transcription error: {e}")
    
    def _flush(self):
        """Flush remaining audio."""
        with self._lock:
            if len(self._buffer) > 0:
                # Pad to minimum size if needed
                min_samples = int(self.sample_rate * 1.0)
                if len(self._buffer) < min_samples:
                    self._buffer = np.pad(
                        self._buffer, 
                        (0, min_samples - len(self._buffer))
                    )
                
                self._transcribe_chunk(self._buffer, self._base_time)
                self._buffer = np.array([], dtype=np.float32)
    
    def get_transcript(self) -> List[TranscriptSegment]:
        """Get all transcribed segments so far."""
        # This would need to track segments - simplified here
        return []
