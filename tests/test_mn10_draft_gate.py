"""MN10 editorial draft-only QA gate tests; synthetic data, not a Pāli translation."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_mn10_editorial_draft import check,FIELDS,METHODS,FOUNDATIONS

class TestMN10DraftSafety(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory()
  self.root=Path(self.t.name)
  self.csv=self.root/'draft.csv';self.orig=self.root/'source.json'
  allmethods=sum(([k]*n for k,n in METHODS.items()),[])
  allfound=sum(([k]*n for k,n in FOUNDATIONS.items()),[])
  self.rows=[];self.original={}
  for i in range(235):
   sid=f'mn10:synthetic-{i:03d}'
   method=allmethods[i]
   pali='Pāli …pe…' if method=='SOURCE_ELLIPSIS_UNEXPANDED' else 'Pāli segment '+str(i)
   self.original[sid]=pali
   self.rows.append([sid,'mn10',pali,'မြန်မာမူကြမ်း','ရှင်းလင်းချက်',
     allfound[i],'review section','AI_DRAFT_UNREVIEWED',method,
     hashlib.sha256(pali.encode()).hexdigest(),
     'sutta/mn/mn10_root-pli-ms.json','a'*40,'0','',
     'https://example.org/original'])
  self.save()
 def tearDown(self):self.t.cleanup()
 def save(self):
  self.orig.write_text(json.dumps(self.original,ensure_ascii=False),encoding='utf-8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(FIELDS);w.writerows(self.rows)
 def test_complete_235_source_drafts(self):
  r=check(self.csv,self.orig)
  self.assertEqual(r['source_segments'],235)
  self.assertFalse(r['release_ready'])
  self.assertEqual(r['human_approved'],0)
 def test_hash_tampering_detected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'hash mismatch'):check(self.csv,self.orig)
 def test_false_approval_blocked(self):
  self.rows[0][12]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto approve'):check(self.csv,self.orig)
 def test_missing_burmese_draft_blocked(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):check(self.csv,self.orig)
 def test_unexpanded_source_flag_mandatory(self):
  row=next(r for r in self.rows if '…' in r[2])
  row[8]='DIRECT_EDITORIAL_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'remain unexpanded'):check(self.csv,self.orig)
 def test_malformed_source_count_fails(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'Exactly 235'):check(self.csv,self.orig)
if __name__=='__main__':unittest.main()
