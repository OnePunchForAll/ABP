import unittest
from src.abp.metrics import (
    create_metrics, validate_metrics,
    create_critical_failures, validate_critical_failures,
    calibration_quality, reproducibility_score,
    compute_no_silent_drift_score, compute_abp_score, explain_metrics
)

class TestMetricParity(unittest.TestCase):
    def setUp(self):
        self.valid_metrics = create_metrics(
            1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0,
            1.0, 1.0, 0.0, 0.0, 150.0, True, 1.0
        )
        self.valid_cf = create_critical_failures(False, False, False, False, False, False)

    def test_valid_metrics_pass(self):
        self.assertTrue(validate_metrics(self.valid_metrics))

    def test_missing_metric_fails(self):
        m = self.valid_metrics.copy()
        del m["runtime_ms"]
        self.assertFalse(validate_metrics(m))

    def test_metric_below_zero_fails(self):
        m = self.valid_metrics.copy()
        m["claim_evidence_coverage"] = -0.1
        self.assertFalse(validate_metrics(m))

    def test_metric_above_one_fails(self):
        m = self.valid_metrics.copy()
        m["claim_evidence_coverage"] = 1.1
        self.assertFalse(validate_metrics(m))

    def test_negative_runtime_fails(self):
        m = self.valid_metrics.copy()
        m["runtime_ms"] = -5.0
        self.assertFalse(validate_metrics(m))

    def test_reproducibility_pass_must_be_boolean(self):
        m = self.valid_metrics.copy()
        m["reproducibility_pass"] = "yes"
        self.assertFalse(validate_metrics(m))

    def test_valid_critical_failures_pass(self):
        self.assertTrue(validate_critical_failures(self.valid_cf))

    def test_missing_critical_failure_fails(self):
        cf = self.valid_cf.copy()
        del cf["hidden_drift_undetected"]
        self.assertFalse(validate_critical_failures(cf))

    def test_abpscore_is_between_0_and_1(self):
        score = compute_abp_score(self.valid_metrics, self.valid_cf)
        self.assertTrue(0.0 <= score <= 1.0)

    def test_calibration_quality_equals_1_minus_error(self):
        m = self.valid_metrics.copy()
        m["calibration_error"] = 0.2
        self.assertAlmostEqual(calibration_quality(m), 0.8)
        
        m["calibration_error"] = 1.5
        self.assertAlmostEqual(calibration_quality(m), 0.0)

    def test_reproducibility_score_maps_correctly(self):
        m = self.valid_metrics.copy()
        m["reproducibility_pass"] = True
        self.assertEqual(reproducibility_score(m), 1.0)
        m["reproducibility_pass"] = False
        self.assertEqual(reproducibility_score(m), 0.0)

    def test_no_silent_drift_score_returns_1_when_perfect(self):
        self.assertEqual(compute_no_silent_drift_score(self.valid_metrics, self.valid_cf), 1.0)

    def test_no_silent_drift_score_returns_0_when_hidden_drift_undetected(self):
        cf = self.valid_cf.copy()
        cf["hidden_drift_undetected"] = True
        self.assertEqual(compute_no_silent_drift_score(self.valid_metrics, cf), 0.0)
        
    def test_no_silent_drift_score_returns_0_when_escape_rate_nonzero(self):
        m = self.valid_metrics.copy()
        m["unreceipted_action_escape_rate"] = 0.1
        self.assertEqual(compute_no_silent_drift_score(m, self.valid_cf), 0.0)

    def test_abpscore_is_capped_at_0_79_when_any_critical_failure_exists(self):
        cf = self.valid_cf.copy()
        cf["policy_bypass_allowed"] = True
        score = compute_abp_score(self.valid_metrics, cf)
        self.assertAlmostEqual(score, 0.79)

    def test_abpscore_is_not_capped_when_all_critical_failures_are_false(self):
        score = compute_abp_score(self.valid_metrics, self.valid_cf)
        self.assertAlmostEqual(score, 1.0)

    def test_explain_metrics_returns_human_readable_text(self):
        text = explain_metrics(self.valid_metrics, self.valid_cf)
        self.assertIn("ABP Score", text)
        self.assertIn("PASS", text)

if __name__ == '__main__':
    unittest.main()
