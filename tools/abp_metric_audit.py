#!/usr/bin/env python3
"""
ABP Full Metric Audit

This tool:
- Runs ABP tests repeatedly.
- Measures speed, reproducibility, and test count stability.
- Measures Python allocation peak with tracemalloc.
- Checks layer module/test coverage.
- Checks static safety invariants.
- Checks dirty-tree/no-silent-drift behavior.
- Simulates bounded safe enhancement loops.
- Tests perfection gate positive and negative controls.
- Generates JSON + Markdown reports.
- Optionally updates README.md with a metrics block.

It does not modify src/ or tests/.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import sys
import time
import tracemalloc
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src" / "abp"
TESTS = ROOT / "tests"
REPORTS = ROOT / "reports"

EXPECTED_LAYERS = {
    "Layer 1 Byte Parity": ["src/abp/parity.py", "tests/test_parity.py"],
    "Layer 2 Hash Parity": ["src/abp/hashing.py", "tests/test_hashing.py"],
    "Layer 3 Evidence Parity": ["src/abp/evidence.py", "src/abp/claims.py", "tests/test_evidence_parity.py"],
    "Layer 4 State Parity": ["src/abp/state.py", "tests/test_state_parity.py"],
    "Layer 5 Policy Parity": ["src/abp/policy.py", "tests/test_policy_parity.py"],
    "Layer 6 Authority Parity": ["src/abp/authority.py", "tests/test_authority_parity.py"],
    "Layer 7 Reversibility Parity": ["src/abp/reversibility.py", "tests/test_reversibility_parity.py"],
    "Layer 8 Receipt Parity": ["src/abp/receipts.py", "tests/test_receipt_parity.py"],
    "Layer 9 Calibration Parity": ["src/abp/calibration.py", "tests/test_calibration_parity.py"],
    "Layer 10 Memory Parity": ["src/abp/memory.py", "tests/test_memory_parity.py"],
    "Layer 11 Adversary Parity": ["src/abp/adversary.py", "tests/test_adversary_parity.py"],
    "Layer 12 Metric Parity": ["src/abp/metrics.py", "tests/test_metric_parity.py"],
    "Layer 13 Enhancement Parity": ["src/abp/enhancement.py", "tests/test_enhancement_parity.py"],
    "Layer 14 Perfection Gate": ["src/abp/perfection.py", "tests/test_perfection_gate.py"],
}

FORBIDDEN_IMPORT_ROOTS = {
    "requests",
    "urllib",
    "urllib3",
    "http",
    "httpx",
    "socket",
    "ftplib",
    "smtplib",
    "telnetlib",
    "webbrowser",
}

FORBIDDEN_CALLS = {
    "eval",
    "exec",
    "compile",
}

README_START = "<!-- ABP_METRICS_START -->"
README_END = "<!-- ABP_METRICS_END -->"


def pct(n: float, d: float) -> float:
    return 0.0 if d == 0 else round((n / d) * 100.0, 4)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def sha256_text_file_normalized(path: Path) -> str:
    data = path.read_bytes()
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_bytes(data)


def run_git(args: list[str]) -> str:
    proc = subprocess.run(
        ["git"] + args,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    return proc.stdout


def tracked_files() -> list[str]:
    return [line.strip() for line in run_git(["ls-files"]).splitlines() if line.strip()]


def git_status(paths: list[str] | None = None) -> list[str]:
    args = ["status", "--porcelain"]
    if paths:
        args += ["--"] + paths
    return [line.rstrip() for line in run_git(args).splitlines() if line.strip()]


def count_python_ast(py: Path) -> dict[str, int]:
    text = py.read_text(encoding="utf-8")
    tree = ast.parse(text, filename=str(py))
    functions = 0
    classes = 0
    test_methods = 0
    imports = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            if node.name.startswith("test_"):
                test_methods += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            imports += 1

    return {
        "lines": len(text.splitlines()),
        "functions": functions,
        "classes": classes,
        "test_methods": test_methods,
        "imports": imports,
    }


def static_safety_audit() -> dict[str, Any]:
    findings: list[dict[str, str]] = []

    for path in tracked_files():
        normalized = path.replace("\\", "/")
        if "__pycache__/" in normalized:
            findings.append({"type": "tracked_cache", "path": path})
        if normalized.endswith(".pyc"):
            findings.append({"type": "tracked_pyc", "path": path})
        if ".venv/" in normalized or "node_modules/" in normalized:
            findings.append({"type": "tracked_environment_or_node", "path": path})

    for py in sorted(SRC.glob("*.py")):
        tree = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in FORBIDDEN_IMPORT_ROOTS:
                        findings.append({
                            "type": "forbidden_import",
                            "file": str(py.relative_to(ROOT)),
                            "import": alias.name,
                        })
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                root = mod.split(".")[0]
                if root in FORBIDDEN_IMPORT_ROOTS:
                    findings.append({
                        "type": "forbidden_from_import",
                        "file": str(py.relative_to(ROOT)),
                        "import": mod,
                    })
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    findings.append({
                        "type": "forbidden_call",
                        "file": str(py.relative_to(ROOT)),
                        "call": node.func.id,
                    })

    return {
        "passed": len(findings) == 0,
        "findings": findings,
        "finding_count": len(findings),
    }


def layer_coverage() -> dict[str, Any]:
    rows = []
    passed = 0
    for layer, paths in EXPECTED_LAYERS.items():
        missing = [p for p in paths if not (ROOT / p).exists()]
        ok = not missing
        if ok:
            passed += 1
        rows.append({
            "layer": layer,
            "required_paths": paths,
            "missing": missing,
            "present": ok,
        })
    return {
        "layers_total": len(EXPECTED_LAYERS),
        "layers_present": passed,
        "layer_coverage_percent": pct(passed, len(EXPECTED_LAYERS)),
        "layers": rows,
    }


def code_inventory() -> dict[str, Any]:
    src_files = sorted(SRC.glob("*.py"))
    test_files = sorted(TESTS.glob("test*.py"))

    src_stats = [count_python_ast(p) for p in src_files]
    test_stats = [count_python_ast(p) for p in test_files]

    return {
        "source_python_files": len(src_files),
        "test_python_files": len(test_files),
        "source_lines": sum(s["lines"] for s in src_stats),
        "test_lines": sum(s["lines"] for s in test_stats),
        "source_functions": sum(s["functions"] for s in src_stats),
        "source_classes": sum(s["classes"] for s in src_stats),
        "test_methods_ast": sum(s["test_methods"] for s in test_stats),
        "source_imports": sum(s["imports"] for s in src_stats),
        "test_imports": sum(s["imports"] for s in test_stats),
    }


def run_suite_once(label: str) -> dict[str, Any]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, "run_tests.py"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )
    elapsed = time.perf_counter() - start
    output = (proc.stdout or "") + (proc.stderr or "")

    match = re.search(r"Ran\s+(\d+)\s+tests", output)
    test_count = int(match.group(1)) if match else None

    log_path = REPORTS / f"metric_gauntlet_{label}.txt"
    log_path.write_text(output, encoding="utf-8")

    return {
        "label": label,
        "returncode": proc.returncode,
        "ok": proc.returncode == 0 and "OK" in output,
        "seconds": elapsed,
        "test_count": test_count,
        "output_sha256": sha256_bytes(output.encode("utf-8")),
        "log_path": str(log_path.relative_to(ROOT)),
        "log_sha256": sha256_file(log_path),
    }


def repeated_test_metrics(repeat: int, expected_tests: int) -> dict[str, Any]:
    runs = [run_suite_once(f"local_run_{i}") for i in range(1, repeat + 1)]
    seconds = [r["seconds"] for r in runs]
    ok_count = sum(1 for r in runs if r["ok"])
    total_tests_observed = sum((r["test_count"] or 0) for r in runs)
    expected_total_tests = expected_tests * repeat
    unique_counts = sorted(set(r["test_count"] for r in runs))

    return {
        "repeat": repeat,
        "runs": runs,
        "runs_passed": ok_count,
        "runs_failed": repeat - ok_count,
        "run_pass_rate_percent": pct(ok_count, repeat),
        "expected_tests_per_run": expected_tests,
        "test_counts_observed": unique_counts,
        "total_tests_observed": total_tests_observed,
        "expected_total_tests": expected_total_tests,
        "test_execution_coverage_percent": pct(total_tests_observed, expected_total_tests),
        "mean_seconds": statistics.mean(seconds),
        "median_seconds": statistics.median(seconds),
        "min_seconds": min(seconds),
        "max_seconds": max(seconds),
        "stdev_seconds": statistics.pstdev(seconds) if len(seconds) > 1 else 0.0,
        "tests_per_second_mean": (expected_tests / statistics.mean(seconds)) if statistics.mean(seconds) > 0 else None,
        "all_runs_ok": ok_count == repeat,
        "all_test_counts_match_expected": unique_counts == [expected_tests],
    }


def inprocess_memory_metrics(expected_tests: int) -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    loader = unittest.defaultTestLoader

    tracemalloc.start()
    start = time.perf_counter()

    suite = loader.discover(str(TESTS), pattern="test*.py")
    with open(os.devnull, "w") as stream:
        runner = unittest.TextTestRunner(stream=stream)
        result = runner.run(suite)

    elapsed = time.perf_counter() - start
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_mb = peak / (1024 * 1024)

    return {
        "ok": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "expected_tests": expected_tests,
        "test_count_match": result.testsRun == expected_tests,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "elapsed_seconds": elapsed,
        "tracemalloc_current_mb": current / (1024 * 1024),
        "tracemalloc_peak_mb": peak_mb,
    }


def safe_loop_metrics() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from src.abp.enhancement import (
        create_enhancement_proposal,
        evaluate_enhancement,
        apply_enhancement_simulated,
    )

    events: list[dict[str, Any]] = []
    max_iterations = 3

    for i in range(1, max_iterations + 1):
        proposal = create_enhancement_proposal(
            proposal_id=f"metric-loop-proposal-{i}",
            target_layer="METRIC",
            weakness="simulated_weakness_only",
            evidence_ref=f"metric-loop-evidence-{i}",
            metric_name="no_silent_drift_score",
            expected_delta=0.01,
            control_change="simulated_non_mutating_control_change",
            regression_test=f"simulated_regression_test_{i}",
            rollback_plan="discard_simulated_proposal",
            risk_level="LOW",
            requires_human_approval=False,
            human_approval=False,
            status="PROPOSED",
        )
        verdict = evaluate_enhancement(proposal, regression_passed=True)
        applied = apply_enhancement_simulated(proposal, regression_passed=True)
        events.append({
            "iteration": i,
            "verdict": verdict,
            "applied_status": applied.get("status"),
            "safe": verdict == "ALLOW" and applied.get("status") == "APPLIED",
        })

    unsafe = create_enhancement_proposal(
        proposal_id="metric-unsafe-critical-no-approval",
        target_layer="POLICY",
        weakness="simulated_high_risk_change",
        evidence_ref="metric-loop-negative",
        metric_name="policy_gate_pass_rate",
        expected_delta=0.5,
        control_change="simulated_policy_change",
        regression_test="simulated_policy_regression_test",
        rollback_plan="discard_simulated_change",
        risk_level="CRITICAL",
        requires_human_approval=True,
        human_approval=False,
        status="PROPOSED",
    )
    unsafe_verdict = evaluate_enhancement(unsafe, regression_passed=True)

    failed_regression = create_enhancement_proposal(
        proposal_id="metric-failed-regression",
        target_layer="METRIC",
        weakness="simulated_regression_failure",
        evidence_ref="metric-loop-regression",
        metric_name="abp_score",
        expected_delta=0.01,
        control_change="simulated_control_change",
        regression_test="simulated_regression_test",
        rollback_plan="discard_simulated_change",
        risk_level="LOW",
        requires_human_approval=False,
        human_approval=False,
        status="PROPOSED",
    )
    failed_verdict = evaluate_enhancement(failed_regression, regression_passed=False)

    safe_events = sum(1 for e in events if e["safe"])
    return {
        "max_iterations": max_iterations,
        "safe_iterations_passed": safe_events,
        "safe_iteration_pass_rate_percent": pct(safe_events, max_iterations),
        "unsafe_critical_without_approval_verdict": unsafe_verdict,
        "unsafe_critical_blocked": unsafe_verdict != "ALLOW",
        "failed_regression_verdict": failed_verdict,
        "failed_regression_blocked": failed_verdict == "BLOCK",
        "autonomous_loop_created": False,
        "source_mutation_allowed": False,
        "events": events,
    }


def perfection_gate_metrics() -> dict[str, Any]:
    sys.path.insert(0, str(ROOT))
    from src.abp.perfection import (
        create_perfection_gate_input,
        evaluate_perfection_gate,
        list_perfection_limitations,
    )

    perfect = create_perfection_gate_input(
        all_tests_pass=True,
        adversarial_mutation_catch_rate=1.0,
        unsupported_high_confidence_claim_escape_rate=0.0,
        unreceipted_action_escape_rate=0.0,
        authority_violation_escape_rate=0.0,
        irreversible_action_bypass_rate=0.0,
        silent_state_drift_detected=False,
        reproducibility_runs=3,
        calibration_metrics_recorded=True,
        known_failures=[],
        external_audit_done=False,
        real_world_validation_done=False,
        scope="LOCAL_TEST_SUITE",
    )

    degraded = create_perfection_gate_input(
        all_tests_pass=True,
        adversarial_mutation_catch_rate=0.99,
        unsupported_high_confidence_claim_escape_rate=0.0,
        unreceipted_action_escape_rate=0.0,
        authority_violation_escape_rate=0.0,
        irreversible_action_bypass_rate=0.0,
        silent_state_drift_detected=False,
        reproducibility_runs=3,
        calibration_metrics_recorded=True,
        known_failures=[],
        external_audit_done=False,
        real_world_validation_done=False,
        scope="LOCAL_TEST_SUITE",
    )

    perfect_verdict = evaluate_perfection_gate(perfect)
    degraded_verdict = evaluate_perfection_gate(degraded)

    return {
        "perfect_local_gate_verdict": perfect_verdict,
        "perfect_local_gate_passed": perfect_verdict == "OPERATIONALLY_PERFECT_V0_1",
        "negative_control_verdict": degraded_verdict,
        "negative_control_passed": degraded_verdict == "NOT_YET_PERFECT",
        "limitations": list_perfection_limitations(perfect),
        "claims_absolute_perfection": False,
    }


def baseline_metrics() -> dict[str, Any]:
    baseline = REPORTS / "ABP_BASELINE_V1_2.md"
    scoreboard = REPORTS / "scoreboard.md"

    return {
        "baseline_report_exists": baseline.exists(),
        "baseline_report_sha256_raw": sha256_file(baseline) if baseline.exists() else None,
        "baseline_report_sha256_lf_normalized": sha256_text_file_normalized(baseline) if baseline.exists() else None,
        "scoreboard_exists": scoreboard.exists(),
        "scoreboard_sha256_raw": sha256_file(scoreboard) if scoreboard.exists() else None,
    }


def compute_score(report: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "test_runs": report["tests"]["all_runs_ok"],
        "test_count": report["tests"]["all_test_counts_match_expected"],
        "layer_coverage": report["layers"]["layer_coverage_percent"] == 100.0,
        "static_audit": report["static_audit"]["passed"],
        "memory": report["memory"]["ok"] and report["memory"]["test_count_match"],
        "safe_loop": (
            report["safe_loop"]["safe_iteration_pass_rate_percent"] == 100.0
            and report["safe_loop"]["unsafe_critical_blocked"]
            and report["safe_loop"]["failed_regression_blocked"]
        ),
        "perfection_gate": (
            report["perfection_gate"]["perfect_local_gate_passed"]
            and report["perfection_gate"]["negative_control_passed"]
        ),
        "dirty_tree_src_tests": report["dirty_tree"]["src_tests_dirty_count"] == 0,
        "baseline": report["baseline"]["baseline_report_exists"],
    }
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    return {
        "checks": checks,
        "checks_passed": passed,
        "checks_total": total,
        "score_percent": pct(passed, total),
    }


def markdown_report(report: dict[str, Any]) -> str:
    tests = report["tests"]
    layers = report["layers"]
    inv = report["inventory"]
    mem = report["memory"]
    score = report["score"]
    safe = report["safe_loop"]
    pg = report["perfection_gate"]
    static = report["static_audit"]
    base = report["baseline"]

    lines = [
        "# ABP v1.2 Metrics Audit",
        "",
        f"Generated: `{report['generated_at_utc']}`",
        "",
        "## Executive Status",
        "",
        f"- Overall metric score: **{score['score_percent']}%** ({score['checks_passed']}/{score['checks_total']} gates)",
        f"- Repeated local test runs: **{tests['runs_passed']}/{tests['repeat']} passed** ({tests['run_pass_rate_percent']}%)",
        f"- Test count stability: **{tests['test_counts_observed']}**",
        f"- Total test executions observed: **{tests['total_tests_observed']} / {tests['expected_total_tests']}** ({tests['test_execution_coverage_percent']}%)",
        f"- Layer coverage: **{layers['layers_present']} / {layers['layers_total']}** ({layers['layer_coverage_percent']}%)",
        f"- Static safety audit findings: **{static['finding_count']}**",
        f"- Safe loop simulation pass rate: **{safe['safe_iteration_pass_rate_percent']}%**",
        f"- Perfection gate local verdict: **{pg['perfect_local_gate_verdict']}**",
        f"- Negative control verdict: **{pg['negative_control_verdict']}**",
        "",
        "## Performance",
        "",
        f"- Mean test-suite wall time: **{tests['mean_seconds']:.6f}s**",
        f"- Median test-suite wall time: **{tests['median_seconds']:.6f}s**",
        f"- Min test-suite wall time: **{tests['min_seconds']:.6f}s**",
        f"- Max test-suite wall time: **{tests['max_seconds']:.6f}s**",
        f"- Mean throughput: **{tests['tests_per_second_mean']:.2f} tests/s**",
        f"- In-process tracemalloc peak: **{mem['tracemalloc_peak_mb']:.3f} MB**",
        "",
        "## Inventory",
        "",
        f"- Source Python files: **{inv['source_python_files']}**",
        f"- Test Python files: **{inv['test_python_files']}**",
        f"- Source lines: **{inv['source_lines']}**",
        f"- Test lines: **{inv['test_lines']}**",
        f"- Source functions: **{inv['source_functions']}**",
        f"- Source classes: **{inv['source_classes']}**",
        f"- AST-discovered test methods: **{inv['test_methods_ast']}**",
        "",
        "## Integrity",
        "",
        f"- Baseline report SHA256 raw: `{base['baseline_report_sha256_raw']}`",
        f"- Baseline report SHA256 LF-normalized: `{base['baseline_report_sha256_lf_normalized']}`",
        f"- Scoreboard SHA256 raw: `{base['scoreboard_sha256_raw']}`",
        "",
        "## Limitations",
        "",
        "- This is a local/repo metrics audit, not a formal proof.",
        "- External audit remains separate.",
        "- Real-world validation remains separate.",
        "- Absolute or universal perfection is not claimed.",
        "",
    ]

    return "\n".join(lines)


def readme_block(report: dict[str, Any]) -> str:
    tests = report["tests"]
    layers = report["layers"]
    mem = report["memory"]
    score = report["score"]
    safe = report["safe_loop"]
    pg = report["perfection_gate"]

    return "\n".join([
        README_START,
        "## ABP v1.2 Validation Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Overall metric gate score | {score['score_percent']}% |",
        f"| Layers passed/present | {layers['layers_present']}/{layers['layers_total']} ({layers['layer_coverage_percent']}%) |",
        f"| Repeated local runs passed | {tests['runs_passed']}/{tests['repeat']} ({tests['run_pass_rate_percent']}%) |",
        f"| Test executions observed | {tests['total_tests_observed']}/{tests['expected_total_tests']} ({tests['test_execution_coverage_percent']}%) |",
        f"| Tests per run | {tests['test_counts_observed']} |",
        f"| Mean suite time | {tests['mean_seconds']:.6f}s |",
        f"| Median suite time | {tests['median_seconds']:.6f}s |",
        f"| Mean throughput | {tests['tests_per_second_mean']:.2f} tests/s |",
        f"| Peak traced Python memory | {mem['tracemalloc_peak_mb']:.3f} MB |",
        f"| Safe loop simulation | {safe['safe_iteration_pass_rate_percent']}% |",
        f"| Unsafe critical proposal blocked | {safe['unsafe_critical_blocked']} |",
        f"| Failed regression blocked | {safe['failed_regression_blocked']} |",
        f"| Local perfection-gate verdict | {pg['perfect_local_gate_verdict']} |",
        f"| Negative control verdict | {pg['negative_control_verdict']} |",
        "",
        "**Scope:** local measured tests and CI validation only. ABP does not claim absolute, universal, externally audited, or real-world perfection.",
        README_END,
    ])


def update_readme(report: dict[str, Any]) -> None:
    path = ROOT / "README.md"
    text = path.read_text(encoding="utf-8")
    block = readme_block(report)

    pattern = re.compile(
        re.escape(README_START) + r".*?" + re.escape(README_END),
        flags=re.DOTALL,
    )

    if pattern.search(text):
        text = pattern.sub(block, text)
    else:
        text = text.rstrip() + "\n\n" + block + "\n"

    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=15)
    parser.add_argument("--expected-tests", type=int, default=183)
    parser.add_argument("--update-readme", action="store_true")
    args = parser.parse_args()

    REPORTS.mkdir(exist_ok=True)

    before_src_tests_status = git_status(["src", "tests"])

    report: dict[str, Any] = {
        "name": "ABP Full Metric Audit",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "expected_tests": args.expected_tests,
        "baseline": baseline_metrics(),
        "inventory": code_inventory(),
        "layers": layer_coverage(),
        "static_audit": static_safety_audit(),
        "tests": repeated_test_metrics(args.repeat, args.expected_tests),
        "memory": inprocess_memory_metrics(args.expected_tests),
        "safe_loop": safe_loop_metrics(),
        "perfection_gate": perfection_gate_metrics(),
    }

    after_src_tests_status = git_status(["src", "tests"])
    report["dirty_tree"] = {
        "before_src_tests_status": before_src_tests_status,
        "after_src_tests_status": after_src_tests_status,
        "src_tests_dirty_count": len(after_src_tests_status),
        "src_tests_clean_after_tests": len(after_src_tests_status) == 0,
    }

    report["score"] = compute_score(report)

    json_path = REPORTS / "ABP_LOCAL_METRICS.json"
    md_path = REPORTS / "ABP_LOCAL_METRICS.md"

    json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    md_path.write_text(markdown_report(report), encoding="utf-8")

    if args.update_readme:
        update_readme(report)

    print(markdown_report(report))

    failures = []
    if not report["tests"]["all_runs_ok"]:
        failures.append("repeated tests failed")
    if not report["tests"]["all_test_counts_match_expected"]:
        failures.append("test count mismatch")
    if report["layers"]["layer_coverage_percent"] != 100.0:
        failures.append("layer coverage incomplete")
    if not report["static_audit"]["passed"]:
        failures.append("static audit findings")
    if report["dirty_tree"]["src_tests_dirty_count"] != 0:
        failures.append("src/tests dirty after test run")
    if not report["memory"]["ok"]:
        failures.append("in-process memory test failed")
    if not report["safe_loop"]["unsafe_critical_blocked"]:
        failures.append("unsafe critical proposal not blocked")
    if not report["safe_loop"]["failed_regression_blocked"]:
        failures.append("failed regression not blocked")
    if not report["perfection_gate"]["negative_control_passed"]:
        failures.append("perfection negative control failed")

    if failures:
        print("FAILURES:", failures, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
