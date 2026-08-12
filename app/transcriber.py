"""Transcription with faster-whisper — singleton model, GPU-aware, cached."""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional

from .config import settings
from .models import Transcript, TranscriptSegment, Word
from .paths import AUDIO_DIR, TRANSCRIPTS_DIR, ensure_workspace

logger = logging.getLogger(__name__)

_model = None
_model_key: Optional[str] = None

ProgressCallback = Callable[[float, str], None]


def extract_audio(source_path: Path, job_temp: Path, progress_cb: Optional[ProgressCallback] = None) -> Path:
    """Extract 16 kHz mono WAV for Whisper using FFmpeg."""
    audio_path = job_temp / "audio.wav"
    ffmpeg = _find_ffmpeg()
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(source_path),
        "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le",
        str(audio_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0 or not audio_path.exists():
        raise RuntimeError("FFmpeg failed to extract audio: " + (proc.stderr or "").strip()[:300])
    if progress_cb:
        progress_cb(100, "Audio extracted")
    return audio_path


def _find_ffmpeg() -> str:
    import shutil

    p = shutil.which("ffmpeg")
    if not p:
        raise RuntimeError(
            "FFmpeg is not installed. Install FFmpeg and add it to PATH to continue."
        )
    return p


def get_whisper_model():
    """Lazy-load a singleton Whisper model. One model instance only."""
    global _model, _model_key
    key = (settings.whisper_model, settings.whisper_device, settings.whisper_compute_type)
    if _model is not None and _model_key == key:
        return _model
    from faster_whisper import WhisperModel

    logger.info(
        "Loading Whisper model=%s device=%s compute=%s",
        settings.whisper_model,
        settings.whisper_device,
        settings.whisper_compute_type,
    )
    _model = WhisperModel(
        settings.whisper_model,
        device=settings.whisper_device,
        compute_type=settings.whisper_compute_type,
    )
    _model_key = key
    return _model


_IGNORED_TOKENS = {"[MUSIC]", "[LAUGHTER]", "[Applause]", "[Applause]"}


def transcribe(
    audio_path: Path,
    progress_cb: Optional[ProgressCallback] = None,
    use_cache: bool = True,
) -> Transcript:
    """Transcribe audio file to a word-level Transcript (cached by file hash)."""
    ensure_workspace()
    cache_key = hashlib.sha1(
        f"{audio_path}:{settings.whisper_model}:{settings.whisper_device}".encode()
    ).hexdigest()
    cache_path = TRANSCRIPTS_DIR / f"{cache_key}.json"

    if use_cache and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return Transcript.model_validate_json(f.read())
        except Exception:
            logger.warning("Corrupt transcript cache, re-transcribing: %s", cache_path)

    model = get_whisper_model()
    if progress_cb:
        progress_cb(5, "Transcribing audio...")

    segments_iter, info = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        vad_filter=settings.whisper_vad,
        beam_size=5,
    )

    segments: list[TranscriptSegment] = []
    total_duration = max(float(info.duration or 0.0), 0.0)
    last_pct = 0.0
    for seg in segments_iter:
        raw_words = list(getattr(seg, "words", None) or [])
        words = [
            Word(
                text=w.word.strip(),
                start=float(w.start),
                end=float(w.end),
                confidence=float(w.probability) if hasattr(w, "probability") else None,
            )
            for w in raw_words
            if w.word.strip() and w.word.strip().upper() not in _IGNORED_TOKENS
        ]
        if not words:
            continue
        text = " ".join(w.text for w in words)
        segments.append(
            TranscriptSegment(
                start=float(seg.start),
                end=float(seg.end),
                text=text,
                words=words,
            )
        )
        if progress_cb and total_duration > 0:
            pct = 5 + float(seg.end) / total_duration * 90
            pct = min(max(pct, last_pct), 95)
            last_pct = pct
            progress_cb(pct, f"Transcribing… {int(seg.end)}/{int(total_duration)}s")

    transcript = Transcript(
        language=getattr(info, "language", "unknown") or "unknown",
        duration=total_duration,
        segments=segments,
    )

    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(transcript.model_dump_json())

    if progress_cb:
        progress_cb(100, "Transcription complete")
    return transcript


def cache_transcript_local(audio_path: Path) -> Optional[Path]:
    """Return cached transcript path if it exists (for retry-AI only)."""
    cache_key = hashlib.sha1(
        f"{audio_path}:{settings.whisper_model}:{settings.whisper_device}".encode()
    ).hexdigest()
    cache_path = TRANSCRIPTS_DIR / f"{cache_key}.json"
    return cache_path if cache_path.exists() else None