"""MN8 fail-closed source hash/translation draft regression fixtures."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn8_editorial_draft import audit,HEADERS,ELLIPSES,LONG
class TestMN8EditorialDraft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name)
  self.csv=self.d/"draft.csv";self.original=self.d/"original.json"
  ids=sorted(ELLIPSES|LONG)+[f"mn8:syn{i}" for i in range(165)]
  self.source={sid:"Pāli …pe…" if sid in ELLIPSES else "Pāli text "+sid for sid in ids}
  self.rows=[]
  for sid,pali in self.source.items():
   method=("SOURCE_ELLIPSIS_UNEXPANDED" if sid in ELLIPSES else
           "LONG_PASSAGE_NEEDS_LITERAL_REVIEW" if sid in LONG else "DIRECT_SEGMENT_AI_DRAFT")
   self.rows.append([sid,"mn8",pali,"မြန်မာဘာသာပြန်မူကြမ်း","ရှင်းလင်းချက်မူကြမ်း",
    "AI_DRAFT_UNREVIEWED",method,hashlib.sha256(pali.encode()).hexdigest(),
    "sutta/mn/mn8_root-pli-ms.json","a"*40,"0","",
    "https://example.org/verified-source"])
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding="utf-8")
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   writer=csv.writer(f);writer.writerow(HEADERS);writer.writerows(self.rows)
 def test_all_170_draft_records_valid(self):
  result=audit(self.csv,self.original)
  self.assertEqual(result["translated_draft_rows"],170)
  self.assertEqual(result["approved"],0)
 def test_false_editorial_approval_fails(self):
  self.rows[0][10]="1";self.write()
  with self.assertRaisesRegex(ValueError,"auto-approved"):audit(self.csv,self.original)
 def test_source_hash_tamper_fails(self):
  self.rows[0][7]="0"*64;self.write()
  with self.assertRaisesRegex(ValueError,"hash mismatch"):audit(self.csv,self.original)
 def test_unexpanded_ellipsis_fails_without_flag(self):
  self.rows[0][6]="DIRECT_SEGMENT_AI_DRAFT";self.write()
  with self.assertRaisesRegex(ValueError,"explicitly flagged"):audit(self.csv,self.original)
 def test_long_passage_review_required(self):
  index=next(i for i,r in enumerate(self.rows) if r[0] in LONG)
  self.rows[index][6]="DIRECT_SEGMENT_AI_DRAFT";self.write()
  with self.assertRaisesRegex(ValueError,"needs detail review"):audit(self.csv,self.original)
 def test_missing_segment_fails(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,"170"):audit(self.csv,self.original)
if __name__=="__main__":unittest.main()
