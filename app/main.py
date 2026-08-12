"""ViralCut AI — FastAPI application."""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from .ai.openrouter import OpenRouterError
from .clipper import detect_nvenc
from .config import settings, is_cuda_available
from .downloader import DownloadError, build_source, fetch_metadata
from .history import get_history, get_job_snapshot, get_project
from .jobs import (
    TERMINAL_STATUSES,
    manager,
    retry_ai_analysis,
    run_analysis_pipeline,
    run_generation_pipeline,
)
from .models import (
    AnalyzeRequest,
    AnalyzeResponse,
    GenerateRequest,
    GenerateResponse,
    SettingsUpdate,
)
from .paths import BASE_DIR, CLIPS_DIR, DOWNLOADS_DIR, ensure_workspace

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("viralcut")


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_workspace()
    try:
        import nvidia_smi  # noqa: F401  (optional info, ignore if missing)
    except ImportError:
        pass
    yield


app = FastAPI(title="ViralCut AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# System info
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/devices")
async def devices():
    cuda = is_cuda_available()
    nvenc = detect_nvenc() if cuda else False
    gpu_name = "NVIDIA GPU"
    if cuda:
        try:
            import ctranslate2

            if ctranslate2.get_cuda_device_count() > 0:
                gpu_name = "CUDA Device"
        except Exception:
            pass
    return {
        "cuda_available": cuda,
        "gpu": gpu_name if cuda else "CPU Mode",
        "nvenc_available": nvenc,
        "whisper_device": settings.whisper_device,
        "whisper_compute_type": settings.whisper_compute_type,
        "model": settings.openrouter_model,
        "api_key_configured": bool(settings.openrouter_api_key),
    }


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
@app.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    job = manager.create("analysis")
    job.data["clip_count"] = req.clip_count
    job.data["min_duration"] = req.min_duration
    job.data["max_duration"] = req.max_duration
    job.data["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    job.data["source_url"] = req.url
    manager.submit(job, lambda j: run_analysis_pipeline(j, req))
    return AnalyzeResponse(job_id=job.job_id, status="queued")


@app.get("/api/progress/{job_id}")
async def progress_sse(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_stream():
        sent = 0
        while True:
            with job._lock:
                events = list(job.events[sent:])
                status, stage, progress, message, error = (
                    job.status,
                    job.stage,
                    job.progress,
                    job.message,
                    job.error,
                )
            for ev in events:
                sent += 1
                yield f"data: {json.dumps(ev)}\n\n"
            if status in TERMINAL_STATUSES:
                yield f"data: {json.dumps({'stage': stage, 'progress': progress, 'message': message, 'status': status, 'error': error})}\n\n"
                break
            yield ": keepalive\n\n"
            await asyncio.sleep(0.4)

    return StreamingResponse(
        event_stream(), media_type="text/event-stream", headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@app.get("/api/results/{job_id}")
async def results(job_id: str):
    job = manager.get(job_id)
    if job is None:
        snapshot = get_job_snapshot(job_id)
        if snapshot:
            return snapshot
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "stage": job.stage,
        "progress": job.progress,
        "message": job.message,
        "error": job.error,
        "error_code": job.error_code,
        "source": job.data.get("source"),
        "results": job.data.get("results") or [],
        "generated_clips": job.data.get("generated_clips") or [],
    }


@app.post("/api/jobs/{job_id}/retry-ai")
async def retry_ai(job_id: str):
    job = manager.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "completed":
        raise HTTPException(status_code=400, detail="Job already completed")
    ok = retry_ai_analysis(job)
    if not ok:
        raise HTTPException(
            status_code=400,
            detail="Cannot retry AI: no saved candidates found for this job.",
        )
    return {"job_id": job_id, "status": "retrying"}


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------
@app.get("/api/metadata")
async def metadata(url: str):
    try:
        info = fetch_metadata(url)
        return build_source(info, url).model_dump()
    except DownloadError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


# ---------------------------------------------------------------------------
# Upload
# ---------------------------------------------------------------------------
@app.post("/api/upload")
async def upload(file: UploadFile):
    allowed = {".mp4", ".mov", ".mkv", ".webm"}
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
    dest_dir = DOWNLOADS_DIR
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"upload_{uuid.uuid4().hex[:8]}{suffix}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)
    source = build_source({}, "", dest)
    source.title = file.filename
    return source.model_dump()


# ---------------------------------------------------------------------------
# Clip generation
# ---------------------------------------------------------------------------
@app.post("/api/clips/{candidate_id}/generate", response_model=GenerateResponse)
async def generate_clip(
    candidate_id: str, req: GenerateRequest, analysis_job_id: str
):
    job = manager.get(analysis_job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Analysis job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis is not complete yet.")
    gen_job = manager.create("generation")
    payload = {
        "analysis_job_id": analysis_job_id,
        "candidate_id": candidate_id,
        "options": req.model_dump(),
    }
    manager.submit(gen_job, lambda j: run_generation_pipeline(j, payload))
    return GenerateResponse(job_id=gen_job.job_id, status="queued")


@app.get("/api/clips/{clip_id}/download")
async def download_clip(clip_id: str):
    path = CLIPS_DIR / f"{clip_id}.mp4"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Clip not found or not rendered yet.")
    return FileResponse(
        path,
        media_type="video/mp4",
        filename=f"viralcut_{clip_id}.mp4",
        content_disposition_type="attachment",
    )


@app.get("/api/clips/{clip_id}/status")
async def clip_status(clip_id: str):
    path = CLIPS_DIR / f"{clip_id}.mp4"
    return {"ready": path.exists(), "clip_id": clip_id}


# ---------------------------------------------------------------------------
# History / projects
# ---------------------------------------------------------------------------
@app.get("/api/history")
async def history():
    return {"projects": get_history()}


@app.get("/api/projects/{project_id}")
async def project(project_id: str):
    data = get_project(project_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return data


# ---------------------------------------------------------------------------
# Settings (server-side, keys never returned)
# ---------------------------------------------------------------------------
@app.post("/api/settings")
async def update_settings(update: SettingsUpdate):
    if update.openrouter_api_key is not None:
        settings.openrouter_api_key = update.openrouter_api_key.strip()
    if update.openrouter_model is not None:
        settings.openrouter_model = update.openrouter_model.strip()
    if update.whisper_model is not None:
        settings.whisper_model = update.whisper_model.strip()
    if update.whisper_device is not None:
        settings.whisper_device = update.whisper_device.strip()
    if update.whisper_compute_type is not None:
        settings.whisper_compute_type = update.whisper_compute_type.strip()
    if update.default_clip_count is not None:
        settings.default_clip_count = max(1, min(20, update.default_clip_count))
    if update.min_clip_duration is not None:
        settings.min_clip_duration = max(5.0, min(300.0, update.min_clip_duration))
    if update.max_clip_duration is not None:
        settings.max_clip_duration = max(
            settings.min_clip_duration, min(600.0, update.max_clip_duration)
        )
    if update.default_caption_style is not None:
        settings.default_caption_style = update.default_caption_style.strip()
    return {"ok": True, "api_key_configured": bool(settings.openrouter_api_key)}


@app.get("/api/settings")
async def get_settings():
    from .captions import STYLES_AVAILABLE

    return {
        "openrouter_model": settings.openrouter_model,
        "api_key_configured": bool(settings.openrouter_api_key),
        "whisper_model": settings.whisper_model,
        "whisper_device": settings.whisper_device,
        "whisper_compute_type": settings.whisper_compute_type,
        "default_clip_count": settings.default_clip_count,
        "min_clip_duration": settings.min_clip_duration,
        "max_clip_duration": settings.max_clip_duration,
        "default_caption_style": settings.default_caption_style,
        "caption_styles": STYLES_AVAILABLE,
    }


# ---------------------------------------------------------------------------
# Static frontend (served when web/dist exists)
# ---------------------------------------------------------------------------
_dist = BASE_DIR / "web" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="web")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.host, port=settings.port, reload=False)