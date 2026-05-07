"""Tests for pitch contour comparison."""

import numpy as np
import pytest

from lab_oralidade.pitch import PitchContour
from lab_oralidade.pitch_comparison import (
    PitchComparisonResult,
    compare_pitch_contours,
    generate_feedback,
)


def _make_pitch_contour(f0_hz: float, duration: float = 1.0, time_step: float = 0.01) -> PitchContour:
    """Create a synthetic pitch contour at a constant frequency."""
    n_frames = int(duration / time_step)
    times = np.linspace(0, duration, n_frames)
    f0_values = np.full(n_frames, f0_hz, dtype=np.float64)
    return PitchContour(times=times, f0_values=f0_values)


def _make_rising_contour(f0_start: float, f0_end: float, duration: float = 1.0) -> PitchContour:
    """Create a linearly rising pitch contour."""
    n_frames = 100
    times = np.linspace(0, duration, n_frames)
    f0_values = np.linspace(f0_start, f0_end, n_frames)
    return PitchContour(times=times, f0_values=f0_values)


class TestComparePitchContours:
    def test_identical_contours_high_correlation(self):
        """Identical pitch contours should give perfect correlation and zero error."""
        contour = _make_pitch_contour(200.0)
        result = compare_pitch_contours(contour, contour)

        assert result.mae_semitones == pytest.approx(0.0, abs=0.01)
        assert result.rmse_semitones == pytest.approx(0.0, abs=0.01)
        assert result.correlation == pytest.approx(1.0, abs=0.01)
        assert result.deviation_regions == []

    def test_different_frequencies_measurable_error(self):
        """Different constant F0 values should produce a measurable MAE in semitones."""
        ref = _make_pitch_contour(200.0)
        tgt = _make_pitch_contour(250.0)
        result = compare_pitch_contours(ref, tgt)

        # 200 -> 250 Hz is about 3.86 semitones
        expected_diff = 12.0 * np.log2(200.0 / 250.0)
        assert result.mae_semitones == pytest.approx(abs(expected_diff), abs=0.1)

    def test_correlated_contours(self):
        """Contours with the same shape but offset should still have high correlation."""
        ref = _make_rising_contour(150.0, 300.0)
        # Same shape, shifted up by ~2 semitones
        tgt = _make_rising_contour(150.0 * 2 ** (2 / 12), 300.0 * 2 ** (2 / 12))
        result = compare_pitch_contours(ref, tgt)

        assert result.correlation > 0.99
        assert result.mae_semitones == pytest.approx(2.0, abs=0.2)

    def test_deviation_regions_detected(self):
        """Large differences should produce deviation regions."""
        ref = _make_pitch_contour(200.0)
        # Target with a big jump in the middle
        n_frames = 100
        times = np.linspace(0, 1.0, n_frames)
        f0 = np.full(n_frames, 200.0)
        f0[40:60] = 400.0  # +12 semitones in the middle
        tgt = PitchContour(times=times, f0_values=f0)

        result = compare_pitch_contours(ref, tgt, deviation_threshold=2.0)
        assert len(result.deviation_regions) > 0

    def test_unvoiced_frames_handled(self):
        """Contours with NaN (unvoiced) frames should not crash."""
        n_frames = 100
        times = np.linspace(0, 1.0, n_frames)
        f0_ref = np.full(n_frames, 200.0)
        f0_ref[0:10] = np.nan
        f0_tgt = np.full(n_frames, 200.0)
        f0_tgt[90:100] = np.nan

        ref = PitchContour(times=times, f0_values=f0_ref)
        tgt = PitchContour(times=times, f0_values=f0_tgt)
        result = compare_pitch_contours(ref, tgt)

        assert not np.isnan(result.mae_semitones)


class TestGenerateFeedback:
    def test_returns_string(self):
        """Feedback should be a non-empty string."""
        contour = _make_pitch_contour(200.0)
        result = compare_pitch_contours(contour, contour)
        feedback = generate_feedback(result)

        assert isinstance(feedback, str)
        assert len(feedback) > 0

    def test_excellent_for_identical(self):
        """Identical contours should produce 'Excelente' feedback."""
        contour = _make_pitch_contour(200.0)
        result = compare_pitch_contours(contour, contour)
        feedback = generate_feedback(result)

        assert "✅" in feedback or "Excelente" in feedback

    def test_poor_for_very_different(self):
        """Very different contours should produce negative feedback."""
        ref = _make_pitch_contour(100.0)
        tgt = _make_pitch_contour(400.0)  # +24 semitones apart
        result = compare_pitch_contours(ref, tgt)
        feedback = generate_feedback(result)

        assert "❌" in feedback


class TestPitchContourMethods:
    def test_smooth(self):
        """Smoothing should not crash and should preserve length."""
        contour = _make_pitch_contour(200.0)
        smoothed = contour.smooth(kernel_size=5)
        assert len(smoothed.f0_values) == len(contour.f0_values)

    def test_to_semitones(self):
        """220 Hz should be exactly 24 semitones above 55 Hz."""
        contour = _make_pitch_contour(220.0)
        semitones = contour.to_semitones(reference_hz=55.0)
        assert semitones[0] == pytest.approx(24.0, abs=0.01)

    def test_normalized_times(self):
        """Normalized times should span [0, 1]."""
        contour = _make_pitch_contour(200.0, duration=2.5)
        norm = contour.normalized_times()
        assert norm[0] == pytest.approx(0.0)
        assert norm[-1] == pytest.approx(1.0)
