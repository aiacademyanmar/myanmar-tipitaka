"""MN1 334-segment Burmese draft importer QA (synthetic fixtures only)."""
import csv,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from import_mn1_myanmar_drafts import FIELDS,build

class TestMN1MyanmarDraft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  p=Path(self.tmp.name)
  self.csv=p/"draft.csv";self.db=p/"draft.sqlite"
  self.records=[]
  for i in range(334):
   pali=("…pe…" if i<154 else "Pali example")+f" {i}"
   method=("ELLIPSIS_SOURCE_REQUIRES_EXPANSION" if i<154 else "TRANSLATED_EXPLICIT_SOURCE")
   self.records.append([f"mn1:{i+1}.1",pali,"မြန်မာဘာသာပြန်မူကြမ်း","အနက်ရှင်းလင်းချက်",
    "AI_DRAFT_UNREVIEWED",method,hashlib.sha256(pali.encode()).hexdigest(),"synthetic-source"])
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(FIELDS);w.writerows(self.records)
 def test_full_synthetic_drafts_unapproved(self):
  result=build(self.csv,self.db)
  self.assertEqual(result["draft_segments"],334)
  self.assertEqual(result["unexpanded_source_abbreviations"],154)
  self.assertFalse(result["release_ready"])
  self.assertEqual(result["MCU_45_verified_books"],0)
 def test_human_review_cannot_be_faked(self):
  self.records[0][4]="SCHOLAR_APPROVED";self.write()
  with self.assertRaises(ValueError):build(self.csv,self.db)
 def test_source_hash_mismatch_fails(self):
  self.records[0][6]="0"*64;self.write()
  with self.assertRaises(ValueError):build(self.csv,self.db)
 def test_omitted_segment_fails(self):
  self.records.pop();self.write()
  with self.assertRaises(ValueError):build(self.csv,self.db)
 def test_bad_ellipsis_marker_fails(self):
  self.records[0][5]="TRANSLATED_EXPLICIT_SOURCE";self.write()
  with self.assertRaises(ValueError):build(self.csv,self.db)

if __name__=="__main__":unittest.main()
