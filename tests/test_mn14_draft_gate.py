"""MN14 fail-closed Pāli/Myanmar draft gate tests; synthetic text fixtures only."""
import csv,hashlib,json,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import validate_mn14_editorial_draft as gate
class TestMN14DraftGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory()
  self.csv=Path(self.tmp.name)/'draft.csv'
  self.original=Path(self.tmp.name)/'source.json'
  self.missing_db=Path(self.tmp.name)/'missing.sqlite'
  self.source={};self.rows=[]
  for i in range(144):
   sid='mn14:13.3' if i==143 else f'mn14:synthetic.{i}'
   method='SOURCE_ELLIPSIS_UNEXPANDED' if i<13 else ('CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if i==143 else 'SEGMENT_LEVEL_WORKING_TRANSLATION')
   pali='Pāli …pe…' if i<13 else 'Pāli segment '+str(i)
   self.source[sid]=pali
   self.rows.append([sid,'mn14',pali,
    'အတိုချုံး [မချဲ့ရသေး]' if i<13 else 'မြန်မာမူကြမ်း',
    'ရှင်းလင်းချက်','Section',1,'AI_DRAFT_UNREVIEWED',method,
    hashlib.sha256(pali.encode()).hexdigest(),
    'sutta/mn/mn14_root-pli-ms.json','a'*40,gate.BLOB,'0','',
    'https://example.org/source'])
  self.save()
 def tearDown(self):self.tmp.cleanup()
 def save(self):
  self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding='utf8')
  with self.csv.open('w',encoding='utf-8-sig',newline='') as f:
   w=csv.writer(f);w.writerow(gate.COLUMNS);w.writerows(self.rows)
 def validate_synthetic(self,combined=None):
  s=json.dumps(list(self.source.items()),ensure_ascii=False,separators=(',',':'))
  ck=0
  for ch in s:ck=(ck*131+ord(ch))%1000000007
  with patch.object(gate,'EXPECTED_SOURCE_CHARS',len(s)),patch.object(gate,'EXPECTED_SOURCE_ROLLING',ck):
   return gate.validate(self.csv,self.original,combined)
 def test_all_144_unapproved_working_drafts(self):
  r=self.validate_synthetic()
  self.assertEqual(r['source_segments'],144)
  self.assertEqual(r['human_approved'],0)
  self.assertFalse(r['APK_ready'])
 def test_wrong_number_of_rows_rejected(self):
  self.rows.pop();self.save()
  with self.assertRaisesRegex(ValueError,'144 records'):self.validate_synthetic()
 def test_source_pali_hash_tampered_rejected(self):
  self.rows[0][9]='0'*64;self.save()
  with self.assertRaisesRegex(ValueError,'SHA mismatch'):self.validate_synthetic()
 def test_false_scholar_approval_rejected(self):
  self.rows[0][13]='1';self.save()
  with self.assertRaisesRegex(ValueError,'auto-approved'):self.validate_synthetic()
 def test_missing_translation_rejected(self):
  self.rows[0][3]='';self.save()
  with self.assertRaisesRegex(ValueError,'Empty Myanmar'):self.validate_synthetic()
 def test_ellipsis_must_remain_unexpanded(self):
  self.rows[0][8]='SEGMENT_LEVEL_WORKING_TRANSLATION';self.save()
  with self.assertRaisesRegex(ValueError,'Unexpanded original'):self.validate_synthetic()
 def test_long_summary_requires_review_flag(self):
  self.rows[-1][8]='SEGMENT_LEVEL_WORKING_TRANSLATION';self.save()
  with self.assertRaisesRegex(ValueError,'13\+1 changed'):self.validate_synthetic()
 def test_missing_combined_db_rejected(self):
  with self.assertRaises(sqlite3.OperationalError):self.validate_synthetic(self.missing_db)
if __name__=='__main__':unittest.main()
