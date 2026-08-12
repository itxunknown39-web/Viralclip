"""Workspace path management."""
from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

WORKSPACE_ROOT = Path(
    os.environ.get("VIRALCUT_WORKSPACE", str(BASE_DIR / "workspace"))
)

DOWNLOADS_DIR = WORKSPACE_ROOT / "downloads"
AUDIO_DIR = WORKSPACE_ROOT / "audio"
TRANSCRIPTS_DIR = WORKSPACE_ROOT / "transcripts"
CANDIDATES_DIR = WORKSPACE_ROOT / "candidates"
PROJECTS_DIR = WORKSPACE_ROOT / "projects"
CLIPS_DIR = WORKSPACE_ROOT / "clips"
TEMP_DIR = WORKSPACE_ROOT / "temp"
LOGS_DIR = WORKSPACE_ROOT / "logs"

HISTORY_FILE = PROJECTS_DIR / "history.json"

_OUTPUT_DIR = WORKSPACE_ROOT / "clips"


def ensure_workspace() -> None:
    for d in (
        DOWNLOADS_DIR,
        AUDIO_DIR,
        TRANSCRIPTS_DIR,
        CANDIDATES_DIR,
        PROJECTS_DIR,
        CLIPS_DIR,
        TEMP_DIR,
        LOGS_DIR,
    ):
        d.mkdir(parents=True, exist_ok=True)


def job_temp_dir(job_id: str) -> Path:
    p = TEMP_DIR / job_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def project_dir(project_id: str) -> Path:
    p = PROJECTS_DIR / project_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def output_dir() -> Path:
    from .config import settings

    p = Path(settings.output_dir)
    if not p.is_absolute():
        p = BASE_DIR / p
    p.mkdir(parents=True, exist_ok=True)
    return p