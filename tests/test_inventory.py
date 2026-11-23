import tempfile
import unittest
from pathlib import Path

from duet2score.data.inventory import scan_dataset, classify
from duet2score.schema import NoteEvent

class InventoryTests(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify(Path("take.MP4")), "video")
        self.assertEqual(classify(Path("score.musicxml")), "score")
        self.assertIsNone(classify(Path("notes.txt")))

    def test_scan_and_flag_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "piece_a"
            a.mkdir()
            (a / "take.mp4").write_bytes(b"test")
            (a / "score.pdf").write_bytes(b"test")
            b = root / "piece_b"
            b.mkdir()
            (b / "take.wav").write_bytes(b"test")
            result = scan_dataset(root)
            self.assertEqual(result["summary"], {"pieces": 2, "video": 1, "audio": 1, "score": 1})
            self.assertFalse(result["pieces"][0]["needs_review"])
            self.assertTrue(result["pieces"][1]["needs_review"])

    def test_note_invariants(self):
        note = NoteEvent(pitch=60, onset_sec=0, offset_sec=1)
        self.assertEqual(note.performed_hand, "unknown")
        with self.assertRaises(ValueError):
            NoteEvent(pitch=128, onset_sec=0, offset_sec=1)

if __name__ == "__main__":
    unittest.main()
