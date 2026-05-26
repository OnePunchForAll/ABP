# ABP Real-World Validation Protocol

## Status

NOT_VALIDATED

## Goal

Validate ABP behavior outside toy/local/CI settings.

## Required deployment evidence

Real-world validation requires operational evidence from a real environment where ABP is used to gate or evaluate agent behavior.

## Minimum evidence

Place evidence here:

```text
evidence/real_world_validation/
```

Expected files:

```text
DEPLOYMENT_CONTEXT.md
OPERATOR_PROTOCOL.md
RUN_LOGS/
INCIDENT_LOG.md
SUCCESS_FAILURE_METRICS.json
VALIDATION_SUMMARY.md
VALIDATION_SUMMARY.sha256.txt
```

## Minimum metrics

Track:

- Number of runs
- Number of actions evaluated
- Number of blocks
- Number of confirms
- Number of verifies
- Number of allowed actions
- Unsupported high-confidence claim escape rate
- Unreceipted action escape rate
- Authority violation escape rate
- Irreversible bypass rate
- Silent drift detection rate
- Human override count
- Incident count
- False positive count
- False negative count

## Acceptance boundary

Real-world validation does not imply universal validity.

It only supports claims within the tested deployment contexts.

## Promotion gate

ABP may only be marked real-world validated when:

```text
deployment context exists
operator protocol exists
run logs exist
incident log exists
success/failure metrics exist
validation summary exists
validation hash exists
```
