def create_authority(principal: str, agent: str, scope: set, allowed_tools: set,
                     expiration: float, budget: float, autonomy_ceiling: int, active: bool = True) -> dict:
    return {
        "principal": principal,
        "agent": agent,
        "scope": scope,
        "allowed_tools": allowed_tools,
        "expiration": expiration,
        "budget": budget,
        "autonomy_ceiling": autonomy_ceiling,
        "active": active
    }

def create_authority_request(agent: str, requested_scope: set, requested_tool: str,
                             requested_cost: float, requested_autonomy: int, current_time: float) -> dict:
    return {
        "agent": agent,
        "requested_scope": requested_scope,
        "requested_tool": requested_tool,
        "requested_cost": requested_cost,
        "requested_autonomy": requested_autonomy,
        "current_time": current_time
    }

def explain_authority_verdict(authority: dict, request: dict) -> str:
    # Check invalid/missing fields
    for k in ["agent", "requested_scope", "requested_tool", "requested_cost", "requested_autonomy", "current_time"]:
        if k not in request or request[k] is None:
            return "INVALID"
            
    if not isinstance(request["requested_cost"], (int, float)):
        return "INVALID"
    if not isinstance(request["requested_autonomy"], int):
        return "INVALID"
        
    if not authority.get("active", False):
        return "INACTIVE"
        
    if request["agent"] != authority["agent"]:
        return "WRONG_AGENT"
        
    if request["current_time"] >= authority["expiration"]:
        return "EXPIRED"
        
    if not request["requested_scope"].issubset(authority["scope"]):
        return "OUT_OF_SCOPE"
        
    if request["requested_tool"] not in authority["allowed_tools"]:
        return "TOOL_DENIED"
        
    if request["requested_cost"] > authority["budget"]:
        return "OVER_BUDGET"
        
    if request["requested_autonomy"] > authority["autonomy_ceiling"]:
        return "OVER_AUTONOMY"
        
    return "ALLOW"

def evaluate_authority(authority: dict, request: dict) -> str:
    return explain_authority_verdict(authority, request)

def authority_allows(authority: dict, request: dict) -> bool:
    return evaluate_authority(authority, request) == "ALLOW"

def narrow_authority(authority: dict, new_scope: set = None, new_allowed_tools: set = None,
                     new_budget: float = None, new_autonomy_ceiling: int = None) -> dict:
    narrowed = authority.copy()
    
    if new_scope is not None:
        narrowed["scope"] = authority["scope"].intersection(new_scope)
        
    if new_allowed_tools is not None:
        narrowed["allowed_tools"] = authority["allowed_tools"].intersection(new_allowed_tools)
        
    if new_budget is not None:
        narrowed["budget"] = min(authority["budget"], new_budget)
        
    if new_autonomy_ceiling is not None:
        narrowed["autonomy_ceiling"] = min(authority["autonomy_ceiling"], new_autonomy_ceiling)
        
    return narrowed
