VALID_TARGET_LAYERS = {
    "BYTE", "HASH", "EVIDENCE", "STATE", "POLICY", "AUTHORITY",
    "REVERSIBILITY", "RECEIPT", "CALIBRATION", "MEMORY", "ADVERSARY", "METRIC"
}
VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_STATUS = {"PROPOSED", "APPROVED", "REJECTED", "APPLIED", "REVERTED", "FAILED"}

def create_enhancement_proposal(proposal_id: str, target_layer: str, weakness: str,
                                evidence_ref: str, metric_name: str, expected_delta: float,
                                control_change: str, regression_test: str, rollback_plan: str,
                                risk_level: str, requires_human_approval: bool,
                                human_approval: bool = False, status: str = "PROPOSED") -> dict:
    return {
        "proposal_id": proposal_id,
        "target_layer": target_layer,
        "weakness": weakness,
        "evidence_ref": evidence_ref,
        "metric_name": metric_name,
        "expected_delta": float(expected_delta) if expected_delta is not None else None,
        "control_change": control_change,
        "regression_test": regression_test,
        "rollback_plan": rollback_plan,
        "risk_level": risk_level,
        "requires_human_approval": requires_human_approval,
        "human_approval": human_approval,
        "status": status,
        "reason": ""
    }

def validate_enhancement_proposal(proposal: dict) -> bool:
    if not isinstance(proposal, dict): return False
    
    required_keys = ["proposal_id", "target_layer", "weakness", "evidence_ref", 
               "metric_name", "control_change", "regression_test", "rollback_plan", "risk_level", "status"]
               
    for field in required_keys:
        if field not in proposal:
            return False
            
    if not proposal.get("proposal_id"): return False
    if not proposal.get("target_layer"): return False
    if not proposal.get("weakness"): return False
    if not proposal.get("metric_name"): return False
    if not proposal.get("control_change"): return False
            
    if not isinstance(proposal.get("expected_delta"), (int, float)):
        return False
        
    if proposal["target_layer"] not in VALID_TARGET_LAYERS:
        return False
    
    if proposal["risk_level"] not in VALID_RISK_LEVELS:
        return False
        
    if proposal["status"] not in VALID_STATUS:
        return False
        
    return True

def evaluate_enhancement(proposal: dict, regression_passed: bool = True) -> str:
    if not validate_enhancement_proposal(proposal):
        return "INVALID"
        
    if not proposal["evidence_ref"]:
        return "BLOCK"
        
    if not proposal["regression_test"]:
        return "BLOCK"
        
    if not proposal["rollback_plan"]:
        return "BLOCK"
        
    if not regression_passed:
        return "BLOCK"
        
    risk = proposal["risk_level"]
    needs_approval = proposal["requires_human_approval"] or risk in ("HIGH", "CRITICAL")
    
    if needs_approval and not proposal["human_approval"]:
        return "CONFIRM"
        
    return "ALLOW"

def enhancement_allows(proposal: dict, regression_passed: bool = True) -> bool:
    return evaluate_enhancement(proposal, regression_passed) == "ALLOW"

def apply_enhancement_simulated(proposal: dict, regression_passed: bool = True) -> dict:
    new_prop = proposal.copy()
    verdict = evaluate_enhancement(new_prop, regression_passed)
    if verdict == "ALLOW":
        new_prop["status"] = "APPLIED"
    else:
        new_prop["status"] = "FAILED"
        new_prop["reason"] = f"Verdict was {verdict}"
    return new_prop

def reject_enhancement(proposal: dict, reason: str) -> dict:
    new_prop = proposal.copy()
    new_prop["status"] = "REJECTED"
    new_prop["reason"] = reason
    return new_prop

def revert_enhancement(proposal: dict, reason: str) -> dict:
    new_prop = proposal.copy()
    new_prop["status"] = "REVERTED"
    new_prop["reason"] = reason
    return new_prop

def explain_enhancement(proposal: dict) -> str:
    verdict = evaluate_enhancement(proposal)
    return f"Enhancement {proposal.get('proposal_id', 'unknown')} targets {proposal.get('target_layer', 'unknown')}. Verdict: {verdict}. Status: {proposal.get('status', 'unknown')}."
