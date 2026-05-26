#!/usr/bin/env python3
from __future__ import annotations

import copy
import unittest

from abp_assurance_gate import (
    ABSOLUTE_CLAIM,
    REQUIRED_EVIDENCE,
    UNCLAIMED_STATUSES,
    evaluate_claim,
    load_status,
    missing_evidence,
    real_world_gate_passed,
    validate_assurance_status,
)


class TestABPAssuranceClaims(unittest.TestCase):
    def setUp(self) -> None:
        self.status = load_status()

    def test_current_github_metric_validation_evidence_exists(self) -> None:
        self.assertEqual(self.status["current_validated_status"], "GITHUB_FULL_METRIC_VALIDATED")
        ok, errors = validate_assurance_status(self.status)
        self.assertTrue(ok, errors)

    def test_formal_proof_claim_is_currently_blocked(self) -> None:
        claim = "formally_proven"
        node = self.status["claims"][claim]
        self.assertEqual(node["status"], "NOT_PROVEN")
        self.assertIs(node["allowed_claim"], False)

        ok, reasons = evaluate_claim(self.status, claim)
        self.assertFalse(ok)
        self.assertIn("formally_proven_allowed_claim_is_false", reasons)

    def test_external_audit_claim_is_currently_blocked(self) -> None:
        claim = "externally_audited"
        node = self.status["claims"][claim]
        self.assertEqual(node["status"], "NOT_AUDITED")
        self.assertIs(node["allowed_claim"], False)

        ok, reasons = evaluate_claim(self.status, claim)
        self.assertFalse(ok)
        self.assertIn("externally_audited_allowed_claim_is_false", reasons)

    def test_real_world_validation_claim_matches_gate_state(self) -> None:
        claim = "real_world_validated"
        node = self.status["claims"][claim]

        if real_world_gate_passed():
            self.assertEqual(node["status"], "REAL_WORLD_VALIDATED_SCOPE_V0_1")
            self.assertIs(node["allowed_claim"], True)
            ok, reasons = evaluate_claim(self.status, claim)
            self.assertTrue(ok, reasons)
        else:
            self.assertEqual(node["status"], "NOT_VALIDATED")
            self.assertIs(node["allowed_claim"], False)
            ok, reasons = evaluate_claim(self.status, claim)
            self.assertFalse(ok)

    def test_real_world_validation_cannot_be_enabled_without_passing_gate(self) -> None:
        mutated = copy.deepcopy(self.status)
        mutated["claims"]["real_world_validated"]["status"] = "REAL_WORLD_VALIDATED_SCOPE_V0_1"
        mutated["claims"]["real_world_validated"]["allowed_claim"] = True

        ok, reasons = evaluate_claim(mutated, "real_world_validated")

        if real_world_gate_passed():
            self.assertTrue(ok, reasons)
        else:
            self.assertFalse(ok)
            acceptable = set(missing_evidence("real_world_validated")) | {"real_world_validation_gate_not_passed"}
            self.assertTrue(any(reason in acceptable for reason in reasons), reasons)

    def test_absolute_or_universal_perfection_is_never_claimable(self) -> None:
        node = self.status["claims"][ABSOLUTE_CLAIM]
        self.assertEqual(node["status"], "NEVER_CLAIMABLE")
        self.assertIs(node["allowed_claim"], False)

        ok, reasons = evaluate_claim(self.status, ABSOLUTE_CLAIM)
        self.assertFalse(ok)
        self.assertIn("absolute_or_universal_perfection_is_never_claimable", reasons)

    def test_formal_proof_cannot_be_enabled_without_evidence(self) -> None:
        mutated = copy.deepcopy(self.status)
        mutated["claims"]["formally_proven"]["status"] = "FORMALLY_PROVEN"
        mutated["claims"]["formally_proven"]["allowed_claim"] = True

        ok, reasons = evaluate_claim(mutated, "formally_proven")
        self.assertFalse(ok)
        self.assertEqual(reasons, missing_evidence("formally_proven"))

    def test_external_audit_cannot_be_enabled_without_evidence(self) -> None:
        mutated = copy.deepcopy(self.status)
        mutated["claims"]["externally_audited"]["status"] = "EXTERNALLY_AUDITED"
        mutated["claims"]["externally_audited"]["allowed_claim"] = True

        ok, reasons = evaluate_claim(mutated, "externally_audited")
        self.assertFalse(ok)
        self.assertEqual(reasons, missing_evidence("externally_audited"))

    def test_absolute_perfection_cannot_be_enabled_even_if_mutated(self) -> None:
        mutated = copy.deepcopy(self.status)
        mutated["claims"][ABSOLUTE_CLAIM]["status"] = "ABSOLUTE_PERFECTION"
        mutated["claims"][ABSOLUTE_CLAIM]["allowed_claim"] = True

        ok, reasons = evaluate_claim(mutated, ABSOLUTE_CLAIM)
        self.assertFalse(ok)
        self.assertEqual(reasons, ["absolute_or_universal_perfection_is_never_claimable"])

        valid, errors = validate_assurance_status(mutated)
        self.assertFalse(valid)
        self.assertIn("absolute_universal_perfection_allowed_claim_must_be_false", errors)
        self.assertIn("absolute_universal_perfection_status_must_be_never_claimable", errors)

    def test_required_evidence_lists_are_non_empty_for_promotable_claims(self) -> None:
        for claim in UNCLAIMED_STATUSES:
            self.assertIn(claim, REQUIRED_EVIDENCE)
            self.assertGreater(len(REQUIRED_EVIDENCE[claim]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
