#!/usr/bin/env python3
"""MN16 Cetokhilasutta strict source-aligned working draft gate.

Not a human-approved translation, not independently verified MCU edition,
and not a test of whether the 45-book native Android APK is complete.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path

EXPECTED_BLOB="dcd87c67be8057c04c8cd5d343df34a7ca7be00b"
EXPECTED_SOURCE="sutta/mn/mn16_root-pli-ms.json"
FIELDS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
"section","topic","draft_status","translation_method","source_sha256",
"source_path","source_commit","published_source_blob_sha","approved","reviewer","source_url"]
EXPECTED_COUNTS={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203,"mn6":51,
"mn7":147,"mn8":170,"mn9":234,"mn10":235,"mn11":132,"mn12":372,
"mn13":152,"mn14":144,"mn15":263,"mn16":83}
ABBREVIATION_IDS={"mn16:4.1","mn16:5.1","mn16:9.1","mn16:10.1",
"mn16:16.1","mn16:17.1","mn16:18.1","mn16:21.1","mn16:22.1"}

def validate(csv_file,original_json,combined_db=None,prior_db=None):
    source=json.loads(Path(original_json).read_text(encoding="utf-8-sig"))
    if not isinstance(source,dict) or len(source)!=83 or not all(k.startswith("mn16:") for k in source):
        raise ValueError("MN16 must have 83 original Pāli source segments")
    raw=json.dumps(source,ensure_ascii=False,indent=2).encode()
    blob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    if blob!=EXPECTED_BLOB:
        raise ValueError("Published original MN16 Git blob SHA mismatch")
    with Path(csv_file).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError("MN16 editorial CSV schema mismatch")
        rows=list(reader)
    if len(rows)!=83:raise ValueError("MN16 needs 83 working draft rows")
    seen=set()
    methods=Counter()
    for r in rows:
        sid=r["segment_id"];pali=r["pali"]
        if sid in seen or sid not in source or r["sutta_uid"]!="mn16":
            raise ValueError("Duplicate or foreign MN16 segment")
        seen.add(sid)
        if source[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=r["source_sha256"]:
            raise ValueError("Original Pāli changed or SHA mismatch "+sid)
        if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
            raise ValueError("Missing Burmese working draft "+sid)
        if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
            raise ValueError("Working draft cannot be auto-approved "+sid)
        if r["source_path"]!=EXPECTED_SOURCE or r["published_source_blob_sha"]!=EXPECTED_BLOB:
            raise ValueError("Missing original source provenance "+sid)
        if ("…" in pali)!=(sid in ABBREVIATION_IDS):
            raise ValueError("MN16 source abbreviation inventory changed "+sid)
        should_ellipsis=sid in ABBREVIATION_IDS
        if should_ellipsis:
            if r["translation_method"]!="SOURCE_ELLIPSIS_UNEXPANDED" or "မချဲ့ရသေး" not in r["translation_draft"]:
                raise ValueError("Unexpanded original Pāli requires visible review flag "+sid)
        elif r["translation_method"]!="SEGMENT_ALIGNED_AI_DRAFT":
            raise ValueError("Unexpected working translation method "+sid)
        methods[r["translation_method"]]+=1
    if seen!=set(source) or dict(methods)!={"SEGMENT_ALIGNED_AI_DRAFT":74,"SOURCE_ELLIPSIS_UNEXPANDED":9}:
        raise ValueError("MN16 draft coverage or nine source abbreviations inconsistent")
    if combined_db:
        db=sqlite3.connect("file:"+str(Path(combined_db).resolve())+"?mode=ro",uri=True)
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Combined SQLite integrity failure")
            counts=dict(db.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))
            if counts!=EXPECTED_COUNTS:raise ValueError("MN1-MN16 count not 2,938")
            if db.execute("SELECT COUNT(*) FROM pali_myanmar WHERE approved != 0").fetchone()[0]:
                raise ValueError("Unreviewed corpus cannot have approved texts")
            for r in rows:
                found=db.execute("SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,draft_status FROM pali_myanmar WHERE segment_id=?",(r["segment_id"],)).fetchone()
                if found!=(r["pali"],r["translation_draft"],r["explanation_draft"],r["source_sha256"],r["draft_status"]):
                    raise ValueError("CSV vs combined SQLite changed "+r["segment_id"])
            if prior_db:
                prev=sqlite3.connect("file:"+str(Path(prior_db).resolve())+"?mode=ro",uri=True)
                try:
                    old=prev.execute("SELECT * FROM pali_myanmar ORDER BY segment_id").fetchall()
                    fresh=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn16' ORDER BY segment_id").fetchall()
                    if len(old)!=2855 or old!=fresh:raise ValueError("Previous 2,855 rows changed")
                finally:prev.close()
        finally:db.close()
    return {"source_segments":83,"Burmese_translation_working_drafts":83,
       "Burmese_explanation_working_drafts":83,"unexpanded_source_abbreviations":9,
       "combined_drafts":2938 if combined_db else None,"scholar_approved":0,
       "MCU_45_original_verified_volumes":0,"signed_release_APK":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True);p.add_argument("--original-json",required=True)
    p.add_argument("--combined-db");p.add_argument("--prior-db")
    a=p.parse_args()
    print(json.dumps(validate(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
