import hashlib

def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def make_source(source_id: str, title: str, text: str) -> dict:
    return {
        "source_id": source_id,
        "title": title,
        "text": text
    }

def make_span(span_id: str, source_id: str, quote: str) -> dict:
    return {
        "span_id": span_id,
        "source_id": source_id,
        "quote": quote
    }
