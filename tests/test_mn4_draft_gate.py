"""Fail-closed MN4 draft intake tests. Synthetic Pāli; no approval workflow."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from import_mn4_editorial_draft import validate_csv,COLUMNS
class TestMN4Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  p=Path(self.tmp.name);self.csv=p/"mn4.csv";self.source=p/"source.json"
  self.obj={f"mn4:{i}.1":"Pāli …pe…" if i in (2,3) else "Pāli text "+str(i) for i in range(165)}
  self.rows=[]
  for i,(sid,pali) in enumerate(self.obj.items()):
   method=("ABBREVIATED_SOURCE_UNEXPANDED" if i in (2,3) else
    "LONG_PASSAGE_PARAPHRASE_REQUIRES_DETAIL_REVIEW" if i in (27,29) else "DIRECT_CONTEXTUAL_AI_DRAFT")
   self.rows.append([sid,"mn4",pali,"မြန်မာမူကြမ်း","ရှင်းလင်းချက်","Section",method,
                    "AI_DRAFT_UNREVIEWED",hashlib.sha256(pali.encode()).hexdigest(),
                    "sutta/mn/mn4_root-pli-ms.json","b"*40,"https://example.org"])
  # Fixture source IDs must match actual flagged names
  for i,sid in ((2,"mn4:5.2"),(3,"mn4:5.3"),(27,"mn4:27.2"),(29,"mn4:29.2")):
   old=self.rows[i][0];self.rows[i][0]=sid
   self.obj[sid]=self.obj.pop(old)
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):
  self.source.write_text(json.dumps(self.obj,ensure_ascii=False))
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(COLUMNS);w.writerows(self.rows)
 def test_synthetic_complete_165_valid(self):
  self.assertEqual(len(validate_csv(self.csv,self.source)),165)
 def test_unapproved_only(self):
  self.rows[0][7]="SCHOLAR_APPROVED";self.write()
  with self.assertRaisesRegex(ValueError,"Cannot auto approve"):validate_csv(self.csv,self.source)
 def test_missing_translation_rejected(self):
  self.rows[0][3]="";self.write()
  with self.assertRaisesRegex(ValueError,"Missing Burmese"):validate_csv(self.csv,self.source)
 def test_hash_mismatch_rejected(self):
  self.rows[0][8]="0"*64;self.write()
  with self.assertRaisesRegex(ValueError,"hash mismatch"):validate_csv(self.csv,self.source)
 def test_wrong_row_count_rejected(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,"Expected 165"):validate_csv(self.csv,self.source)
if __name__=="__main__":unittest.main()
