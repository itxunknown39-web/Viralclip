"""ASS caption generation from word-level transcript with style presets."""
from __future__ import annotations

from .models import Transcript, Word

CHUNK_WORDS = 3  # words per caption group

PRESETS: dict[str, dict] = {
    "bold_white": {
        "font": "Arial",
        "size": 78,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline": 4,
        "bold": -1,
        "italic": 0,
    },
    "hormozi_green": {
        "font": "Arial",
        "size": 86,
        "primary": "&H0000FF00",
        "outline_color": "&H00141414",
        "outline": 4,
        "bold": -1,
        "italic": 0,
    },
    "hormozi_yellow": {
        "font": "Arial",
        "size": 86,
        "primary": "&H0000FFFF",
        "outline_color": "&H00141414",
        "outline": 4,
        "bold": -1,
        "italic": 0,
    },
    "beast_pop": {
        "font": "Impact",
        "size": 96,
        "primary": "&H0000FFFF",
        "outline_color": "&H00000000",
        "outline": 5,
        "bold": -1,
        "italic": -1,
    },
    "one_word_punch": {
        "font": "Arial",
        "size": 96,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline": 5,
        "bold": -1,
        "italic": 0,
    },
    "word_reveal": {
        "font": "Arial",
        "size": 84,
        "primary": "&H000000FF",
        "outline_color": "&H00000000",
        "outline": 3,
        "bold": -1,
        "italic": 0,
    },
    "boxed_tiktok": {
        "font": "Arial",
        "size": 76,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00141414",
        "outline": 2,
        "back_color": "&HAA000000",
        "bold": -1,
        "italic": 0,
    },
    "comic_punch": {
        "font": "Impact",
        "size": 76,
        "primary": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "outline": 5,
        "bold": -1,
        "italic": -1,
    },
    "serif_elegant": {
        "font": "Georgia",
        "size": 68,
        "primary": "&H00F0E6D2",
        "outline_color": "&H003B2A14",
        "outline": 3,
        "bold": 0,
        "italic": -1,
    },
}

STYLES_AVAILABLE = sorted(PRESETS.keys())


def _ts(seconds: float) -> str:
    """ASS time format H:MM:SS.cc"""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int(round((seconds - int(seconds)) * 100))
    if cs == 100:
        s += 1
        cs = 0
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _escape(text: str) -> str:
    return text.replace("{", "(").replace("}", ")").replace("\\", "/")


def _words_in(transcript: Transcript, start: float, end: float) -> list[Word]:
    return [w for w in transcript.all_words() if start <= w.start <= end]


def _base_ass(width: int = 1080, height: int = 1920) -> str:
    return (
        "[Script Info]\n"
        "ScriptType: v4.00+\n"
        "PlayResX: {w}\n"
        "PlayResY: {h}\n"
        "ScaledBorderAndShadow: yes\n"
        "WrapStyle: 0\n\n"
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        "{style_line}\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, "
        "Effect, Text\n"
    ).format(
        w=width,
        h=height,
        style_line="{style}",  # placeholder replaced below
    )


def build_ass(
    transcript: Transcript,
    start: float,
    end: float,
    style: str = "hormozi_green",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Build an ASS subtitle script for [start, end]."""
    preset = PRESETS.get(style, PRESETS["hormozi_green"])
    primary = preset.get("primary", "&H00FFFFFF")
    outline_color = preset.get("outline_color", "&H00000000")
    back_color = preset.get("back_color", "&H80000000")
    outline = preset.get("outline", 4)
    margin_v = int(height * 0.72)

    style_line = (
        f"Style: Cap,{preset['font']},{preset['size']},"
        f"{primary},{primary},{outline_color},{back_color},"
        f"{preset['bold']},0,0,0,100,100,0,0,1,{outline},1,"
        f"2,90,90,{margin_v},1"
    )

    header = _base_ass(width, height).replace("{style}", style_line)
    lines = [header]

    words = _words_in(transcript, start, end)
    for i in range(0, len(words), CHUNK_WORDS):
        chunk = words[i : i + CHUNK_WORDS]
        if not chunk:
            continue
        c_start = chunk[0].start
        c_end = chunk[-1].end
        text = _escape(" ".join(w.text for w in chunk))
        lines.append(
            f"Dialogue: 0,{_ts(c_start)},{_ts(c_end)},Cap,,0,0,0,,{text}"
        )
    return "\n".join(lines)