"""V2.3.9.4 synthetic source-UID split unit tests."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from mcu45_patthana_boundaries_v2394 import classify

class TestPatthanaV2394(unittest.TestCase):
    def test_volume40_before_vitakkattika(self):
        self.assertEqual(classify("patthana1.6","40|41"),40)
    def test_volume41_starts_vitakkattika(self):
        self.assertEqual(classify("patthana1.7","40|41"),41)
        self.assertEqual(classify("patthana1.23","40|41"),41)
    def test_volume42_before_sarammanaduka(self):
        self.assertEqual(classify("patthana2.9","42|43"),42)
        self.assertEqual(classify("patthana2.6-7","42|43"),42)
    def test_volume43_sarammanaduka(self):
        self.assertEqual(classify("patthana2.10","42|43"),43)
        self.assertEqual(classify("patthana2.13","42|43"),43)
    def test_fail_closed_on_uncertain_structure(self):
        for uid,pool in [
          ("patthana1.24","40|41"),("patthana2.14","42|43"),
          ("patthana2.9-10","42|43"),("patthana1.6-7","40|41"),
          ("patthana1.7","42|43"),("pseudotext","40|41")
        ]:
            with self.subTest(uid=uid,pool=pool):
                with self.assertRaises(ValueError):classify(uid,pool)

if __name__ == "__main__":unittest.main()
