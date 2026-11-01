#!/usr/bin/env python3
"""Synthetic-only regression fixtures for the full offline release gate.

The 45 mock paragraphs are test data, NOT scripture, and MUST NOT be
bundled in Android assets or accepted as a real Tipitaka corpus.
"""
from __future__ import annotations
import csv,datetime,hashlib,importlib.util,pathlib,sqlite3,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("release_audit",ROOT/"scripts/audit_full_offline_release.py")
AUDIT=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(AUDIT)

def fixture(directory: pathlib.Path):
    database=directory/"synthetic-test-only.sqlite"
    crosswalk=directory/"synthetic-test-only-crosswalk.csv"
    rows=[]
    db=sqlite3.connect(database)
    db.executescript("""
    PRAGMA foreign_keys=ON;
    CREATE TABLE volumes(volume INTEGER PRIMARY KEY,title_my TEXT,pitaka TEXT,source_file_prefix TEXT,reviewer_reference TEXT,rights_evidence TEXT);
    CREATE TABLE paragraphs(id INTEGER PRIMARY KEY,volume INTEGER,segment_id TEXT,body TEXT,source_ref TEXT,source_sha256 TEXT);
    CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT);
    CREATE TABLE paragraph_explanations(paragraph_id INTEGER,language TEXT,explanation_my TEXT,source_ref TEXT,provenance TEXT,reviewed INTEGER);
    CREATE TABLE paragraph_myanmar_content(paragraph_id INTEGER,segment_id TEXT,content_type TEXT,text_my TEXT,source_ref TEXT,rights_evidence TEXT,reviewer_1 TEXT,reviewer_2 TEXT,review_reference TEXT,reviewed_at TEXT,source_pali_sha256 TEXT,reviewed INTEGER);
    """)
    db.executemany("INSERT INTO build_info VALUES(?,?)",[
        ("source_commit","fixture-only-do-not-publish"),
        ("edition_mapping","45-volume human-reviewed crosswalk"),
        ("pali_paragraph_count","45")])
    for i in range(1,46):
        segment=f"fixture-segment-{i}";body=f"SYNTHETIC TEST PARAGRAPH NUMBER {i}"
        digest=hashlib.sha256(body.encode()).hexdigest()
        prefix=f"mock_source_{i}";rights="synthetic fixture generated for CI"
        db.execute("INSERT INTO volumes VALUES(?,?,?,?,?,?)",(i,f"ကျမ်း {i}","test",prefix,"synthetic QA reference",rights))
        db.execute("INSERT INTO paragraphs VALUES(?,?,?,?,?,?)",(i,i,segment,body,"test-fixture",digest))
        for content_type,myanmar in [
            ("translation",f"စမ်းသပ်ဒေတာ ဘာသာပြန် {i}"),
            ("explanation",f"စမ်းသပ်ဒေတာ ရှင်းလင်းချက် {i}")
        ]:
            db.execute("INSERT INTO paragraph_myanmar_content VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(
                i,segment,content_type,myanmar,"synthetic fixture","synthetic test permission","TEST Reviewer A","TEST Reviewer B",
                "synthetic QA approval",datetime.date.today().isoformat(),digest,1))
        rows.append({"volume_id":str(i),"book_title_my":f"ကျမ်း {i}","pitaka":"test",
            "source_file_prefix":prefix,"mapping_status":"VERIFIED","reviewer_reference":"synthetic QA reference",
            "start_segment_id":segment,"end_segment_id":segment,"rights_evidence":rights})
    with crosswalk.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    db.commit()
    return db,crosswalk

class ReleaseAuditTests(unittest.TestCase):
    def test_missing_database_is_blocked(self):
        with tempfile.TemporaryDirectory() as d:
            report=AUDIT.audit(pathlib.Path(d)/"none.db",pathlib.Path(d)/"none.csv")
            self.assertFalse(report["ready_for_final_offline_apk"])
            self.assertEqual(report["status"],"BLOCKED")
    def test_synthetic_fully_covered_fixture_passes(self):
        with tempfile.TemporaryDirectory() as d:
            db,crosswalk=fixture(pathlib.Path(d))
            db.close()
            report=AUDIT.audit(pathlib.Path(d)/"synthetic-test-only.sqlite",crosswalk)
            self.assertTrue(report["ready_for_final_offline_apk"],report["errors"])
            self.assertEqual(report["approved_translations"],45)
            self.assertEqual(report["approved_explanations"],45)
            self.assertEqual(report["paragraphs_with_both"],45)
    def test_missing_explanation_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            db,crosswalk=fixture(pathlib.Path(d))
            db.execute("DELETE FROM paragraph_myanmar_content WHERE paragraph_id=1 AND content_type='explanation'")
            db.commit();db.close()
            report=AUDIT.audit(pathlib.Path(d)/"synthetic-test-only.sqlite",crosswalk)
            self.assertFalse(report["ready_for_final_offline_apk"])
            self.assertEqual(report["approved_explanations"],44)
    def test_pali_hash_mismatch_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            db,crosswalk=fixture(pathlib.Path(d))
            db.execute("UPDATE paragraph_myanmar_content SET source_pali_sha256=? WHERE paragraph_id=3",("0"*64,))
            db.commit();db.close()
            report=AUDIT.audit(pathlib.Path(d)/"synthetic-test-only.sqlite",crosswalk)
            self.assertFalse(report["ready_for_final_offline_apk"])
            self.assertTrue(any("hash mismatch" in x.lower() for x in report["errors"]))
    def test_invalid_crosswalk_blocks(self):
        with tempfile.TemporaryDirectory() as d:
            db,crosswalk=fixture(pathlib.Path(d));db.close()
            data=crosswalk.read_text(encoding="utf-8").replace("VERIFIED","UNVERIFIED",1)
            crosswalk.write_text(data,encoding="utf-8")
            report=AUDIT.audit(pathlib.Path(d)/"synthetic-test-only.sqlite",crosswalk)
            self.assertFalse(report["ready_for_final_offline_apk"])
            self.assertEqual(report["verified_crosswalk_volumes"],44)

if __name__=="__main__":unittest.main(verbosity=2)
