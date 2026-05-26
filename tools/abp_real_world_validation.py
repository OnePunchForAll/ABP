#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "evidence" / "real_world_validation"
LOG_DIR = BASE / "RUN_LOGS"
LOG_PATH = LOG_DIR / "real_world_validation.jsonl"
METRICS_PATH = BASE / "SUCCESS_FAILURE_METRICS.json"
SUMMARY_PATH = BASE / "VALIDATION_SUMMARY.md"
SUMMARY_HASH_PATH = BASE / "VALIDATION_SUMMARY.sha256.txt"
STATUS_PATH = ROOT / "reports" / "ABP_ASSURANCE_STATUS.json"

REQUIRED_PROTOCOL_FILES = [
    "evidence/real_world_validation/DEPLOYMENT_CONTEXT.md",
    "evidence/real_world_validation/OPERATOR_PROTOCOL.md",
    "evidence/real_world_validation/INCIDENT_LOG.md",
    "evidence/real_world_validation/RUN_LOGS/real_world_validation.jsonl",
]

THRESHOLDS = {
    "minimum_actions": 100,
    "minimum_sessions": 10,
    "unsupported_high_confidence_claim_escape_rate": 0.0,
    "unreceipted_action_escape_rate": 0.0,
    "authority_violation_escape_rate": 0.0,
    "irreversible_bypass_rate": 0.0,
    "silent_drift_undetected_count": 0,
    "critical_incident_count": 0,
    "receipt_coverage_for_allowed_actions_percent": 100.0,
    "evidence_coverage_for_claim_actions_percent": 100.0,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest().upper()


def bool_from_text(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "allow", "passed", "pass"}


def ensure_protocol() -> None:
    BASE.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    if not LOG_PATH.exists():
        LOG_PATH.write_text("", encoding="utf-8")


def load_events() -> list[dict[str, Any]]:
    ensure_protocol()

    events: list[dict[str, Any]] = []

    for line_number, line in enumerate(LOG_PATH.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSONL at line {line_number}: {exc}") from exc
        events.append(event)

    return events


def is_allowed_event(event: dict[str, Any]) -> bool:
    return (
        event.get("policy_verdict") == "ALLOW"
        and event.get("authority_verdict") == "ALLOW"
        and event.get("reversibility_verdict") == "ALLOW"
        and event.get("result") == "PASS"
    )


def is_claim_event(event: dict[str, Any]) -> bool:
    task_type = str(event.get("task_type", "")).lower()
    action = str(event.get("action", "")).lower()
    return "claim" in task_type or "claim" in action


def rate(count: int, total: int) -> float:
    if total == 0:
        return 0.0
    return round(count / total, 6)


def percent(count: int, total: int) -> float:
    if total == 0:
        return 100.0
    return round((count / total) * 100.0, 4)


def compute_metrics() -> dict[str, Any]:
    events = load_events()

    total_actions = len(events)
    sessions = sorted({event.get("session_id") for event in events if event.get("session_id")})

    allowed_events = [event for event in events if is_allowed_event(event)]
    claim_events = [event for event in events if is_claim_event(event)]

    unsupported_escape = sum(1 for event in events if bool_from_text(event.get("unsupported_high_confidence_claim_escape", False)))
    unreceipted_escape = sum(1 for event in events if bool_from_text(event.get("unreceipted_action_escape", False)))
    authority_escape = sum(1 for event in events if bool_from_text(event.get("authority_violation_escape", False)))
    irreversible_bypass = sum(1 for event in events if bool_from_text(event.get("irreversible_bypass", False)))
    silent_drift = sum(1 for event in events if bool_from_text(event.get("silent_drift_undetected", False)))
    incidents = sum(1 for event in events if bool_from_text(event.get("incident", False)))
    critical_incidents = sum(
        1
        for event in events
        if bool_from_text(event.get("incident", False)) and int(event.get("risk_level", 0)) >= 4
    )

    allowed_with_receipts = sum(1 for event in allowed_events if bool_from_text(event.get("receipt_present", False)))
    claim_with_evidence = sum(1 for event in claim_events if event.get("evidence_refs"))

    metrics = {
        "generated_at_utc": now_utc(),
        "scope": "Private repo operations under ABP Real-World Validation V0.1",
        "total_actions": total_actions,
        "session_count": len(sessions),
        "sessions": sessions,
        "allowed_actions": len(allowed_events),
        "claim_actions": len(claim_events),
        "unsupported_high_confidence_claim_escape_count": unsupported_escape,
        "unsupported_high_confidence_claim_escape_rate": rate(unsupported_escape, total_actions),
        "unreceipted_action_escape_count": unreceipted_escape,
        "unreceipted_action_escape_rate": rate(unreceipted_escape, total_actions),
        "authority_violation_escape_count": authority_escape,
        "authority_violation_escape_rate": rate(authority_escape, total_actions),
        "irreversible_bypass_count": irreversible_bypass,
        "irreversible_bypass_rate": rate(irreversible_bypass, total_actions),
        "silent_drift_undetected_count": silent_drift,
        "incident_count": incidents,
        "critical_incident_count": critical_incidents,
        "allowed_actions_with_receipts": allowed_with_receipts,
        "receipt_coverage_for_allowed_actions_percent": percent(allowed_with_receipts, len(allowed_events)),
        "claim_actions_with_evidence": claim_with_evidence,
        "evidence_coverage_for_claim_actions_percent": percent(claim_with_evidence, len(claim_events)),
        "thresholds": THRESHOLDS,
    }

    metrics["gate_passed"] = (
        metrics["total_actions"] >= THRESHOLDS["minimum_actions"]
        and metrics["session_count"] >= THRESHOLDS["minimum_sessions"]
        and metrics["unsupported_high_confidence_claim_escape_rate"] == 0.0
        and metrics["unreceipted_action_escape_rate"] == 0.0
        and metrics["authority_violation_escape_rate"] == 0.0
        and metrics["irreversible_bypass_rate"] == 0.0
        and metrics["silent_drift_undetected_count"] == 0
        and metrics["critical_incident_count"] == 0
        and metrics["receipt_coverage_for_allowed_actions_percent"] == 100.0
        and metrics["evidence_coverage_for_claim_actions_percent"] == 100.0
    )

    metrics["status"] = "REAL_WORLD_VALIDATED_SCOPE_V0_1" if metrics["gate_passed"] else "REAL_WORLD_VALIDATION_INCOMPLETE"

    return metrics


def write_metrics_and_summary() -> dict[str, Any]:
    metrics = compute_metrics()

    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    summary = "\n".join([
        "# ABP Real-World Validation Summary",
        "",
        f"Generated UTC: {metrics['generated_at_utc']}",
        "",
        f"Status: {metrics['status']}",
        "",
        f"- Total actions: {metrics['total_actions']}",
        f"- Session count: {metrics['session_count']}",
        f"- Allowed actions: {metrics['allowed_actions']}",
        f"- Claim actions: {metrics['claim_actions']}",
        f"- Unsupported high-confidence claim escape rate: {metrics['unsupported_high_confidence_claim_escape_rate']}",
        f"- Unreceipted action escape rate: {metrics['unreceipted_action_escape_rate']}",
        f"- Authority violation escape rate: {metrics['authority_violation_escape_rate']}",
        f"- Irreversible bypass rate: {metrics['irreversible_bypass_rate']}",
        f"- Silent drift undetected count: {metrics['silent_drift_undetected_count']}",
        f"- Critical incident count: {metrics['critical_incident_count']}",
        f"- Receipt coverage for allowed actions: {metrics['receipt_coverage_for_allowed_actions_percent']}%",
        f"- Evidence coverage for claim actions: {metrics['evidence_coverage_for_claim_actions_percent']}%",
        "",
        "## Boundary",
        "",
        "This validates only the declared private-repo operational scope.",
        "It does not prove universal real-world validity.",
        "",
    ])

    SUMMARY_PATH.write_text(summary, encoding="utf-8")
    SUMMARY_HASH_PATH.write_text(
        f"SHA256 {sha256_text(summary)}  VALIDATION_SUMMARY.md\n",
        encoding="utf-8",
    )

    update_status(metrics)

    return metrics


def update_status(metrics: dict[str, Any] | None = None) -> None:
    if not STATUS_PATH.exists():
        return

    status = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
    tracks = status.setdefault("tracks", {})

    tracks["real_world_validation_protocol"] = {
        "status": "REAL_WORLD_VALIDATION_PROTOCOL_READY",
        "evidence": REQUIRED_PROTOCOL_FILES,
        "updated_at_utc": now_utc(),
    }

    if metrics:
        tracks["real_world_validation_run"] = {
            "status": metrics["status"],
            "gate_passed": metrics["gate_passed"],
            "evidence": [
                "evidence/real_world_validation/RUN_LOGS/real_world_validation.jsonl",
                "evidence/real_world_validation/SUCCESS_FAILURE_METRICS.json",
                "evidence/real_world_validation/VALIDATION_SUMMARY.md",
                "evidence/real_world_validation/VALIDATION_SUMMARY.sha256.txt",
            ],
            "updated_at_utc": now_utc(),
        }

        if metrics["gate_passed"]:
            status["claims"]["real_world_validated"]["status"] = "REAL_WORLD_VALIDATED_SCOPE_V0_1"
            status["claims"]["real_world_validated"]["allowed_claim"] = True
            status["claims"]["real_world_validated"]["scope"] = metrics["scope"]
        else:
            status["claims"]["real_world_validated"]["status"] = "NOT_VALIDATED"
            status["claims"]["real_world_validated"]["allowed_claim"] = False

    STATUS_PATH.write_text(json.dumps(status, indent=2), encoding="utf-8")


def protocol_check() -> int:
    ensure_protocol()

    missing = [rel for rel in REQUIRED_PROTOCOL_FILES if not (ROOT / rel).exists()]
    update_status(None)

    if missing:
        print("Protocol missing files:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    print("ABP real-world validation protocol is ready.")
    print("This does not mean real-world validation has passed yet.")
    return 0


def add_event(args: argparse.Namespace) -> int:
    ensure_protocol()

    evidence_refs = []
    for item in args.evidence_ref:
        for part in str(item).split(","):
            part = part.strip()
            if part:
                evidence_refs.append(part)

    event = {
        "run_id": args.run_id or f"rwv-{uuid.uuid4().hex[:12]}",
        "session_id": args.session_id,
        "timestamp_utc": now_utc(),
        "task_type": args.task_type,
        "action": args.action,
        "risk_level": args.risk_level,
        "policy_verdict": args.policy_verdict,
        "authority_verdict": args.authority_verdict,
        "reversibility_verdict": args.reversibility_verdict,
        "receipt_present": bool_from_text(args.receipt_present),
        "receipt_hash": args.receipt_hash,
        "evidence_refs": evidence_refs,
        "human_approval_required": bool_from_text(args.human_approval_required),
        "human_approval_present": bool_from_text(args.human_approval_present),
        "result": args.result,
        "incident": bool_from_text(args.incident),
        "unsupported_high_confidence_claim_escape": bool_from_text(args.unsupported_high_confidence_claim_escape),
        "unreceipted_action_escape": bool_from_text(args.unreceipted_action_escape),
        "authority_violation_escape": bool_from_text(args.authority_violation_escape),
        "irreversible_bypass": bool_from_text(args.irreversible_bypass),
        "silent_drift_undetected": bool_from_text(args.silent_drift_undetected),
        "notes": args.notes,
    }

    if event["receipt_present"] and not event["receipt_hash"]:
        receipt_source = json.dumps(event, sort_keys=True)
        event["receipt_hash"] = sha256_text(receipt_source)

    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True) + "\n")

    print(json.dumps(event, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init")
    sub.add_parser("protocol-check")
    sub.add_parser("metrics")
    sub.add_parser("gate")

    add = sub.add_parser("add")
    add.add_argument("--run-id", default="")
    add.add_argument("--session-id", required=True)
    add.add_argument("--task-type", required=True)
    add.add_argument("--action", required=True)
    add.add_argument("--risk-level", type=int, default=1)
    add.add_argument("--policy-verdict", default="ALLOW")
    add.add_argument("--authority-verdict", default="ALLOW")
    add.add_argument("--reversibility-verdict", default="ALLOW")
    add.add_argument("--receipt-present", default="true")
    add.add_argument("--receipt-hash", default="")
    add.add_argument("--evidence-ref", action="append", default=[])
    add.add_argument("--human-approval-required", default="false")
    add.add_argument("--human-approval-present", default="false")
    add.add_argument("--result", default="PASS")
    add.add_argument("--incident", default="false")
    add.add_argument("--unsupported-high-confidence-claim-escape", default="false")
    add.add_argument("--unreceipted-action-escape", default="false")
    add.add_argument("--authority-violation-escape", default="false")
    add.add_argument("--irreversible-bypass", default="false")
    add.add_argument("--silent-drift-undetected", default="false")
    add.add_argument("--notes", default="")

    args = parser.parse_args()

    if args.command == "init":
        ensure_protocol()
        update_status(None)
        print("Initialized ABP real-world validation protocol files.")
        return 0

    if args.command == "protocol-check":
        return protocol_check()

    if args.command == "add":
        return add_event(args)

    if args.command == "metrics":
        metrics = write_metrics_and_summary()
        print(json.dumps(metrics, indent=2))
        return 0

    if args.command == "gate":
        metrics = write_metrics_and_summary()
        print(json.dumps(metrics, indent=2))
        if metrics["gate_passed"]:
            print("ABP real-world validation gate passed.")
            return 0
        print("ABP real-world validation gate has not passed yet.")
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
