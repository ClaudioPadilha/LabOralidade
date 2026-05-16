"""LabOralidade – análise espectral de áudio para fonética."""

from lab_oralidade.audio import AudioSignal, save_temp_wav
from lab_oralidade.pitch import PitchContour, extract_pitch_contour
from lab_oralidade.pitch_comparison import (
    PitchComparisonResult,
    compare_pitch_contours,
    generate_feedback,
)
from lab_oralidade.recording import play, play_file, record, record_until_enter, save_recording
from lab_oralidade.spectrum import SpectrumAnalyzer, SpectrumResult
from lab_oralidade.visualization import (
    plot_comparison,
    plot_pitch,
    plot_pitch_comparison,
    plot_pitch_contour_comparison,
    plot_spectrum,
)

__all__ = [
    "AudioSignal",
    "PitchComparisonResult",
    "PitchContour",
    "SpectrumAnalyzer",
    "SpectrumResult",
    "compare_pitch_contours",
    "extract_pitch_contour",
    "generate_feedback",
    "play",
    "play_file",
    "plot_comparison",
    "plot_pitch",
    "plot_pitch_comparison",
    "plot_pitch_contour_comparison",
    "plot_spectrum",
    "save_temp_wav",
    "record",
    "record_until_enter",
    "save_recording",
]
