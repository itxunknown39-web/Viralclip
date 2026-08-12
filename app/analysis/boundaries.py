"""Clip boundary optimization — snap AI timestamps to natural word/sentence boundaries."""
from __future__ import annotations

from typing import Optional

from ..models import Transcript, Word

_SNAP_PAD = 3.0  # seconds: how far we look for a cleaner boundary


def _words_in_range(transcript: Transcript, start: float, end: float) -> list[Word]:
    return [w for w in transcript.all_words() if start <= w.start <= end]


def snap_start(transcript: Transcript, start: float) -> float:
    """Snap to the nearest word start (never inside a word)."""
    words = transcript.all_words()
    if not words:
        return start
    best = words[0].start
    best_delta = abs(words[0].start - start)
    for w in words:
        if w.start <= start < w.end:
            return w.start
        delta = abs(w.start - start)
        if delta < best_delta:
            best_delta = delta
            best = w.start
    return best


def snap_end(transcript: Transcript, end: float) -> float:
    """Snap to the nearest word end (never inside a word)."""
    words = transcript.all_words()
    if not words:
        return end
    best = words[-1].end
    best_delta = abs(words[-1].end - end)
    for w in words:
        if w.start < end <= w.end:
            return w.end
        delta = abs(w.end - end)
        if delta < best_delta:
            best_delta = delta
            best = w.end
    return best


def _sentence_boundaries(transcript: Transcript) -> list[tuple[float, float]]:
    """Sentence boundaries from segments (approximate sentence = segment)."""
    bounds: list[tuple[float, float]] = []
    for seg in transcript.segments:
        if seg.words:
            bounds.append((seg.words[0].start, seg.words[-1].end))
    return bounds


def optimize_boundaries(
    transcript: Transcript,
    start: float,
    end: float,
    min_duration: float,
    max_duration: float,
) -> tuple[float, float]:
    """Adjust timestamps toward natural boundaries while respecting duration."""
    bounds = _sentence_boundaries(transcript)
    if not bounds:
        return snap_start(transcript, start), snap_end(transcript, end)

    s = snap_start(transcript, start)
    e = snap_end(transcript, end)

    for b_start, _ in bounds:
        if 0 < b_start < s and (s - b_start) <= _SNAP_PAD:
            s = b_start
            break
    for _, b_end in bounds:
        if 0 < (b_end - e) <= _SNAP_PAD:
            e = b_end
            break

    duration = e - s
    if duration < min_duration:
        need = min_duration - duration
        for b_start, b_end in bounds:
            if b_start < s and (s - b_start) >= need:
                s = b_start
                break
        for b_start, b_end in bounds:
            if b_end > e and (b_end - e) >= need:
                e = b_end
                break
        if (e - s) < min_duration and e < transcript.duration:
            e = min(transcript.duration, e + (min_duration - (e - s)))

    if (e - s) > max_duration:
        duration = e - s
        excess = duration - max_duration
        truncate = excess / 2
        for b_start, b_end in reversed(bounds):
            if b_end > e - truncate and (b_end - e) < 0:
                continue
        for b_start, _ in bounds:
            if b_start > s and (b_start - s) >= truncate:
                s = b_start
                break
        else:
            s = min(s + excess, e - 5)
        if (e - s) > max_duration:
            e = s + max_duration

    if e - s < 3.0:
        e = s + max(3.0, min_duration)
    return round(s, 2), round(e, 2)