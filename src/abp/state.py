VALID_RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
VALID_CHECK_STATUSES = {"OPEN", "RESOLVED", "EXPIRED"}

def create_state(goal: str) -> dict:
    state = {
        "goal": goal,
        "knowns": [],
        "unknowns": [],
        "assumptions": [],
        "constraints": [],
        "sources": [],
        "actions_taken": [],
        "pending_checks": [],
        "contradictions": [],
        "commitments": [],
        "risk_level": "LOW",
        "autonomy_level": 0,
        "events": []
    }
    _append_event(state, "create_state", {"goal": goal})
    return state

def validate_state(state: dict) -> bool:
    if not state.get("goal"):
        return False
        
    autonomy = state.get("autonomy_level")
    if not isinstance(autonomy, int) or not (0 <= autonomy <= 5):
        return False
        
    if state.get("risk_level") not in VALID_RISK_LEVELS:
        return False
        
    for commitment in state.get("commitments", []):
        if not commitment.get("authority_basis"):
            return False
            
    for check in state.get("pending_checks", []):
        if check.get("status") not in VALID_CHECK_STATUSES:
            return False
            
    action_ids = {a["action_id"] for a in state.get("actions_taken", [])}
    action_events = {e["action_id"] for e in state.get("events", []) if e.get("type") == "record_action"}
    if not action_ids.issubset(action_events):
        return False
        
    return True

def _append_event(state: dict, event_type: str, details: dict):
    event = {"type": event_type}
    event.update(details)
    state["events"].append(event)

def add_known(state: dict, value: str):
    state["knowns"].append(value)
    _append_event(state, "add_known", {"value": value})

def add_unknown(state: dict, value: str):
    state["unknowns"].append(value)
    _append_event(state, "add_unknown", {"value": value})

def add_assumption(state: dict, value: str):
    state["assumptions"].append(value)
    _append_event(state, "add_assumption", {"value": value})

def add_constraint(state: dict, value: str):
    state["constraints"].append(value)
    _append_event(state, "add_constraint", {"value": value})

def add_pending_check(state: dict, check_id: str, description: str):
    state["pending_checks"].append({
        "check_id": check_id,
        "description": description,
        "status": "OPEN"
    })
    _append_event(state, "add_pending_check", {"check_id": check_id})

def resolve_pending_check(state: dict, check_id: str):
    for check in state["pending_checks"]:
        if check["check_id"] == check_id:
            check["status"] = "RESOLVED"
            _append_event(state, "resolve_pending_check", {"check_id": check_id})
            return
    raise ValueError(f"Check {check_id} not found")

def add_contradiction(state: dict, contradiction_id: str, description: str, active: bool = True):
    state["contradictions"].append({
        "contradiction_id": contradiction_id,
        "description": description,
        "active": active
    })
    _append_event(state, "add_contradiction", {"contradiction_id": contradiction_id, "active": active})

def add_commitment(state: dict, commitment_id: str, description: str, authority_basis: str = None):
    state["commitments"].append({
        "commitment_id": commitment_id,
        "description": description,
        "authority_basis": authority_basis
    })
    _append_event(state, "add_commitment", {"commitment_id": commitment_id})

def record_action(state: dict, action_id: str, description: str):
    state["actions_taken"].append({
        "action_id": action_id,
        "description": description
    })
    _append_event(state, "record_action", {"action_id": action_id})

def can_synthesize(state: dict) -> bool:
    for contradiction in state.get("contradictions", []):
        if contradiction.get("active"):
            return False
    return True
