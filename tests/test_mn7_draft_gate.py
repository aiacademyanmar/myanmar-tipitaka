"""MN7 source-hashed Myanmar editorial draft fail-closed tests (synthetic fixture)."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn7_editorial_draft import check,COLUMNS,ELLIPSES

class TestMN7Draft(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();root=Path(self.t.name)
  self.csv=root/"draft.csv";self.source=root/"source.json"
  ids=sorted(ELLIPSES)+[f"mn7:synthetic{i}" for i in range(144)]
  self.original={sid:("Pāli …pe…" if sid in ELLIPSES else "Pāli text "+sid) for sid in ids}
  self.rows=[]
  for sid,pali in self.original.items():
   self.rows.append([sid,"mn7",pali,"မြန်မာဘာသာပြန်မူကြမ်း","ရှင်းလင်းချက်",
     "AI_DRAFT_UNREVIEWED","SOURCE_ELLIPSIS_UNEXPANDED" if sid in ELLIPSES else "SEGMENT_LEVEL_AI_DRAFT",
     hashlib.sha256(pali.encode()).hexdigest(),"sutta/mn/mn7_root-pli-ms.json","a"*40,"0","","https://example.org"])
  self.save()
 def tearDown(self):self.t.cleanup()
 def save(self):
  self.source.write_text(json.dumps(self.original,ensure_ascii=False),encoding="utf-8")
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(COLUMNS);w.writerows(self.rows)
 def test_complete_147_unreviewed(self):
  self.assertEqual(check(self.csv,self.source)["translation_drafts"],147)
 def test_false_approval_blocked(self):
  self.rows[0][10]="1";self.save()
  with self.assertRaisesRegex(ValueError,"auto approved"):check(self.csv,self.source)
 def test_changed_hash_blocked(self):
  self.rows[0][7]="0"*64;self.save()
  with self.assertRaisesRegex(ValueError,"hash mismatch"):check(self.csv,self.source)
 def test_unexpanded_source_flag_required(self):
  self.rows[0][6]="SEGMENT_LEVEL_AI_DRAFT";self.save()
  with self.assertRaisesRegex(ValueError,"Unexpanded source"):check(self.csv,self.source)
 def test_missing_source_row_blocked(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,"147 rows"):check(self.csv,self.source)

if __name__=="__main__":unittest.main()
