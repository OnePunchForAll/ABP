import unittest
from src.abp.calibration import (
    create_prediction, validate_prediction, record_outcome,
    brier_score, expected_calibration_error, overconfidence_count,
    underconfidence_count, calibration_quality, adjust_autonomy,
    calibration_summary, explain_calibration
)

class TestCalibrationParity(unittest.TestCase):
    def setUp(self):
        self.pred1 = create_prediction("p1", "c1", 0.9, "STRONG", 1000.0)
        self.pred2 = create_prediction("p2", "c2", 0.1, "TENTATIVE", 1000.0)

    def test_valid_unresolved_prediction_passes(self):
        self.assertTrue(validate_prediction(self.pred1))

    def test_invalid_probability_fails(self):
        bad_pred = self.pred1.copy()
        bad_pred["predicted_probability"] = 1.5
        self.assertFalse(validate_prediction(bad_pred))
        
        bad_pred["predicted_probability"] = -0.1
        self.assertFalse(validate_prediction(bad_pred))
        
        bad_pred["predicted_probability"] = "high"
        self.assertFalse(validate_prediction(bad_pred))

    def test_invalid_confidence_fails(self):
        bad_pred = self.pred1.copy()
        bad_pred["confidence"] = "INVALID"
        self.assertFalse(validate_prediction(bad_pred))

    def test_record_outcome_records_true_false(self):
        pred = self.pred1.copy()
        record_outcome(pred, True)
        self.assertEqual(pred["outcome"], True)
        
        record_outcome(pred, False)
        self.assertEqual(pred["outcome"], False)

    def test_invalid_outcome_fails(self):
        pred = self.pred1.copy()
        with self.assertRaises(ValueError):
            record_outcome(pred, "maybe")

    def test_brier_score_computes_expected_value(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        p2 = create_prediction("p2", "c2", 0.1, "STRONG", 100.0, False)
        self.assertAlmostEqual(brier_score([p1, p2]), 0.01)

    def test_brier_score_ignores_unresolved(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        p2 = create_prediction("p2", "c2", 0.5, "STRONG", 100.0, None)
        self.assertAlmostEqual(brier_score([p1, p2]), 0.01)
        self.assertAlmostEqual(brier_score([p2]), 0.0)

    def test_expected_calibration_error_non_negative(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        p2 = create_prediction("p2", "c2", 0.9, "STRONG", 100.0, False)
        ece = expected_calibration_error([p1, p2])
        self.assertGreaterEqual(ece, 0.0)

    def test_overconfidence_count(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, False)
        p2 = create_prediction("p2", "c2", 0.9, "STRONG", 100.0, True)
        self.assertEqual(overconfidence_count([p1, p2]), 1)

    def test_underconfidence_count(self):
        p1 = create_prediction("p1", "c1", 0.1, "TENTATIVE", 100.0, True)
        p2 = create_prediction("p2", "c2", 0.1, "TENTATIVE", 100.0, False)
        self.assertEqual(underconfidence_count([p1, p2]), 1)

    def test_calibration_quality_passes(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        p2 = create_prediction("p2", "c2", 0.1, "TENTATIVE", 100.0, False)
        self.assertEqual(calibration_quality([p1, p2]), "PASS")

    def test_calibration_quality_fails(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, False)
        p2 = create_prediction("p2", "c2", 0.1, "TENTATIVE", 100.0, True)
        self.assertEqual(calibration_quality([p1, p2]), "FAIL")

    def test_adjust_autonomy_preserves(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        self.assertEqual(adjust_autonomy(3, [p1]), 3)

    def test_adjust_autonomy_decreases(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, False)
        self.assertEqual(adjust_autonomy(3, [p1]), 2)

    def test_adjust_autonomy_never_increases(self):
        p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0, True)
        self.assertEqual(adjust_autonomy(3, [p1]), 3)

if __name__ == '__main__':
    unittest.main()
