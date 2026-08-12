"""Video downloading and metadata retrieval with yt-dlp."""
from __future__ import annotations

import hashlib
import logging
import re
import shutil
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

from .config import settings
from .models import VideoSource

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[float, str], None]

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str, fallback: str = "video") -> str:
    clean = _SAFE_NAME.sub("_", name).strip("._")
    return clean[:120] or fallback


def _base_opts(cookies_file: Optional[str] = None) -> dict:
    opts: dict = {
        "format": (
            "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/"
            "best[height<=1080][ext=mp4]/best"
        ),
        "merge_output_format": "mp4",
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "retries": 3,
    }
    cookies = cookies_file or settings.cookies_file
    if cookies and Path(cookies).exists():
        opts["cookiefile"] = str(cookies)
    return opts


class DownloadError(Exception):
    """Human-readable download failure."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def fetch_metadata(url: str) -> dict:
    """Fetch video metadata without downloading. Returns raw yt-dlp info dict."""
    try:
        with yt_dlp.YoutubeDL(_base_opts()) as ydl:
            return ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_download_error(exc)) from exc


def _friendly_download_error(exc: Exception) -> str:
    msg = str(exc).lower()
    if "private" in msg or "members-only" in msg:
        return "This video is private or members-only. We couldn't access it."
    if "age" in msg or "age-restricted" in msg:
        return "This video is age-restricted and couldn't be accessed."
    if "sign in" in msg or "login" in msg or "bot" in msg:
        return (
            "YouTube requires verification for this video. "
            "Add a cookies file in Settings and try again."
        )
    if "unsupported url" in msg or "not a valid" in msg:
        return "This URL is not a supported video link."
    if "no video" in msg or "unavailable" in msg:
        return "This video is unavailable or doesn't exist."
    return f"We couldn't access this video. {msg[:200]}"


def build_source(info: dict, url: str, local_path: Optional[Path] = None) -> VideoSource:
    source_id = hashlib.sha1((url or str(local_path)).encode()).hexdigest()[:16]
    return VideoSource(
        source_id=source_id,
        url=url,
        local_path=str(local_path) if local_path else None,
        title=info.get("title"),
        duration=float(info.get("duration") or 0.0),
        width=info.get("width"),
        height=info.get("height"),
        fps=info.get("fps"),
        thumbnail=info.get("thumbnail"),
        channel=info.get("channel") or info.get("uploader"),
    )


def download_video(
    url: str,
    dest_dir: Path,
    cookies_file: Optional[str] = None,
    progress_cb: Optional[ProgressCallback] = None,
) -> tuple[VideoSource, Path]:
    """Download a video to dest_dir and return (source, local path)."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    def hook(d: dict) -> None:
        if progress_cb is None:
            return
        status = d.get("status")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes") or 0
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            pct = (downloaded / total * 100) if total else 0
            speed = d.get("_speed_str") or ""
            progress_cb(pct, f"Downloading video... {speed}".strip())
        elif status == "finished":
            progress_cb(100, "Download finished, merging streams...")

    opts = _base_opts(cookies_file)
    opts["outtmpl"] = str(dest_dir / "%(id)s.%(ext)s")
    opts["progress_hooks"] = [hook]

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        # yt-dlp may produce multiple files (e.g. .webm+). Find the final mp4.
        candidates = sorted(dest_dir.glob(f"{info.get('id')}.*"))
        final = None
        for c in candidates:
            if c.suffix.lower() == ".mp4":
                final = c
                break
        if final is None and candidates:
            final = candidates[-1]
        if final is None:
            raise DownloadError("The video downloaded but no usable file was found.")
    except yt_dlp.utils.DownloadError as exc:
        raise DownloadError(_friendly_download_error(exc)) from exc

    return build_source(info, url, final), final