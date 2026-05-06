"""Quantitative comparison of spectra."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial.distance import cosine

from lab_oralidade.spectrum import SpectrumResult


@dataclass
class ComparisonResult:
    """Metrics from comparing two spectra."""

    cosine_similarity: float
    dominant_freq_diff_hz: float
    spectral_centroid_diff_hz: float

    @property
    def similarity_percent(self) -> float:
        """Cosine similarity as a percentage (0-100)."""
        return self.cosine_similarity * 100


def compare_spectra(
    reference: SpectrumResult,
    target: SpectrumResult,
    band: tuple[float, float] = (80.0, 4000.0),
) -> ComparisonResult:
    """Compare two spectra quantitatively within a frequency band.

    Focuses on the speech-relevant frequency range by default (80–4000 Hz).
    """
    ref_freqs, ref_mags = reference.band(*band)
    tgt_freqs, tgt_mags = target.band(*band)

    # Align lengths (interpolate target to reference frequency grid)
    if len(ref_mags) != len(tgt_mags):
        tgt_mags = np.interp(ref_freqs, tgt_freqs, tgt_mags)

    # Cosine similarity
    cos_sim = 1.0 - cosine(ref_mags, tgt_mags)

    # Dominant frequency difference
    dom_diff = abs(reference.dominant_frequency - target.dominant_frequency)

    # Spectral centroid difference
    ref_centroid = _spectral_centroid(ref_freqs, ref_mags)
    tgt_centroid = _spectral_centroid(ref_freqs, tgt_mags)
    centroid_diff = abs(ref_centroid - tgt_centroid)

    return ComparisonResult(
        cosine_similarity=cos_sim,
        dominant_freq_diff_hz=dom_diff,
        spectral_centroid_diff_hz=centroid_diff,
    )


def _spectral_centroid(frequencies: np.ndarray, magnitudes: np.ndarray) -> float:
    """Compute spectral centroid (weighted mean frequency)."""
    total = np.sum(magnitudes)
    if total == 0:
        return 0.0
    return float(np.sum(frequencies * magnitudes) / total)
