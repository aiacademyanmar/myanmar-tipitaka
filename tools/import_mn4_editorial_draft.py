#!/usr/bin/env python3
"""MN4 editorial draft intake: independently validates the 165 Pāli and Burmese pairs.

Input CSV contains draft text, NOT approved Myanmar translation. The source JSON
must be the pinned published Mahāsaṅgīti Roman Pāli (MN4), not MCU-45 original.
No release approval or MCU volume verification occurs.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path

N=165
ABBREVIATIONS={"mn4:5.2","mn4:5.3"}
LONG_REVIEW={"mn4:27.2","mn4:29.2"}
EDITION="Mahasangiti Roman Pali (NOT MCU original)"
COLUMNS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
         "section","method","status","source_sha256","source_path","source_commit","source_url"]

def validate_csv(csv_path,source_json):
    obj=json.loads(Path(source_json).read_text(encoding="utf-8-sig"))
    if not isinstance(obj,dict) or len(obj)!=N:raise ValueError("Expected 165 original MN4 source IDs")
    if any(not k.startswith("mn4:") or not isinstance(v,str) for k,v in obj.items()):
        raise ValueError("Unexpected original source ID/text")
    with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=COLUMNS:raise ValueError("Unexpected CSV columns")
        rows=list(reader)
    if len(rows)!=N:raise ValueError("Expected 165 draft rows")
    seen=set()
    for r in rows:
        sid=r["segment_id"]
        if sid in seen or sid not in obj or r["sutta_uid"]!="mn4":raise ValueError("Wrong/duplicate MN4 segment ID")
        seen.add(sid)
        if obj[sid]!=r["pali"] or hashlib.sha256(r["pali"].encode("utf-8")).hexdigest()!=r["source_sha256"]:
            raise ValueError("Pāli source text/hash mismatch: "+sid)
        if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
            raise ValueError("Missing Burmese draft: "+sid)
        if r["status"]!="AI_DRAFT_UNREVIEWED":raise ValueError("Cannot auto approve Burmese draft")
        if r["method"]=="ABBREVIATED_SOURCE_UNEXPANDED" and sid not in ABBREVIATIONS:
            raise ValueError("Unexpected Pāli abbreviation flag")
    if {r["segment_id"] for r in rows if r["method"]=="ABBREVIATED_SOURCE_UNEXPANDED"}!=ABBREVIATIONS:
        raise ValueError("Unreviewed source ellipses not fully flagged")
    if {r["segment_id"] for r in rows if r["method"]=="LONG_PASSAGE_PARAPHRASE_REQUIRES_DETAIL_REVIEW"}!=LONG_REVIEW:
        raise ValueError("Unreviewed long paraphrases not fully flagged")
    return rows

def integrate(prior_db,csv_path,source_json,output):
    rows=validate_csv(csv_path,source_json)
    output=Path(output)
    if output.exists():raise FileExistsError(output)
    prior=sqlite3.connect("file:"+str(Path(prior_db).resolve())+"?mode=ro",uri=True)
    out=sqlite3.connect(output)
    try:
        if prior.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Previous database corrupt")
        previous=prior.execute("SELECT * FROM pali_myanmar").fetchall()
        if len(previous)!=587 or prior.execute("SELECT count(*) FROM pali_myanmar WHERE approved<>0").fetchone()[0]:
            raise ValueError("Expected 587 unapproved MN1-MN3 rows")
        schema=prior.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='pali_myanmar'").fetchone()[0]
        out.execute(schema)
        out.execute("CREATE INDEX idx_mn4_sutta ON pali_myanmar(sutta_uid,segment_id)")
        out.execute("CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT)")
        out.executemany("INSERT INTO pali_myanmar VALUES(?,?,?,?,?,?,?,?,?,?,?)",previous)
        for r in rows:
            out.execute("INSERT INTO pali_myanmar VALUES(?,?,?,?,?,?,?,?,?,?,?)",[
              r["segment_id"],"mn4",r["pali"],r["translation_draft"],r["explanation_draft"],
              r["status"],r["method"],r["source_sha256"],r["source_path"],0,None])
        out.executemany("INSERT INTO metadata VALUES(?,?)",[
          ("source_edition",EDITION),("approved_translation_count","0"),
          ("verified_mcu_books","0"),("release_ready","NO")])
        out.commit()
        if out.execute("PRAGMA integrity_check").fetchone()[0]!="ok" or out.execute("SELECT count(*) FROM pali_myanmar").fetchone()[0]!=752:
            raise ValueError("Combined database failed integrity/count check")
        if out.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn4'").fetchall()!=previous:
            raise ValueError("Previous drafts unexpectedly modified")
        return {"mn4_segments":165,"combined_segments":752,"approved":0,"mcu_books_verified":0,"release_ready":False}
    except Exception:
        out.close();output.unlink(missing_ok=True);raise
    finally:prior.close();out.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for key in ("prior-db","csv","source-json","out"):p.add_argument("--"+key,required=True)
    a=p.parse_args()
    print(json.dumps(integrate(a.prior_db,a.csv,a.source_json,a.out),indent=2))
