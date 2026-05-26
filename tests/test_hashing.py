import unittest
import os
import tempfile
from src.abp.hashing import sha256_bytes, sha256_file, canonical_json_hash, file_drift_detected

class TestHashing(unittest.TestCase):
    def test_file_mutation(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"initial")
            path = f.name
        
        try:
            hash1 = sha256_file(path)
            with open(path, "wb") as f:
                f.write(b"mutated")
            hash2 = sha256_file(path)
            
            self.assertTrue(file_drift_detected(hash1, hash2))
        finally:
            os.remove(path)

    def test_equivalent_json(self):
        obj1 = {"a": 1, "b": 2}
        obj2 = {"b": 2, "a": 1}
        self.assertEqual(canonical_json_hash(obj1), canonical_json_hash(obj2))

    def test_different_json(self):
        obj1 = {"a": 1, "b": 2}
        obj2 = {"a": 1, "b": 3}
        self.assertNotEqual(canonical_json_hash(obj1), canonical_json_hash(obj2))

if __name__ == '__main__':
    unittest.main()
