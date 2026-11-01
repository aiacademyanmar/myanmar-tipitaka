#!/usr/bin/env python3
"""Smoke tests for 45-volume Myanmar editorial batch planning."""
import csv, importlib.util, pathlib, sqlite3, tempfile, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("batch_builder",ROOT/"scripts/build_myanmar_editorial_batches.py")
MOD=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(MOD)
class BatchPlanTests(unittest.TestCase):
 def test_blocked_missing_corpus_still_reports_45_books(self):
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d); cross=d/"cross.csv"
   rows=[]
   for i in range(1,46):
    rows.append({"volume_id":i,"book_title_my":f"ကျမ်း {i}","pitaka":"sutta","source_file_prefix":"candidate","mapping_status":"UNVERIFIED"})
   with cross.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
   report=MOD.make_plan(d/"missing.sqlite",cross,d/"batches",d/"manifest.csv",d/"report.json")
   self.assertEqual(report["status"],"BLOCKED")
   with (d/"manifest.csv").open(encoding="utf-8-sig",newline="") as f:self.assertEqual(len(list(csv.DictReader(f))),45)
 def test_never_generates_myanmar_text(self):
  with tempfile.TemporaryDirectory() as d:
   d=pathlib.Path(d);cross=d/"cross.csv"
   rows=[{"volume_id":i,"book_title_my":f"ကျမ်း {i}","pitaka":"sutta","source_file_prefix":"candidate","mapping_status":"UNVERIFIED"} for i in range(1,46)]
   with cross.open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
   report=MOD.make_plan(d/"missing.sqlite",cross,d/"batches",d/"manifest.csv",d/"report.json")
   self.assertEqual(report["approved_translations"],0)
   self.assertEqual(report["approved_explanations"],0)
if __name__=="__main__":unittest.main(verbosity=2)
