"""
Speaker diarization for the Meeting Intelligence Agent.
Identifies and tracks different speakers in audio.
"""
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

# Try importing pyannote
try:
    from pyannote.audio import Pipeline
    from pyannote.audio.pipelines.utils.hook import ProgressHook
    HAS_PYANNOTE = True
except ImportError:
    HAS_PYANNOTE = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False


@dataclass
class SpeakerSegment:
    """A segment of audio attributed to a speaker."""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float = 1.0
    
    @property
    def duration(self) -> float:
        """Get segment duration in seconds."""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'speaker_id': self.speaker_id,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'confidence': self.confidence,
            'duration': self.duration
        }


@dataclass
class Speaker:
    """Information about a speaker."""
    id: str
    name: Optional[str] = None
    total_speaking_time: float = 0.0
    segment_count: int = 0
    embedding: Optional[np.ndarray] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'total_speaking_time': self.total_speaking_time,
            'segment_count': self.segment_count
        }


@dataclass
class DiarizationResult:
    """Result of speaker diarization."""
    segments: List[SpeakerSegment] = field(default_factory=list)
    speakers: Dict[str, Speaker] = field(default_factory=dict)
    duration: float = 0.0
    
    def get_speaker_timeline(self) -> List[Tuple[float, float, str]]:
        """Get timeline of (start, end, speaker_id) tuples."""
        return [(s.start_time, s.end_time, s.speaker_id) for s in self.segments]
    
    def get_speaker_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics per speaker."""
        stats = {}
        for speaker_id, speaker in self.speakers.items():
            stats[speaker_id] = {
                'name': speaker.name or speaker_id,
                'total_time': speaker.total_speaking_time,
                'percentage': (speaker.total_speaking_time / self.duration * 100) if self.duration > 0 else 0,
                'segments': speaker.segment_count
            }
        return stats
    
    def get_speaker_at_time(self, timestamp: float) -> Optional[str]:
        """Get speaker at a specific timestamp."""
        for seg in self.segments:
            if seg.start_time <= timestamp <= seg.end_time:
                return seg.speaker_id
        return None
    
    def merge_adjacent_segments(self, max_gap: float = 0.5) -> 'DiarizationResult':
        """Merge adjacent segments from the same speaker."""
        if not self.segments:
            return self
        
        merged = []
        current = self.segments[0]
        
        for seg in self.segments[1:]:
            if seg.speaker_id == current.speaker_id and seg.start_time - current.end_time <= max_gap:
                # Merge
                current = SpeakerSegment(
                    speaker_id=current.speaker_id,
                    start_time=current.start_time,
                    end_time=seg.end_time,
                    confidence=(current.confidence + seg.confidence) / 2
                )
            else:
                merged.append(current)
                current = seg
        
        merged.append(current)
        
        # Update speaker stats
        speakers = {}
        for seg in merged:
            if seg.speaker_id not in speakers:
                speakers[seg.speaker_id] = Speaker(id=seg.speaker_id)
            speakers[seg.speaker_id].total_speaking_time += seg.duration
            speakers[seg.speaker_id].segment_count += 1
        
        return DiarizationResult(
            segments=merged,
            speakers=speakers,
            duration=self.duration
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'segments': [s.to_dict() for s in self.segments],
            'speakers': {k: v.to_dict() for k, v in self.speakers.items()},
            'duration': self.duration,
            'stats': self.get_speaker_stats()
        }


class SpeakerDiarizer:
    """
    Performs speaker diarization on audio.
    Uses pyannote.audio for speaker identification.
    """
    
    def __init__(
        self,
        model_name: str = "pyannote/speaker-diarization-3.1",
        hf_token: Optional[str] = None,
        max_speakers: int = 10,
        min_speakers: Optional[int] = None,
        device: str = "auto"
    ):
        """
        Initialize the speaker diarizer.
        
        Args:
            model_name: Pyannote model name
            hf_token: Hugging Face access token
            max_speakers: Maximum number of speakers
            min_speakers: Minimum number of speakers (None for auto)
            device: Device to use ('auto', 'cuda', 'cpu')
        """
        self.model_name = model_name
        self.hf_token = hf_token or os.getenv("HF_TOKEN", "")
        self.max_speakers = max_speakers
        self.min_speakers = min_speakers
        
        # Determine device
        if device == "auto":
            if HAS_TORCH and torch.cuda.is_available():
                self.device = torch.device("cuda")
            else:
                self.device = torch.device("cpu")
        else:
            self.device = torch.device(device)
        
        self._pipeline = None
        self._initialized = False
    
    def _initialize(self):
        """Initialize the diarization pipeline."""
        if self._initialized:
            return
        
        if not HAS_PYANNOTE:
            raise ImportError("pyannote.audio is required for speaker diarization")
        
        logger.info(f"Loading diarization model: {self.model_name}")
        
        # Load pipeline
        self._pipeline = Pipeline.from_pretrained(
            self.model_name,
            use_auth_token=self.hf_token if self.hf_token else None
        )
        
        # Move to device
        if HAS_TORCH:
            self._pipeline = self._pipeline.to(self.device)
        
        self._initialized = True
        logger.info(f"Diarization model loaded on {self.device}")
    
    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """
        Perform speaker diarization on an audio file.
        
        Args:
            audio_path: Path to audio file
            num_speakers: Known number of speakers (None for auto)
            
        Returns:
            DiarizationResult with speaker segments
        """
        self._initialize()
        
        logger.info(f"Diarizing: {audio_path}")
        
        # Configure pipeline
        kwargs = {}
        if num_speakers:
            kwargs['num_speakers'] = num_speakers
        elif self.min_speakers and self.max_speakers:
            kwargs['min_speakers'] = self.min_speakers
            kwargs['max_speakers'] = self.max_speakers
        
        # Run diarization
        diarization = self._pipeline(audio_path, **kwargs)
        
        # Parse results
        segments = []
        speakers = {}
        
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            seg = SpeakerSegment(
                speaker_id=speaker,
                start_time=turn.start,
                end_time=turn.end
            )
            segments.append(seg)
            
            # Update speaker info
            if speaker not in speakers:
                speakers[speaker] = Speaker(id=speaker)
            speakers[speaker].total_speaking_time += seg.duration
            speakers[speaker].segment_count += 1
        
        # Get duration
        duration = segments[-1].end_time if segments else 0.0
        
        result = DiarizationResult(
            segments=segments,
            speakers=speakers,
            duration=duration
        )
        
        # Merge adjacent segments
        result = result.merge_adjacent_segments()
        
        logger.info(f"Found {len(speakers)} speakers")
        
        return result
    
    def diarize_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        num_speakers: Optional[int] = None
    ) -> DiarizationResult:
        """
        Perform speaker diarization on audio array.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            num_speakers: Known number of speakers
            
        Returns:
            DiarizationResult with speaker segments
        """
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            import soundfile as sf
            sf.write(f.name, audio_data, sample_rate)
            try:
                return self.diarize(f.name, num_speakers)
            finally:
                os.unlink(f.name)


class SimpleSpeakerDiarizer:
    """
    Simple speaker diarization using basic audio features.
    Fallback when pyannote is not available.
    """
    
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_duration: float = 0.5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize simple diarizer.
        
        Args:
            sample_rate: Audio sample rate
            frame_duration: Duration of each analysis frame
            similarity_threshold: Threshold for speaker clustering
        """
        self.sample_rate = sample_rate
        self.frame_duration = frame_duration
        self.frame_size = int(sample_rate * frame_duration)
        self.similarity_threshold = similarity_threshold
        
        # Speaker embeddings
        self._embeddings: Dict[str, np.ndarray] = {}
        self._speaker_count = 0
    
    def diarize_array(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000
    ) -> DiarizationResult:
        """
        Perform simple diarization on audio.
        
        Args:
            audio_data: Audio data
            sample_rate: Sample rate
            
        Returns:
            DiarizationResult
        """
        # Resample if needed
        if sample_rate != self.sample_rate:
            from scipy import signal
            audio_data = signal.resample(
                audio_data,
                int(len(audio_data) * self.sample_rate / sample_rate)
            )
        
        segments = []
        speakers = {}
        
        # Process frames
        for i in range(0, len(audio_data) - self.frame_size, self.frame_size):
            frame = audio_data[i:i + self.frame_size]
            start_time = i / self.sample_rate
            end_time = (i + self.frame_size) / self.sample_rate
            
            # Extract simple features
            features = self._extract_features(frame)
            
            # Check if this is voice
            if np.max(np.abs(frame)) < 0.01:
                continue
            
            # Find or create speaker
            speaker_id = self._find_speaker(features)
            
            # Create segment
            seg = SpeakerSegment(
                speaker_id=speaker_id,
                start_time=start_time,
                end_time=end_time
            )
            segments.append(seg)
            
            # Update speaker
            if speaker_id not in speakers:
                speakers[speaker_id] = Speaker(id=speaker_id)
            speakers[speaker_id].total_speaking_time += seg.duration
            speakers[speaker_id].segment_count += 1
        
        duration = len(audio_data) / self.sample_rate
        
        result = DiarizationResult(
            segments=segments,
            speakers=speakers,
            duration=duration
        )
        
        # Merge adjacent
        return result.merge_adjacent_segments()
    
    def _extract_features(self, frame: np.ndarray) -> np.ndarray:
        """Extract simple audio features from frame."""
        from scipy import fftpack
        
        # Basic features: spectral centroid, energy, zero crossing rate
        features = []
        
        # Energy
        energy = np.sum(frame ** 2)
        features.append(energy)
        
        # Zero crossing rate
        zcr = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
        features.append(zcr)
        
        # Spectral features
        spectrum = np.abs(fftpack.fft(frame)[:len(frame) // 2])
        freqs = np.linspace(0, self.sample_rate / 2, len(spectrum))
        
        # Spectral centroid
        centroid = np.sum(freqs * spectrum) / (np.sum(spectrum) + 1e-10)
        features.append(centroid)
        
        # Spectral spread
        spread = np.sqrt(np.sum(((freqs - centroid) ** 2) * spectrum) / (np.sum(spectrum) + 1e-10))
        features.append(spread)
        
        return np.array(features)
    
    def _find_speaker(self, features: np.ndarray) -> str:
        """Find matching speaker or create new one."""
        # Compare with existing speakers
        best_speaker = None
        best_similarity = 0.0
        
        for speaker_id, embedding in self._embeddings.items():
            similarity = self._cosine_similarity(features, embedding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_speaker = speaker_id
        
        # Create new speaker if no match
        if best_similarity < self.similarity_threshold:
            self._speaker_count += 1
            speaker_id = f"SPEAKER_{self._speaker_count:02d}"
            self._embeddings[speaker_id] = features
            return speaker_id
        
        # Update embedding with running average
        if best_speaker:
            self._embeddings[best_speaker] = (
                0.9 * self._embeddings[best_speaker] + 0.1 * features
            )
        
        return best_speaker or "SPEAKER_00"
    
    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)


def get_diarizer(
    use_pyannote: bool = True,
    **kwargs
) -> SpeakerDiarizer:
    """
    Get a speaker diarizer instance.
    
    Args:
        use_pyannote: Whether to use pyannote (if available)
        **kwargs: Additional arguments for the diarizer
        
    Returns:
        SpeakerDiarizer or SimpleSpeakerDiarizer instance
    """
    if use_pyannote and HAS_PYANNOTE:
        return SpeakerDiarizer(**kwargs)
    else:
        logger.warning("Using simple diarizer (pyannote not available)")
        return SimpleSpeakerDiarizer(**kwargs)
