VALID_BLAST_RADIUS = {"NONE", "LOW", "MEDIUM", "HIGH", "CRITICAL"}

def create_reversibility_action(action_id: str, description: str, level: int,
                                evidence_present: bool, policy_verdict: str,
                                authority_verdict: str, human_approval: bool,
                                rollback_plan: bool, compensation_plan: bool,
                                external_verification: bool, authority_basis: bool,
                                blast_radius: str) -> dict:
    return {
        "action_id": action_id,
        "description": description,
        "level": level,
        "evidence_present": evidence_present,
        "policy_verdict": policy_verdict,
        "authority_verdict": authority_verdict,
        "human_approval": human_approval,
        "rollback_plan": rollback_plan,
        "compensation_plan": compensation_plan,
        "external_verification": external_verification,
        "authority_basis": authority_basis,
        "blast_radius": blast_radius
    }

def explain_reversibility_verdict(action: dict) -> str:
    level = action.get("level")
    blast_radius = action.get("blast_radius")
    
    if level not in (0, 1, 2, 3, 4, 5):
        return "INVALID"
    if blast_radius not in VALID_BLAST_RADIUS:
        return "INVALID"
        
    policy = action.get("policy_verdict")
    authority = action.get("authority_verdict")
    
    if policy in ("BLOCK", "HALT"):
        return "BLOCK"
    if policy == "VERIFY":
        return "VERIFY"
        
    req_evidence = False
    req_policy_auth = False
    req_rollback = False
    req_human_approval = False
    req_external_verification = False
    req_authority_basis = False
    req_rollback_or_compensation = False
    
    if level >= 2:
        req_evidence = True
    if level >= 3:
        req_policy_auth = True
    if level >= 4:
        req_rollback = True
    if level == 5:
        req_rollback = False
        req_rollback_or_compensation = True
        req_human_approval = True
        req_external_verification = True
        req_authority_basis = True

    if req_evidence and not action.get("evidence_present"):
        return "BLOCK"
        
    if req_policy_auth:
        if policy not in ("ALLOW", "CONFIRM"):
            return "BLOCK"
        if authority != "ALLOW":
            return "BLOCK"
            
    if req_rollback and not action.get("rollback_plan"):
        return "BLOCK"
        
    if req_rollback_or_compensation and not (action.get("rollback_plan") or action.get("compensation_plan")):
        return "BLOCK"
        
    if req_external_verification and not action.get("external_verification"):
        return "BLOCK"
        
    if req_authority_basis and not action.get("authority_basis"):
        return "BLOCK"
        
    needs_confirm = (policy == "CONFIRM") or req_human_approval
    
    if needs_confirm and not action.get("human_approval"):
        return "CONFIRM"
        
    return "ALLOW"

def evaluate_reversibility(action: dict) -> str:
    return explain_reversibility_verdict(action)

def reversibility_allows(action: dict) -> bool:
    return evaluate_reversibility(action) == "ALLOW"
