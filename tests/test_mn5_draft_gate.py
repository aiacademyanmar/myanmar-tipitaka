"""MN5 Pāli/Burmese editorial draft gate regression tests, synthetic content."""
import csv,hashlib,sys,tempfile,unittest,sqlite3
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn5_editorial_draft import check,COLUMNS
class TestMN5Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.p=Path(self.tmp.name)
  self.csv=self.p/"mn5.csv";self.db=self.p/"missing.sqlite"
  self.records=[]
  for i in range(203):
   pali="Pāli …pe…" if i<6 else "Pāli segment "+str(i)
   method="ELLIPSIS_SOURCE_UNEXPANDED" if i<6 else "CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW" if i<13 else "CONTEXTUAL_DRAFT_REVIEW_REQUIRED"
   self.records.append([f"mn5:{i}.1","mn5",pali,"မြန်မာမူကြမ်း","ရှင်းလင်းချက်","AI_DRAFT_UNREVIEWED",method,
     hashlib.sha256(pali.encode()).hexdigest(),"sutta/mn/mn5_root-pli-ms.json","a"*40,"0","","https://example.org"])
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(COLUMNS);w.writerows(self.records)
 def test_valid_input_proceeds_to_sqlite(self):
  with self.assertRaises(sqlite3.OperationalError):check(self.csv,self.db)
 def test_bad_sha_fails_before_sqlite(self):
  self.records[0][7]="0"*64;self.write()
  with self.assertRaisesRegex(ValueError,"SHA mismatch"):check(self.csv,self.db)
 def test_fabricated_approval_fails(self):
  self.records[0][11]="Scholar";self.write()
  with self.assertRaisesRegex(ValueError,"marked approved"):check(self.csv,self.db)
 def test_wrong_count_fails(self):
  self.records.pop();self.write()
  with self.assertRaisesRegex(ValueError,"203"):check(self.csv,self.db)
 def test_source_ellipsis_must_stay_flagged(self):
  self.records[6][6]="ELLIPSIS_SOURCE_UNEXPANDED";self.write()
  with self.assertRaisesRegex(ValueError,"abbreviation"):check(self.csv,self.db)
if __name__=="__main__":
 import sqlite3
 unittest.main()
