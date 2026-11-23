# Duet2Score

**Audio-visual four-hand piano transcription**: a modular research codebase to convert piano duet performances into performer-aware MIDI and eventually Primo/Secondo MusicXML scores.

## Status

**Scaffold / dataset inventory only.** This repository does **not** claim to include working Transkun, V2N, fusion, hand attribution, score reconstruction, or fingering inference yet. We will benchmark existing pretrained implementations before choosing adapters. Avoid reporting paper metrics as local reproduction results.

## Planned pipeline

1. Data ingestion: videos, audio and score files; source provenance and license metadata.
2. Clip selection / synchronization: remove unrelated intro/outro music and align video/audio to the score.
3. Frozen pretrained audio AMT (Transkun and a comparison model).
4. Visual keyboard events (V2N, where camera geometry is suitable) + four-hand tracking.
5. Confidence-aware audio-visual note/event fusion and performer/hand attribution.
6. Rhythm quantization and two-grand-staff Primo/Secondo engraving to MusicXML/PDF.
7. Evaluation: note onset/offset F1; rhythm/meter; performer-aware accuracy; symbolic score errors; engraving readability.

See [ROADMAP](docs/ROADMAP.md), [DATASET](docs/DATASET.md), and [Baidu Netdisk on Linux](docs/BAIDU_LINUX.md).

## Quick start (Linux)

```bash
git clone https://github.com/fy-zhou/duet2score.git
cd duet2score
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
# Copy *your own* videos, audio and scores into data/raw/<piece-id>/.
duet2score-inventory --root data/raw --out data/manifests/inventory.json
python -m unittest discover -s tests -v
```

A piece directory may hold any mix of PDF, MSCZ, MusicXML, MIDI, MP4, MKV, MP3, FLAC or WAV. The inventory command does not alter the source files. It records counts, sizes, relative paths and optional ffprobe stream metadata. It does **not** automatically align scores and performances.

## Safety and licensing

The repository is **public** and licensed under the existing GPL-3.0. Do not commit copyrighted performance recordings, purchased scores, credentials, Baidu cookies, or pretrained checkpoints without permission. `data/`, `outputs/`, `models/weights/` and environment secrets are gitignored. Models/data from third parties retain their own licenses (check weights separately from code).

## Research principles

- Evaluate **on identical test clips** with fixed thresholds and shared ground truth.
- Keep **reported**, **independently verified**, and **locally reproduced** model metrics separate.
- Keep score staff, performed hand, performer, and observed vs printed fingerings as distinct fields.
- First build a non-learning fusion baseline; add trainable components only if needed.
