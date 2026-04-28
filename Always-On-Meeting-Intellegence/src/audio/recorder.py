"""
Audio recorder for the Meeting Intelligence Agent.
Records audio during meetings for transcription and reference.
"""
import numpy as np
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Callable
from dataclasses import dataclass
import queue
import logging
import wave
import io

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False

from src.audio.audio_utils import save_audio, normalize_audio

logger = logging.getLogger(__name__)


@dataclass
class RecordingMetadata:
    """Metadata for an audio recording."""
    recording_id: str
    file_path: str
    start_time: datetime
    end_time: Optional[datetime]
    duration: float
    sample_rate: int
    channels: int
    format: str
    file_size: int


class AudioBuffer:
    """Thread-safe audio buffer for continuous recording."""
    
    def __init__(self, max_duration: float = 3600, sample_rate: int = 16000):
        """
        Initialize the audio buffer.
        
        Args:
            max_duration: Maximum buffer duration in seconds
            sample_rate: Audio sample rate
        """
        self.max_duration = max_duration
        self.sample_rate = sample_rate
        self.max_samples = int(max_duration * sample_rate)
        
        self._buffer: List[np.ndarray] = []
        self._total_samples = 0
        self._lock = threading.Lock()
    
    def append(self, audio_data: np.ndarray):
        """Append audio data to buffer."""
        with self._lock:
            self._buffer.append(audio_data.copy())
            self._total_samples += len(audio_data)
            
            # Trim if exceeds max duration
            while self._total_samples > self.max_samples and self._buffer:
                removed = self._buffer.pop(0)
                self._total_samples -= len(removed)
    
    def get_all(self) -> np.ndarray:
        """Get all audio data from buffer."""
        with self._lock:
            if not self._buffer:
                return np.array([], dtype=np.float32)
            return np.concatenate(self._buffer)
    
    def get_duration(self) -> float:
        """Get current buffer duration in seconds."""
        with self._lock:
            return self._total_samples / self.sample_rate
    
    def clear(self):
        """Clear the buffer."""
        with self._lock:
            self._buffer.clear()
            self._total_samples = 0


class AudioRecorder:
    """
    Records audio to files.
    Supports real-time streaming and post-recording save.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        channels: int = 1,
        recordings_path: str = "./data/recordings",
        format: str = "wav",
        input_device: Optional[int] = None
    ):
        """
        Initialize the audio recorder.
        
        Args:
            sample_rate: Audio sample rate
            channels: Number of audio channels
            recordings_path: Directory to save recordings
            format: Audio format (wav, flac, mp3)
            input_device: Input device index (None for default)
        """
        if not HAS_SOUNDDEVICE:
            raise ImportError("sounddevice is required for recording")
        
        self.sample_rate = sample_rate
        self.channels = channels
        self.recordings_path = Path(recordings_path)
        self.format = format
        self.input_device = input_device
        
        # Create recordings directory
        self.recordings_path.mkdir(parents=True, exist_ok=True)
        
        # Recording state
        self._recording = False
        self._stream: Optional[sd.InputStream] = None
        self._buffer = AudioBuffer(sample_rate=sample_rate)
        self._current_recording_id: Optional[str] = None
        self._recording_start: Optional[datetime] = None
        
        # Streaming
        self._audio_queue: queue.Queue = queue.Queue()
        self._on_audio_chunk: Optional[Callable[[np.ndarray], None]] = None
        
        # Thread safety
        self._lock = threading.Lock()
    
    def on_audio_chunk(self, callback: Callable[[np.ndarray], None]):
        """Set callback for receiving audio chunks while recording."""
        self._on_audio_chunk = callback
    
    def start_recording(self, recording_id: Optional[str] = None) -> str:
        """
        Start recording audio.
        
        Args:
            recording_id: Optional custom recording ID
            
        Returns:
            Recording ID
        """
        with self._lock:
            if self._recording:
                logger.warning("Already recording")
                return self._current_recording_id or ""
            
            # Generate recording ID
            if recording_id is None:
                recording_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            self._current_recording_id = recording_id
            self._recording_start = datetime.now()
            self._buffer.clear()
            self._recording = True
            
            # Start audio stream
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32',
                device=self.input_device,
                blocksize=int(self.sample_rate * 0.1),  # 100ms blocks
                callback=self._audio_callback
            )
            self._stream.start()
            
            logger.info(f"Started recording: {recording_id}")
            return recording_id
    
    def stop_recording(self, save: bool = True) -> Optional[RecordingMetadata]:
        """
        Stop recording audio.
        
        Args:
            save: Whether to save the recording
            
        Returns:
            Recording metadata if saved, None otherwise
        """
        with self._lock:
            if not self._recording:
                logger.warning("Not recording")
                return None
            
            self._recording = False
            
            # Stop stream
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None
            
            recording_id = self._current_recording_id
            start_time = self._recording_start
            
            # Get recorded audio
            audio_data = self._buffer.get_all()
            duration = len(audio_data) / self.sample_rate
            
            logger.info(f"Stopped recording: {recording_id} (duration: {duration:.1f}s)")
            
            # Save if requested
            metadata = None
            if save and len(audio_data) > 0:
                metadata = self._save_recording(
                    audio_data,
                    recording_id or "unknown",
                    start_time or datetime.now(),
                    duration
                )
            
            # Clear state
            self._current_recording_id = None
            self._recording_start = None
            self._buffer.clear()
            
            return metadata
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        
        if not self._recording:
            return
        
        # Get audio data
        if self.channels == 1:
            audio_data = indata[:, 0]
        else:
            audio_data = indata
        
        # Add to buffer
        self._buffer.append(audio_data)
        
        # Callback for streaming
        if self._on_audio_chunk:
            self._on_audio_chunk(audio_data.copy())
    
    def _save_recording(
        self,
        audio_data: np.ndarray,
        recording_id: str,
        start_time: datetime,
        duration: float
    ) -> RecordingMetadata:
        """Save recording to file."""
        # Generate filename
        filename = f"{recording_id}.{self.format}"
        file_path = self.recordings_path / filename
        
        # Normalize audio
        audio_data = normalize_audio(audio_data)
        
        # Save using soundfile
        if HAS_SOUNDFILE:
            sf.write(str(file_path), audio_data, self.sample_rate)
        else:
            # Fallback to wave module
            with wave.open(str(file_path), 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())
        
        # Get file size
        file_size = file_path.stat().st_size
        
        metadata = RecordingMetadata(
            recording_id=recording_id,
            file_path=str(file_path),
            start_time=start_time,
            end_time=datetime.now(),
            duration=duration,
            sample_rate=self.sample_rate,
            channels=self.channels,
            format=self.format,
            file_size=file_size
        )
        
        logger.info(f"Saved recording: {file_path}")
        return metadata
    
    def add_audio_data(self, audio_data: np.ndarray):
        """Add audio data to buffer (for external sources)."""
        if self._recording:
            self._buffer.append(audio_data)
            
            if self._on_audio_chunk:
                self._on_audio_chunk(audio_data.copy())
    
    def get_current_audio(self) -> np.ndarray:
        """Get current recorded audio."""
        return self._buffer.get_all()
    
    def get_current_duration(self) -> float:
        """Get current recording duration in seconds."""
        return self._buffer.get_duration()
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._recording
    
    @property
    def current_recording_id(self) -> Optional[str]:
        """Get current recording ID."""
        return self._current_recording_id
    
    def list_recordings(self) -> List[str]:
        """List all recordings."""
        recordings = []
        for file in self.recordings_path.glob(f"*.{self.format}"):
            recordings.append(file.stem)
        return sorted(recordings, reverse=True)
    
    def get_recording_path(self, recording_id: str) -> Optional[Path]:
        """Get path to a recording file."""
        file_path = self.recordings_path / f"{recording_id}.{self.format}"
        if file_path.exists():
            return file_path
        return None
    
    def delete_recording(self, recording_id: str) -> bool:
        """Delete a recording."""
        file_path = self.recordings_path / f"{recording_id}.{self.format}"
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Deleted recording: {recording_id}")
            return True
        return False


class StreamingRecorder:
    """
    Real-time streaming recorder that processes audio chunks as they arrive.
    Useful for live transcription.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_duration: float = 0.5,
        on_chunk: Optional[Callable[[np.ndarray, float], None]] = None
    ):
        """
        Initialize the streaming recorder.
        
        Args:
            sample_rate: Audio sample rate
            chunk_duration: Duration of each chunk in seconds
            on_chunk: Callback for each audio chunk (audio_data, timestamp)
        """
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self._on_chunk = on_chunk
        
        self._buffer = np.array([], dtype=np.float32)
        self._start_time: Optional[float] = None
        self._lock = threading.Lock()
    
    def start(self):
        """Start streaming."""
        self._start_time = time.time()
        self._buffer = np.array([], dtype=np.float32)
    
    def add_audio(self, audio_data: np.ndarray):
        """Add audio data and process chunks."""
        with self._lock:
            if self._start_time is None:
                self._start_time = time.time()
            
            # Append to buffer
            self._buffer = np.concatenate([self._buffer, audio_data])
            
            # Process complete chunks
            while len(self._buffer) >= self.chunk_size:
                chunk = self._buffer[:self.chunk_size]
                self._buffer = self._buffer[self.chunk_size:]
                
                # Calculate timestamp
                elapsed = time.time() - self._start_time
                timestamp = elapsed - (len(self._buffer) / self.sample_rate)
                
                if self._on_chunk:
                    self._on_chunk(chunk, timestamp)
    
    def flush(self):
        """Flush remaining audio in buffer."""
        with self._lock:
            if len(self._buffer) > 0 and self._on_chunk:
                timestamp = time.time() - (self._start_time or time.time())
                self._on_chunk(self._buffer.copy(), timestamp)
                self._buffer = np.array([], dtype=np.float32)
    
    def stop(self):
        """Stop streaming and flush."""
        self.flush()
        self._start_time = None
