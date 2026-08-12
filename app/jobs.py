"""Job manager — async background jobs with SSE progress and failure isolation."""
from __future__ import annotations

import json
import logging
import threading
import traceback
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from .ai.openrouter import OpenRouterClient, OpenRouterError
from .ai.ranking import compute_viral_score, scores_dict
from .analysis.boundaries import optimize_boundaries
from .analysis.candidates import generate_candidates
from .analysis.deduplication import deduplicate
from .clipper import render_clip
from .config import settings
from .downloader import DownloadError, download_video
from .history import save_project_record
from .models import (
    AnalyzeRequest,
    GenerateRequest,
    RankedClip,
    Transcript,
)
from .paths import CLIPS_DIR, ensure_workspace, job_temp_dir
from .transcriber import extract_audio, transcribe

logger = logging.getLogger(__name__)

TERMINAL_STATUSES = {"completed", "failed"}


@dataclass
class Job:
    job_id: str
    job_type: str  # "analysis" | "generation"
    status: str = "queued"
    stage: str = "queued"
    progress: float = 0.0
    message: str = "Queued"
    error: Optional[str] = None
    error_code: str = "UNKNOWN_ERROR"
    events: list[dict] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def update(self, stage: str, progress: float, message: str) -> None:
        with self._lock:
            if self.status in TERMINAL_STATUSES:
                return
            self.stage = stage
            self.progress = max(self.progress, min(float(progress), 100.0))
            self.message = message
            self.events.append(
                {
                    "stage": stage,
                    "progress": self.progress,
                    "message": message,
                    "status": self.status,
                }
            )

    def fail(self, error: str, code: str = "UNKNOWN_ERROR") -> None:
        with self._lock:
            if self.status in TERMINAL_STATUSES:
                return
            self.status = "failed"
            self.error = error
            self.error_code = code
            self.stage = "failed"
            self.events.append(
                {
                    "stage": "failed",
                    "progress": self.progress,
                    "message": error,
                    "status": "failed",
                    "error_code": code,
                }
            )

    def complete(self, message: str = "Complete") -> None:
        with self._lock:
            if self.status in TERMINAL_STATUSES:
                return
            self.status = "completed"
            self.stage = "completed"
            self.progress = 100.0
            self.message = message
            self.events.append(
                {
                    "stage": "completed",
                    "progress": 100.0,
                    "message": message,
                    "status": "completed",
                }
            )

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "job_id": self.job_id,
                "job_type": self.job_type,
                "status": self.status,
                "stage": self.stage,
                "progress": self.progress,
                "message": self.message,
                "error": self.error,
                "error_code": self.error_code,
            }


class JobManager:
    """Thread-safe in-memory job registry (singleton)."""

    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, job_type: str) -> Job:
        job = Job(job_id=uuid.uuid4().hex[:12], job_type=job_type)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def all_jobs(self) -> list[Job]:
        with self._lock:
            return list(self._jobs.values())

    def submit(self, job: Job, fn: Callable[[Job], None]) -> Job:
        def wrapper() -> None:
            try:
                fn(job)
            except OpenRouterError as exc:
                job.fail(str(exc), exc.code)
            except DownloadError as exc:
                job.fail(exc.message, "DOWNLOAD_ERROR")
            except Exception as exc:
                logger.exception("Job %s failed", job.job_id)
                job.fail(_friendly_error(exc), _error_code_for(exc))
            finally:
                if job.status not in TERMINAL_STATUSES:
                    job.complete()

        t = threading.Thread(target=wrapper, name=f"job-{job.job_id}", daemon=True)
        t.start()
        return job


manager = JobManager()


def _error_code_for(exc: Exception) -> str:
    if isinstance(exc, OpenRouterError):
        return exc.code
    return "UNKNOWN_ERROR"


def _friendly_error(exc: Exception) -> str:
    msg = str(exc).strip() or type(exc).__name__
    return msg[:500]


# ---------------------------------------------------------------------------
# Analysis pipeline
# ---------------------------------------------------------------------------
STAGE_ORDER = [
    "queued",
    "downloading",
    "extracting_audio",
    "transcribing",
    "finding_candidates",
    "ai_analysis",
    "ranking",
    "completed",
]


def run_analysis_pipeline(job: Job, req: AnalyzeRequest) -> None:
    ensure_workspace()

    job.update("queued", 1, "Queued — preparing download")

    source_data, source_path = download_video(
        req.url,
        job_temp_dir(job.job_id),
        progress_cb=lambda p, m: job.update("downloading", 10 + p * 0.05, m),
    )
    job.data["source"] = source_data.model_dump()
    job.update("downloading", 12, f"Downloaded: {source_data.title or 'video'}")

    job.update("extracting_audio", 14, "Extracting audio...")
    audio_path = extract_audio(
        source_path,
        job_temp_dir(job.job_id),
        progress_cb=lambda p, m: job.update("extracting_audio", 15, m),
    )

    job.update("transcribing", 16, "Loading Whisper...")
    transcript = transcribe(
        audio_path,
        progress_cb=lambda p, m: job.update("transcribing", 16 + p * 0.44, m),
    )
    job.update("transcribing", 60, "Transcript ready")

    job.update("finding_candidates", 61, "Finding candidate moments...")
    candidates = generate_candidates(
        transcript,
        min_duration=req.min_duration,
        max_duration=req.max_duration,
    )
    candidates = deduplicate(candidates)
    job.data["candidates"] = [c.model_dump() for c in candidates]
    job.update(
        "finding_candidates",
        68,
        f"Found {len(candidates)} potential moments",
    )

    job.update("ai_analysis", 69, "AI analyzing potential moments...")
    client = OpenRouterClient()
    ai_results = client.analyze_candidates(
        candidates,
        min_duration=req.min_duration,
        max_duration=req.max_duration,
        progress_cb=lambda p, m: job.update("ai_analysis", 69 + p * 0.23, m),
    )

    job.update("ranking", 93, "Ranking viral moments...")
    ranked = _rank_results(ai_results, transcript, req)
    job.data["results"] = [r.model_dump() for r in ranked]
    job.data["transcript"] = transcript.model_dump()
    job.data["transcript_path"] = str(
        save_project_record(job)  # returns transcript file path
    )
    del job.data["transcript"]
    job.update("ranking", 100, f"{len(ranked)} viral moments ready")


def retry_ai_analysis(job: Job) -> bool:
    """Re-run only the AI analysis stage using saved candidates/transcript."""
    if job.job_type != "analysis" or job.status == "completed":
        return False
    candidates_data = job.data.get("candidates")
    transcript_path = job.data.get("transcript_path")
    if not candidates_data or not transcript_path:
        return False

    transcript = Transcript.model_validate_json(
        Path(transcript_path).read_text(encoding="utf-8")
    )
    from .models import ClipCandidate

    candidates = [ClipCandidate.model_validate(c) for c in candidates_data]
    clip_count = int(job.data.get("clip_count") or settings.default_clip_count)
    min_dur = float(job.data.get("min_duration") or settings.min_clip_duration)
    max_dur = float(job.data.get("max_duration") or settings.max_clip_duration)

    def run(job: Job) -> None:
        job.update("ai_analysis", 1, "Retrying AI analysis...")
        client = OpenRouterClient()
        ai_results = client.analyze_candidates(
            candidates,
            min_duration=min_dur,
            max_duration=max_dur,
            progress_cb=lambda p, m: job.update("ai_analysis", 5 + p * 0.85, m),
        )
        ranked = _rank_results(ai_results, transcript, min_dur, max_dur, clip_count)
        job.data["results"] = [r.model_dump() for r in ranked]
        save_project_record(job)
        job.update("ranked", 100, f"{len(ranked)} viral moments ready")

    manager.submit(job, run)
    return True


def _rank_results(
    ai_results,
    transcript: Transcript,
    min_duration: float,
    max_duration: float,
    clip_count: int,
) -> list[RankedClip]:
    """Server-authoritative ranking: scores, boundaries, dedup, sort."""
    ranked: list[RankedClip] = []
    for analysis in ai_results:
        raw_start = analysis.recommended_start
        raw_end = analysis.recommended_end
        if raw_start is None:
            raw_start = raw_end - max_duration if raw_end else 0.0
        if raw_end is None:
            raw_end = min(raw_start + max_duration, transcript.duration or (raw_start + max_duration))
        s, e = optimize_boundaries(
            transcript, raw_start, raw_end, min_duration, max_duration
        )
        ranked.append(
            RankedClip(
                candidate_id=analysis.candidate_id,
                rank=0,
                viral_score=compute_viral_score(analysis),
                start=s,
                end=e,
                duration=round(max(e - s, 0.0), 2),
                title=analysis.title,
                hook=analysis.hook,
                reason=analysis.reason,
                scores=scores_dict(analysis),
            )
        )
    ranked.sort(key=lambda r: r.viral_score, reverse=True)
    for i, r in enumerate(ranked, 1):
        r.rank = i
    return ranked[:clip_count]


# ---------------------------------------------------------------------------
# Generation pipeline
# ---------------------------------------------------------------------------
def run_generation_pipeline(job: Job, payload: dict) -> None:
    analysis_job = manager.get(payload["analysis_job_id"])
    candidate_id = payload["candidate_id"]
    if analysis_job is None:
        job.fail("The analysis job for this clip no longer exists.", "JOB_NOT_FOUND")
        return

    source_data = analysis_job.data.get("source") or {}
    results_data = analysis_job.data.get("results") or []
    result = next(
        (r for r in results_data if r.get("candidate_id") == candidate_id), None
    )
    if result is None:
        job.fail("Clip result not found. Re-run analysis.", "CLIP_NOT_FOUND")
        return

    source_path = source_data.get("local_path")
    if not source_path or not Path(source_path).exists():
        job.fail(
            "Source video file is missing. Re-run analysis.", "SOURCE_MISSING"
        )
        return

    transcript_path = analysis_job.data.get("transcript_path")
    transcript: Optional[Transcript] = None
    if transcript_path and Path(transcript_path).exists():
        try:
            transcript = Transcript.model_validate_json(
                Path(transcript_path).read_text(encoding="utf-8")
            )
        except Exception:
            transcript = None

    req = GenerateRequest.model_validate(payload["options"])
    clip_id = f"{job.job_id}_{candidate_id}"
    output_path = CLIPS_DIR / f"{clip_id}.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    job.update("queued", 1, "Queued — preparing render")
    job.update("rendering", 5, "Loading source video...")
    job.data["clip_id"] = clip_id
    job.data["output_path"] = str(output_path)
    job.data["candidate_id"] = candidate_id
    job.data["analysis_job_id"] = analysis_job.job_id

    render_clip(
        Path(source_path),
        float(result["start"]),
        float(result["end"]),
        transcript,
        output_path,
        aspect_ratio=req.aspect_ratio,
        width=req.width,
        height=req.height,
        caption_style=req.caption_style,
        captions=req.captions,
        effects_enabled=req.effects,
        progress_cb=lambda p, m: job.update("rendering", 5 + p * 0.95, m),
    )

    existing = analysis_job.data.get("generated_clips") or []
    existing.append(
        {
            "clip_id": clip_id,
            "candidate_id": candidate_id,
            "output_path": str(output_path),
            "options": payload["options"],
        }
    )
    analysis_job.data["generated_clips"] = existing
    save_project_record(analysis_job)
    job.complete("Clip rendered")