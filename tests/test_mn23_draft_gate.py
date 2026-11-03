"""MN23 fail-closed draft gate tests with synthetic Pāli fixtures only."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn23_editorial_draft as gate
class TestMN23DraftGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();d=Path(self.tmp.name)
  self.csv=d/'draft.csv';self.source_json=d/'original.json'
  ids=sorted(gate.ELLIPSES)+sorted(gate.SUMMARIES)+[f'mn23:synthetic.{i}' for i in range(95)]
  self.source={sid:('Pāli …pe…' if sid in gate.ELLIPSES else 'Pāli synthetic '+str(i)) for i,sid in enumerate(ids)}
  self.rows=[]
  for sid,pali in self.source.items():
   ell=sid in gate.ELLIPSES
   method='SOURCE_ELLIPSIS_UNEXPANDED' if ell else 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if sid in gate.SUMMARIES else 'SEGMENT_ALIGNED_AI_DRAFT'
   self.rows.append([sid,'mn23',pali,'အတိုချုံး [မချဲ့ရသေး]' if ell else 'မြန်မာမူကြမ်း','ရှင်းလင်းချက်',
    'section','topic','AI_DRAFT_UNREVIEWED',method,hashlib.sha256(pali.encode()).hexdigest(),
    gate.SOURCE_PATH,'b'*40,self.blob(),'0','','https://example.org/source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def blob(self):
  raw=json.dumps(self.source,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 def save(self):
  self.source_json.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'SOURCE_BLOB',self.blob()):
   return gate.check(self.csv,self.source_json)
 def test_104_unapproved_draft_rows(self):
  result=self.check()
  self.assertEqual(result['MN23_original_source_segments'],104)
  self.assertEqual(result['human_approved'],0)
  self.assertFalse(result['signed_native_APK'])
 def test_missing_source_row_rejected(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'104 working draft rows'):self.check()
 def test_source_hash_tamper_rejected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.check()
 def test_false_scholar_approval_rejected(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'marked approved'):self.check()
 def test_missing_burmese_text_rejected(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Empty Burmese'):self.check()
 def test_ellipsis_cannot_be_silently_expanded(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'silently expanded'):self.check()
 def test_long_summary_requires_reviewer(self):
  index=next(i for i,r in enumerate(self.rows) if r[0] in gate.SUMMARIES)
  self.rows[index][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'review flag'):self.check()
 def test_duplicate_segment_rejected(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate'):self.check()
 def test_unexpected_pali_ellipsis_rejected(self):
  self.source['mn23:synthetic.15']='Pāli …pe…';self.save()
  with self.assertRaisesRegex(ValueError,'four source abbreviations changed'):self.check()
 def test_bad_published_source_blob_rejected(self):
  with patch.object(gate,'SOURCE_BLOB','0'*40):
   with self.assertRaisesRegex(ValueError,'Git blob SHA mismatch'):
    gate.check(self.csv,self.source_json)
if __name__=='__main__':unittest.main()
