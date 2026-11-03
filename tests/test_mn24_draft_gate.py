"""MN24 source and unreviewed-editorial gate regressions on synthetic fixtures only."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn24_editorial_draft as g
class TestMN24(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();d=Path(self.t.name);self.csv=d/'draft.csv';self.orig=d/'original.json'
  ids=sorted(g.ELLIPSES)+sorted(g.SUMMARIES)+[f'mn24:synthetic.{i}' for i in range(124)]
  self.src={k:'Pāli '+str(i)+(' …pe…' if k in g.ELLIPSES else '') for i,k in enumerate(ids)}
  self.rows=[]
  for k,v in self.src.items():
   ell=k in g.ELLIPSES
   meth='SOURCE_ELLIPSIS_UNEXPANDED' if ell else 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if k in g.SUMMARIES else 'SEGMENT_ALIGNED_AI_DRAFT'
   self.rows.append([k,'mn24',v,'အတိုချုံး မချဲ့ရသေး' if ell else 'မြန်မာမူကြမ်း','မြန်မာရှင်းလင်းချက်',
    'Section','Topic','AI_DRAFT_UNREVIEWED',meth,hashlib.sha256(v.encode()).hexdigest(),g.SOURCE_PATH,
    'a'*40,self.blob(),'0','','https://example.org'])
  self.save()
 def tearDown(self):self.t.cleanup()
 def blob(self):
  x=json.dumps(self.src,ensure_ascii=False,indent=2).encode()
  return hashlib.sha1(b'blob '+str(len(x)).encode()+b'\0'+x).hexdigest()
 def save(self):
  self.orig.write_text(json.dumps(self.src,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(g.FIELDS);w.writerows(self.rows)
 def verify(self):
  with patch.object(g,'BLOB',self.blob()):return g.check(self.csv,self.orig)
 def test_complete_and_unapproved(self):
  r=self.verify();self.assertEqual(r['working_draft_rows'],139);self.assertEqual(r['scholar_approved'],0);self.assertFalse(r['native_release_APK'])
 def test_removed_record_rejected(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'139 MN24 Burmese'):self.verify()
 def test_pali_hash_tamper_rejected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'Pali source SHA mismatch'):self.verify()
 def test_false_approval_rejected(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'False scholarly approval'):self.verify()
 def test_missing_burmese_rejected(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):self.verify()
 def test_source_ellipsis_must_remain_unexpanded(self):
  self.rows[0][8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'visibly unexpanded'):self.verify()
 def test_summary_must_remain_flagged(self):
  row=next(r for r in self.rows if r[0] in g.SUMMARIES)
  row[8]='SEGMENT_ALIGNED_AI_DRAFT';self.save()
  with self.assertRaisesRegex(ValueError,'literal review flag'):self.verify()
 def test_duplicate_id_rejected(self):
  self.rows[1][0]=self.rows[0][0];self.save()
  with self.assertRaisesRegex(ValueError,'Duplicate or foreign'):self.verify()
 def test_source_blob_tamper_rejected(self):
  with patch.object(g,'BLOB','0'*40):
   with self.assertRaisesRegex(ValueError,'Git Blob SHA differs'):g.check(self.csv,self.orig)
 def test_unexpected_source_abbreviation_rejected(self):
  self.src['mn24:synthetic.4']='Pāli …pe…';self.save()
  with self.assertRaisesRegex(ValueError,'9 Pali abbreviated'):self.verify()
if __name__=='__main__':unittest.main()
