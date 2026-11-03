"""MN12 working draft QA regression tests using synthetic content, not canonical Pali."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_mn12_editorial_draft import audit,COLS
class MN12GateTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();p=Path(self.t.name)
  self.csv=p/'draft.csv';self.src=p/'original.json'
  self.source={};self.rows=[]
  for i in range(372):
   sid=f'mn12:test{i}.1';method=('SEGMENT_LEVEL_WORKING_TRANSLATION' if i<256 else
     'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if i<360 else 'SOURCE_ELLIPSIS_UNEXPANDED')
   pali='Pāli …pe…' if i>=360 else 'Synthetic Pāli '+str(i)
   self.source[sid]=pali
   self.rows.append([sid,'mn12',pali,'မြန်မာမူကြမ်း','ရှင်းလင်းချက်','section','topic',
    'AI_DRAFT_UNREVIEWED',method,hashlib.sha256(pali.encode()).hexdigest(),
    'sutta/mn/mn12_root-pli-ms.json','a'*40,'0','',
    'https://example.org/source'])
  self.write()
 def tearDown(self):self.t.cleanup()
 def write(self):
  self.src.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf-8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(COLS);w.writerows(self.rows)
 def test_372_working_records(self):
  x=audit(self.csv,self.src)
  self.assertEqual(x['MN12_source'],372)
  self.assertEqual(x['contextual_summaries_not_literal'],104)
  self.assertFalse(x['release_ready'])
 def test_invalid_hash(self):
  self.rows[0][9]='0'*64;self.write()
  with self.assertRaisesRegex(ValueError,'hash mismatch'):audit(self.csv,self.src)
 def test_approval_not_allowed(self):
  self.rows[0][12]='1';self.write()
  with self.assertRaisesRegex(ValueError,'auto-approved'):audit(self.csv,self.src)
 def test_missing_burmese_field(self):
  self.rows[0][3]='';self.write()
  with self.assertRaisesRegex(ValueError,'Missing Myanmar'):audit(self.csv,self.src)
 def test_unexpanded_source_flag_required(self):
  self.rows[-1][8]='SEGMENT_LEVEL_WORKING_TRANSLATION';self.write()
  with self.assertRaisesRegex(ValueError,'not flagged'):audit(self.csv,self.src)
 def test_missing_segment(self):
  self.rows.pop();self.write()
  with self.assertRaisesRegex(ValueError,'372 Myanmar'):audit(self.csv,self.src)
if __name__=='__main__':unittest.main()
