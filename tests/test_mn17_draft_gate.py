"""MN17 synthetic Pāli/Burmese draft QA regressions; never scholarly approval."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import validate_mn17_editorial_draft as gate
class TestMN17(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();d=Path(self.temp.name)
  self.csv=d/"draft.csv";self.src=d/"original.json"
  ids=sorted(gate.ELLIPSIS)+[f"mn17:synthetic.{i}" for i in range(75)]
  self.data={sid:("Pāli …pe…" if sid in gate.ELLIPSIS else "Pāli text "+sid) for sid in ids}
  self.rows=[]
  for sid,pali in self.data.items():
   ell=sid in gate.ELLIPSIS
   self.rows.append([sid,"mn17",pali,
     "မြန်မာမူကြမ်း [မချဲ့ရသေး]" if ell else "မြန်မာမူကြမ်း",
     "ရှင်းလင်းချက်","Section","Topic","AI_DRAFT_UNREVIEWED",
     "SOURCE_ELLIPSIS_UNEXPANDED" if ell else "SEGMENT_ALIGNED_AI_DRAFT",
     hashlib.sha256(pali.encode()).hexdigest(),gate.PATH,"a"*40,
     self.blob(),"0","","https://example.org"])
  self.save()
 def tearDown(self):self.temp.cleanup()
 def blob(self):
  raw=json.dumps(self.data,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 def save(self):
  self.src.write_text(json.dumps(self.data,ensure_ascii=False),encoding="utf-8")
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,"BLOB",self.blob()):
   return gate.check(self.csv,self.src)
 def test_all_83_working_records(self):
  d=self.check()
  self.assertEqual(d["source_pali"],83)
  self.assertFalse(d["signed_APK"])
 def test_missing_source_record(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,"83 draft records"):self.check()
 def test_sha_mismatch(self):
  self.rows[0][9]="0"*64;self.save()
  with self.assertRaisesRegex(ValueError,"SHA mismatch"):self.check()
 def test_no_false_approval(self):
  self.rows[0][13]="1";self.save()
  with self.assertRaisesRegex(ValueError,"Never auto approve"):self.check()
 def test_no_missing_burmese(self):
  self.rows[0][3]="";self.save()
  with self.assertRaisesRegex(ValueError,"Empty Burmese"):self.check()
 def test_no_silent_ellipsis_expansion(self):
  self.rows[0][8]="SEGMENT_ALIGNED_AI_DRAFT";self.save()
  with self.assertRaisesRegex(ValueError,"must be unexpanded"):self.check()
 def test_explicit_ellipsis_warning_required(self):
  self.rows[0][3]="မြန်မာအဓိပ္ပာယ်";self.save()
  with self.assertRaisesRegex(ValueError,"explicit source abbreviation"):self.check()
 def test_unexpected_abbreviation_id(self):
  sid="mn17:synthetic.1";self.data[sid]="Pāli …pe…"
  for r in self.rows:
   if r[0]==sid:
    r[2]=self.data[sid]
    r[9]=hashlib.sha256(r[2].encode()).hexdigest()
  for r in self.rows:r[12]=self.blob()
  self.save()
  with self.assertRaisesRegex(ValueError,"ellipsis ID mismatch"):self.check()
if __name__=="__main__":unittest.main()
