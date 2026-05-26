# ABP Formal Scaffold

Status: FORMAL_SCAFFOLD_READY after local and CI scaffold checks pass.

This folder contains a first formal model of ABP's claim-boundary and safety-gate invariants.

This is not a full formal proof yet. It is a scaffold for machine-checkable modeling.

## Files

- ABP.tla: TLA+ model.
- MC_ABP.cfg: model-checker configuration.
- tools/abp_formal_scaffold_check.py: repository-side scaffold verifier.

## Invariants modeled

- Policy BLOCK never allows.
- Unsupported high-confidence claim never allows.
- Conflicted claim requires VERIFY/BLOCK/HALT.
- Contradicted state cannot synthesize as ALLOW.
- Irreversible action without approval never allows.
- Unreceipted action never allows.
- Unsafe enhancement never allows.
- Absolute/universal perfection never allows.

## Honest boundary

This scaffold supports:

- FORMAL_SCAFFOLD_READY
- FORMAL_MODELING_STARTED

It does not support:

- FORMALLY_PROVEN
- UNIVERSALLY_PROVEN
- ABSOLUTE_PERFECTION
