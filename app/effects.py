"""Optional clip effects — subtle zoom pulse via FFmpeg zoompan."""
from __future__ import annotations

from typing import Optional

EFFECTS_AVAILABLE = ("zoom", "none")


def zoom_filter(width: int, height: int, factor: float = 1.06) -> Optional[str]:
    """Return a zoompan filter string for a subtle slow zoom, or None."""
    if factor <= 1.0:
        return None
    return (
        f"zoompan=z='min(zoom+0.0006,{factor})':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d=1:s={width}x{height}:fps=30"
    )


def build_filter(
    width: int,
    height: int,
    aspect_ratio: str,
    effects: bool,
    has_captions: bool,
    caption_ass: Optional[str] = None,
    fps: float = 30.0,
) -> Optional[str]:
    """Compose the ffmpeg -vf chain for a clip render. Returns None if none needed."""
    parts: list[str] = []

    if aspect_ratio == "9:16":
        # crop center region to 9:16, then scale to target
        parts.append("crop=min(iw,ih*9/16):ih")
        parts.append(f"scale={width}:{height}")
    elif aspect_ratio == "16:9":
        parts.append("crop=iw:min(ih,iw*9/16)")
        parts.append(f"scale={width}:{height}")
    elif aspect_ratio == "1:1":
        parts.append("crop=min(iw,ih):min(iw,ih)")
        parts.append(f"scale={width}:{height}")

    if effects:
        zoom = zoom_filter(width, height)
        if zoom:
            parts.append(zoom)

    if has_captions and caption_ass:
        parts.append(f"ass={_escape_path(caption_ass)}")

    return ",".join(parts) if parts else None


def _escape_path(p: str) -> str:
    return p.replace("\\", "/").replace(":", "\\:")