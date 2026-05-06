# Copilot Instructions – LabOralidade

## Build & Run

```bash
pip install -e ".[dev]"          # install in editable mode with dev deps
pytest                           # run full test suite
pytest tests/test_spectrum.py::TestSpectrumAnalyzer::test_sine_wave_peak  # single test
ruff check src/ tests/           # lint
ruff format src/ tests/          # format
```

## Architecture

This is a Python library + CLI for Fourier spectral analysis of audio, used in language phonetics education.

**Data flow:** Audio file → `AudioSignal` (load/preprocess) → `SpectrumAnalyzer` (FFT) → `SpectrumResult` → visualization or `compare_spectra()`.

Core modules in `src/lab_oralidade/`:

- `audio.py` – File I/O and signal preprocessing (trim silence, normalize). All signals are mono float32 at a consistent sample rate.
- `spectrum.py` – FFT computation and formant estimation via LPC. `SpectrumResult` is the central data object passed between modules.
- `comparison.py` – Quantitative similarity metrics (cosine similarity, spectral centroid difference) between two `SpectrumResult` objects.
- `visualization.py` – Matplotlib plotting. Always returns `Figure` objects; optionally saves to file.
- `cli.py` – Argparse-based CLI with `spectrum` and `compare` subcommands.

## Conventions

- **Immutable data objects:** `AudioSignal` and `SpectrumResult` are frozen dataclasses. Transformations return new instances.
- **Language:** Code identifiers and docstrings in English. User-facing strings (CLI output, plot labels) in Brazilian Portuguese.
- **Units:** Frequencies in Hz, time in seconds, magnitudes are normalized FFT amplitudes.
- **Default sample rate:** 22050 Hz (librosa default). All audio is resampled on load.
- **Testing:** Use synthetic sine waves (`AudioSignal.from_array`) rather than audio fixtures. The helper `_make_sine()` in tests generates known signals.
- **Frequency band for speech comparison:** 80–4000 Hz default in `compare_spectra()`.
- **Plotting:** Functions accept an optional `ax` parameter for embedding in larger figures; otherwise they create their own.
