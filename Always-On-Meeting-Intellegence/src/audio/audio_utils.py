"""
Audio utility functions for the Meeting Intelligence Agent.
"""
import numpy as np
from typing import Tuple, Optional
import soundfile as sf
from pathlib import Path


def calculate_rms(audio_data: np.ndarray) -> float:
    """Calculate the Root Mean Square (RMS) of audio data."""
    if len(audio_data) == 0:
        return 0.0
    return np.sqrt(np.mean(audio_data.astype(np.float64) ** 2))


def calculate_db(audio_data: np.ndarray) -> float:
    """Calculate decibels from audio data."""
    rms = calculate_rms(audio_data)
    if rms == 0:
        return -100.0
    return 20 * np.log10(rms)


def normalize_audio(audio_data: np.ndarray) -> np.ndarray:
    """Normalize audio to [-1, 1] range."""
    max_val = np.max(np.abs(audio_data))
    if max_val == 0:
        return audio_data
    return audio_data / max_val


def resample_audio(
    audio_data: np.ndarray, 
    original_rate: int, 
    target_rate: int
) -> np.ndarray:
    """Resample audio to a different sample rate."""
    if original_rate == target_rate:
        return audio_data
    
    from scipy import signal
    
    # Calculate the resampling ratio
    ratio = target_rate / original_rate
    new_length = int(len(audio_data) * ratio)
    
    return signal.resample(audio_data, new_length)


def convert_to_mono(audio_data: np.ndarray) -> np.ndarray:
    """Convert stereo audio to mono."""
    if len(audio_data.shape) == 1:
        return audio_data
    if audio_data.shape[1] == 1:
        return audio_data.flatten()
    # Average the channels
    return np.mean(audio_data, axis=1)


def split_audio_into_chunks(
    audio_data: np.ndarray, 
    chunk_size: int, 
    overlap: int = 0
) -> list:
    """Split audio data into chunks with optional overlap."""
    chunks = []
    step = chunk_size - overlap
    
    for i in range(0, len(audio_data) - chunk_size + 1, step):
        chunks.append(audio_data[i:i + chunk_size])
    
    # Handle the last chunk
    if len(audio_data) % step != 0:
        last_chunk = audio_data[-chunk_size:]
        if len(last_chunk) == chunk_size:
            chunks.append(last_chunk)
    
    return chunks


def save_audio(
    audio_data: np.ndarray,
    file_path: str,
    sample_rate: int,
    format: str = "wav"
) -> str:
    """Save audio data to a file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure proper extension
    if not path.suffix:
        path = path.with_suffix(f".{format}")
    
    sf.write(str(path), audio_data, sample_rate)
    return str(path)


def load_audio(
    file_path: str, 
    target_sample_rate: Optional[int] = None
) -> Tuple[np.ndarray, int]:
    """Load audio from a file."""
    audio_data, sample_rate = sf.read(file_path)
    
    # Convert to mono if needed
    audio_data = convert_to_mono(audio_data)
    
    # Resample if needed
    if target_sample_rate and sample_rate != target_sample_rate:
        audio_data = resample_audio(audio_data, sample_rate, target_sample_rate)
        sample_rate = target_sample_rate
    
    return audio_data, sample_rate


def get_audio_duration(file_path: str) -> float:
    """Get the duration of an audio file in seconds."""
    info = sf.info(file_path)
    return info.duration


def detect_silence(
    audio_data: np.ndarray,
    sample_rate: int,
    threshold_db: float = -40.0,
    min_silence_duration: float = 0.5
) -> list:
    """Detect silence regions in audio."""
    # Calculate frame size for analysis
    frame_size = int(sample_rate * 0.02)  # 20ms frames
    hop_size = frame_size // 2
    
    silence_regions = []
    in_silence = False
    silence_start = 0
    
    for i in range(0, len(audio_data) - frame_size, hop_size):
        frame = audio_data[i:i + frame_size]
        db = calculate_db(frame)
        
        if db < threshold_db:
            if not in_silence:
                in_silence = True
                silence_start = i / sample_rate
        else:
            if in_silence:
                silence_end = i / sample_rate
                if silence_end - silence_start >= min_silence_duration:
                    silence_regions.append((silence_start, silence_end))
                in_silence = False
    
    # Handle trailing silence
    if in_silence:
        silence_end = len(audio_data) / sample_rate
        if silence_end - silence_start >= min_silence_duration:
            silence_regions.append((silence_start, silence_end))
    
    return silence_regions


def trim_silence(
    audio_data: np.ndarray,
    sample_rate: int,
    threshold_db: float = -40.0,
    padding: float = 0.1
) -> np.ndarray:
    """Trim silence from the beginning and end of audio."""
    frame_size = int(sample_rate * 0.02)
    
    # Find start
    start_idx = 0
    for i in range(0, len(audio_data) - frame_size, frame_size):
        frame = audio_data[i:i + frame_size]
        if calculate_db(frame) >= threshold_db:
            start_idx = max(0, i - int(padding * sample_rate))
            break
    
    # Find end
    end_idx = len(audio_data)
    for i in range(len(audio_data) - frame_size, 0, -frame_size):
        frame = audio_data[i:i + frame_size]
        if calculate_db(frame) >= threshold_db:
            end_idx = min(len(audio_data), i + frame_size + int(padding * sample_rate))
            break
    
    return audio_data[start_idx:end_idx]


def apply_noise_reduction(
    audio_data: np.ndarray,
    sample_rate: int,
    noise_reduce_strength: float = 0.5
) -> np.ndarray:
    """Apply basic noise reduction using spectral gating."""
    from scipy import signal
    
    # Apply a simple high-pass filter to remove low-frequency noise
    nyquist = sample_rate / 2
    cutoff = 80 / nyquist  # 80 Hz cutoff
    
    if cutoff < 1:
        b, a = signal.butter(4, cutoff, btype='high')
        audio_data = signal.filtfilt(b, a, audio_data)
    
    return audio_data
