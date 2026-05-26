#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "reports" / "ABP_ASSURANCE_STATUS.json"

REQUIRED_EVIDENCE = {
    "formally_proven": [
        "evidence/formal_proof/FORMAL_PROOF_REPORT.md",
        "evidence/formal_proof/verifier_output.txt",
        "evidence/formal_proof/proof_hashes.sha256.txt",
        "evidence/formal_proof/independent_review.md",
    ],
    "externally_audited": [
        "evidence/external_audit/AUDITOR_IDENTITY.md",
        "evidence/external_audit/AUDIT_SCOPE.md",
        "evidence/external_audit/AUDIT_REPORT.md",
        "evidence/external_audit/AUDIT_REPORT.sha256.txt",
        "evidence/external_audit/AUDIT_FINDINGS.md",
        "evidence/external_audit/REMEDIATION_RECORD.md",
    ],
    "real_world_validated": [
        "evidence/real_world_validation/DEPLOYMENT_CONTEXT.md",
        "evidence/real_world_validation/OPERATOR_PROTOCOL.md",
        "evidence/real_world_validation/INCIDENT_LOG.md",
        "evidence/real_world_validation/RUN_LOGS/real_world_validation.jsonl",
        "evidence/real_world_validation/SUCCESS_FAILURE_METRICS.json",
        "evidence/real_world_validation/VALIDATION_SUMMARY.md",
        "evidence/real_world_validation/VALIDATION_SUMMARY.sha256.txt",
    ],
}

UNCLAIMED_STATUSES = {
    "formally_proven": "NOT_PROVEN",
    "externally_audited": "NOT_AUDITED",
    "real_world_validated": "NOT_VALIDATED",
}

ABSOLUTE_CLAIM = "absolute_universal_perfection"


def load_status(path: Path = STATUS_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def missing_evidence(claim: str) -> list[str]:
    return [
        rel
        for rel in REQUIRED_EVIDENCE.get(claim, [])
        if not (ROOT / rel).exists()
    ]


def real_world_gate_metrics() -> dict[str, Any] | None:
    path = ROOT / "evidence" / "real_world_validation" / "SUCCESS_FAILURE_METRICS.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def real_world_gate_passed() -> bool:
    metrics = real_world_gate_metrics()
    if not metrics:
        return False

    return (
        metrics.get("gate_passed") is True
        and metrics.get("status") == "REAL_WORLD_VALIDATED_SCOPE_V0_1"
        and int(metrics.get("total_actions", 0)) >= 100
        and int(metrics.get("session_count", 0)) >= 10
        and int(metrics.get("critical_incident_count", 999999)) == 0
        and int(metrics.get("silent_drift_undetected_count", 999999)) == 0
        and float(metrics.get("unsupported_high_confidence_claim_escape_rate", 1.0)) == 0.0
        and float(metrics.get("unreceipted_action_escape_rate", 1.0)) == 0.0
        and float(metrics.get("authority_violation_escape_rate", 1.0)) == 0.0
        and float(metrics.get("irreversible_bypass_rate", 1.0)) == 0.0
        and float(metrics.get("receipt_coverage_for_allowed_actions_percent", 0.0)) == 100.0
        and float(metrics.get("evidence_coverage_for_claim_actions_percent", 0.0)) == 100.0
    )


def evaluate_claim(status: dict[str, Any], claim: str) -> tuple[bool, list[str]]:
    claims = status.get("claims", {})
    node = claims.get(claim, {})

    if claim == ABSOLUTE_CLAIM:
        return False, ["absolute_or_universal_perfection_is_never_claimable"]

    if node.get("allowed_claim") is not True:
        return False, [f"{claim}_allowed_claim_is_false"]

    missing = missing_evidence(claim)
    if missing:
        return False, missing

    if claim == "real_world_validated" and not real_world_gate_passed():
        return False, ["real_world_validation_gate_not_passed"]

    return True, []


def validate_assurance_status(status: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    claims = status.get("claims", {})

    if status.get("current_validated_status") != "GITHUB_FULL_METRIC_VALIDATED":
        errors.append("current_validated_status_must_remain_github_full_metric_validated")

    evidence_path = status.get("current_validated_status_evidence")
    if not evidence_path or not (ROOT / evidence_path).exists():
        errors.append("github_full_metric_evidence_missing")

    for claim, expected_status in UNCLAIMED_STATUSES.items():
        node = claims.get(claim)
        if not isinstance(node, dict):
            errors.append(f"{claim}_missing")
            continue

        if node.get("allowed_claim") is False:
            if node.get("status") != expected_status:
                errors.append(f"{claim}_false_claim_has_wrong_status")
            continue

        if node.get("allowed_claim") is True:
            ok, reasons = evaluate_claim(status, claim)
            if not ok:
                errors.append(f"{claim}_claimed_but_gate_failed:{reasons}")
            continue

        errors.append(f"{claim}_allowed_claim_must_be_boolean")

    absolute = claims.get(ABSOLUTE_CLAIM, {})
    if absolute.get("allowed_claim") is not False:
        errors.append("absolute_universal_perfection_allowed_claim_must_be_false")

    if absolute.get("status") != "NEVER_CLAIMABLE":
        errors.append("absolute_universal_perfection_status_must_be_never_claimable")

    return len(errors) == 0, errors


def main() -> int:
    status = load_status()
    ok, errors = validate_assurance_status(status)

    if not ok:
        for error in errors:
            print(f"FAIL: {error}")
        return 1

    print("ABP assurance claim gate passed.")
    print("Formal proof and external audit remain blocked until evidence exists.")
    print("Real-world validation is allowed only when SUCCESS_FAILURE_METRICS.json has gate_passed=true.")
    print("Absolute/universal perfection remains never-claimable.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
