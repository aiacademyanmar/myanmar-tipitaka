"""MN11 AI draft only integrity gate; synthetic unit tests, no editorial sign-off."""
import csv,hashlib,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from validate_mn11_editorial_draft import audit,HEADERS,DIRECT,LONG

class TestMN11EditorialDraft(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();p=Path(self.tmp.name)
  self.csv=p/'draft.csv';self.source=p/'source.json';self.db=p/'missing.sqlite'
  self.original={};self.rows=[]
  for i in range(132):
   sid=f'mn11:test.{i}'
   pali=('Dīgha Roman Pāli text '*20 if i==131 else 'Roman Pāli segment '+str(i))
   self.original[sid]=pali
   self.rows.append([sid,'mn11',pali,'မြန်မာဘာသာပြန်မူကြမ်း','ရှင်းလင်းချက်မူကြမ်း',
      'Dhamma','mn11','AI_DRAFT_UNREVIEWED',LONG if i==131 else DIRECT,
      hashlib.sha256(pali.encode()).hexdigest(),'sutta/mn/mn11_root-pli-ms.json',
      'b'*40,'0','','https://example.org/original-source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  self.source.write_text(json.dumps(self.original,ensure_ascii=False),encoding='utf-8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(HEADERS);w.writerows(self.rows)
 def test_all_132_unreviewed_pass(self):
  d=audit(self.csv,self.source)
  self.assertEqual(d['Burmese_translation_drafts'],132)
  self.assertFalse(d['final_APK_release_ready'])
 def test_sha_mismatch_rejected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):audit(self.csv,self.source)
 def test_false_scholar_approval_rejected(self):
  self.rows[0][12]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto-approved'):audit(self.csv,self.source)
 def test_missing_burmese_rejected(self):
  self.rows[0][4]='';self.save()
  with self.assertRaisesRegex(ValueError,'Missing Burmese'):audit(self.csv,self.source)
 def test_unexpected_pali_ellipsis_rejected(self):
  self.rows[0][2]='Pāli …pe…'
  self.rows[0][9]=hashlib.sha256(self.rows[0][2].encode()).hexdigest()
  self.original[self.rows[0][0]]=self.rows[0][2];self.save()
  with self.assertRaisesRegex(ValueError,'Unexpected original source abbreviation'):
   audit(self.csv,self.source)
 def test_missing_source_segment_rejected(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'exactly 132'):audit(self.csv,self.source)
 def test_long_passage_requires_review_flag(self):
  self.rows[-1][8]=DIRECT;self.save()
  with self.assertRaisesRegex(ValueError,'Long-passage review flag missing'):
   audit(self.csv,self.source)
 def test_combined_database_absent_rejected(self):
  with self.assertRaises(sqlite3.OperationalError):audit(self.csv,self.source,self.db)
if __name__=='__main__':unittest.main()
