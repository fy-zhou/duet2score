import unittest

from duet2score.data.audit import media_audit, duration


class MediaAuditTests(unittest.TestCase):
    def test_diff_and_flags(self):
        inventory = {"pieces": [{
            "piece_id": "number:0049",
            "issues": [],
            "assets": [
                {"kind": "video", "path": "视频/49.x.mp4",
                 "probe": {"format": {"duration": "103.5"}}},
                {"kind": "audio", "path": "音频/49.x.mp3",
                 "probe": {"format": {"duration": "96.4"}}},
                {"kind": "score", "path": "49.x.pdf"},
            ],
        }]}
        rows = media_audit(inventory, threshold_sec=5)
        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0]["video_minus_audio_sec"], 7.1)
        self.assertIn("duration_difference_review", rows[0]["flags"])

    def test_no_probe_and_extra_pdf(self):
        inventory = {"pieces": [
            {"piece_id": "title:extra", "issues": ["missing_video", "missing_audio"],
             "assets": [{"kind": "score", "path": "extra.pdf"}]}
        ]}
        rows = media_audit(inventory)
        self.assertIsNone(rows[0]["video_sec"])
        self.assertEqual(rows[0]["flags"], "missing_video|missing_audio")
        self.assertIsNone(duration({"probe": {"error": "ffprobe not installed"}}))

    def test_threshold_validation(self):
        with self.assertRaises(ValueError):
            media_audit({"pieces": []}, threshold_sec=-1)


if __name__ == "__main__":
    unittest.main()
