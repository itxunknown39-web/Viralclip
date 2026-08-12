# ViralCut AI — AI Viral Clip Finder

## 1. Project Overview

### Product Name

**ViralCut AI — AI Viral Clip Finder**

### Product Type

AI-powered long-form video → viral short-form clip discovery and generation tool.

### Core Concept

ViralCut AI existing ViralCut-AI codebase ko base bana kar ek upgraded AI clipping platform hoga.

User YouTube ya supported video URL provide karega. System:

1. Video download karega.
2. Audio/transcript generate karega.
3. Word-level timestamps obtain karega.
4. Potential clip candidates identify karega.
5. OpenRouter AI se candidates ko analyze aur rank karega.
6. Best viral moments select karega.
7. Selected moments ko accurate start/end boundaries ke saath extract karega.
8. Optional 9:16 vertical conversion karega.
9. Styled captions apply karega.
10. Final MP4 clips preview aur download ke liye provide karega.

Primary goal: **long-form video ko manually watch kiye baghair best short-form moments discover karna.**

---

# 2. Existing Repository Foundation

Project existing `ViralCut-AI` repository ko base karega.

Existing repository already provides:

* FastAPI backend
* React/Vite frontend
* `yt-dlp` video downloading
* `faster-whisper` transcription
* word-level timestamps
* local clip selection
* FFmpeg rendering
* NVIDIA NVENC support
* 9:16 reframing
* caption presets
* effects
* job queue
* SSE progress
* history
* Google Colab/T4 support

Existing modules ko unnecessarily rewrite nahi karna.

### Reuse Existing Components

```text
app/downloader.py
app/transcriber.py
app/selector.py
app/clipper.py
app/captions.py
app/effects.py
app/jobs.py
app/models.py
app/history.py
app/main.py
```

New AI analysis functionality existing pipeline ke upar add ki jayegi.

---

# 3. Product Goals

## Primary Goals

### G1 — Viral Moment Discovery

Long-form video se automatically high-potential short-form moments identify karna.

### G2 — AI Ranking

Potential clips ko OpenRouter LLM ke through contextual viral score dena.

### G3 — T4 Optimization

Google Colab NVIDIA T4 GPU par memory-efficient aur fast processing.

### G4 — One-Click Workflow

User ko manually transcript, timestamps ya editing karne ki zarurat na ho.

### G5 — Production-Ready Clips

Selected clips directly downloadable MP4 output dein.

### G6 — Modern UI

Existing UI ko modern dark AI SaaS dashboard mein redesign karna.

---

# 4. Non-Goals

V1 mein following features mandatory nahi hain:

* Full browser-based video editor
* Multi-user collaboration
* Cloud video storage
* Social media auto-posting
* Advanced face tracking
* AI-generated B-roll
* AI voice cloning
* Full CapCut replacement
* Automatic music generation
* Complex timeline editor

Focus strictly:

**Find → Rank → Preview → Generate → Download**

---

# 5. Target Users

### Primary Users

* YouTube creators
* Shorts creators
* Podcast creators
* Video editors
* Content agencies
* Clip channels
* Personal brands
* AI content creators

### Main Use Case

User ke paas:

```text
1-hour podcast
2-hour interview
45-minute gaming video
1-hour documentary
90-minute livestream
```

System automatically identify kare:

```text
Top 5–10 strongest short-form moments
```

---

# 6. Core User Flow

```text
Open ViralCut AI
        ↓
New Project
        ↓
Paste Video URL
        ↓
Select Clip Preferences
        ↓
Analyze Video
        ↓
Download / Extract Audio
        ↓
Whisper Transcription
        ↓
Candidate Detection
        ↓
OpenRouter AI Analysis
        ↓
Viral Ranking
        ↓
Results Dashboard
        ↓
Preview Clip
        ↓
Generate Final Clip
        ↓
Download MP4
```

---

# 7. Input Sources

## V1 Supported Input

### URL

Primary input:

```text
YouTube URL
```

Example:

```text
https://www.youtube.com/watch?v=...
```

### Local Upload

Optional support:

```text
.mp4
.mov
.mkv
.webm
```

Existing upload functionality should remain available.

---

# 8. Video Analysis Pipeline

## Stage 1 — Input Validation

Validate:

* URL format
* supported source
* video accessibility
* duration
* available disk space
* available GPU
* file size

Show clear error messages.

---

# 9. Stage 2 — Video Download

Use existing `yt-dlp` downloader.

Requirements:

* Prefer appropriate quality rather than unnecessarily downloading maximum resolution.
* Preserve original source when required for final rendering.
* Handle YouTube extraction failures gracefully.
* Support cookies configuration when required.
* Clean temporary files after job completion.

---

# 10. Stage 3 — Audio Extraction

Extract audio for transcription.

Requirements:

* FFmpeg
* mono audio where appropriate
* speech-optimized format
* avoid unnecessary video decoding

---

# 11. Stage 4 — Transcription

Use:

**faster-whisper + CTranslate2**

T4 configuration:

```text
device = cuda
compute_type = float16
```

Requirements:

* Word-level timestamps
* Sentence segmentation
* VAD
* Automatic language detection
* Transcript caching
* Model caching

The system should not repeatedly transcribe the same source during one project.

---

# 12. Stage 5 — Candidate Clip Generation

Before calling OpenRouter, local processing should generate candidate windows.

This reduces API cost and latency.

Candidate generation should consider:

### Positive Signals

* Strong opening
* Hook keywords
* Questions
* Surprising statements
* Emotional moments
* Strong opinions
* Numbers/statistics
* Story climax
* Punchlines
* Contrarian statements
* Complete thoughts
* High speech density
* Natural sentence boundaries

### Negative Signals

* Starts mid-sentence
* Ends mid-sentence
* Excessive silence
* Repeated statements
* Long introductions
* Greetings
* Sponsor sections
* Context-dependent statements
* Weak conclusions

---

# 13. Candidate Duration

Default target:

```text
20–60 seconds
```

Preferred:

```text
30–45 seconds
```

User-configurable:

```text
15 sec
30 sec
45 sec
60 sec
90 sec
```

The system should prioritize natural narrative boundaries rather than blindly cutting at fixed durations.

---

# 14. OpenRouter AI Analysis

## Purpose

OpenRouter will act as the **intelligent viral-content evaluator**, not the video rendering engine.

The backend sends transcript candidates to OpenRouter.

Never send the entire video.

---

# 15. AI Candidate Input

Example structure:

```json
{
  "candidate_id": "clip_004",
  "start": 862.4,
  "end": 901.7,
  "duration": 39.3,
  "transcript": "..."
}
```

---

# 16. AI Evaluation Criteria

Each candidate should receive scores:

```text
Hook Strength
Curiosity
Emotional Impact
Standalone Value
Story/Punchline
Retention Potential
Shareability
Pacing
```

Each score:

```text
0–10
```

---

# 17. Viral Score

Recommended weighting:

```text
Hook Strength       20%
Emotional Impact    15%
Curiosity           15%
Standalone Value    15%
Story/Punchline     15%
Retention Potential 10%
Shareability        10%
```

Final score:

```text
0–100
```

The scoring algorithm must be deterministic after receiving AI scores.

---

# 18. AI Response Schema

OpenRouter response should be forced into structured JSON.

Example:

```json
{
  "candidate_id": "clip_004",
  "viral_score": 92,
  "scores": {
    "hook": 9,
    "emotion": 9,
    "curiosity": 10,
    "standalone": 9,
    "story": 9,
    "retention": 9,
    "shareability": 8
  },
  "reason": "Strong curiosity gap with a complete standalone insight.",
  "hook": "Most creators misunderstand this...",
  "recommended_start": 862.4,
  "recommended_end": 901.7,
  "title": "Why Most Creators Never Grow"
}
```

Backend must validate the schema before accepting the result.

---

# 19. OpenRouter Configuration

Environment variable:

```text
OPENROUTER_API_KEY=
```

Optional:

```text
OPENROUTER_MODEL=
OPENROUTER_BASE_URL=
```

API key must remain server-side.

### Security Requirement

Never expose:

```text
OPENROUTER_API_KEY
```

to React/frontend JavaScript.

---

# 20. AI Model Strategy

The system should allow model configuration through environment variables rather than hard-coding one model.

Example:

```text
OPENROUTER_MODEL=...
```

This allows future model switching without modifying application code.

---

# 21. Batch AI Analysis

Do not send every candidate as a separate API request when unnecessary.

Use batching:

```text
Transcript
   ↓
20–50 candidates
   ↓
Batch into manageable groups
   ↓
OpenRouter
   ↓
Structured JSON
```

Requirements:

* retry failed requests
* timeout handling
* malformed JSON recovery
* rate-limit handling
* configurable batch size

---

# 22. AI Ranking

After OpenRouter analysis:

```text
Candidate 1 → 94
Candidate 2 → 91
Candidate 3 → 87
Candidate 4 → 84
Candidate 5 → 82
...
```

Default result:

```text
Top 5
```

User option:

```text
Top 3
Top 5
Top 10
Top 20
```

---

# 23. Duplicate Detection

Multiple candidates may represent the same moment.

The backend must merge overlapping candidates.

Example:

```text
Clip A: 10:00–10:40
Clip B: 10:15–10:52
```

These should not appear as two completely independent results if they represent the same highlight.

Use overlap/IoU-based filtering.

---

# 24. Clip Boundary Optimization

AI-selected timestamps should be adjusted to natural word boundaries.

Rules:

* Never cut through words.
* Avoid cutting through sentences.
* Preserve hook.
* Preserve context.
* Preserve punchline.
* Prefer natural beginning/end.
* Respect user duration preference.

---

# 25. Results Dashboard

After analysis, show:

```text
Viral Clips Found
```

Each result card contains:

* Rank
* Viral Score
* Preview
* Start time
* End time
* Duration
* AI-generated title
* Hook
* Why it works
* Score breakdown
* Generate button

Example:

```text
#1
Viral Score: 94

Why Most Creators Never Grow

00:14:22 → 00:14:58
36 seconds

Hook       10/10
Curiosity   9/10
Emotion     9/10
Retention  10/10

[Preview] [Generate Clip]
```

---

# 26. Video Preview

Result cards should include preview functionality.

Requirements:

* HTML5 video player
* start/end preview
* play/pause
* seek
* duration
* thumbnail/poster
* mute/unmute

Preview should not require final rendering.

---

# 27. Clip Generation

When user clicks:

```text
Generate Clip
```

Backend should:

1. Load original source.
2. Seek to optimized start.
3. Apply selected aspect ratio.
4. Apply captions if enabled.
5. Apply selected effects.
6. Encode using NVENC when available.
7. Save MP4.
8. Return downloadable output.

---

# 28. Output Formats

### Default

```text
1080 × 1920
9:16
MP4
H.264
```

### Optional

```text
1920 × 1080
16:9
```

Future:

```text
1:1
4:5
```

---

# 29. Caption System

Reuse existing caption engine and presets.

V1 options:

```text
No Captions
Bold White
Hormozi Green
Hormozi Yellow
Beast Pop
One Word Punch
Word Reveal
Boxed TikTok
Comic Punch
Serif Elegant
```

Existing caption system should not be unnecessarily rewritten.

---

# 30. UI/UX Redesign

## Design Direction

Replace the current cyan-heavy interface with a modern:

**Dark AI SaaS / Creator Studio**

Visual characteristics:

* Dark background
* High contrast
* Clean typography
* Rounded cards
* Subtle borders
* Minimal gradients
* Clear hierarchy
* Modern dashboard
* Responsive layout

Avoid:

* excessive neon
* excessive glassmorphism
* clutter
* unnecessary animations
* huge empty spaces

---

# 31. Main Pages

## Dashboard

Display:

* New Project
* Recent Projects
* Total Videos Analyzed
* Clips Generated
* Recent Results

---

## New Project

Main interface:

```text
Paste Video URL
```

Options:

```text
Clip Count
Clip Duration
Aspect Ratio
Caption Style
Language
Generate Captions
Auto Effects
```

Primary CTA:

```text
Analyze Video
```

---

## Analysis Screen

Show real-time progress:

```text
Downloading video       ✓
Extracting audio        ✓
Transcribing            ✓
Finding candidates      ✓
AI viral analysis       64%
Ranking clips            ...
```

Use existing SSE progress architecture where possible.

---

## Results Screen

Display ranked viral candidates.

Sorting:

```text
Viral Score
Duration
Timestamp
```

---

## History

Display previous projects:

```text
Video
Date
Clips Found
Best Score
Generated Clips
```

---

## Settings

Settings:

```text
OpenRouter API Key
OpenRouter Model
Whisper Model
GPU Device
Default Clip Duration
Default Clip Count
Default Caption Style
Output Directory
Cookies File
```

Sensitive API keys should be masked.

---

# 32. T4 GPU Optimization

Target hardware:

```text
NVIDIA Tesla T4
16 GB VRAM
```

## Whisper

Use:

```text
CUDA
float16
```

Avoid loading multiple large Whisper models simultaneously.

---

## Rendering

Prefer:

```text
h264_nvenc
```

Fallback:

```text
libx264
```

Existing hardware detection should be preserved.

---

## Memory Management

Requirements:

* Release unused GPU memory.
* Avoid simultaneous heavy models.
* Process rendering jobs sequentially by default.
* Cache models.
* Avoid loading full-resolution frames into memory unnecessarily.
* Use temporary files instead of large in-memory video buffers.

---

# 33. T4 Processing Strategy

Recommended pipeline:

```text
Video
 ↓
Audio extraction
 ↓
Whisper GPU
 ↓
Candidate analysis
 ↓
OpenRouter
 ↓
Top clips
 ↓
Original source
 ↓
FFmpeg NVENC
```

AI analysis should not consume GPU resources unnecessarily.

OpenRouter processing happens remotely through API.

---

# 34. Performance Targets

For a typical 30–60 minute video on T4:

Goals:

* Efficient download
* Fast transcription
* Candidate generation without excessive CPU usage
* Minimal API calls
* Final rendering using NVENC

Performance should be benchmarked rather than relying on theoretical estimates.

Create benchmark mode:

```text
python benchmark_pipeline.py
```

Track:

```text
Download time
Audio extraction time
Transcription time
Candidate generation time
OpenRouter analysis time
Rendering time
Total time
Peak VRAM
Peak RAM
```

---

# 35. Job Architecture

Use asynchronous jobs.

Example:

```text
POST /api/analyze
        ↓
job_id
        ↓
background worker
        ↓
SSE progress
```

Existing `/api/progress/{job_id}` SSE mechanism should be reused where compatible.

---

# 36. API Design

## POST `/api/analyze`

Starts video analysis.

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
  "job_id": "abc123"
}
```

---

## GET `/api/progress/{job_id}`

Returns real-time job progress through SSE.

---

## GET `/api/results/{job_id}`

Returns ranked viral candidates.

---

## POST `/api/clips/{clip_id}/generate`

Generates final video.

---

## GET `/api/clips/{clip_id}/download`

Downloads generated MP4.

---

## GET `/api/history`

Returns project history.

---

## GET `/api/devices`

Returns:

```json
{
  "device": "cuda",
  "gpu": "Tesla T4",
  "nvenc": true
}
```

---

# 37. Error Handling

System must handle:

### YouTube Errors

```text
Video unavailable
Private video
Age restriction
Bot verification
Cookies required
Unsupported URL
```

### AI Errors

```text
Invalid API key
Rate limit
Timeout
Malformed JSON
Provider failure
Insufficient credits
```

### GPU Errors

```text
CUDA unavailable
VRAM insufficient
NVENC unavailable
CUDA library missing
```

### File Errors

```text
Disk full
Invalid video
Corrupt media
FFmpeg missing
Permission denied
```

Errors must be human-readable.

---

# 38. Retry Strategy

Retry automatically for:

* temporary OpenRouter failures
* HTTP 429
* HTTP 5xx
* transient download failures

Do not retry indefinitely.

Recommended:

```text
max_retries = 3
```

Use exponential backoff.

---

# 39. Privacy

Local media should remain local except where explicitly required.

Important:

**Video/audio should NOT be uploaded to OpenRouter.**

Only transcript/candidate metadata should be sent.

OpenRouter receives:

```text
Transcript text
Candidate timestamps
Candidate metadata
```

---

# 40. Storage

V1 can remain local-first.

Suggested structure:

```text
workspace/
├── downloads/
├── audio/
├── transcripts/
├── candidates/
├── projects/
├── clips/
├── temp/
└── logs/
```

Each project:

```text
projects/
└── project_id/
    ├── metadata.json
    ├── transcript.json
    ├── candidates.json
    └── results.json
```

---

# 41. Project Metadata

Store:

```json
{
  "project_id": "project_001",
  "source_url": "...",
  "source_title": "...",
  "duration": 3600,
  "created_at": "...",
  "clip_count": 5,
  "status": "completed"
}
```

---

# 42. Security Requirements

* Never expose OpenRouter API key to frontend.
* Validate all uploaded files.
* Sanitize filenames.
* Prevent arbitrary filesystem paths.
* Limit upload size.
* Validate URL inputs.
* Do not execute user-provided shell commands.
* Escape FFmpeg arguments safely.
* Clean temporary files.
* Never log API keys.

---

# 43. Frontend Architecture

Recommended:

```text
web/
├── src/
│   ├── components/
│   │   ├── VideoInput.jsx
│   │   ├── AnalysisProgress.jsx
│   │   ├── ClipCard.jsx
│   │   ├── ScoreBreakdown.jsx
│   │   ├── VideoPreview.jsx
│   │   └── SettingsPanel.jsx
│   │
│   ├── pages/
│   │   ├── Dashboard.jsx
│   │   ├── Create.jsx
│   │   ├── Results.jsx
│   │   ├── History.jsx
│   │   └── Settings.jsx
│   │
│   ├── api/
│   ├── hooks/
│   ├── utils/
│   └── styles/
```

---

# 44. Backend Architecture

Recommended additions:

```text
app/
├── ai/
│   ├── openrouter.py
│   ├── prompts.py
│   ├── schemas.py
│   └── ranking.py
│
├── analysis/
│   ├── candidates.py
│   ├── boundaries.py
│   └── deduplication.py
```

Existing modules remain intact wherever possible.

---

# 45. AI Prompt Requirements

The AI prompt must instruct the model to:

* Analyze only supplied transcript.
* Evaluate short-form potential.
* Prefer complete standalone moments.
* Identify strong hooks.
* Avoid context-dependent clips.
* Avoid weak openings.
* Return valid JSON only.
* Never invent transcript content.
* Return timestamps only within candidate boundaries unless boundary adjustment is explicitly allowed.

---

# 46. Result Quality Requirements

A clip should ideally satisfy:

```text
✓ Strong first 1–3 seconds
✓ Understandable without full video
✓ Clear narrative/idea
✓ Emotional or informational payoff
✓ Natural ending
✓ No unnecessary dead air
✓ Suitable for Shorts/Reels/TikTok
```

---

# 47. Acceptance Criteria

## Input

* [ ] User can paste a YouTube URL.
* [ ] URL is validated.
* [ ] Video metadata is retrieved.
* [ ] Download succeeds when source is accessible.

## Transcription

* [ ] Whisper runs on T4.
* [ ] Word-level timestamps are available.
* [ ] Transcript is cached.

## AI Analysis

* [ ] Candidate clips are generated locally.
* [ ] Candidates are sent to OpenRouter.
* [ ] API key remains backend-only.
* [ ] AI returns structured JSON.
* [ ] Invalid AI responses are handled.
* [ ] Candidates receive viral scores.
* [ ] Results are ranked.

## Results

* [ ] Top clips are displayed.
* [ ] Each clip has score.
* [ ] Each clip has timestamp.
* [ ] Each clip has title.
* [ ] Each clip has hook/reason.
* [ ] User can preview candidates.

## Rendering

* [ ] User can generate selected clip.
* [ ] 9:16 output works.
* [ ] NVENC is used on T4.
* [ ] Captions work.
* [ ] MP4 download works.

## UI

* [ ] Modern dark UI.
* [ ] Responsive layout.
* [ ] Clear progress state.
* [ ] No unnecessary UI clutter.
* [ ] Errors are readable.

---

# 48. V1 Feature Priority

## P0 — Mandatory

1. YouTube URL input
2. `yt-dlp` download
3. T4 Whisper transcription
4. Candidate generation
5. OpenRouter analysis
6. Viral scoring
7. Ranked results
8. Clip preview
9. Clip generation
10. 9:16 output
11. MP4 download
12. Modern UI
13. T4/NVENC optimization

## P1 — Important

1. Caption presets
2. History
3. Local uploads
4. Settings
5. Cookies support
6. Batch analysis
7. Duplicate candidate removal

## P2 — Future

1. Automatic face tracking
2. AI B-roll
3. Auto title/description/hashtags
4. Social media publishing
5. Cloud projects
6. Team collaboration
7. Full browser editor

---

# 49. Definition of Done

The project is considered complete when a user can perform:

```text
YouTube URL
      ↓
Analyze
      ↓
Wait
      ↓
Top 5 Viral Clips
      ↓
Preview
      ↓
Generate
      ↓
1080×1920 MP4
      ↓
Download
```

without manually editing code, manually finding timestamps, or manually analyzing the transcript.

The complete workflow must work on:

**Google Colab + NVIDIA T4 GPU**

and locally where compatible CUDA/NVENC hardware is available.

---

# 50. Final Product Positioning

The product should not feel like a generic video downloader or basic auto-cutter.

Its core positioning is:

> **AI finds the moments. ViralCut turns them into Shorts.**

The main differentiator is the combination of:

```text
Local GPU Processing
        +
faster-whisper
        +
Candidate Detection
        +
OpenRouter AI Reasoning
        +
Viral Scoring
        +
Automatic Clip Generation
```

The final UX should make the product feel like an **AI content repurposing assistant**, while keeping the heavy video processing local/T4 optimized.
