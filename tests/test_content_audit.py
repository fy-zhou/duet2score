import unittest

import numpy as np

from duet2score.data.content_audit import estimate_offset, best_match


class SyncTests(unittest.TestCase):
    def test_positive_offset(self):
        rng = np.random.default_rng(11)
        rate = 100
        audio = rng.normal(0, 0.2, rate*30)
        video = np.r_[np.zeros(2*rate), audio, np.zeros(rate)]
        result = estimate_offset(audio, video, rate=rate, max_shift_sec=5)
        self.assertEqual(result["status"], "candidate_match")
        self.assertAlmostEqual(result["offset_sec"], 2)

    def test_negative_offset(self):
        rng = np.random.default_rng(15)
        rate = 100
        audio = rng.normal(0, 0.2, rate*30)
        video = audio[2*rate:]
        result = estimate_offset(audio, video, rate=rate, max_shift_sec=5)
        self.assertEqual(result["status"], "candidate_match")
        self.assertAlmostEqual(result["offset_sec"], -2)

    def test_unrelated_recording(self):
        rng = np.random.default_rng(29)
        rate = 100
        audio = rng.normal(0, .2, rate*30)
        video = rng.normal(0, .2, rate*30)
        result = estimate_offset(audio, video, rate=rate, max_shift_sec=5)
        self.assertEqual(result["status"], "review_low_confidence")

    def test_silent_template(self):
        self.assertIsNone(best_match(np.zeros(200), np.zeros(400), 100))


if __name__ == "__main__":
    unittest.main()
