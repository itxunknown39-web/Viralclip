"""Deterministic server-side viral score calculation.

The backend is authoritative for scoring — AI component scores feed a fixed
weighted formula so identical AI output always produces identical scores.
"""
from __future__ import annotations

from ..models import AIClipAnalysis

WEIGHTS = {
    "hook": 0.20,
    "emotional": 0.15,
    "curiosity": 0.15,
    "standalone": 0.15,
    "story": 0.15,
    "retention": 0.10,
    "shareability": 0.10,
}

SCORE_KEYS = [
    "hook",
    "curiosity",
    "emotional",
    "standalone",
    "story",
    "retention",
    "shareability",
]


def compute_viral_score(analysis: AIClipAnalysis) -> float:
    """Compute final 0-100 viral score from component scores."""
    components = {
        "hook": analysis.hook_score,
        "emotional": analysis.emotional_score,
        "curiosity": analysis.curiosity_score,
        "standalone": analysis.standalone_score,
        "story": analysis.story_score,
        "retention": analysis.retention_score,
        "shareability": analysis.shareability_score,
    }
    total = sum(
        components[key] * weight for key, weight in WEIGHTS.items() if key in components
    )
    return round(max(0.0, min(100.0, total * 10.0)), 1)


def scores_dict(analysis: AIClipAnalysis) -> dict[str, float]:
    """Flatten component scores to a dict for API responses."""
    out = {
        "hook": round(analysis.hook_score, 1),
        "curiosity": round(analysis.curiosity_score, 1),
        "emotion": round(analysis.emotional_score, 1),
        "standalone": round(analysis.standalone_score, 1),
        "story": round(analysis.story_score, 1),
        "retention": round(analysis.retention_score, 1),
        "shareability": round(analysis.shareability_score, 1),
    }
    return out