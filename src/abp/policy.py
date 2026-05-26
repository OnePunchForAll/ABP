VALID_CLAIM_STATUS = {"FACT", "INFERENCE", "ASSUMPTION", "UNKNOWN", "CONFLICTED", "UNSUPPORTED", "FORBIDDEN"}
VALID_CONFIDENCE = {"VERIFIED", "STRONG", "TENTATIVE", "UNKNOWN"}
VALID_BLAST_RADIUS = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}

BLAST_RADIUS_LEVELS = {
    "NONE": 0,
    "LOW": 1,
    "MEDIUM": 2,
    "HIGH": 3,
    "CRITICAL": 4
}

def create_policy(allowed_actions: set, forbidden_actions: set, requires_approval: set,
                  max_autonomy_level: int, max_blast_radius: str, allowed_scopes: set,
                  fail_closed: bool = True) -> dict:
    return {
        "allowed_actions": allowed_actions,
        "forbidden_actions": forbidden_actions,
        "requires_approval": requires_approval,
        "max_autonomy_level": max_autonomy_level,
        "max_blast_radius": max_blast_radius,
        "allowed_scopes": allowed_scopes,
        "fail_closed": fail_closed
    }

def create_action_request(action_id: str, action_type: str, claim_status: str,
                          confidence: str, scope: str, autonomy_level: int,
                          blast_radius: str, irreversible: bool, approval_present: bool) -> dict:
    return {
        "action_id": action_id,
        "action_type": action_type,
        "claim_status": claim_status,
        "confidence": confidence,
        "scope": scope,
        "autonomy_level": autonomy_level,
        "blast_radius": blast_radius,
        "irreversible": irreversible,
        "approval_present": approval_present
    }

def explain_policy_verdict(policy: dict, action_request: dict) -> str:
    # 1. Invalid fields check
    if action_request["claim_status"] not in VALID_CLAIM_STATUS:
        return "HALT"
    if action_request["confidence"] not in VALID_CONFIDENCE:
        return "HALT"
    if action_request["blast_radius"] not in VALID_BLAST_RADIUS:
        return "HALT"
    if not isinstance(action_request["autonomy_level"], int):
        return "HALT"
    if policy["max_blast_radius"] not in VALID_BLAST_RADIUS:
        return "HALT"

    # 2. Claim status checks
    cs = action_request["claim_status"]
    if cs == "UNKNOWN": return "HALT"
    if cs == "CONFLICTED": return "VERIFY"
    if cs == "UNSUPPORTED": return "BLOCK"
    if cs == "FORBIDDEN": return "BLOCK"

    # 3. Action Type checks
    at = action_request["action_type"]
    if at in policy["forbidden_actions"]:
        return "BLOCK"
    if policy["fail_closed"] and at not in policy["allowed_actions"]:
        return "BLOCK"

    # 4. Scope checks
    if action_request["scope"] not in policy["allowed_scopes"]:
        return "BLOCK"

    # 5. Limits checks
    if action_request["autonomy_level"] > policy["max_autonomy_level"]:
        return "BLOCK"
        
    req_br = BLAST_RADIUS_LEVELS[action_request["blast_radius"]]
    pol_br = BLAST_RADIUS_LEVELS[policy["max_blast_radius"]]
    if req_br > pol_br:
        return "BLOCK"

    # 6. Reversibility and Approval checks
    if action_request["irreversible"] and not action_request["approval_present"]:
        return "CONFIRM"
        
    if at in policy["requires_approval"] and not action_request["approval_present"]:
        return "CONFIRM"

    # If all passed
    return "ALLOW"

def evaluate_policy(policy: dict, action_request: dict) -> str:
    return explain_policy_verdict(policy, action_request)

def policy_allows(policy: dict, action_request: dict) -> bool:
    return evaluate_policy(policy, action_request) == "ALLOW"
