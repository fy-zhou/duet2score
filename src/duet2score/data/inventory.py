"""Inventory local piece directories without modifying recordings or scores."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import Counter
from pathlib import Path

EXTENSIONS = {
    "video": {".mp4", ".mkv", ".mov", ".avi", ".webm"},
    "audio": {".wav", ".flac", ".mp3", ".m4a", ".aiff", ".ogg"},
    "score": {".pdf", ".musicxml", ".mxl", ".mscz", ".mid", ".midi", ".xml", ".png", ".jpg", ".jpeg"},
}

def classify(path: Path) -> str | None:
    suffix = path.suffix.lower()
    for kind, suffixes in EXTENSIONS.items():
        if suffix in suffixes:
            return kind
    return None

def ffprobe_metadata(path: Path) -> dict:
    """Optional metadata, not required for initial dataset inventory."""
    if not shutil.which("ffprobe"):
        return {"error": "ffprobe not found"}
    cmd = ["ffprobe", "-v", "error", "-show_entries",
           "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate",
           "-of", "json", str(path)]
    try:
        run = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=True)
        return json.loads(run.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        return {"error": str(exc)}

def scan_dataset(root: Path, probe: bool = False) -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"dataset directory does not exist: {root}")
    pieces = []
    counts: Counter[str] = Counter()
    for folder in sorted((p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")), key=lambda p: p.name):
        assets = []
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.is_symlink() or any(part.startswith(".") for part in path.relative_to(folder).parts):
                continue
            kind = classify(path)
            if kind is None:
                continue
            item = {
                "kind": kind,
                "path": path.relative_to(root).as_posix(),
                "extension": path.suffix.lower(),
                "bytes": path.stat().st_size,
            }
            if probe and kind in ("audio", "video"):
                item["probe"] = ffprobe_metadata(path)
            assets.append(item)
            counts[kind] += 1
        pieces.append({
            "piece_id": folder.name,
            "assets": assets,
            "has_video": any(x["kind"] == "video" for x in assets),
            "has_audio": any(x["kind"] == "audio" for x in assets),
            "has_score": any(x["kind"] == "score" for x in assets),
            "needs_review": not(any(x["kind"] == "score" for x in assets)
                                and any(x["kind"] in ("audio", "video") for x in assets)),
        })
    return {
        "schema_version": "0.1",
        "root": str(root),
        "summary": {"pieces": len(pieces), **{k: counts[k] for k in ("video", "audio", "score")}},
        "pieces": pieces,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory raw Duet2Score files by piece.")
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/manifests/inventory.json"))
    parser.add_argument("--probe", action="store_true", help="Attach optional ffprobe metadata (requires ffprobe).")
    args = parser.parse_args()
    result = scan_dataset(args.root, probe=args.probe)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    print(f"Written: {args.out.resolve()}")

if __name__ == "__main__":
    main()
