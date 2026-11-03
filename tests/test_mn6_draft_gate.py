"""MN6 draft-only Pali validation synthetic tests (does not claim scholar approval)."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn6_editorial_draft import validate,HEADERS,ELLIPSES,LONG

class MN6QualityGate(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.root=Path(self.t.name)
  self.csv=self.root/"draft.csv";self.original=self.root/"source.json"
  ids=list(sorted(ELLIPSES|LONG))
  ids+=["mn6:synthetic"+str(i) for i in range(51-len(ids))]
  self.source={sid:"Pāli …pe…" if sid in ELLIPSES else "Pāli text "+str(i) for i,sid in enumerate(ids)}
  self.rows=[]
  for sid,pali in self.source.items():
   method="SOURCE_ELLIPSIS_UNEXPANDED" if sid in ELLIPSES else (
    "LONG_PASSAGE_NEEDS_LITERAL_REVIEW" if sid in LONG else "DIRECT_SEGMENT_EDITORIAL_DRAFT")
   self.rows.append([sid,"mn6",pali,"မြန်မာမူကြမ်း","ရှင်းလင်းချက်",
    "AI_DRAFT_UNREVIEWED",method,hashlib.sha256(pali.encode()).hexdigest(),
    "sutta/mn/mn6_root-pli-ms.json","b"*40,"0","",
    "https://example.org/source"])
  self.write()
 def tearDown(self):self.t.cleanup()
 def write(self):
  self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding="utf-8")
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(HEADERS);w.writerows(self.rows)
 def test_valid_unreviewed_source_rows(self):
  self.assertEqual(validate(self.csv,self.original)["source_segments"],51)
 def test_source_hash_mismatch_fails(self):
  self.rows[0][7]="0"*64;self.write()
  with self.assertRaisesRegex(ValueError,"hash mismatch"):validate(self.csv,self.original)
 def test_false_scholar_approval_fails(self):
  self.rows[0][10]="1";self.write()
  with self.assertRaisesRegex(ValueError,"auto-approved"):validate(self.csv,self.original)
 def test_source_ellipsis_not_falsely_expanded(self):
  i=next(i for i,r in enumerate(self.rows) if r[0] in ELLIPSES)
  self.rows[i][6]="DIRECT_SEGMENT_EDITORIAL_DRAFT";self.write()
  with self.assertRaisesRegex(ValueError,"Unexpanded source"):validate(self.csv,self.original)
 def test_missing_segment_fails(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,"51 rows"):validate(self.csv,self.original)
if __name__=="__main__":unittest.main()
