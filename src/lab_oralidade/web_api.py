"""FastAPI-compatible helpers for audio analysis."""

from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from lab_oralidade.audio import AudioSignal
from lab_oralidade.comparison import compare_spectra
from lab_oralidade.pitch import extract_pitch_contour
from lab_oralidade.pitch_comparison import compare_pitch_contours, generate_feedback
from lab_oralidade.spectrum import SpectrumAnalyzer
from lab_oralidade.visualization import plot_comparison, plot_pitch, plot_pitch_contour_comparison


def _encode_plot(fig: plt.Figure) -> str:
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"


def analyze_audio_file(audio_path: str | Path, filename: str) -> dict[str, Any]:
    """Analyze a single audio file and return a JSON-serializable payload."""
    signal = AudioSignal.from_file(audio_path)
    analyzer = SpectrumAnalyzer(n_fft=2048)

    processed = signal.trim_silence().normalize()
    spectrum_result = analyzer.compute(processed)
    contour = extract_pitch_contour(audio_path)

    spectrum_fig = plot_spectrum_payload(spectrum_result)
    pitch_fig = plot_pitch_payload(contour)

    return {
        "filename": filename,
        "duration_seconds": round(float(signal.duration), 3),
        "dominant_frequency_hz": round(float(spectrum_result.dominant_frequency), 2),
        "pitch_mean_hz": round(float(contour.mean_f0), 2),
        "pitch_min_hz": round(float(contour.f0_range[0]), 2),
        "pitch_max_hz": round(float(contour.f0_range[1]), 2),
        "spectrum_image": _encode_plot(spectrum_fig),
        "pitch_image": _encode_plot(pitch_fig),
    }


def compare_audio_files(reference_path: str | Path, target_path: str | Path) -> dict[str, Any]:
    """Compare two audio files and return metrics plus feedback."""
    ref_signal = AudioSignal.from_file(reference_path).trim_silence().normalize()
    tgt_signal = AudioSignal.from_file(target_path).trim_silence().normalize()
    analyzer = SpectrumAnalyzer(n_fft=2048)

    ref_spec = analyzer.compute(ref_signal)
    tgt_spec = analyzer.compute(tgt_signal)
    comparison = compare_spectra(ref_spec, tgt_spec)

    ref_contour = extract_pitch_contour(reference_path)
    tgt_contour = extract_pitch_contour(target_path)
    pitch_comparison = compare_pitch_contours(ref_contour, tgt_contour)
    feedback = generate_feedback(pitch_comparison)
    comparison_fig = plot_comparison(ref_spec, tgt_spec, labels=["Referência", "Aluno"])
    pitch_comp_fig = plot_pitch_contour_comparison(pitch_comparison)

    return {
        "comparison": {
            "similarity_percent": round(float(comparison.similarity_percent), 2),
            "dominant_freq_diff_hz": round(float(comparison.dominant_freq_diff_hz), 2),
            "spectral_centroid_diff_hz": round(float(comparison.spectral_centroid_diff_hz), 2),
            "mae_semitones": round(float(pitch_comparison.mae_semitones), 2),
            "rmse_semitones": round(float(pitch_comparison.rmse_semitones), 2),
            "correlation": round(float(pitch_comparison.correlation), 3),
        },
        "comparison_image": _encode_plot(comparison_fig),
        "pitch_comparison_image": _encode_plot(pitch_comp_fig),
        "feedback": feedback,
    }


def plot_spectrum_payload(result: Any) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(result.frequencies, result.magnitudes, linewidth=0.8)
    ax.set_xlabel("Frequência (Hz)")
    ax.set_ylabel("Magnitude")
    ax.set_title("Espectro de Frequência")
    ax.grid(True, alpha=0.3)
    return fig


def plot_pitch_payload(contour: Any) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(contour.times, contour.f0_values, "o-", markersize=2, linewidth=0.8)
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title("Contorno de Pitch")
    ax.grid(True, alpha=0.3)
    return fig
