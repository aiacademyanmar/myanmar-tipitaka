"""MN15 Pāli/Burmese editorial draft integrity gates; entirely synthetic fixtures."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn15_editorial_draft as gate
class TestMN15Draft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
  self.csv=d/'working_draft.csv';self.original=d/'original.json'
  ids=['mn15:2.2','mn15:4.2']+[f'mn15:synthetic.{i}' for i in range(261)]
  self.source={sid:'Roman Pāli segment '+str(i) for i,sid in enumerate(ids)}
  self.rows=[]
  for sid,pali in self.source.items():
   method='LONG_PASSAGE_NEEDS_LITERAL_REVIEW' if sid in gate.LONG_IDS else 'SEGMENT_ALIGNED_AI_DRAFT'
   self.rows.append([sid,'mn15',pali,'မြန်မာဘာသာပြန်မူကြမ်း','ရှင်းလင်းချက်မူကြမ်း','Section','Topic',
      'AI_DRAFT_UNREVIEWED',method,hashlib.sha256(pali.encode()).hexdigest(),
      gate.SOURCE_PATH,'b'*40,self.blob(),'0','','https://example.org/source'])
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
   return gate.audit(self.csv,self.original)
 def test_263_source_aligned_working_drafts(self):
  r=self.check()
  self.assertEqual(r['source_records'],263)
  self.assertEqual(r['human_approved'],0)
  self.assertFalse(r['native_apk_signed'])
 def test_missing_source_record_rejected(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,'263 MN15'):self.check()
 def test_source_sha_change_rejected(self):
  self.rows[0][9]='0'*64;self.write()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check()
 def test_false_scholar_approval_rejected(self):
  self.rows[0][13]='1';self.write()
  with self.assertRaisesRegex(ValueError,'auto-approved'):self.check()
 def test_missing_burmese_translation_rejected(self):
  self.rows[0][3]='';self.write()
  with self.assertRaisesRegex(ValueError,'Myanmar working draft missing'):self.check()
 def test_two_long_passages_stay_flagged(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.write()
  with self.assertRaisesRegex(ValueError,'long passage review flag'):self.check()
 def test_unexpected_source_ellipsis_rejected(self):
  key='mn15:synthetic.1';self.source[key]='Pāli …pe…'
  for row in self.rows:
   if row[0]==key:
    row[2]='Pāli …pe…';row[9]=hashlib.sha256(row[2].encode()).hexdigest()
  for row in self.rows:row[12]=self.blob()
  self.write()
  with self.assertRaisesRegex(ValueError,'Unexpected MN15 original ellipsis'):self.check()
 def test_missing_source_provenance_rejected(self):
  self.rows[0][12]='0'*40;self.write()
  with self.assertRaisesRegex(ValueError,'Missing pinned source provenance'):self.check()
if __name__=='__main__':unittest.main()
