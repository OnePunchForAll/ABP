import unittest
from src.abp.authority import (
    create_authority, create_authority_request, evaluate_authority,
    authority_allows, narrow_authority, explain_authority_verdict
)

class TestAuthorityParity(unittest.TestCase):
    def setUp(self):
        self.auth = create_authority(
            principal="User",
            agent="Agent1",
            scope={"READ_DB", "WRITE_LOGS"},
            allowed_tools={"query_db", "write_log"},
            expiration=100.0,
            budget=50.0,
            autonomy_ceiling=3,
            active=True
        )
        
    def test_matching_agent_returns_ALLOW(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", 10.0, 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "ALLOW")
        self.assertTrue(authority_allows(self.auth, req))
        
    def test_wrong_agent_returns_WRONG_AGENT(self):
        req = create_authority_request("Agent2", {"READ_DB"}, "query_db", 10.0, 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "WRONG_AGENT")
        
    def test_expired_authority_returns_EXPIRED(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", 10.0, 2, 100.0)
        self.assertEqual(evaluate_authority(self.auth, req), "EXPIRED")
        
    def test_inactive_authority_returns_INACTIVE(self):
        inactive_auth = self.auth.copy()
        inactive_auth["active"] = False
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", 10.0, 2, 50.0)
        self.assertEqual(evaluate_authority(inactive_auth, req), "INACTIVE")
        
    def test_requested_scope_outside_returns_OUT_OF_SCOPE(self):
        req = create_authority_request("Agent1", {"READ_DB", "DELETE_DB"}, "query_db", 10.0, 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "OUT_OF_SCOPE")
        
    def test_requested_tool_denied(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "drop_table", 10.0, 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "TOOL_DENIED")
        
    def test_requested_cost_over_budget(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", 60.0, 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "OVER_BUDGET")
        
    def test_requested_autonomy_over_ceiling(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", 10.0, 4, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "OVER_AUTONOMY")
        
    def test_invalid_fields(self):
        req = create_authority_request("Agent1", {"READ_DB"}, "query_db", "not_a_number", 2, 50.0)
        self.assertEqual(evaluate_authority(self.auth, req), "INVALID")
        
        req2 = {"agent": "Agent1"} # missing fields
        self.assertEqual(evaluate_authority(self.auth, req2), "INVALID")
        
    def test_narrow_authority(self):
        narrowed = narrow_authority(self.auth, new_scope={"READ_DB", "UNKNOWN_SCOPE"}, new_budget=10.0, new_autonomy_ceiling=5)
        self.assertEqual(narrowed["scope"], {"READ_DB"})
        self.assertEqual(narrowed["budget"], 10.0)
        self.assertEqual(narrowed["autonomy_ceiling"], 3)
        self.assertEqual(narrowed["allowed_tools"], {"query_db", "write_log"})
        
        req = create_authority_request("Agent1", {"WRITE_LOGS"}, "write_log", 5.0, 2, 50.0)
        self.assertEqual(evaluate_authority(narrowed, req), "OUT_OF_SCOPE")
        
        req2 = create_authority_request("Agent1", {"READ_DB"}, "query_db", 20.0, 2, 50.0)
        self.assertEqual(evaluate_authority(narrowed, req2), "OVER_BUDGET")

if __name__ == '__main__':
    unittest.main()
