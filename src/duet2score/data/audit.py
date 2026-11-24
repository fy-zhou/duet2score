"""Audit audio/video metadata in an inventory JSON (no media decoding, no alignment)."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def duration(asset: dict | None) -> float | None:
    if not asset:
        return None
    probe = asset.get("probe")
    if not isinstance(probe, dict):
        return None
    try:
        value = float(probe.get("format", {}).get("duration", ""))
        return value if 0 < value < 10**7 else None
    except (ValueError, TypeError, AttributeError):
        return None


def media_audit(inventory: dict, threshold_sec: float = 5.0) -> list[dict]:
    if threshold_sec < 0:
        raise ValueError("threshold_sec must be nonnegative")
    rows = []
    for piece in inventory.get("pieces", []):
        videos = [a for a in piece["assets"] if a["kind"] == "video"]
        audios = [a for a in piece["assets"] if a["kind"] == "audio"]
        scores = [a for a in piece["assets"] if a["kind"] == "score"]
        video = videos[0] if len(videos) == 1 else None
        audio = audios[0] if len(audios) == 1 else None
        dv, da = duration(video), duration(audio)
        delta = round(dv - da, 3) if dv is not None and da is not None else None
        flags = list(piece.get("issues", []))
        if video is not None and dv is None:
            flags.append("video_metadata_unavailable")
        if audio is not None and da is None:
            flags.append("audio_metadata_unavailable")
        if delta is not None and abs(delta) > threshold_sec:
            flags.append("duration_difference_review")
        rows.append({
            "piece_id": piece["piece_id"],
            "video": video["path"] if video else "",
            "audio": audio["path"] if audio else "",
            "score": scores[0]["path"] if len(scores) == 1 else "",
            "video_sec": round(dv, 3) if dv is not None else None,
            "audio_sec": round(da, 3) if da is not None else None,
            "video_minus_audio_sec": delta,
            "flags": "|".join(dict.fromkeys(flags)),
        })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Check duration discrepancies in dataset inventory.")
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("data/manifests/media-audit.csv"))
    parser.add_argument("--threshold-sec", type=float, default=5.0)
    args = parser.parse_args()
    manifest = json.loads(args.inventory.read_text(encoding="utf-8"))
    rows = media_audit(manifest, args.threshold_sec)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[
            "piece_id", "video", "audio", "score", "video_sec", "audio_sec",
            "video_minus_audio_sec", "flags"])
        w.writeheader()
        w.writerows(rows)
    print(f"Pieces: {len(rows)}")
    print(f"Review flags: {sum(bool(row['flags']) for row in rows)}")
    print(f"Missing duration metadata: {sum(row['video_sec'] is None or row['audio_sec'] is None for row in rows)}")
    print(f"Saved CSV: {args.out.resolve()}")
    print("Note: time differences do not verify audio alignment or indicate which section is an intro.")


if __name__ == "__main__":
    main()
