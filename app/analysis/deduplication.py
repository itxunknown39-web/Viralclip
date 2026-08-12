"""Temporal overlap deduplication for candidate windows."""
from __future__ import annotations

from ..models import ClipCandidate


def overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    return max(0.0, min(a_end, b_end) - max(a_start, b_start))


def iou(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    inter = overlap(a_start, a_end, b_start, b_end)
    a_len = max(a_end - a_start, 0.0)
    b_len = max(b_end - b_start, 0.0)
    union = a_len + b_len - inter
    if union <= 0:
        return 0.0
    return inter / union


def deduplicate(
    candidates: list[ClipCandidate],
    threshold: float = 0.50,
    score_key: str = "local_score",
) -> list[ClipCandidate]:
    """Keep the highest-scoring candidate for each overlapping cluster."""
    if not candidates:
        return []
    ranked = sorted(
        candidates, key=lambda c: getattr(c, score_key, c.local_score), reverse=True
    )
    kept: list[ClipCandidate] = []
    for cand in ranked:
        if any(
            iou(cand.start, cand.end, k.start, k.end) >= threshold for k in kept
        ):
            continue
        kept.append(cand)
    kept.sort(key=lambda c: c.start)
    return kept