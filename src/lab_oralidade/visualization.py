"""Spectrum and pitch visualization."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from lab_oralidade.pitch import PitchContour
from lab_oralidade.pitch_comparison import PitchComparisonResult
from lab_oralidade.spectrum import SpectrumResult


def plot_spectrum(
    result: SpectrumResult,
    *,
    title: str = "Espectro de Frequência",
    max_freq: float | None = 5000.0,
    output_path: str | Path | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot a single frequency spectrum."""
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))

    freqs, mags = result.frequencies, result.magnitudes
    if max_freq:
        mask = freqs <= max_freq
        freqs, mags = freqs[mask], mags[mask]

    ax.plot(freqs, mags, linewidth=0.8)
    ax.set_xlabel("Frequência (Hz)")
    ax.set_ylabel("Magnitude")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if fig is None:
        fig = ax.get_figure()

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight")

    return fig


def plot_comparison(
    *spectra: SpectrumResult,
    labels: list[str] | None = None,
    title: str = "Comparação Espectral",
    max_freq: float | None = 5000.0,
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Overlay multiple spectra for visual comparison."""
    fig, ax = plt.subplots(figsize=(12, 5))

    if labels is None:
        labels = [f"Sinal {i + 1}" for i in range(len(spectra))]

    colors = plt.cm.tab10(np.linspace(0, 1, len(spectra)))

    for result, label, color in zip(spectra, labels, colors):
        freqs, mags = result.frequencies, result.magnitudes
        if max_freq:
            mask = freqs <= max_freq
            freqs, mags = freqs[mask], mags[mask]
        ax.plot(freqs, mags, label=label, color=color, linewidth=0.8)

    ax.set_xlabel("Frequência (Hz)")
    ax.set_ylabel("Magnitude")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight")

    return fig


def plot_pitch(
    contour: PitchContour,
    *,
    title: str = "Contorno de Pitch (F0)",
    output_path: str | Path | None = None,
    ax: plt.Axes | None = None,
) -> plt.Figure:
    """Plot a single pitch contour."""
    fig = None
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 4))

    ax.plot(contour.times, contour.f0_values, "o-", markersize=2, linewidth=0.8)
    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if fig is None:
        fig = ax.get_figure()

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight")

    return fig


def plot_pitch_comparison(
    *contours: PitchContour,
    labels: list[str] | None = None,
    title: str = "Comparação de Pitch (F0)",
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Overlay multiple pitch contours for visual comparison."""
    fig, ax = plt.subplots(figsize=(12, 5))

    if labels is None:
        labels = [f"Sinal {i + 1}" for i in range(len(contours))]

    colors = plt.cm.tab10(np.linspace(0, 1, len(contours)))

    for contour, label, color in zip(contours, labels, colors):
        ax.plot(
            contour.times, contour.f0_values,
            "o-", markersize=2, linewidth=0.8,
            label=label, color=color,
        )

    ax.set_xlabel("Tempo (s)")
    ax.set_ylabel("F0 (Hz)")
    ax.set_title(title)
    ax.legend()
    ax.grid(True, alpha=0.3)

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight")

    return fig


def plot_pitch_contour_comparison(
    result: PitchComparisonResult,
    *,
    title: str = "Comparação de Contorno de Pitch",
    output_path: str | Path | None = None,
) -> plt.Figure:
    """Plot pitch comparison with overlay and difference panels.

    Top panel: both contours in semitones overlaid.
    Bottom panel: difference (reference - target) with colored fill.
    """
    fig, (ax_overlay, ax_diff) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Top: overlay of both contours
    ax_overlay.plot(
        result.common_times, result.reference_semitones,
        linewidth=2, label="Referência", color="blue",
    )
    ax_overlay.plot(
        result.common_times, result.target_semitones,
        linewidth=2, label="Aluno", color="orange", alpha=0.8,
    )
    ax_overlay.set_ylabel("Pitch (semitons re 55 Hz)")
    ax_overlay.set_title(title)
    ax_overlay.legend()
    ax_overlay.grid(True, alpha=0.3)

    # Bottom: difference with fill
    ax_diff.plot(
        result.common_times, result.difference,
        linewidth=1.5, color="gray", alpha=0.7,
    )
    ax_diff.axhline(y=0, color="black", linestyle="--", linewidth=0.8)
    ax_diff.fill_between(
        result.common_times, 0, result.difference,
        where=(result.difference > 0),
        color="red", alpha=0.3, label="Aluno mais grave",
    )
    ax_diff.fill_between(
        result.common_times, 0, result.difference,
        where=(result.difference < 0),
        color="green", alpha=0.3, label="Aluno mais agudo",
    )
    ax_diff.set_xlabel("Tempo normalizado")
    ax_diff.set_ylabel("Diferença (semitons)")
    ax_diff.set_title(
        f"Diferença de Pitch — MAE: {result.mae_semitones:.2f} st | "
        f"Correlação: {result.correlation:.3f}"
    )
    ax_diff.legend()
    ax_diff.grid(True, alpha=0.3)

    plt.tight_layout()

    if output_path:
        fig.savefig(str(output_path), dpi=150, bbox_inches="tight")

    return fig
