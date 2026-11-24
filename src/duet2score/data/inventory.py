"""Inventory score/audio/video without altering raw data; supports type-grouped folders."""
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


import csv
import re
import unicodedata
from collections import defaultdict

TYPE_FOLDERS = {"音频", "音频文件", "audio", "audios", "视频", "视频文件", "video", "videos",
                "乐谱", "谱子", "曲谱", "scores", "score", "sheet", "sheets", "sheetmusic"}
NUMBER_PREFIX = re.compile(r"^\s*[（(]?\s*(\d{1,4})(?:\s*[.．、:：_\-）)\]]\s*|\s+|$)")

def match_key(path: Path) -> tuple[str, str]:
    """Conservative candidate pairing; never claims musical identity verification."""
    stem = unicodedata.normalize("NFKC", path.stem).strip()
    match = NUMBER_PREFIX.match(stem)
    if match:
        return f"number:{int(match.group(1)):04d}", "numeric_prefix"
    title = "".join(c for c in stem.casefold() if c.isalnum())
    if title:
        return f"title:{title}", "exact_normalized_title"
    return f"unmatched:{stem}", "unmatched"

def _valid_files(root: Path):
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part.startswith(".") for part in path.relative_to(root).parts):
            continue
        kind = classify(path)
        if kind:
            yield path, kind

def _asset(root: Path, path: Path, kind: str, probe: bool) -> dict:
    item = {"kind": kind, "path": path.relative_to(root).as_posix(),
            "extension": path.suffix.lower(), "bytes": path.stat().st_size}
    if probe and kind in ("audio", "video"):
        item["probe"] = ffprobe_metadata(path)
    return item

def _build_piece(piece_id: str, assets: list[dict], method: str) -> dict:
    counts = Counter(asset["kind"] for asset in assets)
    issues = [f"missing_{kind}" for kind in ("video", "audio", "score") if not counts[kind]]
    issues += [f"multiple_{kind}" for kind in ("video", "audio", "score") if counts[kind] > 1]
    if method == "exact_normalized_title":
        issues.append("title_only_match_unverified")
    if method == "unmatched":
        issues.append("unmatched_filename")
    return {
        "piece_id": piece_id, "match_method": method, "pairing_verified": False,
        "assets": sorted(assets, key=lambda a: (a["kind"], a["path"])),
        "has_video": bool(counts["video"]), "has_audio": bool(counts["audio"]),
        "has_score": bool(counts["score"]), "needs_review": bool(issues), "issues": issues,
    }

def scan_dataset(root: Path, probe: bool = False, layout: str = "auto") -> dict:
    root = root.expanduser().resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"dataset directory does not exist: {root}")
    if layout not in ("auto", "grouped", "by_piece"):
        raise ValueError("layout must be auto, grouped or by_piece")
    if layout == "auto":
        direct_files = any(p.is_file() and classify(p) for p in root.iterdir())
        type_dirs = any(p.is_dir() and p.name.casefold() in TYPE_FOLDERS for p in root.iterdir())
        layout = "grouped" if direct_files or type_dirs else "by_piece"

    pieces = []
    counts: Counter[str] = Counter()
    if layout == "grouped":
        groups: dict[str, list[dict]] = defaultdict(list)
        methods: dict[str, str] = {}
        for path, kind in _valid_files(root):
            key, method = match_key(path)
            groups[key].append(_asset(root, path, kind, probe))
            methods[key] = method
            counts[kind] += 1
        for key in sorted(groups):
            pieces.append(_build_piece(key, groups[key], methods[key]))
    else:
        for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
            assets = []
            for path, kind in _valid_files(folder):
                assets.append(_asset(root, path, kind, probe))
                counts[kind] += 1
            if assets:
                pieces.append(_build_piece(folder.name, assets, "directory"))

    summary = {
        "pieces": len(pieces),
        **{kind: counts[kind] for kind in ("video", "audio", "score")},
        "complete_triplets": sum(
            all(sum(a["kind"] == kind for a in piece["assets"]) == 1
                for kind in ("video", "audio", "score")) for piece in pieces),
        "needs_review": sum(piece["needs_review"] for piece in pieces),
    }
    return {"schema_version": "0.2", "root": str(root), "layout": layout,
            "summary": summary, "pieces": pieces}

def write_csv(inventory: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(["piece_id", "match_method", "pairing_verified",
                         "video", "audio", "score", "issues"])
        for piece in inventory["pieces"]:
            by_kind = {
                kind: [item["path"] for item in piece["assets"] if item["kind"] == kind]
                for kind in ("video", "audio", "score")
            }
            writer.writerow([piece["piece_id"], piece["match_method"], piece["pairing_verified"],
                             *[" | ".join(by_kind[k]) for k in ("video", "audio", "score")],
                             " | ".join(piece["issues"])])

def main() -> None:
    parser = argparse.ArgumentParser(description="Inventory Duet2Score raw files.")
    parser.add_argument("--root", type=Path, default=Path("data/raw"))
    parser.add_argument("--out", type=Path, default=Path("data/manifests/inventory.json"))
    parser.add_argument("--csv", type=Path, help="Optional candidate-pairing CSV.")
    parser.add_argument("--layout", choices=("auto", "grouped", "by_piece"), default="auto")
    parser.add_argument("--probe", action="store_true", help="Optional ffprobe metadata.")
    args = parser.parse_args()
    result = scan_dataset(args.root, probe=args.probe, layout=args.layout)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.csv:
        write_csv(result, args.csv)
    print(json.dumps({"layout": result["layout"], **result["summary"]},
                     ensure_ascii=False, indent=2))
    print(f"Inventory: {args.out.resolve()}")
    if args.csv:
        print(f"Pairing table: {args.csv.resolve()}")

if __name__ == "__main__":
    main()
