#!/usr/bin/env python3
"""MN5 (Anaṅgaṇasutta) editorial draft-only quality gate.

The CSV and SQLite are produced separately by the local translation authoring
workflow; this script checks provenance, counts and that no approval is implied.
Does not certify the translated Pāli's semantic accuracy or MCU edition.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path

EXPECTED=203
COLUMNS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
 "draft_status","translation_method","source_sha256","source_path","source_commit",
 "approved","reviewer","source_url"]

def check(csv_path,combined_sqlite):
    with Path(csv_path).open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=COLUMNS:raise ValueError("MN5 CSV schema mismatch")
        rows=list(reader)
    if len(rows)!=EXPECTED:raise ValueError("MN5 must have 203 source records")
    seen=set();short=summary=0
    for r in rows:
        sid=r["segment_id"]
        if not sid.startswith("mn5:") or sid in seen or r["sutta_uid"]!="mn5":
            raise ValueError("Duplicate or invalid MN5 paragraph id")
        seen.add(sid)
        if hashlib.sha256(r["pali"].encode("utf-8")).hexdigest()!=r["source_sha256"]:
            raise ValueError("Pāli SHA mismatch: "+sid)
        if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
            raise ValueError("Missing Burmese draft: "+sid)
        if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or str(r["approved"])!="0" or r["reviewer"].strip():
            raise ValueError("Unreviewed content must not be marked approved: "+sid)
        if not r["source_path"].endswith("mn5_root-pli-ms.json") or not r["source_commit"]:
            raise ValueError("Pāli source provenance missing: "+sid)
        if "…pe…" in r["pali"]:short+=1
        if "ELLIPSIS" in r["translation_method"] and "…pe…" not in r["pali"]:
            raise ValueError("Source abbreviation flag disagrees with source")
        if r["translation_method"]=="CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW":summary+=1
    if short!=6 or summary!=7:raise ValueError("MN5 review queue changed")
    con=sqlite3.connect("file:"+str(Path(combined_sqlite).resolve())+"?mode=ro",uri=True)
    try:
        if con.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("Combined SQLite corruption")
        count=dict(con.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))
        if count!={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203}:
            raise ValueError("Combined source counts differ from approved draft manifest")
        if con.execute("SELECT count(*) FROM pali_myanmar WHERE approved!=0").fetchone()[0]!=0:
            raise ValueError("Draft-only corpus must not contain approved text")
        for r in rows:
            record=con.execute("""SELECT source_pali_roman,my_translation_draft,
              my_explanation_draft,source_sha256,draft_status FROM pali_myanmar
              WHERE segment_id=?""",(r["segment_id"],)).fetchone()
            if not record or record!=(r["pali"],r["translation_draft"],
               r["explanation_draft"],r["source_sha256"],"AI_DRAFT_UNREVIEWED"):
                raise ValueError("CSV ↔ SQLite draft divergence: "+r["segment_id"])
    finally:con.close()
    return {"mn5_source_segments":EXPECTED,"mn5_translation_drafts":EXPECTED,
            "mn5_explanation_drafts":EXPECTED,"source_ellipses":short,
            "long_summary_review":summary,"combined_draft_rows":955,
            "human_approved":0,"mcu_original_verified_volumes":0,"release_ready":False}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--csv",required=True);p.add_argument("--combined-db",required=True)
    a=p.parse_args()
    print(json.dumps(check(a.csv,a.combined_db),ensure_ascii=False,indent=2))
