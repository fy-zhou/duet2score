"""Read-only content audit: audio-track similarity, timing and basic media/PDF checks."""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

RATE = 8000


def run(cmd: list[str], timeout: int = 600) -> bytes:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if p.returncode:
        raise RuntimeError(p.stderr.decode(errors="replace")[-1000:] or f"exit {p.returncode}")
    return p.stdout


def decode_audio(path: Path, rate: int = RATE) -> np.ndarray:
    raw = run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(path),
               "-map", "0:a:0", "-vn", "-ac", "1", "-ar", str(rate),
               "-f", "f32le", "pipe:1"])
    x = np.frombuffer(raw, dtype="<f4")
    if not x.size or not np.isfinite(x).all():
        raise ValueError("empty or non-finite audio")
    return x


def best_match(template: np.ndarray, search: np.ndarray, rate: int) -> dict | None:
    """Normalized waveform cross-correlation for a template contained in search."""
    n = len(template)
    if n < rate or len(search) < n:
        return None
    t = template.astype(np.float64)
    t -= t.mean()
    energy = np.dot(t, t)
    if energy / n < 1e-9:
        return None
    s = search.astype(np.float64)
    size = 1 << (len(s) + n - 2).bit_length()
    corr = np.fft.irfft(np.fft.rfft(s, size) * np.fft.rfft(t[::-1], size), size)[n-1:len(s)]
    cs = np.r_[0., np.cumsum(s)]
    cs2 = np.r_[0., np.cumsum(s*s)]
    sums = cs[n:] - cs[:-n]
    variance = cs2[n:] - cs2[:-n] - sums*sums/n
    denom = np.sqrt(energy * np.maximum(variance, 1e-12))
    scores = np.where(variance / n > 1e-9, np.abs(corr) / denom, 0.)
    idx = int(np.argmax(scores))
    peak = float(np.clip(scores[idx], 0, 1))
    # Exclude neighbouring samples from the second-best comparison.
    guard = max(1, int(rate * .25))
    alternatives = np.r_[scores[:max(0, idx-guard)], scores[idx+guard+1:]]
    second = float(np.max(alternatives)) if len(alternatives) else 0.
    return {"start_sample": idx, "correlation": round(peak, 4),
            "peak_margin": round(peak - second, 4)}


def estimate_offset(audio: np.ndarray, video_audio: np.ndarray, rate: int = RATE,
                    max_shift_sec: float = 30., min_correlation: float = .55) -> dict:
    """Estimate video audio-track time minus external audio time; never trims media."""
    if rate <= 0 or max_shift_sec < 0 or not 0 <= min_correlation <= 1:
        raise ValueError("invalid synchronization settings")
    n = min(rate * 8, len(audio) // 4)
    if n < rate:
        return {"status": "review_short_audio", "offset_sec": None, "windows": []}
    shift = int(rate * max_shift_sec)
    windows = []
    for fraction in (.2, .5, .8):
        a = int((len(audio) - n) * fraction)
        lo = max(0, a - shift)
        hi = min(len(video_audio), a + shift + n)
        result = best_match(audio[a:a+n], video_audio[lo:hi], rate)
        if result is None:
            continue
        result["audio_start_sec"] = round(a / rate, 4)
        result["offset_sec"] = round((lo + result["start_sample"] - a) / rate, 4)
        result["accepted"] = (result["correlation"] >= min_correlation
                              and result["peak_margin"] >= .02)
        windows.append(result)
    good = [w["offset_sec"] for w in windows if w["accepted"]]
    if len(good) < 2:
        status, offset = "review_low_confidence", None
    elif max(good) - min(good) > .1:
        status, offset = "review_variable_offset", None
    else:
        status, offset = "candidate_match", round(float(np.median(good)), 4)
    return {"status": status, "offset_sec": offset, "windows": windows,
            "max_shift_sec": max_shift_sec, "min_correlation": min_correlation}


def local_path(root: Path, asset: dict) -> Path:
    path = (root / asset["path"]).resolve()
    if not path.is_relative_to(root):
        raise ValueError("asset outside dataset root")
    return path


def inspect_piece(piece: dict, root: Path, full_decode: bool, max_shift: float) -> dict:
    result = {"piece_id": piece["piece_id"], "flags": list(piece.get("issues", []))}
    assets = {}
    for kind in ("audio", "video", "score"):
        group = [a for a in piece["assets"] if a["kind"] == kind]
        if len(group) == 1:
            assets[kind] = local_path(root, group[0])
    tracks = {}
    for kind in ("audio", "video"):
        if kind in assets:
            try:
                tracks[kind] = decode_audio(assets[kind])
                result[kind + "_audio_sec"] = round(len(tracks[kind]) / RATE, 3)
            except Exception as exc:
                result["flags"].append(kind + "_audio_decode_failed")
                result[kind + "_error"] = str(exc)
    if "audio" in tracks and "video" in tracks:
        result["sync"] = estimate_offset(tracks["audio"], tracks["video"], max_shift_sec=max_shift)
        if result["sync"]["status"] != "candidate_match":
            result["flags"].append(result["sync"]["status"])
    if full_decode and "video" in assets:
        try:
            run(["ffmpeg", "-nostdin", "-v", "error", "-xerror", "-i", str(assets["video"]),
                 "-map", "0:v:0", "-an", "-f", "null", "-"])
            result["video_frames_decode"] = "pass"
        except Exception as exc:
            result["video_frames_decode"] = "fail"
            result["video_frames_error"] = str(exc)
            result["flags"].append("video_frames_decode_failed")
    else:
        result["video_frames_decode"] = "not_checked"
    if "score" in assets and assets["score"].suffix.lower() == ".pdf":
        if shutil.which("pdfinfo"):
            try:
                meta = run(["pdfinfo", str(assets["score"])], 30).decode(errors="replace")
                result["pdf_pages"] = next(int(line.split(":", 1)[1]) for line in meta.splitlines()
                                           if line.startswith("Pages:"))
                result["pdf_check"] = "metadata_readable"
            except Exception as exc:
                result["flags"].append("pdf_metadata_failed")
                result["pdf_error"] = str(exc)
        else:
            result["pdf_check"] = "not_checked_pdfinfo_missing"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--root", type=Path, help="Override inventory root")
    parser.add_argument("--out", type=Path, default=Path("data/manifests/content-audit.json"))
    parser.add_argument("--full-decode", action="store_true", help="Also decode every video frame")
    parser.add_argument("--max-shift-sec", type=float, default=30.)
    parser.add_argument("--limit", type=int, help="Inspect only the first N pieces for a smoke test")
    args = parser.parse_args()
    if not shutil.which("ffmpeg"):
        parser.error("ffmpeg is required")
    if args.max_shift_sec < 0 or (args.limit is not None and args.limit <= 0):
        parser.error("invalid shift or limit")
    inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
    root = (args.root or Path(inventory["root"])).expanduser().resolve()
    if not root.is_dir():
        parser.error("dataset root not found")
    rows = []
    for piece in inventory["pieces"][:args.limit]:
        try:
            row = inspect_piece(piece, root, args.full_decode, args.max_shift_sec)
        except Exception as exc:
            row = {"piece_id": piece["piece_id"], "flags": ["audit_failed"], "error": str(exc)}
        rows.append(row)
        print(row["piece_id"], row.get("sync", {}).get("status", "not_checked"),
              row.get("sync", {}).get("offset_sec"), "|".join(row["flags"]), flush=True)
    summary = {"pieces": len(rows), "candidate_matches": sum(r.get("sync", {}).get("status") == "candidate_match" for r in rows),
               "needs_review": sum(bool(r["flags"]) for r in rows),
               "full_decode": args.full_decode}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"summary": summary, "pieces": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with args.out.with_suffix(".csv").open("w", encoding="utf-8-sig", newline="") as f:
        fields = ["piece_id", "audio_audio_sec", "video_audio_sec", "sync_status", "offset_sec",
                  "video_frames_decode", "pdf_pages", "flags"]
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "sync_status": row.get("sync", {}).get("status"),
                             "offset_sec": row.get("sync", {}).get("offset_sec"),
                             "flags": "|".join(row["flags"])})
    print(json.dumps(summary, indent=2))
    print(f"Saved {args.out} and {args.out.with_suffix('.csv')}")
    print("Candidate synchronization is between decoded audio tracks only, not score alignment or visual timing.")

if __name__ == "__main__":
    main()
