"""Spectrum visualization and comparison plots."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

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
