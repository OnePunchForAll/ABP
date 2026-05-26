#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TLA = ROOT / "formal" / "tla" / "ABP.tla"
CFG = ROOT / "formal" / "tla" / "MC_ABP.cfg"
EVIDENCE = ROOT / "evidence" / "formal_proof"
STATUS = ROOT / "reports" / "ABP_ASSURANCE_STATUS.json"

INVARIANTS = [
    "TypeOK",
    "PolicyBlockNeverAllows",
    "UnsupportedHighConfidenceNeverAllows",
    "ConflictedClaimRequiresVerifyOrBlock",
    "ContradictedStateCannotSynthesizeAllow",
    "IrreversibleWithoutApprovalNeverAllows",
    "UnreceiptedActionNeverAllows",
    "UnsafeEnhancementNeverAllows",
    "AbsoluteUniversalPerfectionNeverAllows",
]

CLAIM_STATUSES = ["VERIFIED", "UNSUPPORTED", "CONFLICTED"]
CONFIDENCES = ["HIGH", "LOW"]
POLICIES = ["ALLOW", "BLOCK", "VERIFY", "CONFIRM"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def compute_verdict(state: dict[str, Any]) -> str:
    if state["absolute_claim"]:
        return "BLOCK"
    if state["policy"] == "BLOCK":
        return "BLOCK"
    if state["claim_status"] == "UNSUPPORTED" and state["confidence"] == "HIGH":
        return "BLOCK"
    if state["claim_status"] == "CONFLICTED":
        return "VERIFY"
    if state["contradiction_active"] and state["synthesis_requested"]:
        return "BLOCK"
    if state["irreversible"] and not state["approval"]:
        return "CONFIRM"
    if not state["receipt"]:
        return "BLOCK"
    if not (
        state["enhancement_has_evidence"]
        and state["enhancement_has_regression"]
        and state["enhancement_has_rollback"]
    ):
        return "BLOCK"
    return "ALLOW"


def enumerate_states() -> list[dict[str, Any]]:
    states: list[dict[str, Any]] = []

    for (
        policy,
        claim_status,
        confidence,
        contradiction_active,
        synthesis_requested,
        irreversible,
        approval,
        receipt,
        enhancement_has_evidence,
        enhancement_has_regression,
        enhancement_has_rollback,
        absolute_claim,
    ) in itertools.product(
        POLICIES,
        CLAIM_STATUSES,
        CONFIDENCES,
        [False, True],
        [False, True],
        [False, True],
        [False, True],
        [False, True],
        [False, True],
        [False, True],
        [False, True],
        [False, True],
    ):
        state = {
            "policy": policy,
            "claim_status": claim_status,
            "confidence": confidence,
            "contradiction_active": contradiction_active,
            "synthesis_requested": synthesis_requested,
            "irreversible": irreversible,
            "approval": approval,
            "receipt": receipt,
            "enhancement_has_evidence": enhancement_has_evidence,
            "enhancement_has_regression": enhancement_has_regression,
            "enhancement_has_rollback": enhancement_has_rollback,
            "absolute_claim": absolute_claim,
        }
        state["verdict"] = compute_verdict(state)
        states.append(state)

    return states


def check_bounded_model() -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    states = enumerate_states()

    for state in states:
        verdict = state["verdict"]

        checks = {
            "PolicyBlockNeverAllows": not (state["policy"] == "BLOCK" and verdict == "ALLOW"),
            "UnsupportedHighConfidenceNeverAllows": not (
                state["claim_status"] == "UNSUPPORTED"
                and state["confidence"] == "HIGH"
                and verdict == "ALLOW"
            ),
            "ConflictedClaimRequiresVerifyOrBlock": not (
                state["claim_status"] == "CONFLICTED"
                and verdict not in {"VERIFY", "BLOCK", "HALT"}
            ),
            "ContradictedStateCannotSynthesizeAllow": not (
                state["contradiction_active"]
                and state["synthesis_requested"]
                and verdict == "ALLOW"
            ),
            "IrreversibleWithoutApprovalNeverAllows": not (
                state["irreversible"]
                and not state["approval"]
                and verdict == "ALLOW"
            ),
            "UnreceiptedActionNeverAllows": not (
                not state["receipt"]
                and verdict == "ALLOW"
            ),
            "UnsafeEnhancementNeverAllows": not (
                not (
                    state["enhancement_has_evidence"]
                    and state["enhancement_has_regression"]
                    and state["enhancement_has_rollback"]
                )
                and verdict == "ALLOW"
            ),
            "AbsoluteUniversalPerfectionNeverAllows": not (
                state["absolute_claim"]
                and verdict == "ALLOW"
            ),
        }

        for name, ok in checks.items():
            if not ok:
                failures.append({"invariant": name, "state": state})

    return {
        "states_checked": len(states),
        "failures": failures,
        "passed": len(failures) == 0,
    }


def update_assurance_status(result: dict[str, Any]) -> None:
    if not STATUS.exists():
        return

    status = json.loads(STATUS.read_text(encoding="utf-8"))
    tracks = status.setdefault("tracks", {})

    scaffold_passed = bool(result.get("passed", False))

    tracks["formal_scaffold"] = {
        "status": "FORMAL_SCAFFOLD_READY" if scaffold_passed else "FORMAL_SCAFFOLD_FAILED",
        "allowed_formal_proof_claim": False,
        "evidence": [
            "formal/tla/ABP.tla",
            "formal/tla/MC_ABP.cfg",
            "evidence/formal_proof/FORMAL_SCAFFOLD_REPORT.md",
            "evidence/formal_proof/formal_scaffold_result.json",
            "evidence/formal_proof/formal_scaffold_verifier_output.txt",
            "evidence/formal_proof/formal_scaffold_hashes.sha256.txt",
        ],
        "boundary": "This is a formal scaffold and bounded model sanity check, not a completed formal proof.",
        "updated_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    status["claims"]["formally_proven"]["status"] = "NOT_PROVEN"
    status["claims"]["formally_proven"]["allowed_claim"] = False

    STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")


def main() -> int:
    EVIDENCE.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    if not TLA.exists():
        errors.append("formal/tla/ABP.tla is missing")
    if not CFG.exists():
        errors.append("formal/tla/MC_ABP.cfg is missing")

    tla_text = TLA.read_text(encoding="utf-8") if TLA.exists() else ""
    cfg_text = CFG.read_text(encoding="utf-8") if CFG.exists() else ""

    for invariant in INVARIANTS:
        if invariant not in tla_text:
            errors.append(f"{invariant} missing from ABP.tla")
        if invariant not in cfg_text:
            errors.append(f"{invariant} missing from MC_ABP.cfg")

    bounded = check_bounded_model()
    passed = (not errors) and bounded["passed"]

    result = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "FORMAL_SCAFFOLD_READY" if passed else "FORMAL_SCAFFOLD_FAILED",
        "passed": passed,
        "claim_formally_proven": False,
        "tla_exists": TLA.exists(),
        "cfg_exists": CFG.exists(),
        "invariants_required": INVARIANTS,
        "errors": errors,
        "bounded_model": bounded,
        "boundary": "Scaffold and bounded model sanity check only; not a complete formal proof.",
    }

    (EVIDENCE / "formal_scaffold_result.json").write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    report = "\n".join([
        "# ABP Formal Scaffold Report",
        "",
        f"Generated UTC: {result['generated_at_utc']}",
        "",
        f"Status: {result['status']}",
        "",
        "## Boundary",
        "",
        "This is a formal scaffold and bounded model sanity check.",
        "",
        "It does not make ABP formally proven.",
        "",
        "## Bounded model result",
        "",
        f"- States checked: {bounded['states_checked']}",
        f"- Failures: {len(bounded['failures'])}",
        f"- Passed: {bounded['passed']}",
        "",
        "## Invariants",
        "",
        *[f"- {name}" for name in INVARIANTS],
        "",
    ])

    (EVIDENCE / "FORMAL_SCAFFOLD_REPORT.md").write_text(report, encoding="utf-8")

    verifier_output = "\n".join([
        "ABP formal scaffold checker",
        f"status={result['status']}",
        f"passed={result['passed']}",
        f"states_checked={bounded['states_checked']}",
        f"failures={len(bounded['failures'])}",
        f"bounded_model_passed={bounded['passed']}",
        "claim_formally_proven=False",
    ])

    (EVIDENCE / "formal_scaffold_verifier_output.txt").write_text(
        verifier_output + "\n",
        encoding="utf-8",
    )

    hash_targets = [
        TLA,
        CFG,
        EVIDENCE / "formal_scaffold_result.json",
        EVIDENCE / "FORMAL_SCAFFOLD_REPORT.md",
        EVIDENCE / "formal_scaffold_verifier_output.txt",
    ]

    hashes = [
        f"SHA256 {sha256_file(path)}  {path.relative_to(ROOT).as_posix()}"
        for path in hash_targets
        if path.exists()
    ]

    (EVIDENCE / "formal_scaffold_hashes.sha256.txt").write_text(
        "\n".join(hashes) + "\n",
        encoding="utf-8",
    )

    update_assurance_status(result)

    print(report)

    if not passed:
        print("Formal scaffold check failed.")
        if errors:
            print("Errors:")
            for error in errors:
                print(f"- {error}")
        return 1

    print("ABP formal scaffold check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
