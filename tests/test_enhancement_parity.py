import unittest
from src.abp.enhancement import (
    create_enhancement_proposal, validate_enhancement_proposal, evaluate_enhancement,
    enhancement_allows, apply_enhancement_simulated, reject_enhancement,
    revert_enhancement, explain_enhancement
)

class TestEnhancementParity(unittest.TestCase):
    def setUp(self):
        self.valid_prop = create_enhancement_proposal(
            "p1", "METRIC", "some weakness", "ev_1", "my_metric", 0.5,
            "change X", "test Y", "rollback Z", "LOW", False
        )
        
    def test_valid_proposal_passes(self):
        self.assertTrue(validate_enhancement_proposal(self.valid_prop))
        
    def test_missing_proposal_id_fails(self):
        p = self.valid_prop.copy()
        p["proposal_id"] = ""
        self.assertFalse(validate_enhancement_proposal(p))
        del p["proposal_id"]
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_missing_evidence_ref_fails(self):
        p = self.valid_prop.copy()
        del p["evidence_ref"]
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_missing_regression_test_fails(self):
        p = self.valid_prop.copy()
        del p["regression_test"]
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_missing_rollback_plan_fails(self):
        p = self.valid_prop.copy()
        del p["rollback_plan"]
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_invalid_target_layer_fails(self):
        p = self.valid_prop.copy()
        p["target_layer"] = "UNKNOWN"
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_invalid_risk_level_fails(self):
        p = self.valid_prop.copy()
        p["risk_level"] = "UNKNOWN"
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_invalid_status_fails(self):
        p = self.valid_prop.copy()
        p["status"] = "UNKNOWN"
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_expected_delta_must_be_numeric(self):
        p = self.valid_prop.copy()
        p["expected_delta"] = "not a number"
        self.assertFalse(validate_enhancement_proposal(p))
        
    def test_LOW_proposal_with_evidence_regression_and_rollback_allows(self):
        self.assertEqual(evaluate_enhancement(self.valid_prop), "ALLOW")
        self.assertTrue(enhancement_allows(self.valid_prop))
        
    def test_HIGH_proposal_without_approval_returns_CONFIRM(self):
        p = self.valid_prop.copy()
        p["risk_level"] = "HIGH"
        p["human_approval"] = False
        res = evaluate_enhancement(p)
        self.assertIn(res, ["CONFIRM", "BLOCK"])
        
    def test_HIGH_proposal_with_approval_allows(self):
        p = self.valid_prop.copy()
        p["risk_level"] = "HIGH"
        p["human_approval"] = True
        self.assertEqual(evaluate_enhancement(p), "ALLOW")
        
    def test_proposal_without_evidence_blocks(self):
        p = self.valid_prop.copy()
        p["evidence_ref"] = ""
        self.assertEqual(evaluate_enhancement(p), "BLOCK")
        
    def test_proposal_without_regression_test_blocks(self):
        p = self.valid_prop.copy()
        p["regression_test"] = ""
        self.assertEqual(evaluate_enhancement(p), "BLOCK")
        
    def test_proposal_without_rollback_blocks(self):
        p = self.valid_prop.copy()
        p["rollback_plan"] = ""
        self.assertEqual(evaluate_enhancement(p), "BLOCK")
        
    def test_simulated_apply_sets_status_APPLIED_only_when_allowed(self):
        applied = apply_enhancement_simulated(self.valid_prop)
        self.assertEqual(applied["status"], "APPLIED")
        
        p = self.valid_prop.copy()
        p["regression_test"] = ""
        applied_fail = apply_enhancement_simulated(p)
        self.assertEqual(applied_fail["status"], "FAILED")
        
    def test_failed_regression_blocks_simulated_apply(self):
        applied_fail = apply_enhancement_simulated(self.valid_prop, regression_passed=False)
        self.assertEqual(applied_fail["status"], "FAILED")
        self.assertEqual(evaluate_enhancement(self.valid_prop, regression_passed=False), "BLOCK")
        
    def test_reject_enhancement_sets_status_REJECTED(self):
        rej = reject_enhancement(self.valid_prop, "too risky")
        self.assertEqual(rej["status"], "REJECTED")
        
    def test_revert_enhancement_sets_status_REVERTED(self):
        rev = revert_enhancement(self.valid_prop, "caused bug")
        self.assertEqual(rev["status"], "REVERTED")
        
    def test_enhancement_allows_true_only_for_ALLOW(self):
        self.assertTrue(enhancement_allows(self.valid_prop))
        
        p = self.valid_prop.copy()
        p["regression_test"] = ""
        self.assertFalse(enhancement_allows(p))

if __name__ == '__main__':
    unittest.main()
