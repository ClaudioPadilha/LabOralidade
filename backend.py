from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from lab_oralidade.web_api import analyze_audio_file, compare_audio_files

app = FastAPI(title="LabOralidade API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalysisResponse(BaseModel):
    filename: str
    duration_seconds: float
    dominant_frequency_hz: float
    pitch_mean_hz: float
    pitch_min_hz: float
    pitch_max_hz: float
    spectrum_image: str
    pitch_image: str


class ComparisonResponse(BaseModel):
    comparison: dict
    comparison_image: str
    pitch_comparison_image: Optional[str] = None
    feedback: str


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
def analyze_audio(file: Annotated[UploadFile, File(...)]) -> AnalysisResponse:
    suffix = Path(file.filename or "audio.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = Path(tmp.name)

    try:
        return analyze_audio_file(tmp_path, file.filename or "audio.wav")
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/compare", response_model=ComparisonResponse)
def compare_audio(
    reference: Annotated[UploadFile, File(...)],
    target: Annotated[UploadFile, File(...)],
) -> ComparisonResponse:
    ref_suffix = Path(reference.filename or "reference.wav").suffix or ".wav"
    tgt_suffix = Path(target.filename or "target.wav").suffix or ".wav"

    with tempfile.NamedTemporaryFile(suffix=ref_suffix, delete=False) as ref_tmp:
        ref_tmp.write(reference.file.read())
        ref_path = Path(ref_tmp.name)

    with tempfile.NamedTemporaryFile(suffix=tgt_suffix, delete=False) as tgt_tmp:
        tgt_tmp.write(target.file.read())
        tgt_path = Path(tgt_tmp.name)

    try:
        return compare_audio_files(ref_path, tgt_path)
    except Exception as exc:  # pragma: no cover - defensive path
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        ref_path.unlink(missing_ok=True)
        tgt_path.unlink(missing_ok=True)


if __name__ == "__main__":
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
