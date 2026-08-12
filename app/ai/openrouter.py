"""OpenRouter API client — authentication, retries, validation, error normalization."""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Callable, Optional

import requests

from ..config import settings
from ..models import AIClipAnalysis, ClipCandidate
from ..ai.prompts import build_batch_analysis_prompt
from ..ai.schemas import validate_ai_result

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]

_JSON_FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.DOTALL)


class OpenRouterError(Exception):
    """Normalized OpenRouter failure with a machine-readable code."""

    CODES = (
        "AI_AUTH_ERROR",
        "AI_RATE_LIMIT",
        "AI_TIMEOUT",
        "AI_INVALID_RESPONSE",
        "AI_PROVIDER_ERROR",
        "AI_ERROR",
    )

    def __init__(self, message: str, code: str = "AI_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code if code in self.CODES else "AI_ERROR"


def _extract_json(content: str):
    """Extract a JSON array/object from an LLM response, tolerating fenced blocks."""
    if not content:
        raise OpenRouterError("Empty AI response.", "AI_INVALID_RESPONSE")
    fenced = _JSON_FENCE.search(content)
    if fenced:
        content = fenced.group(1)
    content = content.strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end > start:
            try:
                return json.loads(content[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise OpenRouterError(
            "AI returned malformed JSON.", "AI_INVALID_RESPONSE"
        )


class OpenRouterClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        batch_size: Optional[int] = None,
    ):
        self.api_key = api_key if api_key is not None else settings.openrouter_api_key
        self.model = model if model is not None else settings.openrouter_model
        self.base_url = base_url if base_url is not None else settings.openrouter_base_url
        self.timeout = timeout if timeout is not None else settings.openrouter_timeout
        self.max_retries = (
            max_retries if max_retries is not None else settings.openrouter_max_retries
        )
        self.batch_size = (
            batch_size if batch_size is not None else settings.openrouter_batch_size
        )

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(self, system: str, user: str, max_tokens: int = 4096) -> dict:
        """Single chat completion request with retry + backoff."""
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }
        last_exc: Optional[Exception] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                resp = requests.post(
                    url,
                    headers=self._headers(),
                    json=payload,
                    timeout=self.timeout,
                )
            except requests.exceptions.Timeout:
                last_exc = OpenRouterError(
                    "AI analysis timed out. Please retry.", "AI_TIMEOUT"
                )
            except requests.exceptions.RequestException as exc:
                last_exc = OpenRouterError(
                    f"Could not reach the AI provider: {exc}", "AI_ERROR"
                )
            else:
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                        return data["choices"][0]["message"]["content"]
                    except (KeyError, IndexError, ValueError):
                        raise OpenRouterError(
                            "AI provider returned an unexpected response.",
                            "AI_INVALID_RESPONSE",
                        )
                if resp.status_code == 401 or resp.status_code == 403:
                    raise OpenRouterError(
                        "Invalid OpenRouter API key. Check Settings.",
                        "AI_AUTH_ERROR",
                    )
                if resp.status_code == 429:
                    last_exc = OpenRouterError(
                        "AI analysis is temporarily rate-limited.", "AI_RATE_LIMIT"
                    )
                elif resp.status_code == 402:
                    raise OpenRouterError(
                        "Insufficient OpenRouter credits.", "AI_AUTH_ERROR"
                    )
                elif resp.status_code >= 500:
                    last_exc = OpenRouterError(
                        "The AI provider is temporarily unavailable.", "AI_PROVIDER_ERROR"
                    )
                else:
                    last_exc = OpenRouterError(
                        f"AI provider error (HTTP {resp.status_code}).", "AI_ERROR"
                    )
            if attempt <= self.max_retries:
                backoff = 2 ** attempt
                logger.warning("OpenRouter attempt %d failed, retrying in %ds", attempt, backoff)
                time.sleep(backoff)

        raise last_exc or OpenRouterError("AI analysis failed.", "AI_ERROR")

    def analyze_batch(
        self,
        candidates: list[ClipCandidate],
        min_duration: float,
        max_duration: float,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> list[AIClipAnalysis]:
        """Analyze candidates in batches. Invalid AI results are dropped."""
        if not self.api_key:
            raise OpenRouterError(
                "OpenRouter API key is not configured. Add it in Settings.",
                "AI_AUTH_ERROR",
            )
        if not candidates:
            return []

        results: list[AIClipAnalysis] = []
        total = len(candidates)
        done = 0
        for i in range(0, total, self.batch_size):
            batch = candidates[i : i + self.batch_size]
            system, user = build_batch_analysis_prompt(
                batch, min_duration, max_duration
            )
            content = self.chat(system, user)
            raw = _extract_json(content)
            items = raw if isinstance(raw, list) else raw.get("results", raw.get("analyses", []))
            for item in items:
                parsed = validate_ai_result(item)
                if parsed:
                    results.append(parsed)
                else:
                    logger.warning("Dropped invalid AI result: %s", str(item)[:200])
            done += len(batch)
            if progress_cb:
                progress_cb(done / total * 100, f"AI analyzing {done}/{total} moments...")
        return results

    def analyze_candidates(
        self,
        candidates: list[ClipCandidate],
        min_duration: float = 20.0,
        max_duration: float = 60.0,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> list[AIClipAnalysis]:
        return self.analyze_batch(
            candidates, min_duration, max_duration, progress_cb
        )