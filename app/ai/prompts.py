"""AI prompt building. Isolated from the API client."""
from __future__ import annotations

import json
from typing import Optional

from ..models import ClipCandidate

PROMPT_VERSION = "1.0"

SYSTEM_PROMPT = """You are ViralCut AI, a world-class short-form content strategist.

Your job: given transcript excerpts around candidate moments from a long-form video, evaluate each candidate's potential to go viral as a standalone short clip (YouTube Shorts / TikTok / Reels).

For EVERY candidate, score these dimensions 0-10 (use decimals when uncertain):
- hook_score: how strong and gripping the first few seconds are
- curiosity_score: how much it triggers a curiosity gap
- emotional_score: emotional impact (humor, inspiration, anger, awe, empathy)
- standalone_score: makes sense without watching the full video
- story_score: has a clear narrative shape, payoff or punchline
- retention_score: keeps a viewer watching to the end
- shareability_score: a viewer would WANT to share this

Rules:
- Only use the provided transcript. NEVER invent content, speakers, or facts.
- Prefer complete standalone thoughts with strong openings and natural endings.
- Penalize clips that start mid-sentence, end abruptly, contain long silences, greetings, sponsor talk, or context-dependent statements.
- You may micro-adjust the start/end timestamps, but ONLY within the candidate's existing [start,end] window and only to land on clean sentence boundaries. Return recommended_start/recommended_end as seconds with up to 1 decimal.
- title: compelling short title (max 8 words).
- hook: the single best opening line text (verbatim from the transcript).
- reason: one sentence, why this clip would perform (max 25 words).
- viral_score: 0-100 overall estimate.

Respond ONLY with a single valid JSON array of objects. No markdown, no commentary. Object fields:
candidate_id, viral_score, hook_score, curiosity_score, emotional_score, standalone_score, story_score, retention_score, shareability_score, title, hook, reason, recommended_start, recommended_end"""


def _candidate_payload(c: ClipCandidate) -> dict:
    return {
        "candidate_id": c.candidate_id,
        "start": round(c.start, 1),
        "end": round(c.end, 1),
        "duration": round(c.duration, 1),
        "transcript": c.transcript,
    }


def build_batch_analysis_prompt(
    candidates: list[ClipCandidate],
    min_duration: float = 20.0,
    max_duration: float = 60.0,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a batch of candidates."""
    payload = {
        "instructions": (
            f"Analyze the {len(candidates)} candidate moments below. "
            f"Preferred clip duration {min_duration:.0f}-{max_duration:.0f} seconds. "
            "Return exactly one JSON array entry per candidate_id."
        ),
        "candidates": [_candidate_payload(c) for c in candidates],
    }
    user_prompt = json.dumps(payload, ensure_ascii=False)
    return SYSTEM_PROMPT, user_prompt


def build_single_analysis_prompt(
    candidate: ClipCandidate,
    min_duration: float = 20.0,
    max_duration: float = 60.0,
) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for a single candidate."""
    return build_batch_analysis_prompt([candidate], min_duration, max_duration)