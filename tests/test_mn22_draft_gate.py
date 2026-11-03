"""MN22 structural draft gate regressions; synthetic Pāli fixtures, not translations."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn22_editorial_draft as gate
class TestMN22Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
  self.csv=d/'draft.csv';self.original=d/'original.json'
  self.source={f'mn22:synthetic.{i}':('Pāli …pe…' if i<30 else 'Pāli synthetic '+str(i)) for i in range(359)}
  self.rows=[]
  for sid,pali in self.source.items():
   ell='…' in pali
   self.rows.append([sid,'mn22',pali,
     'အတိုချုံး [မချဲ့ရသေး]' if ell else 'မြန်မာဘာသာပြန်မူကြမ်း','ရှင်းလင်းချက်',
     'အပိုင်း','အတ္တ','AI_DRAFT_UNREVIEWED',
     'SOURCE_ELLIPSIS_UNEXPANDED' if ell else 'SEGMENT_ALIGNED_AI_DRAFT',
     hashlib.sha256(pali.encode()).hexdigest(),gate.SOURCE_PATH,'a'*40,
     self.blob(),'0','','https://example.org'])
  self.write()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  raw=json.dumps(self.source,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 def write(self):
  self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'SOURCE_BLOB',self.blob()):
   return gate.check(self.csv,self.original)
 def test_all_359_unapproved_drafts(self):
  x=self.check()
  self.assertEqual(x['MN22_source_rows'],359)
  self.assertEqual(x['human_approved'],0)
  self.assertFalse(x['signed_APK_ready'])
 def test_missing_row_rejected(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,'359 Burmese drafts'):self.check()
 def test_source_sha_tamper_rejected(self):
  self.rows[0][9]='0'*64;self.write()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check()
 def test_false_scholar_approval_rejected(self):
  self.rows[0][13]='1';self.write()
  with self.assertRaisesRegex(ValueError,'false approval'):self.check()
 def test_missing_burmese_text_rejected(self):
  self.rows[0][3]='';self.write()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):self.check()
 def test_silent_ellipsis_expansion_rejected(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.write()
  with self.assertRaisesRegex(ValueError,'ellipsis flag wrong'):self.check()
 def test_unexpanded_warning_required(self):
  self.rows[0][3]='မြန်မာ';self.write()
  with self.assertRaisesRegex(ValueError,'show review warning'):self.check()
 def test_duplicate_id_rejected(self):
  self.rows[1][0]=self.rows[0][0];self.write()
  with self.assertRaisesRegex(ValueError,'Duplicate/foreign'):self.check()
 def test_new_ellipsis_in_source_rejected(self):
  sid='mn22:synthetic.50';self.source[sid]='Pāli …pe…'
  for r in self.rows:
   if r[0]==sid:r[2]=self.source[sid];r[9]=hashlib.sha256(r[2].encode()).hexdigest()
  for r in self.rows:r[12]=self.blob()
  self.write()
  with self.assertRaisesRegex(ValueError,'30 abbreviations changed'):self.check()
 def test_published_blob_mismatch_rejected(self):
  with patch.object(gate,'SOURCE_BLOB','0'*40):
   with self.assertRaisesRegex(ValueError,'Git Blob SHA mismatch'):
    gate.check(self.csv,self.original)
if __name__=='__main__':unittest.main()
