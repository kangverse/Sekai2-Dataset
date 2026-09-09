#!/usr/bin/env python3
"""Extract the pose/caption pair for one clip from a release tar shard."""

from __future__ import annotations

import argparse
import csv
import shutil
import tarfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--clip-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    matches = []
    with args.manifest.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["clip_id"] == args.clip_id:
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(f"expected one row for {args.clip_id!r}, got {len(matches)}")
    row = matches[0]
    shard = args.repo_root / row["annotation_shard"]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tarfile.open(shard, "r") as archive:
        for column in ("pose_path", "caption_path"):
            member_name = row[column].split("::", 1)[1]
            source = archive.extractfile(member_name)
            if source is None:
                raise RuntimeError(f"missing {member_name!r} in {shard}")
            destination = args.output_dir / Path(member_name).name
            with destination.open("wb") as handle:
                shutil.copyfileobj(source, handle)
            print(destination)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
