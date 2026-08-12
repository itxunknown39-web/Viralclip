# ViralCut AI — Backend + Frontend Implementation Specification

## 1. Objective

Existing `ViralCut-AI` repository ko modify karke complete **AI Viral Clip Finder** application implement karni hai.

Final workflow:

```text
YouTube / Video URL
        ↓
Backend Download
        ↓
Whisper Transcription
        ↓
Local Candidate Detection
        ↓
OpenRouter AI Viral Analysis
        ↓
Ranked Viral Clips
        ↓
Preview
        ↓
Generate
        ↓
9:16 MP4 + Captions
        ↓
Download
```

Implementation must preserve existing working video processing functionality while adding the new AI discovery layer.

---

# 2. Implementation Rules

## DO

* Existing working modules ko reuse karo.
* Existing FFmpeg/Whisper logic ko unnecessarily rewrite mat karo.
* New AI logic ko isolated modules mein rakho.
* OpenRouter API key backend-only rakho.
* T4 GPU ko efficiently use karo.
* Frontend ko modern SaaS dashboard mein redesign karo.
* Every major operation ko progress state do.
* Errors ko readable messages mein convert karo.
* Existing Colab compatibility preserve karo.

## DON'T

* Frontend se directly OpenRouter call mat karo.
* Video OpenRouter ko upload mat karo.
* Entire transcript blindly ek huge request mein mat bhejo.
* Har candidate ke liye unnecessary separate API request mat banao.
* Multiple Whisper models simultaneously load mat karo.
* Existing rendering pipeline ko unnecessarily replace mat karo.
* Fake progress bars mat banao.
* API keys frontend bundle mein expose mat karo.

---

# 3. Backend Implementation

## 3.1 Backend Stack

```text
Python
FastAPI
Pydantic v2
Uvicorn
yt-dlp
faster-whisper
FFmpeg
CUDA
NVENC
OpenRouter API
```

---

# 4. Backend Folder Structure

Create:

```text
app/
├── __init__.py
├── main.py
├── models.py
├── jobs.py
├── downloader.py
├── transcriber.py
├── clipper.py
├── captions.py
├── effects.py
├── history.py
├── paths.py
│
├── ai/
│   ├── __init__.py
│   ├── openrouter.py
│   ├── prompts.py
│   ├── schemas.py
│   └── ranking.py
│
└── analysis/
    ├── __init__.py
    ├── candidates.py
    ├── boundaries.py
    └── deduplication.py
```

Do not duplicate functionality already present in existing modules.

---

# 5. Configuration

Create centralized configuration.

Example:

```python
OPENROUTER_API_KEY
OPENROUTER_MODEL
OPENROUTER_BASE_URL

WHISPER_MODEL
WHISPER_DEVICE
WHISPER_COMPUTE_TYPE

MIN_CLIP_DURATION
MAX_CLIP_DURATION
DEFAULT_CLIP_COUNT
```

Use environment variables.

Never hard-code secrets.

---

# 6. OpenRouter Client

File:

```text
app/ai/openrouter.py
```

Create class:

```python
class OpenRouterClient:
    def analyze_candidates(...)
    def analyze_batch(...)
```

Responsibilities:

* authentication
* HTTP request
* model selection
* timeout
* retry
* rate-limit handling
* JSON parsing
* validation
* error normalization

---

# 7. OpenRouter Request Flow

```text
Candidate Generator
        ↓
Candidate JSON
        ↓
Prompt Builder
        ↓
OpenRouter Client
        ↓
LLM
        ↓
JSON Response
        ↓
Pydantic Validation
        ↓
AI Results
```

---

# 8. AI Prompt

Create:

```text
app/ai/prompts.py
```

The prompt must tell the model:

* Find high-potential short-form moments.
* Evaluate hook strength.
* Evaluate curiosity.
* Evaluate emotional impact.
* Evaluate standalone value.
* Evaluate retention potential.
* Evaluate shareability.
* Avoid clips requiring unnecessary context.
* Avoid incomplete sentences.
* Do not invent information.
* Return strict JSON.
* Keep timestamps inside candidate boundaries.

Prompt version:

```text
VIRAL_PROMPT_VERSION=1.0
```

---

# 9. AI Response Schema

Use Pydantic.

```python
class AIClipAnalysis(BaseModel):
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

Validate score ranges.

---

# 10. Viral Score

Calculate server-side.

```text
Hook             20%
Emotion          15%
Curiosity        15%
Standalone       15%
Story/Punch      15%
Retention        10%
Shareability     10%
```

Never blindly trust an AI-provided final score.

---

# 11. Candidate Generator

File:

```text
app/analysis/candidates.py
```

Input:

```text
Transcript
```

Output:

```text
20–50 candidate windows
```

Candidate signals:

```text
Strong opening
Question
Surprising statement
Emotional statement
Contrarian opinion
Story climax
Punchline
High speech density
Complete thought
```

Negative signals:

```text
Greeting
Long silence
Incomplete sentence
Mid-sentence start
Sponsor segment
Weak ending
Repeated statement
```

---

# 12. Candidate Generation Algorithm

```text
Transcript
    ↓
Sentence boundaries
    ↓
Sliding windows
    ↓
Duration filtering
    ↓
Local scoring
    ↓
Top candidate pool
```

Target:

```text
20–50 candidates
```

Do not send hundreds of candidates to OpenRouter.

---

# 13. Candidate Deduplication

File:

```text
app/analysis/deduplication.py
```

Use temporal overlap.

If:

```text
A = 100–140
B = 110–145
```

and overlap exceeds configured threshold:

```text
IoU >= 0.50
```

keep the stronger candidate.

---

# 14. Boundary Optimizer

File:

```text
app/analysis/boundaries.py
```

Adjust AI timestamps to:

* word boundaries
* sentence boundaries
* natural starts
* natural endings

Never cut inside a word.

---

# 15. Analysis API

Implement:

```text
POST /api/analyze
```

Request:

```json
{
  "url": "...",
  "clip_count": 5,
  "min_duration": 20,
  "max_duration": 60
}
```

Response:

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

# 16. Analysis Job Pipeline

Backend job:

```text
1. Validate URL
2. Retrieve metadata
3. Download source
4. Extract audio
5. Load cached Whisper
6. Transcribe
7. Generate candidates
8. Deduplicate
9. Batch candidates
10. Call OpenRouter
11. Validate AI results
12. Calculate viral scores
13. Rank
14. Save results
15. Mark completed
```

---

# 17. Progress API

Keep existing SSE architecture.

Endpoint:

```text
GET /api/progress/{job_id}
```

Stages:

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
```

Example:

```json
{
  "stage": "ai_analysis",
  "progress": 78,
  "message": "AI is ranking viral moments..."
}
```

---

# 18. Retry AI

If OpenRouter fails temporarily:

```text
Retry 1
↓
exponential backoff
↓
Retry 2
↓
Retry 3
↓
failed
```

Do not restart download/transcription.

User must be able to retry AI analysis separately.

---

# 19. Results API

Implement:

```text
GET /api/results/{job_id}
```

Return:

```json
{
  "job_id": "abc123",
  "status": "completed",
  "results": [
    {
      "rank": 1,
      "viral_score": 94,
      "start": 862.4,
      "end": 901.7,
      "duration": 39.3,
      "title": "Why Most Creators Never Grow",
      "hook": "Most creators misunderstand this...",
      "reason": "Strong curiosity gap...",
      "scores": {
        "hook": 10,
        "curiosity": 9,
        "emotion": 9,
        "standalone": 9,
        "story": 9,
        "retention": 10,
        "shareability": 8
      }
    }
  ]
}
```

---

# 20. Clip Generation API

Implement:

```text
POST /api/clips/{candidate_id}/generate
```

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

---

# 21. Rendering Pipeline

Reuse existing clipper.

```text
Original Source
      ↓
Optimized Start/End
      ↓
Crop/Reframe
      ↓
Scale 1080x1920
      ↓
ASS Captions
      ↓
Optional Effects
      ↓
NVENC
      ↓
MP4
```

---

# 22. GPU Configuration

T4:

```text
Whisper:
CUDA
float16

Rendering:
h264_nvenc
```

Fallback:

```text
CPU
libx264
```

At startup detect:

```text
CUDA available
GPU name
NVENC available
```

---

# 23. Device API

Implement:

```text
GET /api/devices
```

Example:

```json
{
  "cuda_available": true,
  "gpu": "Tesla T4",
  "nvenc_available": true,
  "whisper_device": "cuda"
}
```

---

# 24. Clip Preview

Do not render a second video just for preview.

Preview should use:

* original video
* candidate timestamps

Frontend video player should seek to selected start/end.

---

# 25. History API

Keep existing history implementation if compatible.

Expose:

```text
GET /api/history
```

Store:

```text
project_id
source_title
source_url
created_at
clip_count
best_score
generated_clips
```

---

# 26. Frontend Implementation

## Stack

```text
React
Vite
JavaScript
CSS
HTML5 Video
SSE
Fetch API
```

---

# 27. Frontend Structure

```text
web/src/
├── App.jsx
│
├── api/
│   └── client.js
│
├── components/
│   ├── Sidebar.jsx
│   ├── Header.jsx
│   ├── VideoInput.jsx
│   ├── VideoMetadata.jsx
│   ├── AnalysisProgress.jsx
│   ├── ClipCard.jsx
│   ├── ClipGrid.jsx
│   ├── ScoreBreakdown.jsx
│   ├── VideoPreview.jsx
│   ├── GeneratePanel.jsx
│   ├── DeviceStatus.jsx
│   ├── HistoryList.jsx
│   └── ErrorAlert.jsx
│
├── pages/
│   ├── Dashboard.jsx
│   ├── Create.jsx
│   ├── Results.jsx
│   ├── History.jsx
│   └── Settings.jsx
│
├── hooks/
│   ├── useAnalysis.js
│   ├── useProgress.js
│   └── useVideoPreview.js
│
├── utils/
│   ├── formatTime.js
│   └── formatScore.js
│
└── styles/
    └── styles.css
```

---

# 28. App Shell

Layout:

```text
┌──────────────────────────────────────────────────┐
│ ViralCut AI                         T4 ● Ready   │
├────────────┬─────────────────────────────────────┤
│            │                                     │
│ Dashboard  │                                     │
│ New Project│         Main Content                │
│ History    │                                     │
│ Settings   │                                     │
│            │                                     │
└────────────┴─────────────────────────────────────┘
```

Responsive behavior:

* Desktop sidebar
* Tablet compact sidebar
* Mobile collapsible navigation

---

# 29. Theme

Replace old cyan-heavy design.

Target:

**Premium dark AI creator dashboard**

Use:

* near-black background
* dark elevated surfaces
* subtle borders
* modern accent
* strong white typography
* muted secondary text
* restrained gradients

Avoid:

* excessive neon
* excessive glow
* giant cards
* unnecessary animations
* clutter

---

# 30. Dashboard

Show:

```text
Welcome back

[ + New Project ]

Videos Analyzed
Clips Found
Clips Generated
Average Viral Score
```

Recent projects:

```text
Project
Video
Date
Best Score
Clips
```

---

# 31. New Project Page

Main card:

```text
Find Your Viral Moments
```

URL input:

```text
Paste YouTube or video URL...
```

Button:

```text
Analyze Video
```

Options:

```text
Number of Clips
20–60 sec
Aspect Ratio
Caption Style
Captions On/Off
Effects On/Off
```

Default:

```text
5 clips
20–60 sec
9:16
Captions On
Effects Off
```

---

# 32. Video Metadata

After URL validation show:

```text
Thumbnail
Title
Duration
Channel
Resolution
```

Example:

```text
┌─────────────────────────────────────────────┐
│ [Thumbnail]                                 │
│                                             │
│ The Complete Creator Interview              │
│ 1h 12m                                      │
│ YouTube                                     │
└─────────────────────────────────────────────┘
```

---

# 33. Analysis Screen

Show actual backend progress.

```text
Analyzing your video

✓ Downloading
✓ Extracting audio
✓ Transcribing
✓ Finding candidate moments
● AI viral analysis
○ Ranking clips
```

Progress bar:

```text
████████████████░░░░ 78%
```

Message:

```text
AI is analyzing 32 potential moments...
```

---

# 34. Results Page

Header:

```text
Viral Moments
7 clips found
```

Controls:

```text
Sort:
Viral Score
Duration
Timestamp

Show:
5
10
20
```

---

# 35. Clip Card

Each card:

```text
┌───────────────────────────────────────────┐
│ #1                         VIRAL 94       │
│                                           │
│         VIDEO PREVIEW                    │
│                                           │
│ Why Most Creators Never Grow              │
│ 00:14:22 — 00:14:58                      │
│                                           │
│ Hook       ██████████ 10                  │
│ Curiosity  █████████  9                   │
│ Emotion    █████████  9                   │
│ Retention  ██████████ 10                  │
│                                           │
│ Strong curiosity gap + complete insight.  │
│                                           │
│ [ Preview ]        [ Generate Clip ]      │
└───────────────────────────────────────────┘
```

---

# 36. Viral Score UI

Score categories:

```text
Hook
Curiosity
Emotion
Standalone
Story
Retention
Shareability
```

Use progress bars.

Avoid overwhelming the user with raw technical information.

---

# 37. Preview Player

Requirements:

```text
Play
Pause
Seek
Mute
Duration
```

When user selects a clip:

```text
video.currentTime = candidate.start
```

Preview should stop at:

```text
candidate.end
```

---

# 38. Generate Panel

When user clicks Generate:

```text
Generate Viral Clip

Aspect Ratio
[ 9:16 ]

Captions
[ ON ]

Caption Style
[ Hormozi Green ]

Effects
[ OFF ]

[ Generate ]
```

Show generation progress.

---

# 39. Generated Clip State

After rendering:

```text
Clip Ready

[ Preview ]

[ Download MP4 ]
```

Output:

```text
1080 × 1920
MP4
H.264
```

---

# 40. History Page

Cards/table:

```text
Source Video
Date
Clips
Best Score
Status

[Open]
```

Clicking project opens results.

---

# 41. Settings Page

Sections:

### AI

```text
OpenRouter API Key
Model
```

### Transcription

```text
Whisper Model
Device
Compute Type
```

### Defaults

```text
Clip Count
Duration
Aspect Ratio
Caption Style
```

### System

```text
GPU Status
NVENC Status
FFmpeg Status
```

API key field must be masked.

---

# 42. Device Indicator

Header:

```text
● T4 GPU Ready
```

States:

```text
GPU Ready
CPU Mode
GPU Error
Checking...
```

---

# 43. Frontend API Client

`web/src/api/client.js`

Implement:

```javascript
export async function analyzeVideo(data)
export async function getResults(jobId)
export async function generateClip(candidateId, options)
export async function getHistory()
export async function getDevices()
```

Use a centralized API base URL.

---

# 44. SSE Hook

Create:

```text
useProgress(jobId)
```

Behavior:

```text
jobId exists
    ↓
EventSource()
    ↓
receive progress
    ↓
update React state
    ↓
completed → close connection
```

Handle:

* disconnect
* error
* completed
* failed

---

# 45. Analysis Hook

Create:

```text
useAnalysis()
```

Responsibilities:

* start analysis
* track job ID
* subscribe to progress
* fetch final results
* expose loading/error/result state

---

# 46. Loading States

Every async action must have a clear state.

Examples:

```text
Analyzing...
Generating...
Downloading...
Loading...
Retrying...
```

Disable duplicate submission while request is active.

---

# 47. Error UI

Examples:

### YouTube error

```text
We couldn't access this video.
The video may be private or require authentication.
```

### API error

```text
AI analysis is temporarily unavailable.
You can retry without reprocessing the video.
```

### GPU error

```text
CUDA is unavailable. The application switched to CPU mode.
```

Never display raw Python stack traces to normal users.

---

# 48. Responsive Design

Desktop:

```text
Sidebar + 2/3-column result layout
```

Tablet:

```text
Compact sidebar + 2-column cards
```

Mobile:

```text
Top navigation
Single-column cards
Full-width preview
```

---

# 49. Frontend Performance

Requirements:

* Lazy-load result videos.
* Do not load all generated MP4s simultaneously.
* Use poster images where possible.
* Avoid unnecessary React re-renders.
* Keep SSE state isolated.
* Virtualize long result lists if necessary.

---

# 50. Backend/Frontend Contract

Frontend must never assume undocumented response fields.

API schemas must remain consistent.

If backend returns:

```json
{
  "viral_score": 94
}
```

frontend should use exactly:

```javascript
result.viral_score
```

Do not create inconsistent aliases.

---

# 51. End-to-End User Journey

```text
Dashboard
    ↓
New Project
    ↓
Paste URL
    ↓
Validate
    ↓
Analyze
    ↓
Progress
    ↓
Results
    ↓
Select Clip
    ↓
Preview
    ↓
Generate
    ↓
Render
    ↓
Download
```

---

# 52. Backend Completion Checklist

* [ ] OpenRouter client implemented
* [ ] Environment configuration implemented
* [ ] AI schemas implemented
* [ ] AI prompts isolated
* [ ] Candidate generator implemented
* [ ] Candidate deduplication implemented
* [ ] Boundary optimization implemented
* [ ] Viral score calculation implemented
* [ ] `/api/analyze`
* [ ] `/api/progress/{job_id}`
* [ ] `/api/results/{job_id}`
* [ ] `/api/clips/{candidate_id}/generate`
* [ ] `/api/clips/{clip_id}/download`
* [ ] `/api/devices`
* [ ] `/api/history`
* [ ] Retry handling
* [ ] Error handling
* [ ] Caching
* [ ] T4 optimization
* [ ] NVENC detection

---

# 53. Frontend Completion Checklist

* [ ] New dark UI
* [ ] Dashboard
* [ ] New Project
* [ ] URL input
* [ ] Video metadata
* [ ] Analysis progress
* [ ] Results page
* [ ] Clip cards
* [ ] Viral score display
* [ ] Preview player
* [ ] Generate panel
* [ ] Generation progress
* [ ] Download button
* [ ] History
* [ ] Settings
* [ ] GPU indicator
* [ ] Error states
* [ ] Responsive layout

---

# 54. Final Build Requirement

The final implementation must produce this exact practical experience:

```text
                 VIRALCUT AI

        Paste YouTube Video URL
                    ↓
              Analyze Video
                    ↓
          ┌──────────────────┐
          │ T4 GPU           │
          │ Whisper           │
          │ Candidate Finder  │
          └────────┬─────────┘
                   ↓
             OpenRouter AI
                   ↓
           VIRAL SCORE 94
           VIRAL SCORE 91
           VIRAL SCORE 88
           VIRAL SCORE 85
           VIRAL SCORE 82
                   ↓
              Preview
                   ↓
            Generate Clip
                   ↓
             NVENC Render
                   ↓
             1080×1920 MP4
                   ↓
                Download
```

## Final Engineering Rule

**Existing ViralCut-AI = Media Processing Engine**

**New AI layer = Viral Intelligence Engine**

**New React UI = Creator Experience**

Do not turn the project into an unnecessarily complex rewrite. Extend the existing engine, isolate the new AI functionality, optimize the GPU path, and make the final product feel like a polished standalone AI SaaS application.
