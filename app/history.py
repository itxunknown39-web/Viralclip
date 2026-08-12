"""Project history — JSON filesystem persistence."""
from __future__ import annotations

import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from .config import settings
from .paths import HISTORY_FILE, PROJECTS_DIR, project_dir

logger = logging.getLogger(__name__)


def _project_id(job_id: str) -> str:
    return f"project_{job_id}"


def save_project_record(job) -> Path:
    """Persist analysis job state to workspace/projects/. Returns transcript path."""
    d = project_dir(_project_id(job.job_id))

    metadata = {
        "project_id": _project_id(job.job_id),
        "job_id": job.job_id,
        "source": job.data.get("source"),
        "created_at": job.data.get("created_at")
        or time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": job.status,
        "clip_count": job.data.get("clip_count"),
        "min_duration": job.data.get("min_duration"),
        "max_duration": job.data.get("max_duration"),
        "results": job.data.get("results") or [],
        "generated_clips": job.data.get("generated_clips") or [],
        "ai_model": settings.openrouter_model,
        "prompt_version": settings.prompt_version,
        "scoring_version": settings.scoring_version,
    }
    (d / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    transcript_path = Path(job.data.get("transcript_path") or "")
    transcript = job.data.get("transcript")
    if transcript is not None:
        transcript_path = d / "transcript.json"
        (d / "transcript.json").write_text(
            json.dumps(transcript, ensure_ascii=False), encoding="utf-8"
        )
        job.data["transcript_path"] = str(transcript_path)
    elif not transcript_path.exists():
        for f in ("transcript.json", "candidates.json"):
            p = d / f
            if p.exists():
                continue
            data = job.data.get(f.replace(".json", ""))
            if data is not None:
                p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    _update_history_index(metadata)
    return transcript_path or d / "transcript.json"


def _update_history_index(metadata: dict) -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    entries = []
    if HISTORY_FILE.exists():
        try:
            entries = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            entries = []
    entries = [e for e in entries if e.get("job_id") != metadata.get("job_id")]
    results = metadata.get("results") or []
    best_score = max(
        (float(r["viral_score"]) for r in results if r.get("viral_score")), default=0.0
    )
    entry = {
        "job_id": metadata["job_id"],
        "project_id": metadata["project_id"],
        "source_title": (metadata.get("source") or {}).get("title"),
        "source_url": (metadata.get("source") or {}).get("url"),
        "created_at": metadata["created_at"],
        "clip_count": len(results),
        "best_score": best_score,
        "status": metadata["status"],
        "generated_clips": len(metadata.get("generated_clips") or []),
    }
    entries.insert(0, entry)
    HISTORY_FILE.write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def get_history() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        entries = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return [e for e in entries if isinstance(e, dict)]
    except Exception:
        logger.warning("History file corrupt: %s", HISTORY_FILE)
        return []


def get_project(project_id: str) -> Optional[dict]:
    meta = PROJECTS_DIR / project_id / "metadata.json"
    if not meta.exists():
        return None
    try:
        return json.loads(meta.read_text(encoding="utf-8"))
    except Exception:
        return None


def get_job_snapshot(job_id: str) -> Optional[dict]:
    """Reconstruct a results payload from disk if the job left memory."""
    if not HISTORY_FILE.exists():
        return None
    for entry in get_history():
        if entry.get("job_id") == job_id:
            project = get_project(entry["project_id"])
            if project:
                return {
                    "job_id": job_id,
                    "status": project.get("status", "completed"),
                    "results": project.get("results") or [],
                    "source": project.get("source"),
                    "generated_clips": project.get("generated_clips") or [],
                }
    return None