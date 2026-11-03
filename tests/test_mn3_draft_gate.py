"""MN3 draft quality gate synthetic tests; no permission to approve draft text."""
import csv,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from validate_mn3_editorial_draft import check,COLUMNS

class TestMN3DraftGate(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
  self.csv=self.root/"data.csv";self.db=self.root/"draft.sqlite"
 def tearDown(self):self.tmp.cleanup()
 def make_csv(self,approved=False,invalid_hash=False):
  with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(COLUMNS)
   for i in range(128):
    p="Pāli …" if i<3 else "Pāli source"
    sha=hashlib.sha256(p.encode()).hexdigest()
    if invalid_hash and i==0:sha="0"*64
    w.writerow([f"mn3:{i}.1",p,"မြန်မာမူကြမ်း","ရှင်းလင်းချက်","စာပိုဒ်",
       "SCHOLAR_APPROVED" if approved and i==0 else "AI_DRAFT_UNREVIEWED",
       "ELLIPSIS_SOURCE_REQUIRES_EXPANSION" if i<3 else "DIRECT_SEGMENT_AI_DRAFT",
       sha,"file.json","0"*40])
 def test_missing_combined_db_rejected_after_checks(self):
  self.make_csv()
  with self.assertRaises(Exception):check(self.csv,self.db)
 def test_false_approval_rejected_without_db(self):
  self.make_csv(approved=True)
  with self.assertRaisesRegex(ValueError,"Unapproved content marked reviewed"):check(self.csv,self.db)
 def test_bad_sha_rejected_without_db(self):
  self.make_csv(invalid_hash=True)
  with self.assertRaisesRegex(ValueError,"hash mismatch"):check(self.csv,self.db)
 def test_wrong_count_rejected(self):
  self.csv.write_text(",".join(COLUMNS)+"\n",encoding="utf-8-sig")
  with self.assertRaises(ValueError):check(self.csv,self.db)

if __name__=="__main__":unittest.main()
