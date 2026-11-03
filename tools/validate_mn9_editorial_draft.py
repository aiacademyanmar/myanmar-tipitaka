#!/usr/bin/env python3
"""MN9 Sammādiṭṭhisutta: fail-closed source-aligned editorial draft QA.

Mahāsaṅgīti Roman Pāli is NOT MCU 45-volume Thai-script Pāli.
No programmatic checking can mark a Myanmar translation scholar-approved.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
FIELDS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
"draft_status","translation_method","source_sha256","source_path","source_commit",
"approved","reviewer","source_url"]
VOLUME_COUNTS={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203,"mn6":51,"mn7":147,"mn8":170,"mn9":234}

def verify(csv_file,source_json,combined_db=None,prior_db=None):
    original=json.loads(Path(source_json).read_text(encoding="utf-8-sig"))
    if len(original)!=234 or any(not k.startswith("mn9:") for k in original):
        raise ValueError("MN9 source ID inventory must be exactly 234")
    with Path(csv_file).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError("MN9 CSV schema changed")
        rows=list(reader)
    if len(rows)!=234:raise ValueError("Expected 234 translation/explanation draft rows")
    seen=set();ellipses=0
    for r in rows:
        sid=r["segment_id"]
        if sid in seen or sid not in original or r["sutta_uid"]!="mn9":
            raise ValueError("Duplicate/missing MN9 segment")
        seen.add(sid)
        if r["pali"]!=original[sid] or hashlib.sha256(r["pali"].encode()).hexdigest()!=r["source_sha256"]:
            raise ValueError("Pāli source/hash mismatch: "+sid)
        if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
            raise ValueError("Missing Myanmar editorial text")
        if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
            raise ValueError("Unreviewed draft must not be marked approved")
        if r["translation_method"]=="TRANSLATION_PENDING":raise ValueError("Draft still pending")
        if "…" in r["pali"]:
            ellipses+=1
            if r["translation_method"]!="SOURCE_ELLIPSIS_UNEXPANDED":
                raise ValueError("Truncated original must be flagged")
        if not r["source_path"].endswith("mn9_root-pli-ms.json") or len(r["source_commit"])!=40:
            raise ValueError("Provenance record missing")
    if ellipses!=46 or seen!=set(original):raise ValueError("Source ellipsis/coverage mismatch")
    if combined_db:
        db=sqlite3.connect("file:"+str(Path(combined_db).resolve())+"?mode=ro",uri=True)
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Combined SQLite damaged")
            counts=dict(db.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))
            if counts!=VOLUME_COUNTS:raise ValueError("MN1-MN9 row counts mismatch")
            if db.execute("SELECT count(*) FROM pali_myanmar WHERE approved!=0").fetchone()[0]:
                raise ValueError("Combined draft contains approved text")
            for r in rows:
                pair=db.execute("SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?",(r["segment_id"],)).fetchone()
                if pair!=(r["pali"],r["translation_draft"],r["explanation_draft"],r["source_sha256"]):
                    raise ValueError("CSV and SQLite mismatch: "+r["segment_id"])
            if prior_db:
                prior=sqlite3.connect("file:"+str(Path(prior_db).resolve())+"?mode=ro",uri=True)
                try:
                    if db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn9'").fetchall()!=prior.execute("SELECT * FROM pali_myanmar").fetchall():
                        raise ValueError("Previous 1,323 source drafts modified")
                finally:prior.close()
        finally:db.close()
    return {"mn9_source":234,"mn9_burmese_drafts":234,"source_ellipses_unexpanded":46,
            "combined_draft_rows":1557 if combined_db else None,
            "scholar_approved":0,"MCU45_verified":0,"release_ready":False}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--csv",required=True)
    parser.add_argument("--source-json",required=True)
    parser.add_argument("--combined-db")
    parser.add_argument("--prior-db")
    args=parser.parse_args()
    print(json.dumps(verify(args.csv,args.source_json,args.combined_db,args.prior_db),indent=2))
