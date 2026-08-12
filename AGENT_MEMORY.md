# AGENT MEMORY — ViralCut AI Build State

## Project
ViralCut AI — AI Viral Clip Finder (per PRD.md / TRD.md / Backend+Frontend.md).
Input: YouTube/video URL → download → Whisper → local candidates → OpenRouter AI ranking → viral scores → 9:16 MP4 clips with captions.

## Build Status (current session: complete skeleton, verified)

### Backend (`app/` — FastAPI, Python 3.10+, Pydantic v2)
| File | Status | Notes |
|---|---|---|
| `config.py` | done | env-driven; `WHISPER_DEVICE/COMPUTE_TYPE=auto` resolve via CTranslate2 CUDA detect; keys server-only |
| `paths.py` | done | workspace/downloads/audio/transcripts/projects/clips/temp/logs |
| `models.py` | done | Word/Segment/Transcript/VideoSource/ClipCandidate/AIClipAnalysis/RankedClip + request models (Pydantic v2 validators, score clamps) |
| `downloader.py` | done | yt-dlp metadata + download (≤1080p mp4, merge), friendly errors, cookies support |
| `transcriber.py` | done | faster-whisper singleton, 16kHz mono wav, VAD, word timestamps, transcript cache by hash |
| `captions.py` | done | ASS builder + 9 presets (hormozi_green default), 3-word chunks |
| `effects.py` | done | subtle zoompan + aspect-crop/scale filter chain |
| `clipper.py` | done | ffmpeg render: input seek, reframe, ASS, NVENC auto-detect → libx264 fallback, stderr progress parse |
| `jobs.py` | done | JobManager (threads, SSE events, monotonic progress), analysis + generation pipelines, retry-AI |
| `history.py` | done | JSON projects + history index (metadata/results/transcript persisted) |
| `main.py` | done | all endpoints (see below); serves `web/dist` when built |
| `ai/openrouter.py` | done | retry/backoff, 429/5xx/timeout handling, JSON fence extraction, batch ≤8 |
| `ai/prompts.py` | done | PROMPT_VERSION=1.0, batch + single builders, strict JSON instructions |
| `ai/schemas.py` | done | AIClipAnalysis validation, invalid results dropped with log |
| `ai/ranking.py` | done | deterministic weighted score (Hook 20/Emotion 15/Curiosity 15/Standalone 15/Story 15/Retention 10/Shareability 10) |
| `analysis/candidates.py` | done | sentence-aware sliding windows, local scoring (hook keywords, density, completeness), 20–50 pool |
| `analysis/deduplication.py` | done | IoU ≥ 0.5, keep highest local_score |
| `analysis/boundaries.py` | done | snap to word/sentence boundaries, duration constraints, never cut inside a word |

### API (verified via TestClient)
- `POST /api/analyze` → `{job_id}` (background pipeline)
- `GET /api/progress/{job_id}` → SSE (queued→downloading→extracting_audio→transcribing→finding_candidates→ai_analysis→ranking→completed/failed)
- `GET /api/results/{job_id}` → ranked clips (also served from disk snapshot if job gone)
- `POST /api/jobs/{job_id}/retry-ai` → re-runs only OpenRouter stage
- `GET /api/metadata?url=`, `POST /api/upload`
- `POST /api/clips/{candidate_id}/generate?analysis_job_id=` → generation job
- `GET /api/clips/{clip_id}/download|status`
- `GET /api/history`, `GET /api/projects/{project_id}`
- `GET/POST /api/settings` (key masked, never returned), `GET /api/devices`, `GET /api/health`

### Frontend (`web/` — React 18 + Vite 5, react-router HashRouter)
- Pages: Dashboard (stats+recent), Create (URL input, metadata preview, options, SSE progress), Results (sort, clip cards, preview, generate+download), History, Settings (masked key, whisper/devices)
- Components: Sidebar, Header+DeviceStatus, VideoInput, VideoMetadata, AnalysisProgress, ClipCard, ClipGrid, ScoreBreakdown, VideoPreview (HTML5 seek-to-start/stop-at-end), GeneratePanel, HistoryList, ErrorAlert
- Hooks: useAnalysis, useProgress (EventSource), useVideoPreview
- Utils: formatTime, formatScore; styles.css premium dark theme, responsive (sidebar → top nav)
- `npm run build` → verified, `web/dist` built (served by FastAPI)

### Root
- `requirements.txt` (fastapi, uvicorn, python-multipart, pydantic≥2, yt-dlp, faster-whisper, requests)
- `.env.example`, `.gitignore`, `README.md`, `benchmark_pipeline.py`, `ViralCut_AI_Colab.ipynb` (T4: cuda+float16, NVENC, cloudflared tunnel)

## Verified checks
- `python -m compileall app` — clean
- TestClient: health/devices/analyze/results/history/settings all 200
- Local pipeline unit check: candidates (7), dedup, boundary snap, viral score math (88.0 example) — correct
- `npm install && npm run build` — clean (56 modules, ~191 KB JS)

## Environment notes (this machine)
- Windows, Python 3.14.6 + pip 26.1 (site-packages in `AppData\Roaming\Python\Python314`)
- Node 24 / npm 11
- FFmpeg NOT on PATH — install before rendering (runtime dependency)
- No CUDA locally → CPU mode + libx264 fallback path taken
- `uvicorn[standard]` extras can fail resolution on Python 3.14 → requirements.txt uses plain `uvicorn`

## Next steps (when continuing)
1. Install `faster-whisper` (heavy, needs CUDA wheels on Colab/Linux) — lazy import already guarded
2. Run a real end-to-end job with `OPENROUTER_API_KEY` set (needs .env or env var; settings load at import time — restart server after changing)
3. Fix uvicorn[standard]/httptools notes if Colab warns
4. Optional: unit tests per TRD §56-59 (tests/ dir)
5. Optional: face-tracking/advanced effects (P2 per PRD)

## Conventions / gotchas
- API key: backend-only; frontend Settings POSTs it, GET returns only `api_key_configured`
- `candidate_id` is `clip_NNN`; generation job ids used as clip ids for download (`{gen_job_id}_{candidate_id}`)
- Results endpoint falls back to disk (`history.get_job_snapshot`) so reloads after server restart still work
- Transcript/candidates saved to `workspace/projects/{project_id}/` after analysis → enables retry-AI without re-download