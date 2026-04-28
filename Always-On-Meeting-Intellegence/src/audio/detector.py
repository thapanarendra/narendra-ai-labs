"""
Audio activity detection for the Meeting Intelligence Agent.
Detects voice activity to automatically start/stop recording.
"""
import numpy as np
import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass
from enum import Enum
import logging

try:
    import webrtcvad
    HAS_WEBRTCVAD = True
except ImportError:
    HAS_WEBRTCVAD = False

try:
    import sounddevice as sd
    HAS_SOUNDDEVICE = True
except ImportError:
    HAS_SOUNDDEVICE = False

from src.audio.audio_utils import calculate_rms, calculate_db

logger = logging.getLogger(__name__)


class VoiceActivityState(Enum):
    """Voice activity states."""
    SILENCE = "silence"
    VOICE_DETECTED = "voice_detected"
    SPEAKING = "speaking"
    PAUSE = "pause"


@dataclass
class VoiceActivityEvent:
    """Event data for voice activity changes."""
    state: VoiceActivityState
    timestamp: float
    duration: float
    confidence: float
    audio_level_db: float


class VoiceActivityDetector:
    """
    Detects voice activity in audio streams.
    Uses WebRTC VAD for accurate voice detection.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        sensitivity: float = 0.3,
        frame_duration_ms: int = 30,
        speech_threshold: float = 0.5,
        silence_threshold: float = 2.0,
        min_speech_duration: float = 0.3
    ):
        """
        Initialize the voice activity detector.
        
        Args:
            sample_rate: Audio sample rate (must be 8000, 16000, 32000, or 48000 for WebRTC VAD)
            sensitivity: Detection sensitivity (0.0 - 1.0, lower = more sensitive)
            frame_duration_ms: Frame duration for VAD (must be 10, 20, or 30 ms)
            speech_threshold: Ratio of speech frames to trigger speech detection
            silence_threshold: Seconds of silence to consider speech ended
            min_speech_duration: Minimum speech duration to trigger event
        """
        self.sample_rate = sample_rate
        self.sensitivity = sensitivity
        self.frame_duration_ms = frame_duration_ms
        self.speech_threshold = speech_threshold
        self.silence_threshold = silence_threshold
        self.min_speech_duration = min_speech_duration
        
        # Calculate frame size
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # Initialize WebRTC VAD if available
        self.vad = None
        if HAS_WEBRTCVAD:
            self.vad = webrtcvad.Vad()
            # Aggressiveness mode (0-3, 3 = most aggressive filtering)
            aggressiveness = int((1 - sensitivity) * 3)
            self.vad.set_mode(aggressiveness)
        
        # State tracking
        self._state = VoiceActivityState.SILENCE
        self._speech_start_time: Optional[float] = None
        self._last_speech_time: Optional[float] = None
        self._speech_frames = 0
        self._total_frames = 0
        
        # Callbacks
        self._on_voice_start: Optional[Callable[[VoiceActivityEvent], None]] = None
        self._on_voice_end: Optional[Callable[[VoiceActivityEvent], None]] = None
        self._on_state_change: Optional[Callable[[VoiceActivityEvent], None]] = None
        
        # Energy threshold for fallback detection
        self._energy_threshold = -30 + (sensitivity * 20)  # dB
        
        # Ring buffer for smoothing
        self._speech_history = []
        self._history_size = 10
    
    @property
    def state(self) -> VoiceActivityState:
        """Get current voice activity state."""
        return self._state
    
    def on_voice_start(self, callback: Callable[[VoiceActivityEvent], None]):
        """Set callback for when voice activity starts."""
        self._on_voice_start = callback
    
    def on_voice_end(self, callback: Callable[[VoiceActivityEvent], None]):
        """Set callback for when voice activity ends."""
        self._on_voice_end = callback
    
    def on_state_change(self, callback: Callable[[VoiceActivityEvent], None]):
        """Set callback for any state change."""
        self._on_state_change = callback
    
    def process_frame(self, audio_frame: np.ndarray) -> VoiceActivityEvent:
        """
        Process an audio frame and detect voice activity.
        
        Args:
            audio_frame: Audio data as numpy array (float32 or int16)
            
        Returns:
            VoiceActivityEvent with current state
        """
        current_time = time.time()
        
        # Ensure correct frame size
        if len(audio_frame) != self.frame_size:
            # Pad or truncate
            if len(audio_frame) < self.frame_size:
                audio_frame = np.pad(audio_frame, (0, self.frame_size - len(audio_frame)))
            else:
                audio_frame = audio_frame[:self.frame_size]
        
        # Calculate audio level
        audio_level_db = calculate_db(audio_frame)
        
        # Detect speech in frame
        is_speech = self._detect_speech_in_frame(audio_frame)
        
        # Update history
        self._speech_history.append(is_speech)
        if len(self._speech_history) > self._history_size:
            self._speech_history.pop(0)
        
        # Calculate speech ratio in history
        speech_ratio = sum(self._speech_history) / len(self._speech_history)
        
        # Update state machine
        old_state = self._state
        self._total_frames += 1
        
        if is_speech:
            self._speech_frames += 1
            self._last_speech_time = current_time
            
            if self._state == VoiceActivityState.SILENCE:
                if speech_ratio >= self.speech_threshold:
                    self._state = VoiceActivityState.VOICE_DETECTED
                    self._speech_start_time = current_time
            
            elif self._state == VoiceActivityState.VOICE_DETECTED:
                duration = current_time - (self._speech_start_time or current_time)
                if duration >= self.min_speech_duration:
                    self._state = VoiceActivityState.SPEAKING
            
            elif self._state == VoiceActivityState.PAUSE:
                self._state = VoiceActivityState.SPEAKING
        
        else:
            if self._state in (VoiceActivityState.SPEAKING, VoiceActivityState.VOICE_DETECTED):
                if self._last_speech_time:
                    silence_duration = current_time - self._last_speech_time
                    if silence_duration >= self.silence_threshold:
                        self._state = VoiceActivityState.SILENCE
                        self._reset_tracking()
                    elif silence_duration >= 0.5:
                        self._state = VoiceActivityState.PAUSE
        
        # Calculate confidence
        confidence = speech_ratio if is_speech else 1 - speech_ratio
        
        # Calculate duration
        duration = 0.0
        if self._speech_start_time:
            duration = current_time - self._speech_start_time
        
        # Create event
        event = VoiceActivityEvent(
            state=self._state,
            timestamp=current_time,
            duration=duration,
            confidence=confidence,
            audio_level_db=audio_level_db
        )
        
        # Trigger callbacks
        if self._state != old_state:
            if self._on_state_change:
                self._on_state_change(event)
            
            if self._state == VoiceActivityState.SPEAKING and old_state == VoiceActivityState.VOICE_DETECTED:
                if self._on_voice_start:
                    self._on_voice_start(event)
            
            elif self._state == VoiceActivityState.SILENCE and old_state in (VoiceActivityState.SPEAKING, VoiceActivityState.PAUSE):
                if self._on_voice_end:
                    self._on_voice_end(event)
        
        return event
    
    def _detect_speech_in_frame(self, audio_frame: np.ndarray) -> bool:
        """Detect if frame contains speech using VAD or energy threshold."""
        # Try WebRTC VAD first
        if self.vad is not None:
            try:
                # Convert to int16 for WebRTC VAD
                if audio_frame.dtype == np.float32 or audio_frame.dtype == np.float64:
                    audio_int16 = (audio_frame * 32767).astype(np.int16)
                else:
                    audio_int16 = audio_frame.astype(np.int16)
                
                return self.vad.is_speech(audio_int16.tobytes(), self.sample_rate)
            except Exception as e:
                logger.debug(f"WebRTC VAD failed, using energy threshold: {e}")
        
        # Fallback to energy threshold
        db = calculate_db(audio_frame)
        return db > self._energy_threshold
    
    def _reset_tracking(self):
        """Reset speech tracking state."""
        self._speech_start_time = None
        self._last_speech_time = None
        self._speech_frames = 0
        self._total_frames = 0
        self._speech_history.clear()
    
    def reset(self):
        """Reset the detector to initial state."""
        self._state = VoiceActivityState.SILENCE
        self._reset_tracking()


class AudioActivityMonitor:
    """
    Monitors audio input for activity and manages voice detection.
    Runs continuously in the background.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        input_device: Optional[int] = None,
        sensitivity: float = 0.3,
        silence_threshold: float = 2.0,
        min_speech_duration: float = 3.0
    ):
        """
        Initialize the audio activity monitor.
        
        Args:
            sample_rate: Audio sample rate
            input_device: Input device index (None for default)
            sensitivity: Detection sensitivity
            silence_threshold: Seconds of silence to end activity
            min_speech_duration: Minimum speech duration to trigger meeting
        """
        if not HAS_SOUNDDEVICE:
            raise ImportError("sounddevice is required for audio monitoring")
        
        self.sample_rate = sample_rate
        self.input_device = input_device
        self.sensitivity = sensitivity
        self.silence_threshold = silence_threshold
        self.min_speech_duration = min_speech_duration
        
        # Create VAD
        self.vad = VoiceActivityDetector(
            sample_rate=sample_rate,
            sensitivity=sensitivity,
            silence_threshold=silence_threshold,
            min_speech_duration=min_speech_duration
        )
        
        # State
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stream: Optional[sd.InputStream] = None
        
        # Callbacks
        self._on_meeting_start: Optional[Callable[[], None]] = None
        self._on_meeting_end: Optional[Callable[[float], None]] = None
        self._on_audio_data: Optional[Callable[[np.ndarray], None]] = None
        
        # Meeting tracking
        self._meeting_active = False
        self._meeting_start_time: Optional[float] = None
    
    def on_meeting_start(self, callback: Callable[[], None]):
        """Set callback for when a meeting starts."""
        self._on_meeting_start = callback
    
    def on_meeting_end(self, callback: Callable[[float], None]):
        """Set callback for when a meeting ends (receives duration in seconds)."""
        self._on_meeting_end = callback
    
    def on_audio_data(self, callback: Callable[[np.ndarray], None]):
        """Set callback for receiving audio data."""
        self._on_audio_data = callback
    
    def start(self):
        """Start monitoring audio."""
        if self._running:
            return
        
        self._running = True
        
        # Set up VAD callbacks
        self.vad.on_voice_start(self._handle_voice_start)
        self.vad.on_voice_end(self._handle_voice_end)
        
        # Start audio stream
        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype='float32',
            device=self.input_device,
            blocksize=self.vad.frame_size,
            callback=self._audio_callback
        )
        self._stream.start()
        
        logger.info("Audio activity monitor started")
    
    def stop(self):
        """Stop monitoring audio."""
        self._running = False
        
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        
        # Handle any active meeting
        if self._meeting_active:
            self._end_meeting()
        
        logger.info("Audio activity monitor stopped")
    
    def _audio_callback(self, indata, frames, time_info, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio stream status: {status}")
        
        # Get audio data
        audio_data = indata[:, 0]  # First channel
        
        # Process through VAD
        self.vad.process_frame(audio_data)
        
        # Forward audio data if in meeting
        if self._meeting_active and self._on_audio_data:
            self._on_audio_data(audio_data.copy())
    
    def _handle_voice_start(self, event: VoiceActivityEvent):
        """Handle voice activity start."""
        if not self._meeting_active and event.duration >= self.min_speech_duration:
            self._start_meeting()
    
    def _handle_voice_end(self, event: VoiceActivityEvent):
        """Handle voice activity end."""
        if self._meeting_active:
            self._end_meeting()
    
    def _start_meeting(self):
        """Start a new meeting."""
        self._meeting_active = True
        self._meeting_start_time = time.time()
        
        logger.info("Meeting started")
        
        if self._on_meeting_start:
            self._on_meeting_start()
    
    def _end_meeting(self):
        """End the current meeting."""
        duration = 0.0
        if self._meeting_start_time:
            duration = time.time() - self._meeting_start_time
        
        self._meeting_active = False
        self._meeting_start_time = None
        
        logger.info(f"Meeting ended (duration: {duration:.1f}s)")
        
        if self._on_meeting_end:
            self._on_meeting_end(duration)
    
    @property
    def is_meeting_active(self) -> bool:
        """Check if a meeting is currently active."""
        return self._meeting_active
    
    @staticmethod
    def list_input_devices() -> list:
        """List available input devices."""
        if not HAS_SOUNDDEVICE:
            return []
        
        devices = []
        for i, device in enumerate(sd.query_devices()):
            if device['max_input_channels'] > 0:
                devices.append({
                    'index': i,
                    'name': device['name'],
                    'channels': device['max_input_channels'],
                    'sample_rate': device['default_samplerate']
                })
        return devices
