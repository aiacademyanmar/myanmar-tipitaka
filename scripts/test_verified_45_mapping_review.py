#!/usr/bin/env python3
"""Synthetic-only validation for V2.3.6.5 boundary review packets."""
import csv,hashlib,importlib.util,pathlib,sqlite3,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("review",ROOT/"scripts/prepare_verified_45_mapping_review.py")
review=importlib.util.module_from_spec(spec);spec.loader.exec_module(review)
SHA="a"*40
class ReviewTests(unittest.TestCase):
 def fixture(self,root):
  db=root/"source.sqlite";conn=sqlite3.connect(db)
  conn.executescript("CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT);"
                     "CREATE TABLE source_segments(segment_id TEXT PRIMARY KEY,body TEXT,source_file TEXT,source_commit TEXT,sha256 TEXT);")
  conn.execute("INSERT INTO build_info VALUES('commit',?)",(SHA,))
  for key in ("s:2","s:10","s:3"):
   body="Pali source TEST "+key
   conn.execute("INSERT INTO source_segments VALUES(?,?,?,?,?)",(key,body,"vinaya/test/one.json",SHA,hashlib.sha256(body.encode()).hexdigest()))
  conn.commit();conn.close()
  cross=root/"cross.csv";candidates=root/"candidates.csv"
  with cross.open("w",encoding="utf-8",newline="") as f:
   writer=csv.DictWriter(f,fieldnames=["volume_id","book_title_my","pitaka"]);writer.writeheader()
   for i in range(1,46):writer.writerow({"volume_id":i,"book_title_my":f"ကျမ်း {i}","pitaka":"vinaya"})
  with candidates.open("w",encoding="utf-8",newline="") as f:
   writer=csv.DictWriter(f,fieldnames=["volume_id","candidate_bilara_prefix"]);writer.writeheader()
   for i in range(1,46):writer.writerow({"volume_id":i,"candidate_bilara_prefix":"vinaya/test"})
  return db,cross,candidates
 def test_candidate_packet_does_not_approve_any_volume(self):
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory);db,cross,candidates=self.fixture(root)
   report=review.generate(db,cross,candidates,root/"review")
   self.assertEqual(report["human_verified_45_volume_mappings"],0)
   self.assertFalse(report["ready_to_generate_45_volume_sqlite"])
   with (root/"review"/"candidate_source_file_boundaries.csv").open(encoding="utf-8-sig",newline="") as f:
    rows=list(csv.DictReader(f))
   self.assertEqual(len(rows),45)
   self.assertEqual(rows[0]["first_segment_id"],"s:2")
   self.assertEqual(rows[0]["last_segment_id"],"s:3")
   self.assertEqual(rows[0]["review_status"],"CANDIDATE_ONLY")
 def test_sha_tampering_rejected(self):
  with tempfile.TemporaryDirectory() as directory:
   root=pathlib.Path(directory);db,cross,candidates=self.fixture(root)
   with sqlite3.connect(db) as conn:conn.execute("UPDATE source_segments SET body='tampered' WHERE segment_id='s:10'")
   with self.assertRaisesRegex(ValueError,"provenance/hash mismatch|source SHA"):
    review.generate(db,cross,candidates,root/"review")
if __name__=="__main__":unittest.main(verbosity=2)
