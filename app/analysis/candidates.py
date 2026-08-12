"""Candidate clip generation from a word-level transcript.

Local deterministic processing only — no GPU, no API calls.
Generates 20-50 candidate windows aligned to sentence boundaries.
"""
from __future__ import annotations

import re
from typing import Optional

from ..models import ClipCandidate, Transcript, Word

HOOK_KEYWORDS = {
    "never", "always", "secret", "why", "how", "stop", "start", "truth", "actually",
    "worst", "best", "biggest", "big mistake", "nobody", "everyone", "if you",
    "here's", "heres", "the key", "the real", "shocking", "crazy", "insane",
    "listen", "look", "imagine", "number one", "number 1", "important",
}

GREETING_PATTERNS = re.compile(
    r"^\s*(hey|hi|hello|welcome|thanks for|thank you for watching|so basically|"
    r"um|uh|okay? so|alright? so|good morning|good evening|guys? come on)",
    re.IGNORECASE,
)

ENDOF_SENTENCE = re.compile(r"[.!?…\"'”’]+$")

NUMBERS = re.compile(r"\d")


def _split_long_segments(transcript: Transcript, max_words: int = 90) -> list[dict]:
    """Normalize into sentence-like chunks with word-level boundaries."""
    sentences: list[dict] = []
    for seg in transcript.segments:
        words = seg.words
        if not words:
            continue
        current: list[Word] = []
        for w in words:
            current.append(w)
            is_end = ENDOF_SENTENCE.search(w.text.strip())
            if is_end or len(current) >= max_words:
                sentences.append({"words": current, "text": " ".join(x.text for x in current)})
                current = []
        if current:
            sentences.append({"words": current, "text": " ".join(x.text for x in current)})
    if not sentences:
        sentences.append(
            {"words": transcript.all_words(), "text": " ".join(w.text for w in transcript.all_words())}
        )
    return sentences


def _window_transcript(chunks: list[dict]) -> str:
    return " ".join(c["text"] for c in chunks).strip()


def _speech_density(chunks: list[dict], window_start: float, window_end: float) -> float:
    dur = max(window_end - window_start, 1.0)
    spoken = sum((w.end - w.start) for c in chunks for w in c["words"])
    return min(spoken / dur, 1.0)


def _hook_score(text: str) -> float:
    lowered = text.lower().strip()
    score = 0.0
    if "?" in text[-6:]:
        score += 0.4
    if NUMBERS.search(text[:40]):
        score += 0.3
    words = set(re.findall(r"[a-z']+", lowered[:80]))
    hits = words & HOOK_KEYWORDS
    score += min(len(hits) * 0.2, 0.6)
    if GREETING_PATTERNS.search(lowered):
        score -= 0.8
    if lowered.startswith(("so ", "and ", "but ")):
        score -= 0.3
    return max(0.0, min(1.0, score))


def _completeness_score(first: dict, last: dict, prev: Optional[dict], next_: Optional[dict]) -> float:
    """Starts/ends at sentence boundaries with no continuation tokens."""
    score = 1.0
    first_text = first["text"].strip().lower()
    last_text = last["text"].strip()
    if prev and not ENDOF_SENTENCE.search(prev["text"].strip()):
        score -= 0.2
    if GREETING_PATTERNS.search(first_text):
        score -= 0.3
    if next_ and len(next_["text"].strip()) < 3:
        score -= 0.2
    if not ENDOF_SENTENCE.search(last_text) and len(last_text) < 12:
        score -= 0.2
    return max(0.0, min(1.0, score))


def _local_score(density: float, hook: float, completeness: float) -> float:
    return round(0.45 * density + 0.35 * hook + 0.20 * completeness, 4)


def generate_candidates(
    transcript: Transcript,
    min_duration: float = 20.0,
    max_duration: float = 60.0,
    max_candidates: int = 40,
) -> list[ClipCandidate]:
    """Generate candidate windows using a sentence-aware sliding window."""
    sentences = _split_long_segments(transcript)
    if not sentences:
        return []

    candidates: list[ClipCandidate] = []
    n = len(sentences)

    idx = 0
    while idx < n:
        window: list[dict] = []
        window_start = sentences[idx]["words"][0].start
        window_end = window_start
        j = idx
        while j < n:
            j_end = sentences[j]["words"][-1].end
            window_len = j_end - window_start
            if window_len > max_duration and window:
                break
            window.append(sentences[j])
            window_end = j_end
            window_len = window_end - window_start
            if window_len >= min_duration:
                break
            j += 1
        if window:
            density = _speech_density(window, window_start, window_end)
            text = _window_transcript(window)
            hook = _hook_score(text)
            prev = sentences[idx - 1] if idx > 0 else None
            next_ = sentences[j + 1] if j + 1 < n else None
            completeness = _completeness_score(window[0], window[-1], prev, next_)
            score = _local_score(density, hook, completeness)
            candidates.append(
                ClipCandidate(
                    candidate_id=f"clip_{idx:03d}",
                    start=round(window_start, 2),
                    end=round(window_end, 2),
                    duration=round(window_end - window_start, 2),
                    transcript=text,
                    local_score=score,
                    hook_score=round(hook, 2),
                    completeness_score=round(completeness, 2),
                    speech_density_score=round(density, 2),
                )
            )
        idx += 1

    candidates.sort(key=lambda c: c.local_score, reverse=True)
    return candidates[:max_candidates]