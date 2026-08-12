"""FFmpeg clip rendering — trim, reframe, captions, effects, NVENC."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from .captions import build_ass
from .effects import build_filter
from .models import Transcript

ProgressCallback = Callable[[float, str], None]

_TIME_RE = re.compile(r"time=(\d+):(\d+):(\d+(?:\.\d+)?)")


def find_ffmpeg() -> str:
    p = shutil.which("ffmpeg")
    if not p:
        raise RuntimeError(
            "FFmpeg is not installed. Install FFmpeg and add it to PATH, or "
            "the app will run in CPU fallback mode without it."
        )
    return p


def detect_nvenc() -> bool:
    """Return True if the local FFmpeg build supports h264_nvenc."""
    try:
        proc = subprocess.run(
            [find_ffmpeg(), "-hide_banner", "-encoders"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return "h264_nvenc" in proc.stdout
    except Exception:
        return False


def detect_cpu_fallback_ok() -> bool:
    try:
        find_ffmpeg()
        return True
    except Exception:
        return False


def render_clip(
    source_path: Path,
    start: float,
    end: float,
    transcript: Optional[Transcript],
    output_path: Path,
    aspect_ratio: str = "9:16",
    width: int = 1080,
    height: int = 1920,
    caption_style: str = "hormozi_green",
    captions: bool = True,
    effects_enabled: bool = False,
    progress_cb: Optional[ProgressCallback] = None,
) -> Path:
    """Render a clip from source. Returns output path."""
    ffmpeg = find_ffmpeg()
    duration = max(end - start, 0.5)

    ass_path: Optional[Path] = None
    caption_ass: Optional[str] = None
    if captions and transcript is not None and transcript.all_words():
        ass_path = output_path.with_suffix(".ass")
        caption_ass = build_ass(transcript, start, end, style=caption_style)
        ass_path.write_text(caption_ass, encoding="utf-8")

    vf = build_filter(
        width,
        height,
        aspect_ratio,
        effects_enabled,
        bool(caption_ass),
        caption_ass,
    )

    encoder = "h264_nvenc" if detect_nvenc() else "libx264"
    cmd = [
        ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-stats",
        "-ss", f"{start:.2f}",
        "-i", str(source_path),
        "-t", f"{duration:.2f}",
    ]
    if vf:
        cmd += ["-vf", vf]
    cmd += ["-c:v", encoder]
    if encoder == "libx264":
        cmd += ["-preset", "medium", "-crf", "20"]
    else:
        cmd += ["-preset", "p4", "-rc", "vbr", "-cq", "23"]
    cmd += ["-c:a", "aac", "-b:a", "160k", "-ar", "48000"]
    cmd += ["-movflags", "+faststart", str(output_path)]

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    assert proc.stderr is not None
    last_pct = 0.0
    for line in proc.stderr:
        m = _TIME_RE.search(line)
        if m and duration > 0:
            hh, mm, ss = int(m.group(1)), int(m.group(2)), float(m.group(3))
            elapsed = hh * 3600 + mm * 60 + ss
            pct = min(max(elapsed / duration * 100, last_pct), 99)
            last_pct = pct
            if progress_cb:
                progress_cb(pct, f"Rendering clip… {int(pct)}%")
    returncode = proc.wait()
    if returncode != 0 or not output_path.exists():
        raise RuntimeError("FFmpeg failed to render the clip. Try again or check logs.")
    if progress_cb:
        progress_cb(100, "Clip rendered")
    if ass_path and ass_path.exists():
        try:
            ass_path.unlink()
        except OSError:
            pass
    return output_path