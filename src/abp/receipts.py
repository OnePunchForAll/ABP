import hashlib
import json

VALID_STATUS = {"success", "failure", "partial", "blocked", "confirmed", "verified"}
VALID_POLICY_VERDICT = {"ALLOW", "VERIFY", "BLOCK", "HALT", "CONFIRM"}

def create_receipt(receipt_id: str, agent: str, principal: str, action: str, target: str,
                   scope: str, input_hash: str, output_hash: str, timestamp: float,
                   cost: float, status: str, policy_verdict: str, reversibility_level: int,
                   evidence_refs: list, state_before: str, state_after: str,
                   signature_placeholder: str) -> dict:
    return {
        "receipt_id": receipt_id,
        "agent": agent,
        "principal": principal,
        "action": action,
        "target": target,
        "scope": scope,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "timestamp": timestamp,
        "cost": cost,
        "status": status,
        "policy_verdict": policy_verdict,
        "reversibility_level": reversibility_level,
        "evidence_refs": evidence_refs,
        "state_before": state_before,
        "state_after": state_after,
        "signature_placeholder": signature_placeholder
    }

def explain_receipt_validation(receipt: dict) -> str:
    if not isinstance(receipt, dict):
        return "INVALID_TYPE"
        
    required_fields = [
        "receipt_id", "agent", "principal", "action", "target", "scope",
        "input_hash", "output_hash", "timestamp", "cost", "status",
        "policy_verdict", "reversibility_level", "evidence_refs",
        "state_before", "state_after", "signature_placeholder"
    ]
    
    string_fields = {
        "receipt_id", "agent", "principal", "action", "target", "scope",
        "input_hash", "output_hash", "state_before", "state_after", "signature_placeholder"
    }
    
    for f in required_fields:
        val = receipt.get(f)
        if val is None:
            return f"MISSING_{f.upper()}"
        if f in string_fields and val == "":
            return f"MISSING_{f.upper()}"
                
    if receipt["policy_verdict"] not in VALID_POLICY_VERDICT:
        return "INVALID_POLICY_VERDICT"
        
    if receipt["status"] not in VALID_STATUS:
        return "INVALID_STATUS"
        
    if not isinstance(receipt["evidence_refs"], list):
        return "INVALID_EVIDENCE_REFS"
        
    if not isinstance(receipt["cost"], (int, float)) or receipt["cost"] < 0:
        return "INVALID_COST"
        
    rev_level = receipt["reversibility_level"]
    if not isinstance(rev_level, int) or not (0 <= rev_level <= 5):
        return "INVALID_REVERSIBILITY_LEVEL"
        
    return "VALID"

def validate_receipt(receipt: dict) -> bool:
    return explain_receipt_validation(receipt) == "VALID"

def receipt_hash(receipt: dict) -> str:
    canonical = json.dumps(receipt, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    hex_digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"sha256:{hex_digest}"

def receipt_allows(receipt: dict) -> bool:
    if not validate_receipt(receipt):
        return False
    return receipt.get("policy_verdict") == "ALLOW"

def action_has_receipt(receipt: dict) -> bool:
    if receipt is None:
        return False
    return validate_receipt(receipt)
