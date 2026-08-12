"""Pydantic data models shared across the application."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Transcript models
# ---------------------------------------------------------------------------
class Word(BaseModel):
    text: str
    start: float
    end: float
    confidence: Optional[float] = None


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str
    words: list[Word] = Field(default_factory=list)


class Transcript(BaseModel):
    language: str = "unknown"
    duration: float = 0.0
    segments: list[TranscriptSegment] = Field(default_factory=list)

    def all_words(self) -> list[Word]:
        words: list[Word] = []
        for seg in self.segments:
            words.extend(seg.words)
        return words


# ---------------------------------------------------------------------------
# Source models
# ---------------------------------------------------------------------------
class VideoSource(BaseModel):
    source_id: str
    url: Optional[str] = None
    local_path: Optional[str] = None
    title: Optional[str] = None
    duration: float = 0.0
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    thumbnail: Optional[str] = None
    channel: Optional[str] = None


# ---------------------------------------------------------------------------
# Candidate models
# ---------------------------------------------------------------------------
class ClipCandidate(BaseModel):
    candidate_id: str
    start: float
    end: float
    duration: float
    transcript: str
    local_score: float = 0.0
    hook_score: Optional[float] = None
    completeness_score: Optional[float] = None
    speech_density_score: Optional[float] = None


# ---------------------------------------------------------------------------
# AI analysis models
# ---------------------------------------------------------------------------
class AIClipAnalysis(BaseModel):
    candidate_id: str
    viral_score: float = Field(ge=0, le=100)
    hook_score: float = Field(ge=0, le=10)
    curiosity_score: float = Field(ge=0, le=10)
    emotional_score: float = Field(ge=0, le=10)
    standalone_score: float = Field(ge=0, le=10)
    story_score: float = Field(ge=0, le=10)
    retention_score: float = Field(ge=0, le=10)
    shareability_score: float = Field(ge=0, le=10)
    title: str = ""
    hook: str = ""
    reason: str = ""
    recommended_start: Optional[float] = None
    recommended_end: Optional[float] = None

    @field_validator("viral_score")
    @classmethod
    def _clamp_viral(cls, v: float) -> float:
        return max(0.0, min(100.0, v))

    @field_validator(
        "hook_score",
        "curiosity_score",
        "emotional_score",
        "standalone_score",
        "story_score",
        "retention_score",
        "shareability_score",
    )
    @classmethod
    def _clamp_component(cls, v: float) -> float:
        return max(0.0, min(10.0, v))


class RankedClip(BaseModel):
    candidate_id: str
    rank: int
    viral_score: float
    start: float
    end: float
    duration: float
    title: str
    hook: str
    reason: str
    scores: dict[str, float]
    transcript: str = ""


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=4)
    clip_count: int = Field(default=5, ge=1, le=20)
    min_duration: float = Field(default=20.0, ge=5, le=300)
    max_duration: float = Field(default=60.0, ge=5, le=600)

    @field_validator("max_duration")
    @classmethod
    def _validate_duration_range(cls, v: float, info) -> float:
        mn = info.data.get("min_duration", 20.0)
        if v < mn:
            raise ValueError("max_duration must be >= min_duration")
        return v


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str = "queued"


class GenerateRequest(BaseModel):
    aspect_ratio: str = Field(default="9:16", pattern="^(9:16|16:9|1:1|4:5)$")
    width: int = Field(default=1080, ge=320, le=3840)
    height: int = Field(default=1920, ge=320, le=3840)
    caption_style: str = "hormozi_green"
    captions: bool = True
    effects: bool = False


class GenerateResponse(BaseModel):
    job_id: str
    status: str = "queued"


class SettingsUpdate(BaseModel):
    openrouter_api_key: Optional[str] = None
    openrouter_model: Optional[str] = None
    whisper_model: Optional[str] = None
    whisper_device: Optional[str] = None
    whisper_compute_type: Optional[str] = None
    default_clip_count: Optional[int] = None
    min_clip_duration: Optional[float] = None
    max_clip_duration: Optional[float] = None
    default_caption_style: Optional[str] = None