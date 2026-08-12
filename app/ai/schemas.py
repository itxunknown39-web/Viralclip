"""Pydantic schemas for AI analysis I/O."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..models import AIClipAnalysis


class BatchAIRequest(BaseModel):
    candidates: list[dict]
    min_duration: float = 20.0
    max_duration: float = 60.0


class BatchAIResponse(BaseModel):
    results: list[AIClipAnalysis] = Field(default_factory=list)


def validate_ai_result(raw: dict) -> Optional[AIClipAnalysis]:
    """Validate and coerce a raw AI result dict. Returns None if unusable."""
    try:
        return AIClipAnalysis.model_validate(raw)
    except Exception:
        return None