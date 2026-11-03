"""MN9 fail-closed source/draft validation tests using synthetic Pāli fixtures."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn9_editorial_draft import verify,FIELDS

class TestMN9(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.path=Path(self.tmp.name)
  self.csv=self.path/"mn9.csv"
  self.source=self.path/"mn9.json"
  self.original={f"mn9:synthetic{i}": ("Pāli …pe…" if i<46 else "Pāli source "+str(i)) for i in range(234)}
  self.rows=[]
  for sid,pali in self.original.items():
   method="SOURCE_ELLIPSIS_UNEXPANDED" if "…" in pali else "EXPLICIT_EDITORIAL_AI_DRAFT"
   self.rows.append([sid,"mn9",pali,"မြန်မာဘာသာပြန်မူကြမ်း","ရှင်းလင်းချက်မူကြမ်း",
    "AI_DRAFT_UNREVIEWED",method,hashlib.sha256(pali.encode()).hexdigest(),
    "sutta/mn/mn9_root-pli-ms.json","a"*40,"0","",
    "https://example.org/source"])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  self.source.write_text(json.dumps(self.original,ensure_ascii=False),encoding="utf-8")
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(FIELDS);w.writerows(self.rows)
 def test_all_234_unreviewed(self):
  result=verify(self.csv,self.source)
  self.assertEqual(result["mn9_burmese_drafts"],234)
  self.assertFalse(result["release_ready"])
 def test_tampered_source_hash_blocked(self):
  self.rows[0][7]="f"*64;self.save()
  with self.assertRaisesRegex(ValueError,"hash mismatch"):verify(self.csv,self.source)
 def test_false_approval_blocked(self):
  self.rows[0][10]="1";self.save()
  with self.assertRaisesRegex(ValueError,"must not be marked approved"):verify(self.csv,self.source)
 def test_unexpanded_ellipsis_required(self):
  self.rows[0][6]="EXPLICIT_EDITORIAL_AI_DRAFT";self.save()
  with self.assertRaisesRegex(ValueError,"Truncated original"):verify(self.csv,self.source)
 def test_row_count_checked(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,"234"):verify(self.csv,self.source)
 def test_missing_translation_blocked(self):
  self.rows[0][3]="";self.save()
  with self.assertRaisesRegex(ValueError,"Missing Myanmar"):verify(self.csv,self.source)
if __name__=="__main__":unittest.main()
