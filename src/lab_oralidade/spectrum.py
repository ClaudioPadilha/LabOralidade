"""Fourier spectral analysis of audio signals."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.fft import rfft, rfftfreq

from lab_oralidade.audio import AudioSignal


@dataclass(frozen=True)
class SpectrumResult:
    """Result of a spectral analysis."""

    frequencies: NDArray[np.float64]
    magnitudes: NDArray[np.float64]
    sample_rate: int
    n_fft: int

    @property
    def dominant_frequency(self) -> float:
        """Frequency with the highest magnitude."""
        return float(self.frequencies[np.argmax(self.magnitudes)])

    def band(self, low_hz: float, high_hz: float) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Extract a frequency band subset."""
        mask = (self.frequencies >= low_hz) & (self.frequencies <= high_hz)
        return self.frequencies[mask], self.magnitudes[mask]


class SpectrumAnalyzer:
    """Configurable FFT-based spectrum analyzer."""

    def __init__(self, n_fft: int = 2048, window: str = "hann"):
        self.n_fft = n_fft
        self.window = window

    def compute(self, signal: AudioSignal) -> SpectrumResult:
        """Compute the magnitude spectrum of an audio signal."""
        samples = signal.samples

        # Apply window function
        if len(samples) > self.n_fft:
            samples = samples[: self.n_fft]
        win = np.ones(len(samples))
        if self.window == "hann":
            win = np.hanning(len(samples))
        elif self.window == "hamming":
            win = np.hamming(len(samples))
        windowed = samples * win

        # Compute FFT
        spectrum = rfft(windowed, n=self.n_fft)
        magnitudes = np.abs(spectrum) / self.n_fft
        frequencies = rfftfreq(self.n_fft, d=1.0 / signal.sample_rate)

        return SpectrumResult(
            frequencies=frequencies,
            magnitudes=magnitudes,
            sample_rate=signal.sample_rate,
            n_fft=self.n_fft,
        )

    def compute_formants(
        self, signal: AudioSignal, n_formants: int = 4
    ) -> list[float]:
        """Estimate formant frequencies using LPC-based peak picking.

        Returns the first n_formants formant frequencies in Hz.
        Useful for vowel comparison in phonetics.
        """
        from scipy.signal import lfilter, lpc

        pre_emphasized = np.append(signal.samples[0], signal.samples[1:] - 0.97 * signal.samples[:-1])

        # LPC analysis
        order = 2 + signal.sample_rate // 1000
        a = lpc(pre_emphasized.astype(np.float64), order)

        # Find roots of LPC polynomial
        roots = np.roots(a)
        roots = roots[np.imag(roots) >= 0]  # keep positive frequencies

        # Convert to frequencies
        angles = np.arctan2(np.imag(roots), np.real(roots))
        freqs = sorted(angles * (signal.sample_rate / (2 * np.pi)))
        freqs = [f for f in freqs if 90 < f < signal.sample_rate / 2]

        return freqs[:n_formants]
