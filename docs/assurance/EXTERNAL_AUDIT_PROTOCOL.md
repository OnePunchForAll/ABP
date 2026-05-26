# ABP External Audit Protocol

## Status

NOT_AUDITED

## Goal

Obtain independent third-party review of ABP's claims, implementation, tests, workflows, metrics, and boundaries.

## Auditor requirements

The auditor must be independent from the original implementation.

The audit report should include:

- Auditor name or organization
- Date
- Scope
- Methods
- Files reviewed
- Tests reproduced
- Findings
- Severity ratings
- Recommendations
- Reproduction instructions
- Final verdict
- Signature, publication URL, or equivalent attestation
- Report SHA256 hash

## Minimum audit scope

The audit should cover:

- Source code
- Tests
- CI workflows
- Local metric audit
- GitHub metric collector
- Assurance status file
- Claim boundaries
- Absolute perfection denial
- Safe loop simulation
- Evidence handling
- Failure modes

## Required evidence location

```text
evidence/external_audit/
```

Expected files:

```text
AUDITOR_IDENTITY.md
AUDIT_SCOPE.md
AUDIT_REPORT.md
AUDIT_REPORT.sha256.txt
AUDIT_FINDINGS.md
REMEDIATION_RECORD.md
```

## Promotion gate

ABP may only be marked externally audited when all required files exist and the audit report is independent.

## Boundary

Internal CI, self-review, and ChatGPT review do not count as an external audit.
