# Dataset contract (v0.1)

## Raw layout

```text
data/raw/
  piece_001/
    performance.mp4
    score.pdf
    performance.wav       # optional
  piece_002/
    take1.mkv
    score.musicxml
```

Run `duet2score-inventory --root data/raw --out data/manifests/inventory.json --probe`. No file is renamed, trimmed or converted during inventory. `ffprobe` is optional.

## Fields to collect next

- piece_id and composition / arrangement / performer
- source and license of each recording/score
- audio/video frame rate, resolution, channels, sample rate, duration
- camera: overhead / oblique / lateral / cuts / hands visible
- score type: PDF scan, native PDF, MusicXML, MIDI, MSCZ
- approximate intro, start, end and repeated/missing sections
- score/performance mismatch and whether fingering is printed
- split by **piece or arrangement**, not random windows

For inference and evaluation, keep `part`, `staff`, `voice`, `performed_hand`, `score_finger`, `observed_finger` distinct. Printed fingerings may not be what performers actually use. Missing fingering annotations are unknown rather than negative labels.

## Copyright

Raw audio/video and commercial scores stay on the research machine; do not push them to the public GitHub repo. Dataset manifests should be reviewed before publication because filenames and URLs may contain identifying or licensed content.
