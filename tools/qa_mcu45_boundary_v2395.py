#!/usr/bin/env python3
"""V2.3.9.5 fail-closed QA gate for the 45-volume source paragraph review DB.

Checks exported source-candidate accounting and reviewer evidence.
Passing this QA gate does NOT certify MCU paragraph/edition equivalence.
The independent MCU target corpus and actual reviewer sign-off are still required.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

BASELINE={"source_segments":444701,"candidate_segments":425953,"scope_exceptions":18748}

def validate(qa_path, source_path=None):
    db=sqlite3.connect("file:"+str(Path(qa_path).resolve())+"?mode=ro",uri=True)
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("Review SQLite integrity check failed")
        n=db.execute("SELECT count(*) FROM segment_assignment").fetchone()[0]
        excluded=db.execute("SELECT count(*) FROM source_scope_exceptions").fetchone()[0]
        books=db.execute("SELECT count(*) FROM mcu_volume_review").fetchone()[0]
        endpoints=db.execute("SELECT count(*) FROM natural_boundary_candidates").fetchone()[0]
        if (n,excluded,books,endpoints)!=(425953,18748,45,90):
            raise ValueError("Unexpected source coverage or reviewer rows")
        ids={r[0] for r in db.execute("SELECT mcu_volume FROM mcu_volume_review")}
        if ids!=set(range(1,46)):
            raise ValueError("Not exactly MCU books 1–45")
        sums=db.execute("SELECT sum(candidate_segments) FROM mcu_volume_review").fetchone()[0]
        if sums!=n:
            raise ValueError("Per-volume candidate totals disagree")
        duplicates=db.execute("""SELECT count(*) FROM (
          SELECT source_order FROM segment_assignment GROUP BY source_order HAVING count(*)>1
        )""").fetchone()[0]
        if duplicates:
            raise ValueError("Overlapping segment assignments")
        missing_hash=db.execute("SELECT count(*) FROM segment_assignment WHERE source_sha256_passed!=1").fetchone()[0]
        if missing_hash:
            raise ValueError("Missing hash evidence")
        bad_book=db.execute("""SELECT count(*) FROM mcu_volume_review WHERE
          edition_verified!=0 OR first_boundary_review!='MCU_REFERENCE_PENDING'
          OR last_boundary_review!='MCU_REFERENCE_PENDING'
          OR missing_vs_mcu!='UNKNOWN_NO_TARGET_CORPUS'
          OR extra_vs_mcu!='UNKNOWN_NO_TARGET_CORPUS'""").fetchone()[0]
        if bad_book:
            raise ValueError("An unverified source candidate was marked as MCU approved")
        hashes_checked=None
        if source_path:
            source=sqlite3.connect("file:"+str(Path(source_path).resolve())+"?mode=ro",uri=True)
            try:
                if source.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                    raise ValueError("Source SQLite corrupt")
                hashes_checked=0
                for sid,pali,digest in source.execute("SELECT segment_id,pali,sha256 FROM segments"):
                    if hashlib.sha256(pali.encode("utf-8")).hexdigest()!=digest:
                        raise ValueError("Source SHA-256 mismatch: "+sid)
                    hashes_checked+=1
                if hashes_checked!=n+excluded:
                    raise ValueError("Source-to-review total mismatch")
            finally:source.close()
        return {"version":"2.3.9.5","source_segments":n+excluded,
           "mcu_source_candidate_segments":n,"excluded_segments":excluded,
           "mcu_books_with_review_rows":books,"source_boundary_samples":endpoints,
           "verified_mcu_full_books":0,"source_hashes_checked":hashes_checked,
           "mcus_missing_extra":"UNKNOWN_INDEPENDENT_TARGET_NOT_IMPORTED",
           "release_ready":False,"qa_status":"SOURCE_QA_PASS_MCU_EDITION_NOT_VERIFIED"}
    finally:db.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--qa",type=Path,required=True)
    ap.add_argument("--source",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--require-release-ready",action="store_true")
    args=ap.parse_args()
    result=validate(args.qa,args.source)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if args.out:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    if args.require_release_ready:
        raise SystemExit("RELEASE BLOCKED: independent MCU paragraph comparison not completed")
