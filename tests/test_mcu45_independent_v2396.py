"""V2.3.9.6 independent MCU reference fail-closed regression tests."""
import csv, hashlib, json, sqlite3, tempfile, unittest, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from mcu45_independent_reference_v2396 import audit, COLUMNS

class TestIndependentReference(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name)
        self.a,self.s,self.csv,self.m,self.out=[p/n for n in ("a.sqlite","s.sqlite","target.csv","manifest.json","out.json")]
        a=sqlite3.connect(self.a)
        a.executescript("""CREATE TABLE mcu_volume_review(mcu_volume INTEGER PRIMARY KEY,basket TEXT,title TEXT,candidate_segments INTEGER);
        CREATE TABLE segment_assignment(segment_id TEXT PRIMARY KEY,proposed_mcu_volume INTEGER);""")
        for i in range(1,46):
            a.execute("INSERT INTO mcu_volume_review VALUES(?,?,?,?)",(i,"vinaya","Test volume",1 if i==1 else 0))
        a.execute("INSERT INTO segment_assignment VALUES('s1:1.1',1)")
        a.commit();a.close()
        s=sqlite3.connect(self.s)
        s.execute("CREATE TABLE segments(segment_id TEXT PRIMARY KEY,pali TEXT,sha256 TEXT)")
        pali="Sādhu"
        s.execute("INSERT INTO segments VALUES(?,?,?)",("s1:1.1",pali,hashlib.sha256(pali.encode()).hexdigest()))
        s.commit();s.close()
        self.manifest=[{"mcu_volume":i,"complete_independent_corpus":False} for i in range(1,46)]
        self.write([])
    def tearDown(self):self.tmp.cleanup()
    def write(self,rows):
        self.m.write_text(json.dumps({"volumes":self.manifest}))
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f);w.writerow(COLUMNS);w.writerows(rows)
    def run_audit(self):
        return audit(self.a,self.s,self.csv,self.m,self.out)
    def test_empty_independent_reference_does_not_claim_zero_missing(self):
        r=self.run_audit()
        self.assertEqual(r["verified_mcu_books"],0)
        self.assertIsNone(r["volumes"][0]["source_not_in_target"])
        self.assertEqual(r["volumes"][0]["status"],"NO_INDEPENDENT_MCU_CORPUS")
    def test_partial_reference_does_not_claim_completeness(self):
        self.write([[1,"MCU:1","s1:1.1","Sādhu","https://example.org","PENDING"]])
        r=self.run_audit()
        self.assertEqual(r["volumes"][0]["status"],"PARTIAL_MCU_REFERENCE")
        self.assertIsNone(r["volumes"][0]["source_not_in_target"])
    def test_complete_matching_reference_still_is_not_approved(self):
        self.manifest[0].update(complete_independent_corpus=True,edition="MCU",source_url="https://example.org",source_sha256="a"*64,reviewer="editor")
        self.write([[1,"MCU:1","s1:1.1","Sādhu","https://example.org","MATCH_REVIEWED"]])
        r=self.run_audit()
        self.assertEqual(r["volumes"][0]["status"],"EVIDENCE_READY_NOT_APPROVED")
        self.assertFalse(r["volumes"][0]["approved"])
        self.assertEqual(r["volumes"][0]["source_not_in_target"],0)
    def test_duplicate_crosswalk_is_rejected(self):
        self.write([[1,"MCU:1","s1:1.1","Sādhu","https://x","PENDING"],
          [1,"MCU:2","s1:1.1","Sādhu","https://x","PENDING"]])
        with self.assertRaises(ValueError):self.run_audit()

if __name__=="__main__":unittest.main()
