# ABP - Agent Byte Parity

ABP is a reference implementation of **Agentic Evidence-Parity Control Theory**: every byte, file, claim, source, state, policy, permission, action, receipt, outcome, and memory update must preserve an explicit parity invariant or fall back to verification, confirmation, rollback, or block.

**Compression:** ControlledParityAcrossAllStateTransitions or NoSilentDrift

## Current validation status

| Track | Result |
|---|---:|
| Core layers implemented | 14/14 |
| Unit tests per run | 183 |
| Local repeated runs | 15/15 (100.0%) |
| Local test executions | 2745/2745 (100.0%) |
| GitHub workflow success | 6/6 (100%) |
| GitHub job pass rate | 30/30 (100%) |
| Metric gauntlet mean suite time | 0.138142 s |
| Mean traced Python peak memory | 0.9494 MB |
| Formal scaffold states checked | 12288 |
| Formal scaffold failures | 0 |
| Real-world scoped actions | 100 |
| Real-world scoped sessions | 10 |
| Real-world critical incidents | 0 |
| Receipt coverage | 100.0% |
| Evidence coverage | 100.0% |

## Honest claim boundary

| Claim | Status |
|---|---:|
| Local operational baseline | VERIFIED_LOCAL_OPERATIONAL_BASELINE |
| GitHub CI validation | GITHUB_FULL_METRIC_VALIDATED |
| Formal proof scaffold | FORMAL_SCAFFOLD_READY |
| Real-world validation | REAL_WORLD_VALIDATED_SCOPE_V0_1 |
| External audit | NOT_AUDITED |
| Formal proof | NOT_PROVEN |
| Absolute / universal perfection | NEVER_CLAIMABLE |

ABP is real-world validated only for the declared private-repo operational scope used in Validation V0.1. It does **not** claim unrestricted real-world safety, external audit, formal proof beyond the scaffold, or absolute/universal perfection.

## Architecture

1. Byte Parity
2. Hash Parity
3. Evidence Parity
4. State Parity
5. Policy Parity
6. Authority Parity
7. Reversibility Parity
8. Receipt Parity
9. Calibration Parity
10. Memory Parity
11. Adversary Parity
12. Metric Parity
13. Enhancement Parity
14. Perfection Gate

## Quick start

- python .\run_tests.py
- python .\tools\abp_metric_audit.py --repeat 15 --expected-tests 183
- python .\tools\abp_assurance_gate.py
- python .\tools\abp_assurance_claim_tests.py
- python .\tools\abp_formal_scaffold_check.py
- python .\tools\abp_real_world_validation.py gate

## Cost control

GitHub Actions workflows in the public release are **manual-only** with workflow_dispatch. Push-triggered and pull-request-triggered workflow runs are disabled to avoid accidental paid CI usage.

## Evidence

Key public evidence files:

- reports/ABP_GITHUB_CI_METRICS.json
- reports/ABP_ASSURANCE_STATUS.json
- evidence/formal_proof/FORMAL_SCAFFOLD_REPORT.md
- evidence/real_world_validation/SUCCESS_FAILURE_METRICS.json
- evidence/real_world_validation/VALIDATION_SUMMARY.md

Raw local run logs and failed-attempt logs are intentionally excluded from the public release.

## License

No open-source license has been selected yet. Until a license is added, all rights are reserved by default.
