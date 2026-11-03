"""MN13 fail-closed source/editorial coverage tests using synthetic text.

No synthetic test is treated as a real scholarly translation.
"""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn13_editorial_draft as gate

class TestMN13(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name)
  self.csv=p/'mn13.csv';self.orig=p/'original.json'
  self.data={}
  for i in range(152):
   sid=f'mn13:test.{i}'
   self.data[sid]='Pāli text '+str(i)+(' …pe…' if i>=147 else '')
  # Pad synthetic original to exact expected canonical JSON length, without claiming canonical content.
  def encode():return json.dumps(list(self.data.items()),ensure_ascii=False,separators=(',',':'))
  self.data['mn13:test.1']+='x'*(17585-len(encode()))
  self.checksum=0
  for c in encode():self.checksum=(self.checksum*131+ord(c))%1000000007
  self.rows=[]
  for i,(sid,pali) in enumerate(self.data.items()):
   method='SOURCE_ELLIPSIS_UNEXPANDED' if i>=147 else (
     'CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW' if i>=125 else
     'SEGMENT_LEVEL_WORKING_TRANSLATION')
   self.rows.append([sid,'mn13',pali,'မြန်မာမူကြမ်း','ရှင်းလင်းချက်',
    'နိဒါန်း','ကာမ','AI_DRAFT_UNREVIEWED',method,
    hashlib.sha256(pali.encode('utf8')).hexdigest(),
    gate.SOURCE,gate.BLOB,'0','',
    'https://github.com/suttacentral/bilara-data/'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  self.orig.write_text(json.dumps(self.data,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   writer=csv.writer(f);writer.writerow(gate.FIELDS);writer.writerows(self.rows)
 def audited(self):
  with patch.object(gate,'CHECKSUM',self.checksum):
   return gate.audit(self.csv,self.orig)
 def test_152_working_draft_rows(self):
  self.assertEqual(self.audited()['source_segments'],152)
  self.assertFalse(self.audited()['release_ready'])
 def test_false_scholar_approval_blocked(self):
  self.rows[0][12]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto approve'):self.audited()
 def test_hash_tamper_rejected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.audited()
 def test_missing_translation_rejected(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Myanmar'):self.audited()
 def test_ellipsis_flag_required(self):
  self.rows[-1][8]='SEGMENT_LEVEL_WORKING_TRANSLATION';self.save()
  with self.assertRaisesRegex(ValueError,'Unexpanded source'):self.audited()
 def test_wrong_method_count_rejected(self):
  self.rows[0][8]='CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW';self.save()
  with self.assertRaisesRegex(ValueError,'inventory changed'):self.audited()
 def test_missing_segment_rejected(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'152 MN13'):self.audited()
 def test_source_content_tamper_rejected(self):
  self.data['mn13:test.0']='other';self.save()
  with self.assertRaisesRegex(ValueError,'source text-checksum mismatch'):self.audited()
if __name__=='__main__':unittest.main()
