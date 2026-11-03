"""MN20 fail-closed source/translation tests; Pāli fixtures are synthetic, not canonical."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn20_editorial_draft as gate

class TestMN20Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
  self.csv=d/'draft.csv';self.source=d/'source.json'
  ids=sorted(gate.REVIEW_IDS)+[f'mn20:synthetic.{i}' for i in range(79)]
  self.original={sid:'Synthetic Roman Pāli paragraph '+str(i) for i,sid in enumerate(ids)}
  self.rows=[]
  for sid,pali in self.original.items():
   method='CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW' if sid in gate.REVIEW_IDS else 'SEGMENT_ALIGNED_AI_DRAFT'
   self.rows.append([sid,'mn20',pali,'မြန်မာ AI မူကြမ်း','မြန်မာ ရှင်းလင်းချက်',
     'Section','Topic','AI_DRAFT_UNREVIEWED',method,
     hashlib.sha256(pali.encode()).hexdigest(),gate.SOURCE_PATH,'a'*40,
     self.blob(),'0','','https://example.org/source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  b=json.dumps(self.original,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 def save(self):
  self.source.write_text(json.dumps(self.original,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'SOURCE_BLOB',self.blob()):return gate.check(self.csv,self.source)
 def test_87_working_entries(self):
  v=self.check();self.assertEqual(v['source_rows'],87);self.assertEqual(v['scholar_approved'],0);self.assertFalse(v['signed_native_APK'])
 def test_record_count_fails(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'87 source-linked'):self.check()
 def test_source_hash_tamper_fails(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA256 tampered'):self.check()
 def test_false_approval_fails(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto-approved'):self.check()
 def test_missing_burmese_fails(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):self.check()
 def test_review_classification_fails(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'review flag mismatch'):self.check()
 def test_duplicate_id_fails(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate or foreign'):self.check()
 def test_extra_original_ellipsis_fails(self):
  sid='mn20:synthetic.0';self.original[sid]='Extra Pāli …pe…'
  for r in self.rows:
   if r[0]==sid:
    r[2]=self.original[sid];r[9]=hashlib.sha256(r[2].encode()).hexdigest()
  for r in self.rows:r[12]=self.blob()
  self.save()
  with self.assertRaisesRegex(ValueError,'abbreviation inventory'):self.check()
 def test_wrong_source_blob_fails(self):
  self.rows[0][12]='f'*40;self.save()
  with self.assertRaisesRegex(ValueError,'provenance'):self.check()

if __name__=='__main__':unittest.main()
