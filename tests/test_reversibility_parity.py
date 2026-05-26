import unittest
from src.abp.reversibility import (
    create_reversibility_action, evaluate_reversibility,
    reversibility_allows, explain_reversibility_verdict
)

class TestReversibilityParity(unittest.TestCase):
    def test_level_0_THINK_allows(self):
        action = create_reversibility_action("a1", "think", 0, False, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "ALLOW")
        self.assertTrue(reversibility_allows(action))

    def test_level_1_DRAFT_allows(self):
        action = create_reversibility_action("a1", "draft", 1, False, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "ALLOW")

    def test_level_2_without_evidence_returns_VERIFY_or_BLOCK(self):
        action = create_reversibility_action("a1", "rec", 2, False, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        res = evaluate_reversibility(action)
        self.assertIn(res, ["VERIFY", "BLOCK"])

    def test_level_2_with_evidence_allows(self):
        action = create_reversibility_action("a1", "rec", 2, True, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "ALLOW")

    def test_level_3_requires_policy_and_authority_allow(self):
        action = create_reversibility_action("a1", "mod", 3, True, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "ALLOW")
        
        action_p_fail = create_reversibility_action("a1", "mod", 3, True, "BLOCK", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action_p_fail), "BLOCK")
        
        action_a_fail = create_reversibility_action("a1", "mod", 3, True, "ALLOW", "BLOCK", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action_a_fail), "BLOCK")

    def test_level_4_requires_rollback_plan(self):
        action = create_reversibility_action("a1", "exec", 4, True, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "BLOCK")
        
        action["rollback_plan"] = True
        self.assertEqual(evaluate_reversibility(action), "ALLOW")

    def test_level_5_without_approval_returns_CONFIRM(self):
        action = create_reversibility_action("a1", "commit", 5, True, "ALLOW", "ALLOW", False, True, False, True, True, "LOW")
        self.assertEqual(evaluate_reversibility(action), "CONFIRM")

    def test_level_5_without_external_verification_returns_CONFIRM_or_BLOCK(self):
        action = create_reversibility_action("a1", "commit", 5, True, "ALLOW", "ALLOW", True, True, False, False, True, "LOW")
        res = evaluate_reversibility(action)
        self.assertIn(res, ["CONFIRM", "BLOCK"])

    def test_level_5_with_compensation_plan_and_all_gates_passes(self):
        action = create_reversibility_action("a1", "commit", 5, True, "ALLOW", "ALLOW", True, False, True, True, True, "LOW")
        self.assertEqual(evaluate_reversibility(action), "ALLOW")

    def test_policy_BLOCK_returns_BLOCK(self):
        action = create_reversibility_action("a1", "draft", 1, False, "BLOCK", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "BLOCK")

    def test_policy_VERIFY_returns_VERIFY(self):
        action = create_reversibility_action("a1", "draft", 1, False, "VERIFY", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "VERIFY")

    def test_authority_denied_blocks_level_3_plus(self):
        action = create_reversibility_action("a1", "mod", 3, True, "ALLOW", "TOOL_DENIED", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "BLOCK")

    def test_invalid_level_returns_INVALID(self):
        action = create_reversibility_action("a1", "mod", 6, True, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertEqual(evaluate_reversibility(action), "INVALID")

    def test_invalid_blast_radius_returns_INVALID(self):
        action = create_reversibility_action("a1", "mod", 1, True, "ALLOW", "ALLOW", False, False, False, False, False, "GALAXY")
        self.assertEqual(evaluate_reversibility(action), "INVALID")

    def test_reversibility_allows_only_for_ALLOW(self):
        action = create_reversibility_action("a1", "think", 0, False, "ALLOW", "ALLOW", False, False, False, False, False, "LOW")
        self.assertTrue(reversibility_allows(action))
        
        action["policy_verdict"] = "BLOCK"
        self.assertFalse(reversibility_allows(action))

if __name__ == '__main__':
    unittest.main()
