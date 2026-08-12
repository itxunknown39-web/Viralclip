# ViralCut AI — Technical Requirements Document

## 1. Document Overview

### Product

**ViralCut AI — AI Viral Clip Finder**

### Document Type

Technical Requirements Document (TRD)

### Version

1.0

### Technical Objective

Existing `ViralCut-AI` Python/FastAPI + React/Vite codebase ko extend karke ek AI-powered viral clip discovery and generation system implement karna.

Core technical pipeline:

```text
Video URL / Upload
        ↓
yt-dlp / Upload Handler
        ↓
Media Metadata
        ↓
Audio Extraction
        ↓
faster-whisper
        ↓
Word-level Transcript
        ↓
Local Candidate Generator
        ↓
Candidate Deduplication
        ↓
OpenRouter AI Analysis
        ↓
Viral Scoring
        ↓
Boundary Optimization
        ↓
Ranked Clip Results
        ↓
FFmpeg + NVENC
        ↓
9:16 MP4
```

---

# 2. Existing Technology Stack

## Backend

```text
Python 3.10+
FastAPI
Uvicorn
Pydantic v2
yt-dlp
faster-whisper
CTranslate2
FFmpeg
requests/httpx
```

Existing repository already uses FastAPI, `yt-dlp`, `faster-whisper`, Pydantic and related dependencies.

## Frontend

```text
React
Vite
JavaScript
CSS
```

## GPU

Primary target:

```text
NVIDIA Tesla T4
16 GB VRAM
CUDA
NVENC
```

## External AI

```text
OpenRouter API
```

OpenRouter is used only for semantic candidate analysis and ranking.

---

# 3. System Architecture

```text
┌───────────────────────────────────────────────┐
│                  React UI                     │
│                                               │
│ Dashboard → Create → Analysis → Results      │
│                         ↓                     │
│                      History                  │
└───────────────────────┬───────────────────────┘
                        │ HTTP / SSE
                        ▼
┌───────────────────────────────────────────────┐
│                 FastAPI                      │
│                                               │
│ API Routes                                    │
│ Job Manager                                   │
│ Validation                                    │
│ Project Manager                               │
└───────────────┬───────────────┬───────────────┘
                │               │
                ▼               ▼
       ┌──────────────┐  ┌───────────────┐
       │ Media Engine │  │ AI Engine     │
       │              │  │               │
       │ yt-dlp       │  │ Candidate     │
       │ FFmpeg       │  │ Analyzer      │
       │ Whisper      │  │ OpenRouter     │
       └──────┬───────┘  └───────┬───────┘
              │                  │
              └────────┬─────────┘
                       ▼
               Result / Clip Store
```

---

# 4. Architectural Principles

## 4.1 Local-First

Video/audio processing remains local.

Only transcript/candidate text is sent to OpenRouter.

## 4.2 GPU-Aware

All compute-heavy compatible workloads must use T4 CUDA/NVENC.

## 4.3 Modular

AI functionality must be separated from:

* downloading
* transcription
* rendering
* UI

## 4.4 Provider-Agnostic AI

OpenRouter model should be configurable through environment variables.

## 4.5 Failure Isolation

An OpenRouter failure must not corrupt:

* downloaded source
* transcript
* project metadata
* existing results

---

# 5. Repository Structure

Target structure:

```text
ViralCut-AI/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── jobs.py
│   ├── downloader.py
│   ├── transcriber.py
│   ├── clipper.py
│   ├── captions.py
│   ├── effects.py
│   ├── history.py
│   ├── paths.py
│   │
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── openrouter.py
│   │   ├── prompts.py
│   │   ├── schemas.py
│   │   └── ranking.py
│   │
│   └── analysis/
│       ├── __init__.py
│       ├── candidates.py
│       ├── boundaries.py
│       └── deduplication.py
│
├── web/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── styles/
│   │
│   └── dist/
│
├── workspace/
│   ├── downloads/
│   ├── audio/
│   ├── transcripts/
│   ├── candidates/
│   ├── projects/
│   ├── clips/
│   ├── temp/
│   └── logs/
│
├── benchmark_pipeline.py
├── requirements.txt
├── .env
└── README.md
```

---

# 6. Environment Configuration

Required:

```env
OPENROUTER_API_KEY=
```

Recommended:

```env
OPENROUTER_MODEL=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

WHISPER_MODEL=medium
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16

OUTPUT_DIR=workspace/clips
TEMP_DIR=workspace/temp

MAX_CLIPS=10
MIN_CLIP_DURATION=20
MAX_CLIP_DURATION=60
```

Optional:

```env
VIRALCUT_COOKIES_FILE=
```

---

# 7. Configuration Rules

Configuration priority:

```text
Environment Variables
        ↓
Application Config
        ↓
Request-level overrides
        ↓
Hard defaults
```

Secrets must never be committed.

`.env` must be included in `.gitignore`.

---

# 8. Data Models

## 8.1 VideoSource

```python
class VideoSource:
    source_id: str
    url: str | None
    local_path: str | None
    title: str | None
    duration: float
    width: int | None
    height: int | None
    fps: float | None
```

---

# 9. Transcript Models

```python
class Word:
    text: str
    start: float
    end: float
    confidence: float | None
```

```python
class TranscriptSegment:
    start: float
    end: float
    text: str
    words: list[Word]
```

```python
class Transcript:
    language: str
    duration: float
    segments: list[TranscriptSegment]
    words: list[Word]
```

---

# 10. Candidate Model

```python
class ClipCandidate:
    candidate_id: str
    start: float
    end: float
    duration: float
    transcript: str

    local_score: float

    hook_score: float | None
    completeness_score: float | None
    speech_density_score: float | None
```

---

# 11. AI Analysis Model

```python
class AIClipAnalysis:
    candidate_id: str

    viral_score: float

    hook_score: float
    curiosity_score: float
    emotional_score: float
    standalone_score: float
    story_score: float
    retention_score: float
    shareability_score: float

    title: str
    hook: str
    reason: str

    recommended_start: float
    recommended_end: float
```

---

# 12. Final Clip Model

```python
class GeneratedClip:
    clip_id: str
    candidate_id: str

    start: float
    end: float
    duration: float

    viral_score: float

    output_path: str
    width: int
    height: int

    caption_style: str | None
    created_at: str
```

---

# 13. Job Model

```python
class AnalysisJob:
    job_id: str
    status: str

    progress: float
    stage: str

    source: VideoSource | None
    candidates: list[ClipCandidate]
    results: list[AIClipAnalysis]

    error: str | None
```

Status values:

```text
queued
downloading
extracting_audio
transcribing
finding_candidates
ai_analysis
ranking
completed
failed
cancelled
```

---

# 14. API Requirements

## POST `/api/analyze`

### Request

```json
{
  "url": "https://youtube.com/watch?v=...",
  "clip_count": 5,
  "min_duration": 20,
  "max_duration": 60
}
```

### Response

```json
{
  "job_id": "job_abc123",
  "status": "queued"
}
```

---

# 15. GET `/api/progress/{job_id}`

SSE endpoint.

Events:

```text
download
audio
transcription
candidate_generation
ai_analysis
ranking
completed
error
```

Example event:

```json
{
  "stage": "ai_analysis",
  "progress": 67,
  "message": "Analyzing viral potential..."
}
```

---

# 16. GET `/api/results/{job_id}`

Response:

```json
{
  "job_id": "job_abc123",
  "status": "completed",
  "results": [
    {
      "candidate_id": "clip_001",
      "viral_score": 94,
      "start": 862.4,
      "end": 901.7,
      "duration": 39.3,
      "title": "Why Most Creators Never Grow",
      "hook": "Most creators misunderstand this...",
      "reason": "Strong curiosity gap..."
    }
  ]
}
```

---

# 17. POST `/api/clips/{candidate_id}/generate`

Request:

```json
{
  "aspect_ratio": "9:16",
  "width": 1080,
  "height": 1920,
  "caption_style": "hormozi_green",
  "captions": true,
  "effects": false
}
```

Response:

```json
{
  "clip_id": "generated_001",
  "status": "queued"
}
```

---

# 18. GET `/api/clips/{clip_id}/download`

Returns MP4 file.

Headers should correctly specify:

```text
Content-Type: video/mp4
Content-Disposition: attachment
```

---

# 19. GET `/api/devices`

Response:

```json
{
  "cuda_available": true,
  "gpu": "Tesla T4",
  "nvenc_available": true,
  "whisper_device": "cuda"
}
```

---

# 20. OpenRouter Integration

Create:

```text
app/ai/openrouter.py
```

Responsibilities:

* API authentication
* request construction
* model selection
* timeout
* retry
* rate-limit handling
* JSON parsing
* error normalization

---

# 21. OpenRouter Request

HTTP:

```text
POST /chat/completions
```

Headers:

```text
Authorization: Bearer <OPENROUTER_API_KEY>
Content-Type: application/json
```

Model:

```text
OPENROUTER_MODEL
```

---

# 22. AI Prompt Architecture

Prompts should be separated from API client.

```text
app/ai/prompts.py
```

Functions:

```python
build_candidate_analysis_prompt(...)
build_batch_analysis_prompt(...)
```

Do not hard-code prompts directly inside API request functions.

---

# 23. AI Output Validation

Use Pydantic schemas.

Example:

```python
class AIAnalysisResponse(BaseModel):
    candidate_id: str
    viral_score: float
    hook_score: float
    curiosity_score: float
    emotional_score: float
    standalone_score: float
    story_score: float
    retention_score: float
    shareability_score: float
    title: str
    hook: str
    reason: str
    recommended_start: float
    recommended_end: float
```

Reject invalid results.

---

# 24. AI Score Calculation

OpenRouter provides component scores.

Backend calculates final score.

```text
final_score =
    hook * 0.20
  + emotional * 0.15
  + curiosity * 0.15
  + standalone * 0.15
  + story * 0.15
  + retention * 0.10
  + shareability * 0.10
```

Normalize to:

```text
0–100
```

Backend should remain authoritative for scoring.

---

# 25. Candidate Generation

Create:

```text
app/analysis/candidates.py
```

Algorithm:

```text
Transcript
   ↓
Sentence boundaries
   ↓
Sliding windows
   ↓
Duration filtering
   ↓
Hook detection
   ↓
Speech density
   ↓
Completeness
   ↓
Local scoring
   ↓
Top candidate pool
```

Candidate pool target:

```text
20–50 candidates
```

before OpenRouter.

---

# 26. Candidate Window Strategy

Do not use fixed timestamp cuts only.

Candidate boundaries should align to:

* sentence start
* sentence end
* word boundaries
* paragraph/topic changes

Window durations:

```text
minimum = 20 sec
preferred = 30–45 sec
maximum = 60 sec
```

unless user overrides.

---

# 27. Boundary Optimization

Create:

```text
app/analysis/boundaries.py
```

Requirements:

* snap start to nearest word boundary
* snap end to nearest word boundary
* avoid sentence truncation
* maintain hook
* maintain payoff
* respect duration constraints

---

# 28. Candidate Deduplication

Create:

```text
app/analysis/deduplication.py
```

Use temporal overlap.

Example:

```text
A = 100–140
B = 110–145
```

If overlap exceeds threshold:

```text
IoU >= 0.5
```

retain highest-scoring candidate.

---

# 29. Whisper Requirements

Model loading must be singleton/cached.

Do not initialize Whisper separately for every job.

Recommended:

```python
model = WhisperModel(
    model_size,
    device="cuda",
    compute_type="float16"
)
```

---

# 30. Whisper Memory Strategy

T4 has 16 GB VRAM.

Requirements:

* lazy model loading
* singleton model
* model cache
* no duplicate model instances
* release temporary tensors
* avoid loading unrelated GPU models

Only one heavy inference workload should normally occupy GPU at a time.

---

# 31. Audio Pipeline

Use FFmpeg.

Recommended:

```text
Video
 ↓
Audio extraction
 ↓
mono
 ↓
16 kHz
 ↓
Whisper
```

Temporary audio should be deleted after successful transcription unless debugging mode is enabled.

---

# 32. Video Rendering Pipeline

Final clip:

```text
Original Video
      ↓
Trim
      ↓
Reframe
      ↓
Scale
      ↓
Caption Overlay
      ↓
Optional Effects
      ↓
NVENC
      ↓
MP4
```

---

# 33. NVENC Configuration

Primary encoder:

```text
h264_nvenc
```

Fallback:

```text
libx264
```

Encoder selection:

```text
NVENC available
    ↓
h264_nvenc

otherwise
    ↓
CPU libx264
```

---

# 34. 9:16 Rendering

Default:

```text
1080x1920
```

Source landscape video should be reframed using existing clipper logic.

Do not stretch video.

Preferred:

```text
crop-to-fill
```

Optional future:

```text
blurred background + foreground
```

---

# 35. Caption Rendering

Reuse existing ASS caption generation.

Pipeline:

```text
Transcript Words
      ↓
ASS Builder
      ↓
Subtitle File
      ↓
FFmpeg
      ↓
Final MP4
```

Caption generation must use the same optimized clip boundaries.

---

# 36. Progress Reporting

Every major stage must emit progress.

Example:

```text
0–10%   Download
10–15%  Audio extraction
15–60%  Transcription
60–70%  Candidate generation
70–90%  OpenRouter analysis
90–95%  Ranking
95–100% Complete
```

Progress must never jump backward.

---

# 37. Job Concurrency

Default:

```text
1 heavy GPU job at a time
```

Reason:

Multiple Whisper/render jobs can cause:

* VRAM exhaustion
* CUDA failures
* performance degradation

CPU-only operations can run asynchronously where safe.

---

# 38. Temporary File Management

Every job receives:

```text
workspace/temp/{job_id}/
```

Files:

```text
source.*
audio.wav
transcript.json
candidates.json
ai_results.json
```

On successful completion:

* retain required project files
* delete unnecessary temporary files

On failure:

* preserve logs
* optionally preserve failed intermediate files in debug mode

---

# 39. Cache Strategy

Cache:

### Video metadata

Key:

```text
hash(source_url)
```

### Transcript

Key:

```text
hash(source_id + whisper_model)
```

### AI results

Key:

```text
hash(candidate_transcript + model + scoring_version)
```

This prevents unnecessary repeated processing.

---

# 40. History Storage

V1 can use JSON/local filesystem.

Example:

```text
workspace/projects/{project_id}/metadata.json
```

No database is mandatory for V1.

Architecture should allow future SQLite/PostgreSQL migration.

---

# 41. Frontend API Layer

Create:

```text
web/src/api/client.js
```

Functions:

```javascript
analyzeVideo()
getResults()
generateClip()
getHistory()
getDevices()
```

SSE:

```javascript
subscribeToProgress(jobId)
```

---

# 42. Frontend State

Required state:

```text
sourceUrl
project
jobId
jobStatus
progress
currentStage
results
selectedClip
generationStatus
errors
settings
```

Avoid excessive global state.

---

# 43. UI Components

Required:

```text
VideoInput
VideoMetadata
AnalysisProgress
ClipCard
ScoreBreakdown
VideoPreview
GeneratePanel
HistoryList
SettingsPanel
DeviceStatus
ErrorAlert
```

---

# 44. Device Status

Header/dashboard should show:

```text
GPU: Tesla T4
CUDA: Ready
NVENC: Ready
```

or:

```text
GPU: CPU Mode
```

This helps users immediately understand processing mode.

---

# 45. UI Theme

Design system:

```text
Background: near-black
Cards: dark elevated surfaces
Borders: subtle
Primary accent: restrained modern accent
Typography: clean sans-serif
```

Avoid excessive neon/cyan from the original interface.

Animations should be limited to:

* progress
* loading
* hover
* result appearance

---

# 46. API Security

All backend endpoints must validate:

* request schema
* file types
* file size
* URLs
* path inputs
* IDs

Never pass raw user strings directly into shell commands.

Use argument arrays/subprocess APIs rather than shell interpolation.

---

# 47. YouTube Cookie Handling

Support:

```text
VIRALCUT_COOKIES_FILE
```

Cookie file must:

* never be returned in API responses
* never be logged
* never be exposed to frontend
* never be committed

---

# 48. Error Taxonomy

Define normalized backend errors:

```text
DOWNLOAD_ERROR
TRANSCRIPTION_ERROR
GPU_ERROR
AI_AUTH_ERROR
AI_RATE_LIMIT
AI_TIMEOUT
AI_INVALID_RESPONSE
FFMPEG_ERROR
STORAGE_ERROR
VALIDATION_ERROR
UNKNOWN_ERROR
```

Frontend maps these to human-readable messages.

---

# 49. Logging

Use structured application logging.

Log:

```text
job_id
stage
duration
status
error_code
```

Never log:

```text
OPENROUTER_API_KEY
cookies
authorization headers
```

---

# 50. Performance Metrics

Benchmark must capture:

```text
video_duration
download_seconds
transcription_seconds
candidate_seconds
ai_seconds
render_seconds
total_seconds
peak_vram
peak_ram
```

Store benchmark results as JSON/CSV.

---

# 51. T4 Performance Requirements

System must:

* detect CUDA
* detect T4
* use FP16 Whisper
* use NVENC
* avoid duplicate model loading
* avoid unnecessary 1080p intermediate renders
* process GPU-heavy stages sequentially
* clean GPU memory where applicable

---

# 52. Failure Recovery

If OpenRouter fails:

```text
Download ✓
Transcript ✓
Candidates ✓
AI ✗
```

The project should remain recoverable.

User should be able to:

```text
Retry AI Analysis
```

without downloading/transcribing again.

Similarly, if rendering fails:

```text
Retry Render
```

without rerunning AI analysis.

---

# 53. Idempotency

Operations should be idempotent where possible.

Example:

```text
Same video
+
Same transcript
+
Same AI model
+
Same prompt version
```

should reuse cached results.

---

# 54. Prompt Versioning

Store:

```text
PROMPT_VERSION = "1.0"
```

AI cache key must include prompt version.

When prompt changes:

```text
1.0 → 1.1
```

old results can be invalidated intentionally.

---

# 55. AI Model Versioning

Store:

```text
model_name
prompt_version
scoring_version
```

inside project metadata.

Example:

```json
{
  "ai_model": "...",
  "prompt_version": "1.0",
  "scoring_version": "1.0"
}
```

---

# 56. Testing Strategy

## Unit Tests

Test:

* candidate generation
* duration filtering
* boundary optimization
* deduplication
* viral score calculation
* Pydantic validation
* API payload validation

---

# 57. Integration Tests

Test complete:

```text
URL
 ↓
Download
 ↓
Transcript
 ↓
Candidates
 ↓
Mock OpenRouter
 ↓
Results
```

OpenRouter should be mocked in automated tests.

---

# 58. Rendering Tests

Test:

* 9:16
* 16:9
* captions
* no captions
* NVENC
* CPU fallback
* corrupted input
* missing FFmpeg

---

# 59. GPU Tests

On T4:

```text
CUDA available
Whisper CUDA
FP16
NVENC
```

Verify no unexpected CPU fallback.

---

# 60. Acceptance Test

Final acceptance scenario:

```text
1. Launch application.
2. Confirm T4 detected.
3. Paste YouTube URL.
4. Click Analyze.
5. Video downloads.
6. Transcript completes.
7. Candidates generated.
8. OpenRouter evaluates candidates.
9. Top 5 results appear.
10. User previews result.
11. User clicks Generate.
12. FFmpeg uses NVENC.
13. 1080x1920 MP4 is created.
14. User downloads clip.
15. Project appears in History.
```

---

# 61. Deployment Target

## Primary

Google Colab:

```text
T4 GPU
+
FastAPI
+
React/Vite
+
Cloudflare Tunnel
```

Existing Colab workflow should be updated rather than replaced.

## Secondary

Local Windows/Linux:

```text
Python
FFmpeg
CUDA
NVIDIA GPU
```

---

# 62. Colab Requirements

Notebook must:

1. Clone repository.
2. Install dependencies.
3. Verify GPU.
4. Verify CUDA.
5. Verify FFmpeg.
6. Configure environment.
7. Start FastAPI.
8. Start frontend if required.
9. Expose application.
10. Display application URL.

Notebook must not create unnecessary test notebooks/files during normal execution.

---

# 63. Dependency Requirements

Base dependencies:

```text
fastapi
uvicorn[standard]
python-multipart
pydantic
yt-dlp
faster-whisper
requests
indic-transliteration
```

Add only required dependencies.

Avoid unnecessary packages that increase Colab startup time or dependency conflicts.

---

# 64. Backward Compatibility

Existing functionality must remain operational:

* local video upload
* YouTube downloading
* transcription
* captions
* clip rendering
* 9:16 output
* history
* GPU detection

New AI functionality should be additive.

---

# 65. Migration Strategy

### Phase 1

Audit existing repository.

### Phase 2

Refactor shared models/configuration only where necessary.

### Phase 3

Add:

```text
app/ai/
app/analysis/
```

### Phase 4

Add new APIs.

### Phase 5

Upgrade frontend.

### Phase 6

Integrate T4 optimizations.

### Phase 7

Add testing.

### Phase 8

Update Colab.

### Phase 9

Run full benchmark.

---

# 66. Implementation Priority

## P0

```text
OpenRouter client
Candidate generator
AI schemas
AI ranking
Analyze API
Results API
New Results UI
T4 optimization
Clip generation integration
```

## P1

```text
History improvements
Settings
Caching
Retry system
Advanced captions
```

## P2

```text
Cloud storage
Authentication
Social publishing
Advanced AI editing
```

---

# 67. Technical Definition of Done

The implementation is complete when:

```text
✓ Existing repository starts successfully
✓ FastAPI starts without errors
✓ React frontend builds successfully
✓ T4 is detected
✓ Whisper uses CUDA/FP16
✓ yt-dlp downloads supported URLs
✓ Transcript contains word timestamps
✓ Local candidate generator produces candidates
✓ OpenRouter analyzes candidates
✓ AI response is schema validated
✓ Viral score is calculated server-side
✓ Duplicate candidates are removed
✓ Results are ranked
✓ User can preview clips
✓ User can generate clips
✓ NVENC is used when available
✓ 1080x1920 MP4 renders correctly
✓ Captions render correctly
✓ Downloads work
✓ Failed AI requests can be retried
✓ Failed renders can be retried
✓ History persists
✓ API keys remain server-side
✓ Cookies remain private
✓ Temporary files are cleaned
✓ CPU fallback works
✓ Colab T4 workflow works
```

---

# 68. Final Technical Architecture

```text
                     ┌──────────────────────┐
                     │      React UI        │
                     └──────────┬───────────┘
                                │
                         HTTP + SSE
                                │
                     ┌──────────▼───────────┐
                     │       FastAPI        │
                     └──────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
              ▼                 ▼                 ▼
       ┌────────────┐   ┌──────────────┐  ┌────────────┐
       │ Downloader │   │ Transcriber  │  │ Job System │
       │   yt-dlp   │   │ faster-whisper│ │    SSE     │
       └──────┬─────┘   └──────┬───────┘  └────────────┘
              │                 │
              │                 ▼
              │        ┌─────────────────┐
              │        │ Candidate Engine│
              │        └────────┬────────┘
              │                 │
              │                 ▼
              │        ┌─────────────────┐
              │        │   OpenRouter    │
              │        │   AI Analyzer   │
              │        └────────┬────────┘
              │                 │
              │                 ▼
              │        ┌─────────────────┐
              │        │ Viral Ranker    │
              │        └────────┬────────┘
              │                 │
              └────────┬────────┘
                       ▼
                ┌───────────────┐
                │ FFmpeg/NVENC  │
                │ Clip Renderer │
                └───────┬───────┘
                        │
                        ▼
                 ┌─────────────┐
                 │ Final MP4   │
                 │ 1080x1920   │
                 └─────────────┘
```

# 69. Core Engineering Principle

The system must follow this rule:

**Do not use the GPU or OpenRouter for work that can be solved cheaply with local deterministic processing.**

Therefore:

```text
Whisper
→ GPU

Candidate generation
→ Local CPU

Semantic viral analysis
→ OpenRouter

Final video rendering
→ T4 NVENC

UI
→ Browser
```

This architecture keeps the application **fast, cost-efficient, T4-friendly, modular, and scalable for future SaaS development.**
