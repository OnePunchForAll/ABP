import unittest
from src.abp.policy import (
    create_policy, create_action_request, evaluate_policy,
    policy_allows, explain_policy_verdict
)

class TestPolicyParity(unittest.TestCase):
    def setUp(self):
        self.policy = create_policy(
            allowed_actions={"READ", "WRITE"},
            forbidden_actions={"DELETE"},
            requires_approval={"WRITE"},
            max_autonomy_level=3,
            max_blast_radius="MEDIUM",
            allowed_scopes={"LOCAL"},
            fail_closed=True
        )

    def test_allowed_action_returns_ALLOW(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "ALLOW")
        self.assertTrue(policy_allows(self.policy, req))

    def test_forbidden_action_returns_BLOCK(self):
        req = create_action_request("a1", "DELETE", "FACT", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "BLOCK")

    def test_unknown_claim_status_returns_HALT(self):
        req = create_action_request("a1", "READ", "UNKNOWN", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "HALT")

    def test_conflicted_claim_status_returns_VERIFY(self):
        req = create_action_request("a1", "READ", "CONFLICTED", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "VERIFY")

    def test_unsupported_claim_status_returns_BLOCK(self):
        req = create_action_request("a1", "READ", "UNSUPPORTED", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "BLOCK")

    def test_irreversible_action_without_approval_returns_CONFIRM(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", 1, "LOW", True, False)
        self.assertEqual(evaluate_policy(self.policy, req), "CONFIRM")

    def test_irreversible_action_with_approval_returns_ALLOW(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", 1, "LOW", True, True)
        self.assertEqual(evaluate_policy(self.policy, req), "ALLOW")

    def test_out_of_scope_action_returns_BLOCK(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "REMOTE", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "BLOCK")

    def test_action_above_max_autonomy_level_returns_BLOCK(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", 4, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "BLOCK")

    def test_action_above_max_blast_radius_returns_BLOCK(self):
        req = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", 1, "HIGH", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "BLOCK")

    def test_invalid_action_fields_fail_closed(self):
        req = create_action_request("a1", "READ", "INVALID_CLAIM", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "HALT")

        req2 = create_action_request("a1", "READ", "FACT", "VERIFIED", "LOCAL", "not_int", "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req2), "HALT")

    def test_requires_approval_without_approval_returns_CONFIRM(self):
        req = create_action_request("a1", "WRITE", "FACT", "VERIFIED", "LOCAL", 1, "LOW", False, False)
        self.assertEqual(evaluate_policy(self.policy, req), "CONFIRM")
        
        req_with_app = create_action_request("a1", "WRITE", "FACT", "VERIFIED", "LOCAL", 1, "LOW", False, True)
        self.assertEqual(evaluate_policy(self.policy, req_with_app), "ALLOW")

if __name__ == '__main__':
    unittest.main()
