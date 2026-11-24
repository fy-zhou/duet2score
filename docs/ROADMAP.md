# Implementation roadmap

## Phase 0 — data ingestion (implemented)

- [x] Package setup, ignore private data, basic event schema
- [x] Raw-piece inventory CLI, optional ffprobe metadata
- [x] ffmpeg audio extraction helper
- [x] Run initial grouped inventory: 49 video + 49 audio + 50 score; 49 filename-matched triplets (user local run)
- [x] Add optional ffprobe-based duration audit (command, not yet executed on real data)
- [x] Resolve one duplicate PDF locally; 49 candidate triplets (user confirmation)
- [x] Implement read-only content audit and synthetic synchronization tests (local run on real data pending)
- [ ] Validate audio/video contents and duration anomalies; confirm 49 candidate pairs manually
- [ ] Inspect dataset statistics and define ground truth/held-out tracks
- [ ] Automatically localize actual performance (intro/outro removal, subsequence matching)

## Phase 1 — reproduce pretrained baselines (not implemented)

- [ ] Transkun: code + weight SHA, installed environment, paper metric reproduction
- [ ] Second audio AMT baseline (e.g. Onsets and Frames/ByteDance), shared note evaluation
- [ ] V2N: verify video geometry and evaluate against audio branch on common clips
- [ ] Existing score conversion approaches: DuET, MuseScore and alternatives
- [ ] Read/reproduce published hand-assignment methods if source and weights are obtainable

## Phase 2 — minimal audio-visual fusion

- [ ] Synchronize audio, video and coordinate systems
- [ ] Stable performer identities and four tracked hands
- [ ] Confidence-aware note-to-key / finger associations
- [ ] Physical and temporal consistency constraints; handle occlusion/unknown hand
- [ ] Ablation: audio-only / visual-only / independent fusion / constrained fusion

## Phase 3 — score reconstruction and validation

- [ ] Shared tempo/meter grid, Primo/Secondo two-grand-staff MusicXML export
- [ ] Note onset/offset F1; beat/downbeat timing; hand-aware note F1
- [ ] Symbolic score correctness (MUSTER or equivalent), separate from PDF layout
- [ ] Blind human engraving/readability assessment; optional sparse fingering

**Never mark a paper result as locally reproduced until weight, test split, evaluator, tolerance, logs and output are archived.**
