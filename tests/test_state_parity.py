import unittest
from src.abp.state import (
    create_state, validate_state, add_known, add_unknown, add_assumption,
    add_constraint, add_pending_check, resolve_pending_check, add_contradiction,
    add_commitment, record_action, can_synthesize
)

class TestStateParity(unittest.TestCase):
    def test_valid_state_passes(self):
        state = create_state("Solve the problem")
        self.assertTrue(validate_state(state))

    def test_empty_goal_fails(self):
        state = create_state("")
        self.assertFalse(validate_state(state))
        
        state2 = create_state("Goal")
        state2["goal"] = None
        self.assertFalse(validate_state(state2))

    def test_invalid_risk_level_fails(self):
        state = create_state("Goal")
        state["risk_level"] = "INVALID"
        self.assertFalse(validate_state(state))

    def test_invalid_autonomy_level_fails(self):
        state = create_state("Goal")
        state["autonomy_level"] = 6
        self.assertFalse(validate_state(state))
        state["autonomy_level"] = "0"
        self.assertFalse(validate_state(state))

    def test_commitment_without_authority_basis_fails(self):
        state = create_state("Goal")
        add_commitment(state, "c1", "Do something", authority_basis=None)
        self.assertFalse(validate_state(state))
        
        state2 = create_state("Goal")
        add_commitment(state2, "c2", "Do something else", authority_basis="User override")
        self.assertTrue(validate_state(state2))

    def test_pending_check_with_invalid_status_fails(self):
        state = create_state("Goal")
        add_pending_check(state, "chk1", "Check this")
        state["pending_checks"][0]["status"] = "INVALID_STATUS"
        self.assertFalse(validate_state(state))

    def test_active_contradiction_blocks_synthesis(self):
        state = create_state("Goal")
        add_contradiction(state, "cont1", "A conflicts with B", active=True)
        self.assertFalse(can_synthesize(state))

    def test_resolved_contradictions_allow_synthesis(self):
        state = create_state("Goal")
        add_contradiction(state, "cont1", "A conflicts with B", active=False)
        self.assertTrue(can_synthesize(state))
        
    def test_no_contradictions_allow_synthesis(self):
        state = create_state("Goal")
        self.assertTrue(can_synthesize(state))

    def test_record_action_appends(self):
        state = create_state("Goal")
        record_action(state, "act1", "Did a thing")
        self.assertEqual(len(state["actions_taken"]), 1)
        
        action_events = [e for e in state["events"] if e["type"] == "record_action"]
        self.assertEqual(len(action_events), 1)
        self.assertEqual(action_events[0]["action_id"], "act1")

    def test_every_state_update_appends_event(self):
        state = create_state("Goal")
        initial_events = len(state["events"])
        
        add_known(state, "K1")
        add_unknown(state, "U1")
        add_assumption(state, "A1")
        add_constraint(state, "C1")
        add_pending_check(state, "chk2", "desc")
        resolve_pending_check(state, "chk2")
        add_contradiction(state, "cont2", "desc", active=False)
        add_commitment(state, "com1", "desc", authority_basis="Auth")
        
        # 8 updates made
        self.assertEqual(len(state["events"]), initial_events + 8)

if __name__ == '__main__':
    unittest.main()
