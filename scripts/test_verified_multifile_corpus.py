#!/usr/bin/env python3
"""Synthetic-only regression tests for the 45-volume multi-file Pali assembler.

These test records ARE NOT Tipitaka and must never ship in an Android APK.
No human-edition approval is inferred from these generated fixtures.
"""
from __future__ import annotations
import csv,hashlib,importlib.util,pathlib,sqlite3,tempfile,unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("multi",ROOT/"scripts/build_verified_multifile_corpus.py")
multi=importlib.util.module_from_spec(spec)
spec.loader.exec_module(multi)
COMMIT="c"*40
COLUMNS_CW=("volume_id","book_title_my","pitaka","source_file_prefix","mapping_status","reviewer_reference","rights_evidence")
COLUMNS_SPAN=("volume_id","span_order","source_file","start_segment_id","end_segment_id",
              "first_sha256","last_sha256","mapping_status","reviewer_reference","rights_evidence","independent_reference")
def write(path,cols,rows):
    with path.open("w",encoding="utf-8",newline="") as fp:
        writer=csv.DictWriter(fp,fieldnames=cols)
        writer.writeheader();writer.writerows(rows)
def fixture(directory):
    src=directory/"TEST_ONLY_source.sqlite"
    crosswalk=directory/"TEST_ONLY_crosswalk.csv"
    spans=directory/"TEST_ONLY_spans.csv"
    db=sqlite3.connect(src)
    db.executescript("CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT);"
        "CREATE TABLE source_segments(segment_id TEXT PRIMARY KEY,body TEXT,source_file TEXT,source_commit TEXT,sha256 TEXT);")
    db.execute("INSERT INTO build_info VALUES('commit',?)",(COMMIT,))
    cw=[];span_rows=[]
    for volume in range(1,46):
        cw.append({"volume_id":volume,"book_title_my":f"စမ်းသပ်ကျမ်း {volume}",
                   "pitaka":"sutta","source_file_prefix":"sutta/test",
                   "mapping_status":"VERIFIED","reviewer_reference":"synthetic-test-only",
                   "rights_evidence":"synthetic-test-only"})
        # Volume 1 has two distinct source files to exercise multi-file spans.
        files=[f"sutta/test/v{volume}a.json",f"sutta/test/v{volume}b.json"] if volume==1 else [f"sutta/test/v{volume}.json"]
        for order,path in enumerate(files,1):
            segment=f"TEST{volume}_{order}"
            body=f"NOT SCRIPTURE synthetic Pali test segment {segment}"
            digest=hashlib.sha256(body.encode("utf-8")).hexdigest()
            db.execute("INSERT INTO source_segments VALUES(?,?,?,?,?)",(segment,body,path,COMMIT,digest))
            span_rows.append({"volume_id":volume,"span_order":order,"source_file":path,
              "start_segment_id":segment,"end_segment_id":segment,"first_sha256":digest,"last_sha256":digest,
              "mapping_status":"VERIFIED","reviewer_reference":"synthetic-test-only",
              "rights_evidence":"synthetic-test-only","independent_reference":"synthetic-test-only"})
    db.commit();db.close()
    write(crosswalk,COLUMNS_CW,cw);write(spans,COLUMNS_SPAN,span_rows)
    return src,crosswalk,spans,span_rows

class MultiFileTests(unittest.TestCase):
    def run_build(self,d,src,cw,spans):
        return multi.build(src,cw,spans,d/"output.sqlite",d/"report.json")

    def test_two_file_volume_and_45_volumes(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp);src,cw,spans,_=fixture(d)
            report=self.run_build(d,src,cw,spans)
            self.assertEqual(report["volumes"],45)
            self.assertEqual(report["spans"],46)
            self.assertEqual(report["pali_paragraphs"],46)
            with sqlite3.connect(d/"output.sqlite") as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM volume_source_spans WHERE volume=1").fetchone()[0],2)
                self.assertEqual(db.execute("SELECT COUNT(DISTINCT volume) FROM paragraphs").fetchone()[0],45)
                self.assertEqual(db.execute("PRAGMA integrity_check").fetchone()[0],"ok")

    def test_unapproved_span_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp);src,cw,spans,records=fixture(d)
            records[0]["mapping_status"]="UNVERIFIED"
            write(spans,COLUMNS_SPAN,records)
            with self.assertRaisesRegex(ValueError,"not approved"):
                self.run_build(d,src,cw,spans)
            self.assertFalse((d/"output.sqlite").exists())

    def test_sha_mismatch_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp);src,cw,spans,records=fixture(d)
            records[0]["first_sha256"]="0"*64
            write(spans,COLUMNS_SPAN,records)
            with self.assertRaisesRegex(ValueError,"hash evidence mismatch"):
                self.run_build(d,src,cw,spans)
            self.assertFalse((d/"output.sqlite").exists())

    def test_segment_reuse_across_volumes_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp);src,cw,spans,records=fixture(d)
            # Same exact source file and segment assigned to volume 2.
            for k in ("source_file","start_segment_id","end_segment_id","first_sha256","last_sha256"):
                records[2][k]=records[0][k]
            write(spans,COLUMNS_SPAN,records)
            with self.assertRaisesRegex(ValueError,"overlaps"):
                self.run_build(d,src,cw,spans)
            self.assertFalse((d/"output.sqlite").exists())

    def test_missing_volume_span_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=pathlib.Path(tmp);src,cw,spans,records=fixture(d)
            write(spans,COLUMNS_SPAN,[r for r in records if r["volume_id"]!=45])
            with self.assertRaisesRegex(ValueError,"spans must be ordered|no mapped Pali segments"):
                self.run_build(d,src,cw,spans)
            self.assertFalse((d/"output.sqlite").exists())

if __name__=="__main__":unittest.main(verbosity=2)
