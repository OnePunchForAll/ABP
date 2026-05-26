# Deployment Context

Status: TEMPLATE_READY

## Scope

Private repo operations, file edits, GitHub workflow validation, evidence reports, and agent-safety decision logging under strict mode.

## Environment

- Repository: OnePunchForAll/ABP
- Mode: strict
- Network: GitHub operations only when explicitly approved
- Mutation: source/test mutation only through explicit user-approved commits
- Autonomous loops: blocked except bounded non-mutating simulation

## Validation target

Collect at least 100 real actions across at least 10 sessions.

## Boundary

This validation scope does not prove universal real-world safety.
