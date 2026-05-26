import unittest
from src.abp.memory import (
    create_memory, validate_memory, compute_decay_score,
    update_decay, add_contradiction, refresh_memory, expire_memory,
    memory_can_be_policy, memory_is_active, explain_memory
)

class TestMemoryParity(unittest.TestCase):
    def setUp(self):
        self.current_time = 1000000.0
        self.valid_mem = create_memory(
            memory_id="m1", claim_id="c1", created_at=self.current_time,
            last_checked=self.current_time, half_life_days=30.0,
            decay_score=1.0, status="ACTIVE", confidence="VERIFIED",
            contradiction_refs=[], evidence_refs=["e1"], source_layer="L10"
        )
        
    def test_valid_memory_passes(self):
        self.assertTrue(validate_memory(self.valid_mem))
        
    def test_missing_memory_id_fails(self):
        m = self.valid_mem.copy()
        m["memory_id"] = None
        self.assertFalse(validate_memory(m))
        m["memory_id"] = ""
        self.assertFalse(validate_memory(m))

    def test_missing_claim_id_fails(self):
        m = self.valid_mem.copy()
        m["claim_id"] = None
        self.assertFalse(validate_memory(m))

    def test_invalid_half_life_days_fails(self):
        m = self.valid_mem.copy()
        m["half_life_days"] = 0.0
        self.assertFalse(validate_memory(m))
        m["half_life_days"] = -1.0
        self.assertFalse(validate_memory(m))
        
    def test_invalid_decay_score_fails(self):
        m = self.valid_mem.copy()
        m["decay_score"] = 1.1
        self.assertFalse(validate_memory(m))
        m["decay_score"] = -0.1
        self.assertFalse(validate_memory(m))

    def test_invalid_status_fails(self):
        m = self.valid_mem.copy()
        m["status"] = "INVALID_STATUS"
        self.assertFalse(validate_memory(m))

    def test_invalid_confidence_fails(self):
        m = self.valid_mem.copy()
        m["confidence"] = "INVALID"
        self.assertFalse(validate_memory(m))

    def test_contradiction_refs_must_be_list(self):
        m = self.valid_mem.copy()
        m["contradiction_refs"] = None
        self.assertFalse(validate_memory(m))

    def test_evidence_refs_must_be_list(self):
        m = self.valid_mem.copy()
        m["evidence_refs"] = "str"
        self.assertFalse(validate_memory(m))

    def test_compute_decay_score_returns_1_at_age_0(self):
        self.assertEqual(compute_decay_score(self.current_time, self.current_time, 30.0), 1.0)

    def test_compute_decay_score_returns_half_at_half_life(self):
        half_life_secs = 30.0 * 86400.0
        score = compute_decay_score(self.current_time, self.current_time + half_life_secs, 30.0)
        self.assertAlmostEqual(score, 0.5)

    def test_old_memory_becomes_DECAYED_below_threshold(self):
        m = self.valid_mem.copy()
        half_life_secs = 30.0 * 86400.0
        update_decay(m, self.current_time + 2 * half_life_secs, threshold=0.5)
        self.assertEqual(m["status"], "DECAYED")

    def test_add_contradiction_makes_memory_CONTRADICTED(self):
        m = self.valid_mem.copy()
        add_contradiction(m, "ctr1")
        self.assertEqual(m["status"], "CONTRADICTED")
        self.assertIn("ctr1", m["contradiction_refs"])

    def test_contradicted_memory_cannot_be_policy(self):
        m = self.valid_mem.copy()
        add_contradiction(m, "ctr1")
        self.assertFalse(memory_can_be_policy(m, self.current_time))

    def test_UNKNOWN_confidence_cannot_be_policy(self):
        m = self.valid_mem.copy()
        m["confidence"] = "UNKNOWN"
        self.assertFalse(memory_can_be_policy(m, self.current_time))

    def test_TENTATIVE_confidence_cannot_be_policy(self):
        m = self.valid_mem.copy()
        m["confidence"] = "TENTATIVE"
        self.assertFalse(memory_can_be_policy(m, self.current_time))

    def test_ACTIVE_VERIFIED_fresh_memory_can_be_policy(self):
        m = self.valid_mem.copy()
        m["confidence"] = "VERIFIED"
        self.assertTrue(memory_can_be_policy(m, self.current_time))

    def test_ACTIVE_STRONG_fresh_memory_can_be_policy(self):
        m = self.valid_mem.copy()
        m["confidence"] = "STRONG"
        self.assertTrue(memory_can_be_policy(m, self.current_time))

    def test_stale_memory_cannot_be_policy(self):
        m = self.valid_mem.copy()
        stale_time = self.current_time + 31.0 * 86400.0
        self.assertFalse(memory_can_be_policy(m, stale_time, freshness_days=30))

    def test_refresh_memory_restores_ACTIVE_when_contradiction_free(self):
        m = self.valid_mem.copy()
        m["status"] = "DECAYED" 
        refresh_memory(m, self.current_time) 
        self.assertEqual(m["status"], "ACTIVE")

    def test_expire_memory_sets_EXPIRED(self):
        m = self.valid_mem.copy()
        expire_memory(m)
        self.assertEqual(m["status"], "EXPIRED")

    def test_memory_is_active_true_only_for_ACTIVE(self):
        m = self.valid_mem.copy()
        self.assertTrue(memory_is_active(m))
        expire_memory(m)
        self.assertFalse(memory_is_active(m))

if __name__ == '__main__':
    unittest.main()
