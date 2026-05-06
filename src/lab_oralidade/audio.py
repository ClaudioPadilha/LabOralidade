"""Audio file loading and signal preprocessing."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class AudioSignal:
    """Immutable representation of a mono audio signal."""

    samples: NDArray[np.float32]
    sample_rate: int

    @classmethod
    def from_file(cls, path: str | Path, target_sr: int = 22050) -> AudioSignal:
        """Load an audio file and resample to target sample rate.

        Converts to mono if stereo. Supports wav, mp3, flac, ogg.
        """
        samples, sr = librosa.load(str(path), sr=target_sr, mono=True)
        return cls(samples=samples, sample_rate=sr)

    @classmethod
    def from_array(cls, samples: NDArray[np.float32], sample_rate: int) -> AudioSignal:
        """Create from a numpy array (useful for testing with synthetic signals)."""
        return cls(samples=np.asarray(samples, dtype=np.float32), sample_rate=sample_rate)

    @property
    def duration(self) -> float:
        """Duration in seconds."""
        return len(self.samples) / self.sample_rate

    def trim_silence(self, top_db: float = 20.0) -> AudioSignal:
        """Remove leading and trailing silence."""
        trimmed, _ = librosa.effects.trim(self.samples, top_db=top_db)
        return AudioSignal(samples=trimmed, sample_rate=self.sample_rate)

    def normalize(self) -> AudioSignal:
        """Peak-normalize to [-1, 1]."""
        peak = np.max(np.abs(self.samples))
        if peak == 0:
            return self
        return AudioSignal(samples=self.samples / peak, sample_rate=self.sample_rate)
