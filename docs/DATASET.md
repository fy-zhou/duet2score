# Dataset contract (v0.2)

## Supported layouts

### Type-grouped Bella Lucas collection (current dataset)

```text
Bella Lucas/
  1.曲目名.pdf
  2.曲目名.pdf
  ...
  音频/
    1.曲目名.mp3
  视频/
    1.曲目名.mp4
```

The first inventory reported **49 MP4, 49 MP3, 50 PDF (148 files, ~1.3 GB)**. These are user-reported counts, **not validated 49-way pairs**. The extra PDF must be inspected; matches are provisional even when there are exactly one of each type.

### Per-piece subdirectories (alternative)

```text
data/raw/
  piece_001/
    performance.mp4
    score.pdf
    performance.wav
```

## First inventory on Linux

```bash
cd ~/duet2score
source .venv/bin/activate
DATA="$(find "$HOME/datasets/duet2score" -type d -name 'Bella Lucas' -print -quit)"
duet2score-inventory \
  --root "$DATA" \
  --layout grouped \
  --out data/manifests/bella-lucas-inventory.json \
  --csv data/manifests/bella-lucas-pairs.csv \
  --probe
```

If you store the dataset at a different location, update `DATA`. No need to copy your raw files into Git. `--probe` requires `ffprobe` for duration and stream metadata; omit it for a faster, dependency-free scan.

The scanner uses leading track numbers when present (e.g. `49.Lala Land`), otherwise **exact normalized filenames**. Every group gets `pairing_verified: false`; missing or duplicate file types are flagged in `issues`, along with title-only matches. This **does not** validate audio content, score arrangements, clip synchronization, or intro/outro music.

Inspect `bella-lucas-pairs.csv` before adopting a ground-truth split. PDF with different numbers or aliases must be reconciled manually or with a future manifest override.

## Next annotations

- Stable piece identifier, composition / arrangement / performer
- Source and license of score and recording
- Audio/video stream codec, duration, frame rate, sample rate and camera view
- Approximate music start/end, unrelated intro, edit/camera cuts, repeats
- Score/performance mismatch, whether fingerings are printed
- Split by **piece or arrangement**, never random windows
- Separate `part`, `staff`, `voice`, `performed_hand`, `score_finger` and `observed_finger`

## Copyright and privacy

Never commit raw MP3/MP4/PDF files, credentials, downloader account storage, or model checkpoints to the public repository. `data/` is ignored. Before publishing a manifest, review its filenames and source metadata for private or copyrighted material.

## Content audit (after resolving duplicate scores)

Install the optional audio-audit dependency and system tools (ffmpeg and poppler-utils on Debian/Ubuntu). Regenerate the manifest after any file changes.

```bash
python -m pip install -e '.[audit]'
python -m duet2score.data.content_audit \\
  --inventory data/manifests/bella-lucas-inventory.json \\
  --out data/manifests/content-audit.json \\
  --full-decode
```

The command writes JSON and CSV, decodes the two audio tracks, optionally verifies all video frames, checks PDF metadata, and estimates relative audio-track offsets using three normalized waveform correlation windows. A candidate match is not verified score correspondence. The offset is decoded MP4 audio-track time minus decoded external MP3 time. It is not a proof of video-frame synchronization, and matching intro music is not identified by this method. Review low-confidence, variable-offset, decode-failure, and missing-metadata cases before any trimming. Raw files are never modified.
