"""Pitch contour comparison between reference and target audio."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from lab_oralidade.pitch import SEMITONE_REFERENCE_HZ, PitchContour


@dataclass
class PitchComparisonResult:
    """Result of comparing two pitch contours."""

    common_times: NDArray[np.float64]
    reference_semitones: NDArray[np.float64]
    target_semitones: NDArray[np.float64]
    difference: NDArray[np.float64]
    mae_semitones: float
    rmse_semitones: float
    correlation: float
    deviation_regions: list[tuple[float, float]]


def compare_pitch_contours(
    reference: PitchContour,
    target: PitchContour,
    *,
    n_points: int = 100,
    deviation_threshold: float = 2.0,
    smooth: bool = True,
    smooth_kernel: int = 5,
) -> PitchComparisonResult:
    """Compare two pitch contours on a normalized time axis.

    Both contours are time-normalized to [0, 1], interpolated to a common
    grid, and converted to semitones for perceptually meaningful comparison.

    Args:
        reference: Pitch contour of the reference (native speaker).
        target: Pitch contour of the target (student).
        n_points: Number of interpolation points on the common time axis.
        deviation_threshold: Semitone threshold for flagging deviation regions.
        smooth: Whether to apply median smoothing before comparison.
        smooth_kernel: Kernel size for median filter (must be odd).

    Returns:
        PitchComparisonResult with aligned contours, metrics, and deviation regions.
    """
    if smooth:
        reference = reference.smooth(smooth_kernel)
        target = target.smooth(smooth_kernel)

    # Normalize times and convert to semitones
    ref_norm_times = reference.normalized_times()
    tgt_norm_times = target.normalized_times()
    ref_semitones = reference.to_semitones()
    tgt_semitones = target.to_semitones()

    # Common time grid
    common_times = np.linspace(0.0, 1.0, n_points)

    # Interpolate reference (voiced frames only)
    ref_interp = _interpolate_voiced(ref_norm_times, ref_semitones, common_times)
    tgt_interp = _interpolate_voiced(tgt_norm_times, tgt_semitones, common_times)

    # Compute difference
    difference = ref_interp - tgt_interp

    # Metrics (only where both have valid values)
    valid = ~(np.isnan(ref_interp) | np.isnan(tgt_interp))
    if np.sum(valid) > 0:
        diff_valid = difference[valid]
        mae = float(np.mean(np.abs(diff_valid)))
        rmse = float(np.sqrt(np.mean(diff_valid**2)))
        correlation = float(np.corrcoef(ref_interp[valid], tgt_interp[valid])[0, 1])
    else:
        mae = rmse = float("nan")
        correlation = float("nan")

    # Identify deviation regions
    deviation_regions = _find_deviation_regions(
        common_times, difference, deviation_threshold
    )

    return PitchComparisonResult(
        common_times=common_times,
        reference_semitones=ref_interp,
        target_semitones=tgt_interp,
        difference=difference,
        mae_semitones=mae,
        rmse_semitones=rmse,
        correlation=correlation,
        deviation_regions=deviation_regions,
    )


def generate_feedback(result: PitchComparisonResult) -> str:
    """Generate Portuguese-language textual feedback from a pitch comparison.

    Returns a formatted string with quality assessment, metrics, and
    regions that need attention.
    """
    lines: list[str] = []
    lines.append("=== ANÁLISE DE CONTORNO DE PITCH ===\n")

    if np.isnan(result.mae_semitones):
        lines.append("Não foi possível comparar os contornos (segmentos vozeados insuficientes).")
        return "\n".join(lines)

    # Quality assessment
    mae = result.mae_semitones
    if mae < 1.0:
        lines.append("✅ Excelente! Seu contorno de pitch está muito próximo da referência.")
    elif mae < 2.0:
        lines.append("👍 Bom! O padrão de entonação é reconhecível com pequenas variações.")
    elif mae < 3.0:
        lines.append("⚠️ Razoável. Diferenças perceptíveis de pitch detectadas.")
    else:
        lines.append("❌ Diferenças significativas encontradas. Foque em acompanhar o contorno.")

    lines.append(f"\nMétricas:")
    lines.append(f"  • Erro médio de pitch: {mae:.2f} semitons")
    lines.append(f"  • RMSE: {result.rmse_semitones:.2f} semitons")
    lines.append(f"  • Correlação: {result.correlation:.3f}")

    if result.deviation_regions:
        lines.append(f"\n⚠️ Regiões que precisam de atenção (tempo normalizado 0–1):")
        for start, end in result.deviation_regions:
            lines.append(f"  • {start:.2f} – {end:.2f}")

    return "\n".join(lines)


def _interpolate_voiced(
    norm_times: NDArray[np.float64],
    semitones: NDArray[np.float64],
    common_times: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Interpolate voiced portions of a pitch contour onto a common time grid."""
    valid = ~np.isnan(semitones)
    if np.sum(valid) < 2:
        return np.full_like(common_times, np.nan)

    interp_fn = interp1d(
        norm_times[valid],
        semitones[valid],
        kind="linear",
        bounds_error=False,
        fill_value=np.nan,
    )
    return interp_fn(common_times)


def _find_deviation_regions(
    times: NDArray[np.float64],
    difference: NDArray[np.float64],
    threshold: float,
    gap_threshold: float = 0.05,
) -> list[tuple[float, float]]:
    """Identify continuous time regions where |difference| exceeds threshold."""
    high_dev = np.abs(difference) > threshold
    high_dev &= ~np.isnan(difference)

    if not np.any(high_dev):
        return []

    dev_times = times[high_dev]
    regions: list[tuple[float, float]] = []
    start = dev_times[0]

    for i in range(1, len(dev_times)):
        if dev_times[i] - dev_times[i - 1] > gap_threshold:
            regions.append((float(start), float(dev_times[i - 1])))
            start = dev_times[i]

    regions.append((float(start), float(dev_times[-1])))
    return regions
