from typing import Dict, Optional
from src.abp.evidence import sha256_text

VALID_STATUS = {"FACT", "INFERENCE", "ASSUMPTION", "UNKNOWN"}
VALID_CONFIDENCE = {"VERIFIED", "STRONG", "TENTATIVE", "UNKNOWN"}

def make_claim(claim_id: str, text: str, status: str, confidence: str,
               source_id: Optional[str] = None, span_id: Optional[str] = None, 
               quote_hash: Optional[str] = None) -> dict:
    return {
        "claim_id": claim_id,
        "text": text,
        "status": status,
        "confidence": confidence,
        "source_id": source_id,
        "span_id": span_id,
        "quote_hash": quote_hash
    }

def validate_claim(claim: dict, sources: Dict[str, dict], spans: Dict[str, dict]) -> bool:
    if not claim.get("claim_id"): return False
    if not claim.get("text"): return False
    if claim.get("status") not in VALID_STATUS: return False
    if claim.get("confidence") not in VALID_CONFIDENCE: return False

    has_source = bool(claim.get("source_id"))
    has_span = bool(claim.get("span_id"))
    has_hash = bool(claim.get("quote_hash"))
    
    is_supported = has_source and has_span and has_hash
    
    if claim.get("confidence") in {"VERIFIED", "STRONG"}:
        if not is_supported:
            return False
            
    if has_source or has_span or has_hash:
        if not is_supported:
            return False
            
        source_id = claim["source_id"]
        span_id = claim["span_id"]
        
        if source_id not in sources:
            return False
        if span_id not in spans:
            return False
            
        span = spans[span_id]
        if span["source_id"] != source_id:
            return False
            
        source = sources[source_id]
        if span["quote"] not in source["text"]:
            return False
            
        if sha256_text(span["quote"]) != claim["quote_hash"]:
            return False
            
    return True
