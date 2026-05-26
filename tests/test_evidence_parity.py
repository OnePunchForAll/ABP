import unittest
from src.abp.evidence import sha256_text, make_source, make_span
from src.abp.claims import make_claim, validate_claim

class TestEvidenceParity(unittest.TestCase):
    def setUp(self):
        self.sources = {
            "src1": make_source("src1", "Test Book", "This is the source text. It contains a quote.")
        }
        self.spans = {
            "span1": make_span("span1", "src1", "It contains a quote")
        }
        self.valid_hash = sha256_text("It contains a quote")

    def test_valid_claim_passes(self):
        claim = make_claim("c1", "There is a quote.", "FACT", "VERIFIED", "src1", "span1", self.valid_hash)
        self.assertTrue(validate_claim(claim, self.sources, self.spans))

    def test_claim_without_source_fails(self):
        claim = make_claim("c1", "There is a quote.", "FACT", "VERIFIED", None, "span1", self.valid_hash)
        self.assertFalse(validate_claim(claim, self.sources, self.spans))

    def test_claim_without_span_fails(self):
        claim = make_claim("c1", "There is a quote.", "FACT", "VERIFIED", "src1", None, self.valid_hash)
        self.assertFalse(validate_claim(claim, self.sources, self.spans))

    def test_claim_with_forged_quote_hash_fails(self):
        claim = make_claim("c1", "There is a quote.", "FACT", "VERIFIED", "src1", "span1", "forged_hash")
        self.assertFalse(validate_claim(claim, self.sources, self.spans))

    def test_high_confidence_unsupported_claim_fails(self):
        claim = make_claim("c1", "Just trust me.", "FACT", "STRONG")
        self.assertFalse(validate_claim(claim, self.sources, self.spans))

    def test_unknown_claim_without_evidence_passes(self):
        claim = make_claim("c1", "Maybe aliens exist.", "UNKNOWN", "UNKNOWN")
        self.assertTrue(validate_claim(claim, self.sources, self.spans))
        
if __name__ == '__main__':
    unittest.main()
