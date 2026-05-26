import unittest
from src.abp.perfection import (
    create_perfection_gate_input, validate_perfection_gate_input,
    evaluate_perfection_gate, perfection_gate_passes, explain_perfection_gate,
    list_perfection_blockers, list_perfection_limitations
)

class TestPerfectionGate(unittest.TestCase):
    def setUp(self):
        self.perfect = create_perfection_gate_input(
            all_tests_pass=True,
            adversarial_mutation_catch_rate=1.0,
            unsupported_high_confidence_claim_escape_rate=0.0,
            unreceipted_action_escape_rate=0.0,
            authority_violation_escape_rate=0.0,
            irreversible_action_bypass_rate=0.0,
            silent_state_drift_detected=False,
            reproducibility_runs=3,
            calibration_metrics_recorded=True,
            known_failures=[],
            external_audit_done=False,
            real_world_validation_done=False,
            scope="LOCAL_TEST_SUITE"
        )
        
    def test_valid_gate_input_passes(self):
        self.assertTrue(validate_perfection_gate_input(self.perfect))
        
    def test_missing_required_field_fails(self):
        p = self.perfect.copy()
        del p["all_tests_pass"]
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_invalid_rate_below_zero_fails(self):
        p = self.perfect.copy()
        p["adversarial_mutation_catch_rate"] = -0.1
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_invalid_rate_above_one_fails(self):
        p = self.perfect.copy()
        p["adversarial_mutation_catch_rate"] = 1.1
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_reproducibility_runs_must_be_integer(self):
        p = self.perfect.copy()
        p["reproducibility_runs"] = 3.5
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_known_failures_must_be_list(self):
        p = self.perfect.copy()
        p["known_failures"] = "None"
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_invalid_scope_fails(self):
        p = self.perfect.copy()
        p["scope"] = "GLOBAL"
        self.assertFalse(validate_perfection_gate_input(p))
        
    def test_perfect_local_gate_returns_OPERATIONALLY_PERFECT_V0_1(self):
        self.assertEqual(evaluate_perfection_gate(self.perfect), "OPERATIONALLY_PERFECT_V0_1")
        self.assertTrue(perfection_gate_passes(self.perfect))
        
    def test_all_tests_pass_False_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["all_tests_pass"] = False
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_adversarial_catch_rate_below_1_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["adversarial_mutation_catch_rate"] = 0.99
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_unsupported_high_confidence_claim_escape_above_0_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["unsupported_high_confidence_claim_escape_rate"] = 0.01
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_unreceipted_action_escape_above_0_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["unreceipted_action_escape_rate"] = 0.01
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_authority_violation_escape_above_0_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["authority_violation_escape_rate"] = 0.01
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_irreversible_bypass_above_0_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["irreversible_action_bypass_rate"] = 0.01
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_silent_state_drift_detected_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["silent_state_drift_detected"] = True
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_reproducibility_runs_below_3_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["reproducibility_runs"] = 2
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_missing_calibration_metrics_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["calibration_metrics_recorded"] = False
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_known_failures_non_empty_returns_NOT_YET_PERFECT(self):
        p = self.perfect.copy()
        p["known_failures"] = ["bug1"]
        self.assertEqual(evaluate_perfection_gate(p), "NOT_YET_PERFECT")
        
    def test_external_audit_missing_appears_as_limitation_not_local_blocker(self):
        lims = list_perfection_limitations(self.perfect)
        self.assertIn("not externally audited", lims)
        self.assertEqual(evaluate_perfection_gate(self.perfect), "OPERATIONALLY_PERFECT_V0_1")
        
    def test_real_world_validation_missing_appears_as_limitation_not_local_blocker(self):
        lims = list_perfection_limitations(self.perfect)
        self.assertIn("not real-world validated", lims)
        self.assertEqual(evaluate_perfection_gate(self.perfect), "OPERATIONALLY_PERFECT_V0_1")
        
    def test_perfection_gate_passes_true_only_for_OPERATIONALLY_PERFECT(self):
        self.assertTrue(perfection_gate_passes(self.perfect))
        p = self.perfect.copy()
        p["known_failures"] = ["bug1"]
        self.assertFalse(perfection_gate_passes(p))
        
    def test_explain_perfection_gate_never_claims_absolute_perfection(self):
        exp = explain_perfection_gate(self.perfect)
        self.assertIn("does NOT claim absolute", exp)
        self.assertIn("strictly bound to local", exp)

if __name__ == '__main__':
    unittest.main()
