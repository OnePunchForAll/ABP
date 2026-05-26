import hashlib

def compute_byte_parity(data: bytes) -> int:
    from src.abp.parity import xor_parity
    parity = 0
    for byte in data:
        parity ^= xor_parity(byte)
    return parity

def compute_hash_parity(data: bytes) -> str:
    from src.abp.hashing import sha256_bytes
    return sha256_bytes(data)

from src.abp.claims import make_claim, validate_claim
from src.abp.evidence import sha256_text
from src.abp.state import create_state, add_unknown, add_contradiction, can_synthesize
from src.abp.policy import evaluate_policy, create_action_request, create_policy
from src.abp.authority import evaluate_authority, create_authority, narrow_authority
from src.abp.reversibility import evaluate_reversibility, create_reversibility_action
from src.abp.receipts import create_receipt, action_has_receipt, receipt_hash
from src.abp.calibration import create_prediction, record_outcome, calibration_quality, adjust_autonomy
from src.abp.memory import create_memory, memory_can_be_policy

TARGET_LAYERS = {
    "BYTE", "HASH", "EVIDENCE", "STATE", "POLICY", "AUTHORITY",
    "REVERSIBILITY", "RECEIPT", "CALIBRATION", "MEMORY"
}

def create_attack_result(attack_id: str, target_layer: str, attack_name: str,
                         expected_result: str, actual_result: str, passed: bool,
                         failure_reason: str = "") -> dict:
    return {
        "attack_id": attack_id,
        "target_layer": target_layer,
        "attack_name": attack_name,
        "expected_result": expected_result,
        "actual_result": actual_result,
        "passed": passed,
        "failure_reason": failure_reason
    }

def validate_attack_result(result: dict) -> bool:
    if not isinstance(result, dict):
        return False
        
    req = ["attack_id", "target_layer", "attack_name", "expected_result", "actual_result", "passed"]
    for f in req:
        if f not in result or result[f] is None:
            if f == "passed" and result.get(f) is False:
                pass
            elif result.get(f) == "":
                return False
            else:
                return False
                
    if result.get("target_layer") not in TARGET_LAYERS:
        return False
        
    if not isinstance(result.get("passed"), bool):
        return False
        
    if result["passed"] and result.get("failure_reason"):
        return False
        
    if not result["passed"] and not result.get("failure_reason"):
        return False
        
    return True

def run_byte_flip_attack() -> dict:
    data = b"hello world"
    original_parity = compute_byte_parity(data)
    
    tampered_data = b"hello vorld"
    tampered_parity = compute_byte_parity(tampered_data)
    
    passed = (original_parity != tampered_parity)
    return create_attack_result("a1", "BYTE", "byte_flip", "mismatch",
                                "mismatch" if passed else "match", passed,
                                "" if passed else "parity did not catch flip")

def run_hash_tamper_attack() -> dict:
    data = b"important data"
    h1 = compute_hash_parity(data)
    
    tampered = b"important datb"
    h2 = compute_hash_parity(tampered)
    
    passed = (h1 != h2)
    return create_attack_result("a2", "HASH", "hash_tamper", "mismatch",
                                "mismatch" if passed else "match", passed,
                                "" if passed else "hash collision")

def run_forged_quote_hash_attack() -> dict:
    real_quote = "the earth is round"
    bad_hash = sha256_text("the earth is flat")
    
    claim = make_claim("c1", "earth is flat", "FACT", "VERIFIED", "src1", "span1", bad_hash)
    sources = {"src1": {"source_id": "src1", "text": "the earth is round and round"}}
    spans = {"span1": {"span_id": "span1", "source_id": "src1", "quote": real_quote}}
    valid = validate_claim(claim, sources, spans)
    
    passed = not valid
    return create_attack_result("a3", "EVIDENCE", "forged_quote", "invalid",
                                "invalid" if passed else "valid", passed,
                                "" if passed else "validation accepted forged quote")

def run_high_confidence_unsupported_claim_attack() -> dict:
    claim = make_claim("c2", "x", "FACT", "VERIFIED", None, None, None)
    valid = validate_claim(claim, {}, {})
    passed = not valid
    return create_attack_result("a4", "EVIDENCE", "unsupported_claim", "invalid",
                                "invalid" if passed else "valid", passed,
                                "" if passed else "accepted VERIFIED without source")

def run_state_contradiction_attack() -> dict:
    st = create_state("goal1")
    add_contradiction(st, "c1", "c2")
    res = can_synthesize(st)
    passed = not res
    return create_attack_result("a5", "STATE", "state_contradiction", "HALT",
                                "HALT" if passed else "SYNTHESIZED", passed,
                                "" if passed else "synthesized with contradiction")

def run_policy_forbidden_action_attack() -> dict:
    req = create_action_request("a1", "WRITE", "FACT", "VERIFIED", "s1", 5, "HIGH", False, False)
    pol = create_policy({"READ"}, {"WRITE"}, set(), 5, "HIGH", {"s1"})
    
    res = evaluate_policy(pol, req)
    passed = (res == "HALT" or res == "BLOCK")
    return create_attack_result("a6", "POLICY", "forbidden_action", "BLOCK/HALT",
                                res, passed, "" if passed else f"policy returned {res}")

def run_authority_scope_expansion_attack() -> dict:
    auth = create_authority("p", "a", {"s1"}, {"t1"}, 100.0, 10.0, 3)
    narrowed = narrow_authority(auth, new_scope={"s1", "s2"}, new_allowed_tools={"t1", "t2"}, new_budget=100.0)
    passed = (narrowed["scope"] == {"s1"} and narrowed["allowed_tools"] == {"t1"} and narrowed["budget"] == 10.0)
    return create_attack_result("a7", "AUTHORITY", "scope_expansion", "Narrowed",
                                "Narrowed" if passed else "Expanded", passed,
                                "" if passed else "authority expanded")

def run_irreversible_without_approval_attack() -> dict:
    action = create_reversibility_action("a", "desc", 5, True, "ALLOW", "ALLOW", False, False, False, True, True, "CRITICAL")
    res = evaluate_reversibility(action)
    passed = res in ("CONFIRM", "BLOCK")
    return create_attack_result("a8", "REVERSIBILITY", "irreversible_unapproved", "CONFIRM/BLOCK",
                                res, passed, "" if passed else f"returned {res}")

def run_action_without_receipt_attack() -> dict:
    passed = not action_has_receipt(None)
    return create_attack_result("a9", "RECEIPT", "missing_receipt", "False",
                                "False" if passed else "True", passed,
                                "" if passed else "allowed missing receipt")

def run_bad_calibration_attack() -> dict:
    p1 = create_prediction("p1", "c1", 0.9, "STRONG", 100.0)
    record_outcome(p1, False)
    qual = calibration_quality([p1])
    aut = adjust_autonomy(3, [p1])
    passed = (qual == "FAIL" and aut < 3)
    return create_attack_result("a10", "CALIBRATION", "bad_calibration", "FAIL & reduce",
                                f"{qual} & {aut}", passed, "" if passed else "did not penalize")

def run_stale_memory_policy_attack() -> dict:
    m = create_memory("m1", "c1", 0.0, 0.0, 30.0, 1.0, "ACTIVE", "VERIFIED", [], [], "L10")
    passed = not memory_can_be_policy(m, 60.0 * 86400.0, freshness_days=30)
    return create_attack_result("a11", "MEMORY", "stale_memory", "False",
                                "False" if passed else "True", passed,
                                "" if passed else "allowed stale memory")

def run_all_adversary_attacks() -> list:
    return [
        run_byte_flip_attack(),
        run_hash_tamper_attack(),
        run_forged_quote_hash_attack(),
        run_high_confidence_unsupported_claim_attack(),
        run_state_contradiction_attack(),
        run_policy_forbidden_action_attack(),
        run_authority_scope_expansion_attack(),
        run_irreversible_without_approval_attack(),
        run_action_without_receipt_attack(),
        run_bad_calibration_attack(),
        run_stale_memory_policy_attack()
    ]
