"""MN21 fail-closed regression tests with synthetic Pāli fixture; not translation verification."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn21_editorial_draft as gate

class TestMN21DraftGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
  self.csv=d/'draft.csv';self.original=d/'source.json'
  ids=sorted(gate.ELLIPSES)+[f'mn21:synthetic.{i}' for i in range(225)]
  self.source={sid:('Pāli …pe…' if sid in gate.ELLIPSES else 'Pāli text '+sid) for sid in ids}
  self.rows=[]
  for sid,pali in self.source.items():
   ell=sid in gate.ELLIPSES
   self.rows.append([sid,'mn21',pali,'အတိုချုံး [မချဲ့ရသေး]' if ell else 'မြန်မာမူကြမ်း','မြန်မာရှင်းလင်းချက်','Section','Topic','AI_DRAFT_UNREVIEWED','SOURCE_ELLIPSIS_UNEXPANDED' if ell else 'SEGMENT_ALIGNED_AI_DRAFT',hashlib.sha256(pali.encode()).hexdigest(),gate.PATH,'a'*40,self.blob(),'0','','https://example.org/source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  b=json.dumps(self.source,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 def save(self):
  self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'BLOB',self.blob()):
   return gate.validate(self.csv,self.original)
 def test_227_source_draft_rows(self):
  result=self.check();self.assertEqual(result['source_rows'],227)
  self.assertEqual(result['human_approved'],0)
  self.assertFalse(result['signed_APK'])
 def test_missing_record_fails(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'227 rows'):self.check()
 def test_pali_hash_tamper_fails(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check()
 def test_false_scholar_approval_fails(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto-approved'):self.check()
 def test_missing_burmese_fails(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Burmese draft missing'):self.check()
 def test_silent_ellipsis_expansion_fails(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'explicit flag'):self.check()
 def test_visible_ellipsis_warning_required(self):
  self.rows[0][3]='မြန်မာဘာသာပြန်';self.save()
  with self.assertRaisesRegex(ValueError,'falsely expanded'):self.check()
 def test_duplicate_source_id_fails(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate or invalid'):self.check()
 def test_missing_provenance_fails(self):
  self.rows[0][12]='0'*40;self.save()
  with self.assertRaisesRegex(ValueError,'provenance missing'):self.check()
 def test_unexpected_ellipsis_fails(self):
  sid='mn21:synthetic.0';self.source[sid]='Pāli …pe…'
  for r in self.rows:
   if r[0]==sid:r[2]=self.source[sid];r[9]=hashlib.sha256(r[2].encode()).hexdigest()
  for r in self.rows:r[12]=self.blob()
  self.save()
  with self.assertRaisesRegex(ValueError,'abbreviation inventory changed'):self.check()

if __name__=='__main__':unittest.main()
