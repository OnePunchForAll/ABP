import unittest
from src.abp.parity import even_parity, odd_parity, xor_parity, flip_bit, count_ones

class TestParity(unittest.TestCase):
    def test_all_256_bytes(self):
        for i in range(256):
            self.assertEqual(even_parity(i), not odd_parity(i))
            self.assertEqual(even_parity(i), xor_parity(i) == 0)

    def test_single_bit_flip_detection(self):
        original = 0b10101010
        flipped = flip_bit(original, 0)
        self.assertNotEqual(even_parity(original), even_parity(flipped))

    def test_double_bit_flip_evasion(self):
        original = 0b10101010
        flipped_once = flip_bit(original, 0)
        flipped_twice = flip_bit(flipped_once, 1)
        # Even parity is same, thus evades detection
        self.assertEqual(even_parity(original), even_parity(flipped_twice))

    def test_invalid_byte(self):
        with self.assertRaises(ValueError):
            even_parity(256)
        with self.assertRaises(ValueError):
            even_parity(-1)

if __name__ == '__main__':
    unittest.main()
