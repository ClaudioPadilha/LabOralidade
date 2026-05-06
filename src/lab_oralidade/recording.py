"""Microphone audio recording and playback."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
from numpy.typing import NDArray

from lab_oralidade.audio import AudioSignal

DEFAULT_SAMPLE_RATE = 22050
DEFAULT_CHANNELS = 1


def record(
    duration: float,
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    device: int | str | None = None,
) -> AudioSignal:
    """Record audio from the microphone for a fixed duration.

    Args:
        duration: Recording length in seconds.
        sample_rate: Sample rate in Hz.
        device: Audio input device index or name. None uses system default.

    Returns:
        AudioSignal with the recorded samples.
    """
    print(f"Gravando {duration:.1f}s...")
    samples: NDArray[np.float32] = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=DEFAULT_CHANNELS,
        dtype="float32",
        device=device,
    )
    sd.wait()
    print("Gravação finalizada.")
    return AudioSignal.from_array(samples.flatten(), sample_rate=sample_rate)


def record_until_enter(
    *,
    sample_rate: int = DEFAULT_SAMPLE_RATE,
    device: int | str | None = None,
    max_duration: float = 30.0,
) -> AudioSignal:
    """Record audio until the user presses Enter (or max_duration is reached).

    Uses a streaming approach with a callback to capture audio in chunks.
    """
    frames: list[NDArray[np.float32]] = []

    def _callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    stream = sd.InputStream(
        samplerate=sample_rate,
        channels=DEFAULT_CHANNELS,
        dtype="float32",
        device=device,
        callback=_callback,
    )

    print("Gravando... pressione Enter para parar.")
    with stream:
        try:
            input()
        except KeyboardInterrupt:
            pass

    if not frames:
        samples = np.zeros(0, dtype=np.float32)
    else:
        samples = np.concatenate(frames).flatten()

    # Enforce max duration
    max_samples = int(max_duration * sample_rate)
    samples = samples[:max_samples]

    print(f"Gravação finalizada ({len(samples) / sample_rate:.1f}s).")
    return AudioSignal.from_array(samples, sample_rate=sample_rate)


def play(signal: AudioSignal, *, device: int | str | None = None) -> None:
    """Play an AudioSignal through the default output device.

    Blocks until playback is complete.
    """
    print(f"Reproduzindo ({signal.duration:.1f}s)...")
    sd.play(signal.samples, samplerate=signal.sample_rate, device=device)
    sd.wait()
    print("Reprodução finalizada.")


def play_file(path: str | Path, *, device: int | str | None = None) -> None:
    """Load and play an audio file."""
    signal = AudioSignal.from_file(path)
    play(signal, device=device)


def save_recording(signal: AudioSignal, path: str | Path) -> Path:
    """Save an AudioSignal to a WAV file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(path), signal.samples, signal.sample_rate)
    return path
