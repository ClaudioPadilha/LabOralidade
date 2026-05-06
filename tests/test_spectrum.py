"""Tests for spectral analysis."""

import numpy as np
import pytest

from lab_oralidade.audio import AudioSignal
from lab_oralidade.comparison import compare_spectra
from lab_oralidade.spectrum import SpectrumAnalyzer, SpectrumResult


def _make_sine(freq: float, duration: float = 0.5, sr: int = 22050) -> AudioSignal:
    """Generate a pure sine wave for testing."""
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    samples = np.sin(2 * np.pi * freq * t).astype(np.float32)
    return AudioSignal.from_array(samples, sample_rate=sr)


class TestSpectrumAnalyzer:
    def test_sine_wave_peak(self):
        """A pure 440 Hz sine should have its dominant frequency near 440 Hz."""
        signal = _make_sine(440.0)
        analyzer = SpectrumAnalyzer(n_fft=4096)
        result = analyzer.compute(signal)

        assert abs(result.dominant_frequency - 440.0) < 15.0

    def test_spectrum_result_band(self):
        """Band extraction should limit frequencies correctly."""
        signal = _make_sine(1000.0)
        analyzer = SpectrumAnalyzer(n_fft=2048)
        result = analyzer.compute(signal)

        freqs, mags = result.band(500.0, 1500.0)
        assert freqs.min() >= 500.0
        assert freqs.max() <= 1500.0
        assert len(freqs) > 0

    def test_different_frequencies_produce_different_spectra(self):
        """Two different frequencies should yield different dominant peaks."""
        analyzer = SpectrumAnalyzer(n_fft=4096)
        result_a = analyzer.compute(_make_sine(300.0))
        result_b = analyzer.compute(_make_sine(800.0))

        assert abs(result_a.dominant_frequency - result_b.dominant_frequency) > 400.0


class TestComparison:
    def test_identical_signals_high_similarity(self):
        """Identical signals should have similarity close to 100%."""
        signal = _make_sine(440.0)
        analyzer = SpectrumAnalyzer(n_fft=2048)
        spec = analyzer.compute(signal)

        result = compare_spectra(spec, spec)
        assert result.similarity_percent > 99.0

    def test_different_signals_lower_similarity(self):
        """Different frequencies should yield lower similarity."""
        analyzer = SpectrumAnalyzer(n_fft=2048)
        spec_a = analyzer.compute(_make_sine(300.0))
        spec_b = analyzer.compute(_make_sine(1200.0))

        result = compare_spectra(spec_a, spec_b)
        assert result.similarity_percent < 80.0


class TestAudioSignal:
    def test_duration(self):
        signal = _make_sine(440.0, duration=1.0, sr=22050)
        assert abs(signal.duration - 1.0) < 0.001

    def test_normalize(self):
        samples = np.array([0.5, -0.3, 0.2], dtype=np.float32)
        signal = AudioSignal.from_array(samples, sample_rate=22050)
        normalized = signal.normalize()
        assert np.max(np.abs(normalized.samples)) == pytest.approx(1.0)
