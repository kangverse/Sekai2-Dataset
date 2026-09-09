#!/usr/bin/env python3
"""Download source videos and reconstruct annotation-aligned Sekai2 clips."""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path

DEFAULT_FORMAT = (
    "bestvideo[height<=720][fps<=30]+bestaudio/"
    "best[height<=720][fps<=30]"
)


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def read_rows(path: Path, clip_ids: set[str], dataset: str | None, limit: int | None):
    rows = []
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if dataset and row["dataset"] != dataset:
                continue
            if clip_ids and row["clip_id"] not in clip_ids:
                continue
            rows.append(row)
            if limit is not None and len(rows) >= limit:
                break
    if clip_ids:
        found = {row["clip_id"] for row in rows}
        missing = sorted(clip_ids - found)
        if missing:
            raise ValueError(f"clip_id not found: {missing}")
    return rows


def find_cached_source(cache_dir: Path, video_id: str) -> Path | None:
    candidates = [
        path
        for path in cache_dir.glob(video_id + ".*")
        if path.suffix not in {".json", ".part", ".ytdl"}
    ]
    return sorted(candidates)[0] if candidates else None


def download_source(
    row: dict[str, str], cache_dir: Path, yt_dlp: str, format_selector: str
) -> Path:
    existing = find_cached_source(cache_dir, row["video_id"])
    if existing:
        return existing
    template = str(cache_dir / (row["video_id"] + ".%(ext)s"))
    command = [
        yt_dlp,
        "--no-playlist",
        "--no-part",
        "--write-info-json",
        "--merge-output-format",
        "mkv",
        "-f",
        format_selector,
        "-o",
        template,
        row["url"],
    ]
    run(command)
    downloaded = find_cached_source(cache_dir, row["video_id"])
    if downloaded is None:
        raise RuntimeError(f"yt-dlp produced no media file for {row['video_id']}")
    return downloaded


def reconstruct_one(row: dict[str, str], source: Path, output: Path, ffmpeg: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    command = [
        ffmpeg,
        "-y",
        "-nostdin",
        "-loglevel",
        "error",
        "-i",
        str(source),
        # Output-side -ss is slower but frame accurate.  Do not move it before -i.
        "-ss",
        row["start_time"],
        "-t",
        row["duration"],
        "-map",
        "0:v:0",
        "-map",
        "0:a:0?",
        "-vf",
        (
            f"fps={row['fps']},"
            f"scale={row['frame_width']}:{row['frame_height']}:flags=lanczos"
        ),
        "-frames:v",
        row["num_frames"],
        "-fps_mode",
        "cfr",
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        str(output),
    ]
    run(command)


def probe_video(path: Path, ffprobe: str) -> dict[str, object]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_read_frames",
        "-of",
        "json",
        str(path),
    ]
    output = subprocess.run(command, check=True, capture_output=True, text=True).stdout
    return json.loads(output)["streams"][0]


def validate_encoded(row: dict[str, str], output: Path, ffprobe: str) -> None:
    stream = probe_video(output, ffprobe)
    numerator, denominator = map(int, stream["avg_frame_rate"].split("/"))
    fps = numerator / denominator
    expected = {
        "width": int(row["frame_width"]),
        "height": int(row["frame_height"]),
        "frames": int(row["num_frames"]),
    }
    actual = {
        "width": int(stream["width"]),
        "height": int(stream["height"]),
        "frames": int(stream["nb_read_frames"]),
    }
    if actual != expected or abs(fps - float(row["fps"])) > 1e-6:
        raise RuntimeError(
            f"encoded verification failed for {output}: expected={expected}, "
            f"actual={actual}, fps={fps}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--clip-id", action="append", default=[])
    parser.add_argument("--dataset", choices=("sekai", "sekai2"))
    parser.add_argument("--limit", type=int)
    parser.add_argument("--format", default=DEFAULT_FORMAT)
    parser.add_argument("--yt-dlp", default="yt-dlp")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument(
        "--remove-source",
        action="store_true",
        help="Delete each cached source after all selected clips are reconstructed.",
    )
    args = parser.parse_args()

    for executable in (args.yt_dlp, args.ffmpeg, args.ffprobe):
        if shutil.which(executable) is None:
            raise RuntimeError(f"required executable not found: {executable}")

    rows = read_rows(args.manifest, set(args.clip_id), args.dataset, args.limit)
    if not rows:
        raise RuntimeError("no perspective rows selected")
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["video_id"]].append(row)

    for video_rows in grouped.values():
        source = download_source(video_rows[0], args.cache_dir, args.yt_dlp, args.format)
        for row in video_rows:
            output = args.output_dir / row["dataset"] / row["clip_id"]
            reconstruct_one(row, source, output, args.ffmpeg)
            validate_encoded(row, output, args.ffprobe)
            print(f"OK {row['clip_id']} -> {output}")
        if args.remove_source:
            source.unlink()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
