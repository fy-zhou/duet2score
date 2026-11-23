"""Thin common interface; concrete pretrained adapters will be added after benchmarking."""
from typing import Protocol, Sequence
from pathlib import Path
from duet2score.schema import NoteEvent

class AudioTranscriber(Protocol):
    def transcribe(self, audio_path: Path) -> Sequence[NoteEvent]: ...

class VisualTranscriber(Protocol):
    def transcribe(self, video_path: Path) -> Sequence[NoteEvent]: ...

# TODO: implement verified Transkun, V2N, and comparison adapters.
