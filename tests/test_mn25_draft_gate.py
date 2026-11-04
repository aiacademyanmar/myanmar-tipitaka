"""MN25 strict editorial integrity tests using synthetic Roman Pāli.

These tests cannot assert that Burmese translations are scholar approved.
"""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn25_editorial_draft as gate
class MN25DraftGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name)
  self.csv=p/'draft.csv';self.src=p/'pali.json'
  self.source={f'mn25:synthetic.{i}':('Pāli …pe…' if i<25 else 'Pāli synthetic '+str(i)) for i in range(199)}
  self.rows=[]
  for i,(sid,pli) in enumerate(self.source.items()):
   method='SOURCE_ELLIPSIS_UNEXPANDED' if i<25 else 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if i<37 else 'SEGMENT_ALIGNED_AI_DRAFT'
   my='အတိုချုံး [မချဲ့ရသေး]' if i<25 else 'အဓိပ္ပာယ်အနှစ်ချုပ် — အပြည့်ပြန်စစ်ရန်' if i<37 else 'မြန်မာဘာသာပြန်မူကြမ်း'
   self.rows.append([sid,'mn25',pli,my,'မြန်မာရှင်းလင်းချက်','Section','Topic',
    'AI_DRAFT_UNREVIEWED',method,hashlib.sha256(pli.encode()).hexdigest(),
    gate.SOURCE_PATH,'a'*40,self.blob(),'0','','https://example.org'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  b=json.dumps(self.source,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
 def save(self):
  self.src.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'BLOB',self.blob()):return gate.check(self.csv,self.src)
 def test_199_source_records(self):
  x=self.check();self.assertEqual(x['source_segments'],199);self.assertEqual(x['scholar_approved'],0);self.assertFalse(x['native_APK_built'])
 def test_missing_source_row_fails(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'199 MN25'):self.check()
 def test_source_hash_tamper_fails(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check()
 def test_false_scholar_approval_fails(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'False human approval'):self.check()
 def test_missing_translation_fails(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Myanmar'):self.check()
 def test_ellipsis_unexpanded_flag_fails(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'ellipsis classification incorrect'):self.check()
 def test_ellipsis_warning_required(self):
  self.rows[0][3]='မြန်မာ';self.save()
  with self.assertRaisesRegex(ValueError,'visible warning'):self.check()
 def test_contextual_summary_warning_required(self):
  self.rows[30][3]='မူကြမ်း';self.save()
  with self.assertRaisesRegex(ValueError,'visible warning'):self.check()
 def test_duplicate_segment_id_fails(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate/foreign'):self.check()
 def test_source_blob_immutable(self):
  with patch.object(gate,'BLOB','0'*40):
   with self.assertRaisesRegex(ValueError,'published Git blob mismatch'):gate.check(self.csv,self.src)
if __name__=='__main__':unittest.main()
