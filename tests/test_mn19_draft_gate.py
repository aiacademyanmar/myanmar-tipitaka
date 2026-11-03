"""MN19 fail-closed QA regression tests with synthetic Pāli fixtures only."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn19_editorial_draft as gate

class TestMN19Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name)
  self.csv=p/'draft.csv';self.source=p/'source.json'
  ids=sorted(gate.ELLIPSES)+[f'mn19:synthetic.{i}' for i in range(117)]
  self.original={sid:('Roman Pāli …pe…' if sid in gate.ELLIPSES else 'Roman Pāli paragraph '+str(i)) for i,sid in enumerate(ids)}
  self.rows=[]
  for sid,pali in self.original.items():
   ell=sid in gate.ELLIPSES
   self.rows.append([sid,'mn19',pali,
    'အတိုချုံး [မချဲ့ရသေး]' if ell else 'မြန်မာဘာသာပြန်မူကြမ်း',
    'ရှင်းလင်းချက်မူကြမ်း','Section','Topic','AI_DRAFT_UNREVIEWED',
    'SOURCE_ELLIPSIS_UNEXPANDED' if ell else 'SEGMENT_ALIGNED_AI_DRAFT',
    hashlib.sha256(pali.encode()).hexdigest(),gate.SOURCE_PATH,'a'*40,
    self.blob(),'0','','https://example.org/source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  b=json.dumps(self.original,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 def save(self):
  self.source.write_text(json.dumps(self.original,ensure_ascii=False),encoding='utf-8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'SOURCE_BLOB',self.blob()):return gate.check(self.csv,self.source)
 def test_123_source_aligned_drafts(self):
  r=self.check()
  self.assertEqual(r['source_rows'],123)
  self.assertEqual(r['scholar_approved'],0)
  self.assertFalse(r['signed_native_APK'])
 def test_missing_record_fails(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'123 source-linked'):self.check()
 def test_sha_tamper_fails(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA256 tampered'):self.check()
 def test_false_approval_fails(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto-approved'):self.check()
 def test_blank_translation_fails(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):self.check()
 def test_silent_ellipsis_expansion_fails(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'visibly unexpanded'):self.check()
 def test_ellipsis_warning_required(self):
  self.rows[0][3]='မြန်မာဘာသာပြန်';self.save()
  with self.assertRaisesRegex(ValueError,'visibly marked'):self.check()
 def test_duplicate_source_id_fails(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate or foreign'):self.check()
 def test_unexpected_source_ellipsis_fails(self):
  sid='mn19:synthetic.5';self.original[sid]='Pāli …pe…'
  for r in self.rows:
   if r[0]==sid:r[2]=self.original[sid];r[9]=hashlib.sha256(r[2].encode()).hexdigest()
  for r in self.rows:r[12]=self.blob()
  self.save()
  with self.assertRaisesRegex(ValueError,'abbreviation inventory'):self.check()
 def test_bad_provenance_fails(self):
  self.rows[0][12]='0'*40;self.save()
  with self.assertRaisesRegex(ValueError,'source provenance'):self.check()
if __name__=='__main__':unittest.main()
