import unittest
from src.abp.adversary import (
    create_attack_result, validate_attack_result,
    run_byte_flip_attack, run_hash_tamper_attack,
    run_forged_quote_hash_attack, run_high_confidence_unsupported_claim_attack,
    run_state_contradiction_attack, run_policy_forbidden_action_attack,
    run_authority_scope_expansion_attack, run_irreversible_without_approval_attack,
    run_action_without_receipt_attack, run_bad_calibration_attack,
    run_stale_memory_policy_attack, run_all_adversary_attacks
)

class TestAdversaryParity(unittest.TestCase):
    def test_valid_attack_result_passes(self):
        res = create_attack_result("a1", "BYTE", "test", "exp", "act", True, "")
        self.assertTrue(validate_attack_result(res))

    def test_invalid_attack_result_fails(self):
        res = create_attack_result("a1", "INVALID", "test", "exp", "act", True, "")
        self.assertFalse(validate_attack_result(res))
        
        res2 = create_attack_result("a1", "BYTE", "test", "exp", "act", False, "")
        self.assertFalse(validate_attack_result(res2))
        
        res3 = create_attack_result("a1", "BYTE", "test", "exp", "act", True, "oops")
        self.assertFalse(validate_attack_result(res3))

    def test_byte_flip_attack_passes(self):
        self.assertTrue(run_byte_flip_attack()["passed"])

    def test_hash_tamper_attack_passes(self):
        self.assertTrue(run_hash_tamper_attack()["passed"])

    def test_forged_quote_hash_attack_passes(self):
        self.assertTrue(run_forged_quote_hash_attack()["passed"])

    def test_high_confidence_unsupported_claim_attack_passes(self):
        self.assertTrue(run_high_confidence_unsupported_claim_attack()["passed"])

    def test_state_contradiction_attack_passes(self):
        self.assertTrue(run_state_contradiction_attack()["passed"])

    def test_policy_forbidden_action_attack_passes(self):
        self.assertTrue(run_policy_forbidden_action_attack()["passed"])

    def test_authority_scope_expansion_attack_passes(self):
        self.assertTrue(run_authority_scope_expansion_attack()["passed"])

    def test_irreversible_without_approval_attack_passes(self):
        self.assertTrue(run_irreversible_without_approval_attack()["passed"])

    def test_action_without_receipt_attack_passes(self):
        self.assertTrue(run_action_without_receipt_attack()["passed"])

    def test_bad_calibration_attack_passes(self):
        self.assertTrue(run_bad_calibration_attack()["passed"])

    def test_stale_memory_policy_attack_passes(self):
        self.assertTrue(run_stale_memory_policy_attack()["passed"])

    def test_run_all_adversary_attacks_returns_all_passing(self):
        results = run_all_adversary_attacks()
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertTrue(r["passed"], f"Attack {r['attack_name']} failed: {r['failure_reason']}")

if __name__ == '__main__':
    unittest.main()
