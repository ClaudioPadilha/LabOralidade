"""Fundamental frequency (F0) extraction using Praat via parselmouth."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import parselmouth
from numpy.typing import NDArray
from scipy.signal import medfilt


SEMITONE_REFERENCE_HZ = 55.0


@dataclass(frozen=True)
class PitchContour:
    """Result of a pitch (F0) extraction."""

    times: NDArray[np.float64]
    f0_values: NDArray[np.float64]

    @property
    def voiced_mask(self) -> NDArray[np.bool_]:
        """Boolean mask where True indicates voiced frames."""
        return ~np.isnan(self.f0_values) & (self.f0_values > 0)

    @property
    def mean_f0(self) -> float:
        """Mean F0 over voiced frames."""
        voiced = self.f0_values[self.voiced_mask]
        return float(np.mean(voiced)) if len(voiced) > 0 else 0.0

    @property
    def f0_range(self) -> tuple[float, float]:
        """(min, max) F0 over voiced frames."""
        voiced = self.f0_values[self.voiced_mask]
        if len(voiced) == 0:
            return (0.0, 0.0)
        return (float(np.min(voiced)), float(np.max(voiced)))

    def smooth(self, kernel_size: int = 5) -> PitchContour:
        """Apply median filter to remove pitch tracking outliers.

        Only filters voiced frames; unvoiced (NaN) frames are preserved.
        """
        f0 = self.f0_values.copy()
        voiced = self.voiced_mask
        if np.sum(voiced) >= kernel_size:
            f0[voiced] = medfilt(f0[voiced], kernel_size=kernel_size)
        return PitchContour(times=self.times.copy(), f0_values=f0)

    def to_semitones(self, reference_hz: float = SEMITONE_REFERENCE_HZ) -> NDArray[np.float64]:
        """Convert F0 values to semitones relative to a reference frequency.

        Unvoiced frames remain as NaN. Default reference is 55 Hz (A1),
        which keeps values positive for typical speech ranges.
        """
        with np.errstate(divide="ignore", invalid="ignore"):
            semitones = 12.0 * np.log2(self.f0_values / reference_hz)
        return semitones

    def normalized_times(self) -> NDArray[np.float64]:
        """Return times scaled to [0, 1] range."""
        t_min, t_max = self.times.min(), self.times.max()
        if t_max == t_min:
            return np.zeros_like(self.times)
        return (self.times - t_min) / (t_max - t_min)


def extract_pitch_contour(
    sound_path: str | Path,
    time_step: float = 0.01,
    pitch_floor: float = 75.0,
    pitch_ceiling: float = 600.0,
) -> PitchContour:
    """Extract the pitch contour (F0) from an audio file.

    Args:
        sound_path: Path to the audio file.
        time_step: Time step in seconds for F0 analysis (default 10ms).
        pitch_floor: Minimum expected F0 in Hz.
        pitch_ceiling: Maximum expected F0 in Hz.

    Returns:
        PitchContour with time points and corresponding F0 values.
        Unvoiced frames have F0 = 0 (replaced with NaN in the contour).
    """
    snd = parselmouth.Sound(str(sound_path))
    pitch = snd.to_pitch(
        time_step=time_step,
        pitch_floor=pitch_floor,
        pitch_ceiling=pitch_ceiling,
    )
    f0_values = pitch.selected_array["frequency"].copy()
    times = pitch.xs()

    # Replace unvoiced (0.0) with NaN for cleaner plotting
    f0_values[f0_values == 0.0] = np.nan

    return PitchContour(times=np.array(times), f0_values=f0_values)
