"""Pure source UID split regression tests; no edition approval implied."""
import importlib.util
import unittest
from pathlib import Path

PATH=Path(__file__).resolve().parents[1] / "tools" / "mcu45_apadana_patthana_v2393.py"
SPEC=importlib.util.spec_from_file_location("mcu45_v2393",PATH)
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

class BoundaryRulesTest(unittest.TestCase):
    def test_apadana_cut(self):
        self.assertEqual(m.boundary("32|33","tha-ap412"),(32,None))
        self.assertEqual(m.boundary("32|33","tha-ap413"),(33,None))
        self.assertEqual(m.boundary("32|33","thi-ap1"),(33,None))
    def test_patthana_cut(self):
        self.assertEqual(m.boundary("40|41|42|43|44|45","patthana1.1"),(None,"40|41"))
        self.assertEqual(m.boundary("40|41|42|43|44|45","patthana2.6-7"),(None,"42|43"))
        for i in (3,4,5,6):
            self.assertEqual(m.boundary("40|41|42|43|44|45",f"patthana{i}.1"),(44,None))
        for i in (7,12,13,18,19,24):
            self.assertEqual(m.boundary("40|41|42|43|44|45",f"patthana{i}.1"),(45,None))
    def test_fail_closed(self):
        with self.assertRaises(ValueError):m.boundary("32|33","invalid")
        with self.assertRaises(ValueError):m.boundary("40|41|42|43|44|45","patthana25.1")

if __name__=="__main__": unittest.main()
