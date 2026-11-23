"""Shared event types. Musical score staff is not the same as performed hand."""
from dataclasses import dataclass
from typing import Literal

Part = Literal["primo", "secondo", "unknown"]
Hand = Literal["primo_right", "primo_left", "secondo_right", "secondo_left", "unknown"]

@dataclass(frozen=True)
class NoteEvent:
    pitch: int
    onset_sec: float
    offset_sec: float
    confidence: float | None = None
    part: Part = "unknown"
    performed_hand: Hand = "unknown"
    staff: int | None = None
    voice: int | None = None
    score_finger: int | None = None
    observed_finger: int | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.pitch <= 127:
            raise ValueError("pitch must be a MIDI note number (0..127)")
        if self.onset_sec < 0 or self.offset_sec < self.onset_sec:
            raise ValueError("invalid note interval")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
        for finger in (self.score_finger, self.observed_finger):
            if finger is not None and finger not in (1, 2, 3, 4, 5):
                raise ValueError("finger must be 1..5 or unknown")
