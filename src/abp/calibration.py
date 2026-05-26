VALID_CONFIDENCE = {"VERIFIED", "STRONG", "TENTATIVE", "UNKNOWN"}

def create_prediction(prediction_id: str, claim_id: str, predicted_probability: float,
                      confidence: str, created_at: float, outcome: bool = None) -> dict:
    return {
        "prediction_id": prediction_id,
        "claim_id": claim_id,
        "predicted_probability": predicted_probability,
        "confidence": confidence,
        "outcome": outcome,
        "created_at": created_at
    }

def validate_prediction(prediction: dict) -> bool:
    if not isinstance(prediction, dict): return False
    req = ["prediction_id", "claim_id", "predicted_probability", "confidence", "created_at"]
    for f in req:
        if f not in prediction or prediction[f] is None:
            if f in ("predicted_probability", "created_at") and prediction.get(f) == 0.0:
                pass
            else:
                return False
                
    prob = prediction.get("predicted_probability")
    if not isinstance(prob, (int, float)) or not (0.0 <= prob <= 1.0):
        return False
        
    if prediction.get("confidence") not in VALID_CONFIDENCE:
        return False
        
    if "outcome" in prediction and prediction["outcome"] not in (True, False, None):
        return False
        
    return True

def record_outcome(prediction: dict, outcome: bool):
    if outcome not in (True, False):
        raise ValueError("Outcome must be True or False")
    prediction["outcome"] = outcome

def brier_score(predictions: list) -> float:
    resolved = [p for p in predictions if p.get("outcome") is not None]
    if not resolved:
        return 0.0
    
    squared_errors = []
    for p in resolved:
        actual = 1.0 if p["outcome"] else 0.0
        error = (p["predicted_probability"] - actual) ** 2
        squared_errors.append(error)
        
    return sum(squared_errors) / len(squared_errors)

def expected_calibration_error(predictions: list, bins: int = 10) -> float:
    resolved = [p for p in predictions if p.get("outcome") is not None]
    if not resolved:
        return 0.0
        
    bin_bounds = [i/bins for i in range(bins+1)]
    ece = 0.0
    total = len(resolved)
    
    for i in range(bins):
        lower = bin_bounds[i]
        upper = bin_bounds[i+1]
        
        if i == bins - 1:
            in_bin = [p for p in resolved if lower <= p["predicted_probability"] <= upper]
        else:
            in_bin = [p for p in resolved if lower <= p["predicted_probability"] < upper]
            
        if not in_bin:
            continue
            
        bin_count = len(in_bin)
        avg_pred = sum(p["predicted_probability"] for p in in_bin) / bin_count
        avg_true = sum(1.0 if p["outcome"] else 0.0 for p in in_bin) / bin_count
        
        ece += (bin_count / total) * abs(avg_pred - avg_true)
        
    return ece

def overconfidence_count(predictions: list, threshold: float = 0.8) -> int:
    resolved = [p for p in predictions if p.get("outcome") is not None]
    count = 0
    for p in resolved:
        if p["predicted_probability"] >= threshold and not p["outcome"]:
            count += 1
    return count

def underconfidence_count(predictions: list, threshold: float = 0.4) -> int:
    resolved = [p for p in predictions if p.get("outcome") is not None]
    count = 0
    for p in resolved:
        if p["predicted_probability"] <= threshold and p["outcome"]:
            count += 1
    return count

def calibration_quality(predictions: list, max_brier: float = 0.25, max_ece: float = 0.25) -> str:
    resolved = [p for p in predictions if p.get("outcome") is not None]
    if not resolved:
        return "PASS"
    b_score = brier_score(predictions)
    ece_score = expected_calibration_error(predictions)
    
    if b_score <= max_brier and ece_score <= max_ece:
        return "PASS"
    return "FAIL"

def adjust_autonomy(current_autonomy: int, predictions: list) -> int:
    quality = calibration_quality(predictions)
    if quality == "FAIL":
        return max(0, current_autonomy - 1)
    return current_autonomy

def calibration_summary(predictions: list) -> dict:
    return {
        "brier_score": brier_score(predictions),
        "ece": expected_calibration_error(predictions),
        "overconfidence_count": overconfidence_count(predictions),
        "underconfidence_count": underconfidence_count(predictions),
        "quality": calibration_quality(predictions)
    }

def explain_calibration(predictions: list) -> str:
    summary = calibration_summary(predictions)
    return f"Quality: {summary['quality']} (Brier: {summary['brier_score']:.4f}, ECE: {summary['ece']:.4f})"
