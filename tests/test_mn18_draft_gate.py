"""MN18 unreviewed draft editorial QA: eight fail-closed synthetic tests."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn18_editorial_draft as gate
class TestMN18(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();p=Path(self.t.name)
  self.csv=p/'draft.csv';self.original=p/'source.json'
  ids=sorted(gate.ELLIPSIS)+sorted(gate.LONG)+[f'mn18:synthetic-{i}' for i in range(123)]
  self.src={k:('Pāli …pe…' if k in gate.ELLIPSIS else 'Pāli '+k) for k in ids}
  self.rows=[]
  for sid,v in self.src.items():
   m='SOURCE_ELLIPSIS_UNEXPANDED' if sid in gate.ELLIPSIS else 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if sid in gate.LONG else 'SEGMENT_ALIGNED_AI_DRAFT'
   self.rows.append([sid,'mn18',v,'မူကြမ်း မချဲ့ရသေး' if sid in gate.ELLIPSIS else 'မြန်မာမူကြမ်း','ရှင်းလင်းချက်','1','topic','AI_DRAFT_UNREVIEWED',m,hashlib.sha256(v.encode()).hexdigest(),gate.SOURCE,'a'*40,self.blob(),'0','','https://example.org'])
  self.save()
 def tearDown(self):self.t.cleanup()
 def blob(self):
  r=json.dumps(self.src,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(r)).encode()+b'\0'+r).hexdigest()
 def save(self):
  self.original.write_text(json.dumps(self.src,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
 def check(self):
  with patch.object(gate,'BLOB',self.blob()):return gate.validate(self.csv,self.original)
 def test_all_150_working_drafts(self):
  v=self.check();self.assertEqual(v['MN18_source'],150);self.assertEqual(v['scholar_approved'],0)
 def test_missing_segment(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'150 draft records'):self.check()
 def test_source_sha_tamper(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'hash differs'):self.check()
 def test_false_approval(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'No auto-approval'):self.check()
 def test_blank_burmese_translation(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):self.check()
 def test_source_ellipsis_not_silently_expanded(self):
  self.rows[0][3]='မူကြမ်း';self.save()
  with self.assertRaisesRegex(ValueError,'stay explicit'):self.check()
 def test_nine_long_review_flags(self):
  ix=next(i for i,r in enumerate(self.rows) if r[0] in gate.LONG)
  self.rows[ix][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'classification mismatch'):self.check()
 def test_published_source_mismatch(self):
  with patch.object(gate,'BLOB','0'*40):
   with self.assertRaisesRegex(ValueError,'Git blob mismatch'):gate.validate(self.csv,self.original)
if __name__=='__main__':unittest.main()
