# ViralCut AI — AI Viral Clip Finder

Paste a YouTube URL → AI finds, ranks, and renders your most viral short-form moments as 1080×1920 MP4 clips.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/itxunknown39-web/Viralclip/blob/main/ViralCut_AI_Colab.ipynb)

```
YouTube / Video URL
      ↓
Backend Download (yt-dlp)
      ↓
Whisper Transcription (GPU)
      ↓
Local Candidate Detection
      ↓
OpenRouter AI Viral Analysis
      ↓
Ranked Viral Clips (Viral Score 0-100)
      ↓
Preview → Generate → Download
```

## Architecture

| Layer | Tech | Role |
|---|---|---|
| Backend | Python + FastAPI | Job pipeline, media engine, AI engine |
| AI layer | `app/ai/` | OpenRouter client, prompts, schemas, deterministic viral scoring |
| Analysis | `app/analysis/` | Local candidate generator, dedup (IoU), boundary optimization |
| Frontend | React + Vite | Dark AI creator dashboard, SSE progress |

## Repository Structure

```
app/
├── main.py            FastAPI app + endpoints
├── config.py          Central env configuration
├── paths.py           Workspace directories
├── models.py          Pydantic data models
├── downloader.py      yt-dlp download + metadata
├── transcriber.py     faster-whisper (singleton, GPU-aware, cached)
├── clipper.py         FFmpeg rendering (NVENC → libx264 fallback)
├── captions.py        ASS captions with presets
├── effects.py         Optional zoom effects
├── jobs.py            Background job manager + pipelines
├── history.py         JSON project persistence
├── ai/
│   ├── openrouter.py  Retry/backoff client, JSON recovery
│   ├── prompts.py     Isolated prompts (PROMPT_VERSION)
│   ├── schemas.py     Pydantic AI response validation
│   └── ranking.py     Server-authoritative viral score
└── analysis/
    ├── candidates.py  20-50 candidate windows from transcript
    ├── deduplication.py
    └── boundaries.py  Snap to natural boundaries
web/                   React + Vite frontend
workspace/             downloads, audio, transcripts, projects, clips
```

## Quick Start

### 1. Backend

```bash
pip install -r requirements.txt
cp .env.example .env        # add OPENROUTER_API_KEY
python -m app.main          # or: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Requires FFmpeg on PATH. On T4/Colab, `WHISPER_DEVICE=cuda`, `WHISPER_COMPUTE_TYPE=float16`; encoder auto-selects `h264_nvenc` when available.

### 2. Frontend (dev)

```bash
cd web
npm install
npm run dev                # http://localhost:5173 (proxies /api to :8000)
```

### 3. Production frontend

```bash
cd web && npm run build
```

`app/main.py` serves `web/dist` automatically when present: open `http://localhost:8000`.

## API

| Endpoint | Description |
|---|---|
| `POST /api/analyze` | Start analysis `{url, clip_count, min_duration, max_duration}` → `{job_id}` |
| `GET /api/progress/{job_id}` | SSE progress events (queued → downloading → extracting_audio → transcribing → finding_candidates → ai_analysis → ranking → completed/failed) |
| `GET /api/results/{job_id}` | Ranked viral clips with scores, titles, hooks, reasons |
| `POST /api/jobs/{job_id}/retry-ai` | Retry only the AI stage (no re-download/re-transcribe) |
| `GET /api/metadata?url=…` | Video metadata preview |
| `POST /api/upload` | Local file upload (.mp4/.mov/.mkv/.webm) |
| `POST /api/clips/{candidate_id}/generate?analysis_job_id=…` | Render clip `{aspect_ratio, width, height, caption_style, captions, effects}` |
| `GET /api/clips/{clip_id}/download` | Download rendered MP4 |
| `GET /api/history` | Project history |
| `GET /api/devices` | GPU / NVENC / Whisper device status |
| `GET|POST /api/settings` | Server-side settings (API key never returned) |

## Viral Scoring (server-side, deterministic)

```
Hook 20% · Emotion 15% · Curiosity 15% · Standalone 15% · Story 15% · Retention 10% · Shareability 10%
```

AI provides component scores (0–10); the backend owns the final score so results are reproducible.

## Configuration

All config via environment variables (see `.env.example`): `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, `WHISPER_MODEL`, `WHISPER_DEVICE`, `WHISPER_COMPUTE_TYPE`, `MIN/MAX_CLIP_DURATION`, `MAX_CLIPS`, `VIRALCUT_COOKIES_FILE`, and more.

Secrets stay server-side: the API key is never sent to the browser, cookies are never exposed, and video/audio are never uploaded to OpenRouter (only transcript text).

## Benchmark

```bash
python benchmark_pipeline.py --url "https://youtube.com/watch?v=..." --clip-count 5
```

## Colab

Open `ViralCut_AI_Colab.ipynb` (Runtime → Run all) with a T4 GPU for the full hosted workflow.

## Notes

- GPU-heavy work (Whisper, rendering) is sequential; candidate generation and AI analysis are lightweight CPU/API.
- Whisper model is a lazy singleton; transcripts are cached by content hash.
- One job at a time for heavy stages avoids T4 VRAM exhaustion.