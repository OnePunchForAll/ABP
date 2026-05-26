VALID_MEMORY_STATUS = {"ACTIVE", "DECAYED", "CONTRADICTED", "EXPIRED", "UNKNOWN"}
VALID_CONFIDENCE = {"VERIFIED", "STRONG", "TENTATIVE", "UNKNOWN"}

def create_memory(memory_id: str, claim_id: str, created_at: float, last_checked: float,
                  half_life_days: float, decay_score: float, status: str, confidence: str,
                  contradiction_refs: list, evidence_refs: list, source_layer: str) -> dict:
    return {
        "memory_id": memory_id,
        "claim_id": claim_id,
        "created_at": created_at,
        "last_checked": last_checked,
        "half_life_days": half_life_days,
        "decay_score": decay_score,
        "status": status,
        "confidence": confidence,
        "contradiction_refs": contradiction_refs,
        "evidence_refs": evidence_refs,
        "source_layer": source_layer
    }

def validate_memory(memory: dict) -> bool:
    if not isinstance(memory, dict):
        return False
        
    required_fields = ["memory_id", "claim_id", "created_at", "last_checked"]
    for f in required_fields:
        if f not in memory or memory[f] is None:
            if f in ("created_at", "last_checked") and memory.get(f) == 0.0:
                pass
            elif memory.get(f) == "":
                return False
            else:
                return False

    if memory.get("memory_id") == "" or memory.get("claim_id") == "":
        return False

    half_life = memory.get("half_life_days")
    if not isinstance(half_life, (int, float)) or half_life <= 0:
        return False
        
    decay_score = memory.get("decay_score")
    if not isinstance(decay_score, (int, float)) or not (0.0 <= decay_score <= 1.0):
        return False
        
    if memory.get("status") not in VALID_MEMORY_STATUS:
        return False
        
    if memory.get("confidence") not in VALID_CONFIDENCE:
        return False
        
    if not isinstance(memory.get("contradiction_refs"), list):
        return False
        
    if not isinstance(memory.get("evidence_refs"), list):
        return False
        
    return True

def compute_decay_score(created_at: float, current_time: float, half_life_days: float) -> float:
    age_seconds = current_time - created_at
    if age_seconds < 0:
        age_seconds = 0
    age_days = age_seconds / 86400.0
    return 0.5 ** (age_days / half_life_days)

def update_decay(memory: dict, current_time: float, threshold: float = 0.5):
    if not validate_memory(memory):
        return
        
    score = compute_decay_score(memory["created_at"], current_time, memory["half_life_days"])
    memory["decay_score"] = score
    
    if memory["contradiction_refs"]:
        memory["status"] = "CONTRADICTED"
    elif memory["status"] != "EXPIRED":
        if score < threshold:
            memory["status"] = "DECAYED"
        else:
            memory["status"] = "ACTIVE"

def add_contradiction(memory: dict, contradiction_id: str):
    if "contradiction_refs" in memory and isinstance(memory["contradiction_refs"], list):
        if contradiction_id not in memory["contradiction_refs"]:
            memory["contradiction_refs"].append(contradiction_id)
        memory["status"] = "CONTRADICTED"

def refresh_memory(memory: dict, current_time: float, evidence_ref=None, confidence=None):
    memory["last_checked"] = current_time
    if evidence_ref and isinstance(memory.get("evidence_refs"), list):
        if evidence_ref not in memory["evidence_refs"]:
            memory["evidence_refs"].append(evidence_ref)
    if confidence and confidence in VALID_CONFIDENCE:
        memory["confidence"] = confidence
        
    update_decay(memory, current_time)

def expire_memory(memory: dict):
    memory["status"] = "EXPIRED"

def memory_can_be_policy(memory: dict, current_time: float, freshness_days: int = 30) -> bool:
    if not validate_memory(memory):
        return False
        
    if memory["status"] != "ACTIVE":
        return False
        
    if memory["contradiction_refs"]:
        return False
        
    if memory["confidence"] not in ("VERIFIED", "STRONG"):
        return False
        
    age_seconds = current_time - memory["last_checked"]
    age_days = age_seconds / 86400.0
    
    if age_days > freshness_days:
        return False
        
    return True

def memory_is_active(memory: dict) -> bool:
    if not validate_memory(memory):
        return False
    return memory["status"] == "ACTIVE"

def explain_memory(memory: dict) -> str:
    if not validate_memory(memory):
        return "INVALID"
    return f"Status: {memory['status']}, Confidence: {memory['confidence']}, Score: {memory['decay_score']:.3f}"
