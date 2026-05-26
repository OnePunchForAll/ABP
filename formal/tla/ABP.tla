---- MODULE ABP ----
EXTENDS Naturals, Sequences, TLC

CONSTANTS
    ALLOW,
    BLOCK,
    VERIFY,
    CONFIRM,
    HALT,
    VERIFIED,
    UNSUPPORTED,
    CONFLICTED,
    HIGH,
    LOW

VARIABLES
    policy,
    claimStatus,
    confidence,
    contradictionActive,
    synthesisRequested,
    irreversible,
    approval,
    receipt,
    enhancementHasEvidence,
    enhancementHasRegression,
    enhancementHasRollback,
    absoluteClaim,
    verdict

TypeOK ==
    /\ policy \in {ALLOW, BLOCK, VERIFY, CONFIRM}
    /\ claimStatus \in {VERIFIED, UNSUPPORTED, CONFLICTED}
    /\ confidence \in {HIGH, LOW}
    /\ contradictionActive \in BOOLEAN
    /\ synthesisRequested \in BOOLEAN
    /\ irreversible \in BOOLEAN
    /\ approval \in BOOLEAN
    /\ receipt \in BOOLEAN
    /\ enhancementHasEvidence \in BOOLEAN
    /\ enhancementHasRegression \in BOOLEAN
    /\ enhancementHasRollback \in BOOLEAN
    /\ absoluteClaim \in BOOLEAN
    /\ verdict \in {ALLOW, BLOCK, VERIFY, CONFIRM, HALT}

Init ==
    /\ policy \in {ALLOW, BLOCK, VERIFY, CONFIRM}
    /\ claimStatus \in {VERIFIED, UNSUPPORTED, CONFLICTED}
    /\ confidence \in {HIGH, LOW}
    /\ contradictionActive \in BOOLEAN
    /\ synthesisRequested \in BOOLEAN
    /\ irreversible \in BOOLEAN
    /\ approval \in BOOLEAN
    /\ receipt \in BOOLEAN
    /\ enhancementHasEvidence \in BOOLEAN
    /\ enhancementHasRegression \in BOOLEAN
    /\ enhancementHasRollback \in BOOLEAN
    /\ absoluteClaim \in BOOLEAN
    /\ verdict = HALT

ComputeVerdict(v) ==
    IF absoluteClaim THEN BLOCK
    ELSE IF policy = BLOCK THEN BLOCK
    ELSE IF claimStatus = UNSUPPORTED /\ confidence = HIGH THEN BLOCK
    ELSE IF claimStatus = CONFLICTED THEN VERIFY
    ELSE IF contradictionActive /\ synthesisRequested THEN BLOCK
    ELSE IF irreversible /\ ~approval THEN CONFIRM
    ELSE IF ~receipt THEN BLOCK
    ELSE IF ~(enhancementHasEvidence /\ enhancementHasRegression /\ enhancementHasRollback) THEN BLOCK
    ELSE ALLOW

Next ==
    /\ verdict' = ComputeVerdict(verdict)
    /\ UNCHANGED <<
        policy,
        claimStatus,
        confidence,
        contradictionActive,
        synthesisRequested,
        irreversible,
        approval,
        receipt,
        enhancementHasEvidence,
        enhancementHasRegression,
        enhancementHasRollback,
        absoluteClaim
    >>

PolicyBlockNeverAllows ==
    policy = BLOCK => verdict # ALLOW

UnsupportedHighConfidenceNeverAllows ==
    claimStatus = UNSUPPORTED /\ confidence = HIGH => verdict # ALLOW

ConflictedClaimRequiresVerifyOrBlock ==
    claimStatus = CONFLICTED => verdict \in {VERIFY, BLOCK, HALT}

ContradictedStateCannotSynthesizeAllow ==
    contradictionActive /\ synthesisRequested => verdict # ALLOW

IrreversibleWithoutApprovalNeverAllows ==
    irreversible /\ ~approval => verdict # ALLOW

UnreceiptedActionNeverAllows ==
    ~receipt => verdict # ALLOW

UnsafeEnhancementNeverAllows ==
    ~(enhancementHasEvidence /\ enhancementHasRegression /\ enhancementHasRollback) => verdict # ALLOW

AbsoluteUniversalPerfectionNeverAllows ==
    absoluteClaim => verdict # ALLOW

Spec == Init /\ [][Next]_<<
    policy,
    claimStatus,
    confidence,
    contradictionActive,
    synthesisRequested,
    irreversible,
    approval,
    receipt,
    enhancementHasEvidence,
    enhancementHasRegression,
    enhancementHasRollback,
    absoluteClaim,
    verdict
>>

====
