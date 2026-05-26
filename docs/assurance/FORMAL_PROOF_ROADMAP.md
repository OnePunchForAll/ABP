# ABP Formal Proof Roadmap

## Status

NOT_PROVEN

## Goal

Convert ABP from tested reference implementation into a machine-checkable formal system.

## Candidate proof target

Any of these may be acceptable:

- Lean
- Coq
- Isabelle/HOL
- Dafny
- TLA+
- Alloy, for bounded model checking only

## Minimum formal objects

### State

A formal representation of:

- Byte
- Hash
- Claim
- Evidence
- State
- Policy
- Authority
- Reversibility
- Receipt
- Prediction
- Memory
- Adversary
- Metric
- Enhancement
- PerfectionGate

### Transition

A formal state transition relation:

```text
Transition : State -> Action -> Verdict -> State
```

### Invariant

The central ABP invariant:

```text
NoSilentDrift:
Every accepted state transition is either parity-preserving, evidence-recorded, reversible, authorized, receipted, and policy-allowed, or else the system halts, verifies, confirms, or blocks.
```

### Theorem candidates

```text
Theorem 1:
For every action with policy BLOCK, ABP cannot produce ALLOW.

Theorem 2:
For every irreversible action without required approval, ABP cannot produce ALLOW.

Theorem 3:
For every unsupported high-confidence claim, ABP cannot produce VERIFIED.

Theorem 4:
For every contradicted active state, ABP cannot synthesize.

Theorem 5:
For every valid receipt, tampering changes its hash.

Theorem 6:
For every accepted enhancement proposal, evidence, regression test, rollback plan, and risk gates are satisfied.

Theorem 7:
Absolute perfection is not derivable from local operational perfection.
```

## Required proof artifacts

Place final artifacts here:

```text
evidence/formal_proof/
```

Expected files:

```text
spec/
theorems/
verifier_output.txt
proof_hashes.sha256.txt
independent_review.md
FORMAL_PROOF_REPORT.md
```

## Promotion gate

ABP may only be marked formally proven when:

```text
FORMAL_PROOF_REPORT.md exists
verifier_output.txt exists
proof_hashes.sha256.txt exists
independent_review.md exists
the proof checker exits successfully
the proof scope is explicitly stated
```

## Boundary

Passing tests is not formal proof. GitHub CI validation is strong engineering evidence, but it is not mathematical proof.
