import hashlib
import json
from typing import Any

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: str) -> str:
    hash_sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def canonical_json_hash(obj: Any) -> str:
    # Sort keys, remove spaces
    canonical_str = json.dumps(obj, sort_keys=True, separators=(',', ':'))
    return sha256_bytes(canonical_str.encode('utf-8'))

def file_drift_detected(before_hash: str, after_hash: str) -> bool:
    return before_hash != after_hash
