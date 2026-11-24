import tempfile
import unittest
from pathlib import Path

from duet2score.data.inventory import scan_dataset, classify, match_key, write_csv
from duet2score.schema import NoteEvent


class InventoryTests(unittest.TestCase):
    def test_classify(self):
        self.assertEqual(classify(Path("take.MP4")), "video")
        self.assertEqual(classify(Path("score.musicxml")), "score")
        self.assertIsNone(classify(Path("notes.txt")))

    def test_by_piece(self):
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
            self.assertEqual(result["layout"], "by_piece")
            self.assertEqual(result["summary"]["pieces"], 2)
            self.assertEqual((result["summary"]["video"], result["summary"]["audio"],
                              result["summary"]["score"]), (1, 1, 1))
            self.assertFalse(result["pieces"][0]["has_audio"])
            self.assertTrue(result["pieces"][0]["needs_review"])

    def test_grouped_chinese_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "视频").mkdir()
            (root / "音频").mkdir()
            (root / "视频" / "49.Lala Land OST Medley.mp4").write_bytes(b"video")
            (root / "音频" / "49.Lala Land.mp3").write_bytes(b"audio")
            (root / "49.Lala Land OST Medley.pdf").write_bytes(b"score")
            (root / "50.Missing Video.pdf").write_bytes(b"extra")
            result = scan_dataset(root)
            self.assertEqual(result["layout"], "grouped")
            self.assertEqual(result["summary"]["pieces"], 2)
            self.assertEqual(result["summary"]["complete_triplets"], 1)
            self.assertEqual(result["summary"]["needs_review"], 1)
            paired = next(p for p in result["pieces"] if p["piece_id"] == "number:0049")
            self.assertFalse(paired["needs_review"])
            self.assertFalse(paired["pairing_verified"])
            csvpath = root / "pairs.csv"
            write_csv(result, csvpath)
            self.assertIn("49.Lala Land OST Medley.mp4", csvpath.read_text(encoding="utf-8-sig"))

    def test_duplicate_score_requires_review(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "视频").mkdir()
            (root / "音频").mkdir()
            for parent, name in [("视频", "1.A.mp4"), ("音频", "1.A.mp3"),
                                 ("", "1.A.pdf"), ("", "1.B.pdf")]:
                (root / parent / name).write_bytes(b"x")
            result = scan_dataset(root)
            self.assertEqual(result["summary"]["complete_triplets"], 0)
            self.assertEqual(result["summary"]["needs_review"], 1)
            self.assertIn("multiple_score", result["pieces"][0]["issues"])

    def test_filename_key(self):
        self.assertEqual(match_key(Path("2.骷髅之舞 Danse Macabre.mp4"))[0], "number:0002")
        self.assertEqual(match_key(Path("Lala-Land.pdf"))[0], "title:lalaland")

    def test_note_invariants(self):
        note = NoteEvent(pitch=60, onset_sec=0, offset_sec=1)
        self.assertEqual(note.performed_hand, "unknown")
        with self.assertRaises(ValueError):
            NoteEvent(pitch=128, onset_sec=0, offset_sec=1)


if __name__ == "__main__":
    unittest.main()
