"""Extract original audio from a video into lossless PCM WAV with ffmpeg."""
from __future__ import annotations
import argparse
import shutil
import subprocess
from pathlib import Path

def extract_audio(video: Path, output: Path, overwrite: bool = False) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is required (sudo apt install ffmpeg)")
    if not video.is_file():
        raise FileNotFoundError(video)
    if output.exists() and not overwrite:
        raise FileExistsError(f"{output} already exists; pass --overwrite")
    output.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y" if overwrite else "-n",
                    "-i", str(video), "-vn", "-c:a", "pcm_s16le", str(output)], check=True)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("video", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    extract_audio(args.video, args.output, overwrite=args.overwrite)
    print(f"Audio saved: {args.output}")

if __name__ == "__main__":
    main()
