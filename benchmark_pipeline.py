"""ViralCut AI — pipeline benchmark.

Usage:
    python benchmark_pipeline.py --url "<youtube url>" [--clip-count 5] [--min-duration 20] [--max-duration 60]

Measures download, audio extraction, transcription, candidate generation,
AI analysis and (optionally) rendering time, plus peak RAM.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import tracemalloc
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.downloader import download_video
from app.transcriber import extract_audio, transcribe
from app.analysis.candidates import generate_candidates
from app.analysis.deduplication import deduplicate
from app.ai.openrouter import OpenRouterClient
from app.jobs import _rank_results, manager
from app.history import save_project_record
from app.paths import TEMP_DIR


def bench(url: str, clip_count: int = 5, min_duration: float = 20, max_duration: float = 60) -> dict:
    job = manager.create("analysis")
    job.data["clip_count"] = clip_count
    job.data["min_duration"] = min_duration
    job.data["max_duration"] = max_duration
    job.data["created_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    metrics: dict[str, float] = {}
    tracemalloc.start()

    t0 = time.time()
    source, path = download_video(url, TEMP_DIR / job.job_id)
    metrics["download_seconds"] = round(time.time() - t0, 2)

    t0 = time.time()
    audio = extract_audio(path, TEMP_DIR / job.job_id)
    metrics["audio_extraction_seconds"] = round(time.time() - t0, 2)

    t0 = time.time()
    transcript = transcribe(audio)
    metrics["transcription_seconds"] = round(time.time() - t0, 2)

    t0 = time.time()
    candidates = generate_candidates(transcript, min_duration, max_duration)
    candidates = deduplicate(candidates)
    metrics["candidate_seconds"] = round(time.time() - t0, 2)
    metrics["candidate_count"] = len(candidates)

    t0 = time.time()
    client = OpenRouterClient()
    ai_results = client.analyze_candidates(candidates, min_duration, max_duration)
    metrics["ai_seconds"] = round(time.time() - t0, 2)

    t0 = time.time()
    ranked = _rank_results(ai_results, transcript, min_duration, max_duration, clip_count)
    metrics["ranking_seconds"] = round(time.time() - t0, 2)
    metrics["result_count"] = len(ranked)

    job.data["results"] = [r.model_dump() for r in ranked]
    job.data["transcript"] = transcript.model_dump()
    save_project_record(job)

    _, peak = tracemalloc.get_traced_memory()
    metrics["peak_ram_mb"] = round(peak / 1024 / 1024, 1)
    tracemalloc.stop()

    metrics["total_seconds"] = round(sum(
        metrics[k] for k in (
            "download_seconds", "audio_extraction_seconds", "transcription_seconds",
            "candidate_seconds", "ai_seconds", "ranking_seconds",
        )
    ), 2)
    metrics["video_duration"] = round(transcript.duration, 1)

    report = {
        "timestamp": datetime.now().isoformat(),
        "url": url,
        "settings": {
            "whisper_model": settings.whisper_model,
            "whisper_device": settings.whisper_device,
            "whisper_compute_type": settings.whisper_compute_type,
            "openrouter_model": settings.openrouter_model,
        },
        "metrics": metrics,
        "best_scores": [r["viral_score"] for r in job.data["results"][:5]],
    }

    out_dir = Path("benchmarks")
    out_dir.mkdir(exist_ok=True)
    fname = out_dir / f"bench_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    fname.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"\nSaved to {fname}")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="ViralCut AI pipeline benchmark")
    parser.add_argument("--url", required=True, help="YouTube or video URL")
    parser.add_argument("--clip-count", type=int, default=5)
    parser.add_argument("--min-duration", type=float, default=20.0)
    parser.add_argument("--max-duration", type=float, default=60.0)
    args = parser.parse_args()
    try:
        bench(args.url, args.clip_count, args.min_duration, args.max_duration)
    except KeyboardInterrupt:
        print("Benchmark interrupted.")
        sys.exit(1)


if __name__ == "__main__":
    main()