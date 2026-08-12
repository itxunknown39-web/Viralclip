"""Centralized configuration loaded from environment variables.

Priority: environment variables -> application config -> hard defaults.
Secrets (OPENROUTER_API_KEY, cookies) are never exposed to the frontend.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def is_cuda_available() -> bool:
    """Detect CUDA without importing torch (faster-whisper uses CTranslate2)."""
    try:
        import ctranslate2

        return ctranslate2.get_cuda_device_count() > 0
    except Exception:
        try:
            import torch

            return bool(torch.cuda.is_available())
        except Exception:
            return False


@dataclass
class Settings:
    # --- OpenRouter ---
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/auto"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_timeout: float = 120.0
    openrouter_max_retries: int = 3
    openrouter_batch_size: int = 8

    # --- Whisper ---
    whisper_model: str = "medium"
    whisper_device: str = "auto"          # auto | cuda | cpu
    whisper_compute_type: str = "auto"    # auto | float16 | int8
    whisper_vad: bool = True

    # --- Clip defaults ---
    default_clip_count: int = 5
    min_clip_duration: float = 20.0
    max_clip_duration: float = 60.0
    default_aspect_ratio: str = "9:16"
    default_caption_style: str = "hormozi_green"

    # --- Rendering ---
    output_dir: str = ""

    # --- Cookies ---
    cookies_file: str = ""

    # --- Versions ---
    prompt_version: str = "1.0"
    scoring_version: str = "1.0"

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    def resolve(self) -> "Settings":
        """Resolve 'auto' values deterministically from the environment."""
        if self.whisper_device == "auto":
            self.whisper_device = "cuda" if is_cuda_available() else "cpu"
        if self.whisper_compute_type == "auto":
            self.whisper_compute_type = (
                "float16" if self.whisper_device == "cuda" else "int8"
            )
        if not self.output_dir:
            self.output_dir = "workspace/clips"
        return self

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
            openrouter_model=os.environ.get("OPENROUTER_MODEL", "openrouter/auto"),
            openrouter_base_url=os.environ.get(
                "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
            ),
            openrouter_timeout=_env_float("OPENROUTER_TIMEOUT", 120.0),
            openrouter_max_retries=_env_int("OPENROUTER_MAX_RETRIES", 3),
            openrouter_batch_size=_env_int("OPENROUTER_BATCH_SIZE", 8),
            whisper_model=os.environ.get("WHISPER_MODEL", "medium"),
            whisper_device=os.environ.get("WHISPER_DEVICE", "auto"),
            whisper_compute_type=os.environ.get("WHISPER_COMPUTE_TYPE", "auto"),
            whisper_vad=os.environ.get("WHISPER_VAD", "1") not in ("0", "false", "False"),
            default_clip_count=_env_int("MAX_CLIPS", 5),
            min_clip_duration=_env_float("MIN_CLIP_DURATION", 20.0),
            max_clip_duration=_env_float("MAX_CLIP_DURATION", 60.0),
            default_aspect_ratio=os.environ.get("DEFAULT_ASPECT_RATIO", "9:16"),
            default_caption_style=os.environ.get(
                "DEFAULT_CAPTION_STYLE", "hormozi_green"
            ),
            output_dir=os.environ.get("OUTPUT_DIR", ""),
            cookies_file=os.environ.get("VIRALCUT_COOKIES_FILE", ""),
            prompt_version=os.environ.get("PROMPT_VERSION", "1.0"),
            scoring_version=os.environ.get("SCORING_VERSION", "1.0"),
            host=os.environ.get("HOST", "0.0.0.0"),
            port=_env_int("PORT", 8000),
        )


settings = Settings.from_env().resolve()