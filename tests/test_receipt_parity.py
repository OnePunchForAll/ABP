import unittest
from src.abp.receipts import (
    create_receipt, validate_receipt, receipt_hash,
    receipt_allows, action_has_receipt, explain_receipt_validation
)

class TestReceiptParity(unittest.TestCase):
    def setUp(self):
        self.valid_receipt = create_receipt(
            receipt_id="r1", agent="Agent1", principal="User1",
            action="READ", target="DB", scope="LOCAL",
            input_hash="hash_in", output_hash="hash_out",
            timestamp=1234.56, cost=1.0, status="success",
            policy_verdict="ALLOW", reversibility_level=0,
            evidence_refs=["ev1", "ev2"], state_before="s1",
            state_after="s2", signature_placeholder="SIG_123"
        )
        
    def test_valid_receipt_passes(self):
        self.assertTrue(validate_receipt(self.valid_receipt))
        
    def test_missing_fields_fail(self):
        fields = [
            "receipt_id", "agent", "principal", "action", "target", "scope",
            "input_hash", "output_hash", "timestamp", "state_before",
            "state_after", "signature_placeholder"
        ]
        for f in fields:
            bad_r = self.valid_receipt.copy()
            bad_r[f] = "" if isinstance(bad_r[f], str) else None
            self.assertFalse(validate_receipt(bad_r), f"Failed to reject missing {f}")
            bad_r[f] = None
            self.assertFalse(validate_receipt(bad_r), f"Failed to reject None {f}")

    def test_invalid_policy_verdict_fails(self):
        bad_r = self.valid_receipt.copy()
        bad_r["policy_verdict"] = "INVALID_VERDICT"
        self.assertFalse(validate_receipt(bad_r))
        self.assertEqual(explain_receipt_validation(bad_r), "INVALID_POLICY_VERDICT")

    def test_invalid_status_fails(self):
        bad_r = self.valid_receipt.copy()
        bad_r["status"] = "INVALID_STATUS"
        self.assertFalse(validate_receipt(bad_r))
        self.assertEqual(explain_receipt_validation(bad_r), "INVALID_STATUS")

    def test_evidence_refs_must_be_list(self):
        bad_r = self.valid_receipt.copy()
        bad_r["evidence_refs"] = "not_a_list"
        self.assertFalse(validate_receipt(bad_r))
        self.assertEqual(explain_receipt_validation(bad_r), "INVALID_EVIDENCE_REFS")

    def test_negative_cost_fails(self):
        bad_r = self.valid_receipt.copy()
        bad_r["cost"] = -1.0
        self.assertFalse(validate_receipt(bad_r))
        self.assertEqual(explain_receipt_validation(bad_r), "INVALID_COST")

    def test_invalid_reversibility_level_fails(self):
        bad_r = self.valid_receipt.copy()
        bad_r["reversibility_level"] = 6
        self.assertFalse(validate_receipt(bad_r))
        bad_r["reversibility_level"] = -1
        self.assertFalse(validate_receipt(bad_r))
        self.assertEqual(explain_receipt_validation(bad_r), "INVALID_REVERSIBILITY_LEVEL")

    def test_receipt_hash_stable(self):
        r1 = self.valid_receipt.copy()
        r2 = self.valid_receipt.copy()
        self.assertEqual(receipt_hash(r1), receipt_hash(r2))

    def test_receipt_hash_changes_after_tampering(self):
        r1 = self.valid_receipt.copy()
        hash1 = receipt_hash(r1)
        
        r1["cost"] = 999.0
        hash2 = receipt_hash(r1)
        self.assertNotEqual(hash1, hash2)

    def test_receipt_allows_only_valid_allow(self):
        self.assertTrue(receipt_allows(self.valid_receipt))
        
        bad_policy = self.valid_receipt.copy()
        bad_policy["policy_verdict"] = "BLOCK"
        self.assertFalse(receipt_allows(bad_policy))
        
        invalid_receipt = self.valid_receipt.copy()
        invalid_receipt["status"] = "INVALID_STATUS"
        self.assertFalse(receipt_allows(invalid_receipt))

    def test_action_has_receipt_false_for_none(self):
        self.assertFalse(action_has_receipt(None))

    def test_action_has_receipt_false_for_invalid(self):
        bad_r = self.valid_receipt.copy()
        bad_r["cost"] = -1
        self.assertFalse(action_has_receipt(bad_r))

if __name__ == '__main__':
    unittest.main()
