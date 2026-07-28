from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest

from lab_oralidade.web_api import analyze_audio_file, compare_audio_files


@pytest.fixture
def synthetic_audio(tmp_path: Path) -> Path:
    path = tmp_path / "synthetic.wav"
    sample_rate = 22050
    duration = 0.5
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    samples = 0.6 * np.sin(2 * np.pi * 220 * t).astype(np.float32)

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        pcm = (samples * 32767).astype(np.int16)
        wav_file.writeframes(pcm.tobytes())

    return path


def test_analyze_audio_file_returns_expected_payload(synthetic_audio: Path) -> None:
    payload = analyze_audio_file(synthetic_audio, "synthetic.wav")

    assert payload["filename"] == "synthetic.wav"
    assert payload["duration_seconds"] > 0
    assert payload["dominant_frequency_hz"] > 0
    assert payload["pitch_mean_hz"] >= 0
    assert payload["spectrum_image"].startswith("data:image/png;base64,")
    assert payload["pitch_image"].startswith("data:image/png;base64,")


def test_compare_audio_files_returns_comparison_payload(synthetic_audio: Path) -> None:
    payload = compare_audio_files(synthetic_audio, synthetic_audio)

    assert payload["comparison"]["similarity_percent"] >= 0
    assert payload["comparison_image"].startswith("data:image/png;base64,")
    assert payload["feedback"]
