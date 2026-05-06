"""LabOralidade – análise espectral de áudio para fonética."""

from lab_oralidade.audio import AudioSignal
from lab_oralidade.recording import play, play_file, record, record_until_enter, save_recording
from lab_oralidade.spectrum import SpectrumAnalyzer, SpectrumResult
from lab_oralidade.visualization import plot_comparison, plot_spectrum

__all__ = [
    "AudioSignal",
    "SpectrumAnalyzer",
    "SpectrumResult",
    "play",
    "play_file",
    "plot_comparison",
    "plot_spectrum",
    "record",
    "record_until_enter",
    "save_recording",
]
