#!/usr/bin/env python3
"""Fail-closed audit for the exact SQLite asset consumed by the Android reader.

This is a verification gate, not a corpus generator. It never invents scripture,
Myanmar translations, reviewer identities, or approval status.
"""
import csv, json, sqlite3, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DB=ROOT/"app/src/main/assets/tipitaka_offline.sqlite"
CROSSWALK=ROOT/"corpus/45_volume_crosswalk.csv"
EXPECTED_PARAGRAPHS=425_953
REQUIRED_TABLES={"paragraphs","paragraph_explanations"}
REQUIRED_PARAGRAPH_COLUMNS={"id","volume","body","source_ref"}
REQUIRED_EXPLANATION_COLUMNS={"paragraph_id","language","explanation_my","source_ref","provenance","reviewed"}
report={"database":str(DB.relative_to(ROOT)),"exists":DB.is_file(),"expected_volumes":45,
        "expected_paragraphs":EXPECTED_PARAGRAPHS,"checks":{},"errors":[]}
if not DB.is_file():
    report["errors"].append("Missing Android offline SQLite asset. Supply a licensed, verified database at app/src/main/assets/tipitaka_offline.sqlite.")
else:
    try:
        con=sqlite3.connect(f"file:{DB}?mode=ro",uri=True)
        tables={r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        report["checks"]["tables"]=sorted(tables)
        missing=sorted(REQUIRED_TABLES-tables)
        if missing: report["errors"].append("Missing required tables: "+", ".join(missing))
        if not missing:
            paragraph_cols={r[1] for r in con.execute("PRAGMA table_info(paragraphs)")}
            explanation_cols={r[1] for r in con.execute("PRAGMA table_info(paragraph_explanations)")}
            missing_p=sorted(REQUIRED_PARAGRAPH_COLUMNS-paragraph_cols)
            missing_e=sorted(REQUIRED_EXPLANATION_COLUMNS-explanation_cols)
            if missing_p: report["errors"].append("paragraphs missing columns: "+", ".join(missing_p))
            if missing_e: report["errors"].append("paragraph_explanations missing columns: "+", ".join(missing_e))
            if missing_p or missing_e: raise ValueError("SQLite schema is incompatible with the native reader")
            volumes=con.execute("SELECT COUNT(DISTINCT volume) FROM paragraphs").fetchone()[0]
            count=con.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
            empty=con.execute("SELECT COUNT(*) FROM paragraphs WHERE body IS NULL OR trim(body)='' OR source_ref IS NULL OR trim(source_ref)=''").fetchone()[0]
            per_volume={str(v):con.execute("SELECT COUNT(*) FROM paragraphs WHERE volume=?",(v,)).fetchone()[0] for v in range(1,46)}
            report["checks"].update({"distinct_volumes":volumes,"paragraph_count":count,"empty_or_unreferenced":empty,"paragraphs_per_volume":per_volume})
            if volumes!=45:report["errors"].append(f"Expected 45 distinct volumes, found {volumes}.")
            if count!=EXPECTED_PARAGRAPHS:report["errors"].append(f"Expected {EXPECTED_PARAGRAPHS} source-aligned paragraphs, found {count}.")
            if empty:report["errors"].append(f"{empty} paragraphs have empty text or missing source references.")
            absent=[v for v,n in per_volume.items() if n==0]
            if absent:report["errors"].append("Empty volumes: "+", ".join(absent))
            exp=con.execute("SELECT COUNT(*) FROM paragraph_explanations").fetchone()[0]
            approved=con.execute("SELECT COUNT(*) FROM paragraph_explanations WHERE reviewed=1 AND language='my'").fetchone()[0]
            report["checks"].update({"explanation_rows":exp,"reviewed_explanation_rows":approved})
            if "paragraph_myanmar_content" in tables:
                rows=con.execute("SELECT content_type,COUNT(*) FROM paragraph_myanmar_content WHERE reviewed=1 GROUP BY content_type").fetchall()
                report["checks"]["reviewed_myanmar_content"]={k:v for k,v in rows}
            else:
                report["checks"]["reviewed_myanmar_content"]={"status":"table_missing"}
        integrity=con.execute("PRAGMA integrity_check").fetchone()[0]
        fk=con.execute("PRAGMA foreign_key_check").fetchall()
        report["checks"]["integrity_check"]=integrity
        report["checks"]["foreign_key_violations"]=len(fk)
        if integrity.lower()!="ok":report["errors"].append("SQLite integrity_check failed: "+str(integrity))
        if fk:report["errors"].append(f"SQLite foreign_key_check found {len(fk)} violations.")
        con.close()
    except Exception as e:
        report["errors"].append("Database audit error: "+str(e))
if not CROSSWALK.is_file():
    report["errors"].append("Missing 45-volume crosswalk.")
else:
    with CROSSWALK.open(encoding="utf-8-sig",newline="") as f: rows=list(csv.DictReader(f))
    report["checks"]["crosswalk_rows"]=len(rows)
    ids=[r.get("volume_id","").strip() for r in rows]
    report["checks"]["crosswalk_verified_rows"]=sum(1 for r in rows if r.get("mapping_status","").upper()=="VERIFIED")
    report["checks"]["crosswalk_unique_volume_ids"]=len(set(ids))
    report["checks"]["crosswalk_missing_source_prefix"]=sum(1 for r in rows if not r.get("source_file_prefix","").strip())
    report["checks"]["crosswalk_missing_reviewer_reference"]=sum(1 for r in rows if r.get("mapping_status","").upper()=="VERIFIED" and not r.get("reviewer_reference","").strip())
    if len(set(ids))!=45 or set(ids)!={str(i) for i in range(1,46)}: report["errors"].append("Crosswalk volume_id must contain each ID 1..45 exactly once.")
    if report["checks"]["crosswalk_missing_source_prefix"]: report["errors"].append("Crosswalk has missing source_file_prefix values.")
    if report["checks"]["crosswalk_missing_reviewer_reference"]: report["errors"].append("Verified crosswalk rows require reviewer_reference.")
    if len(rows)!=45:report["errors"].append(f"Expected 45 crosswalk rows, found {len(rows)}.")
    if report["checks"]["crosswalk_verified_rows"]!=45:
        report["errors"].append("45-volume crosswalk is not fully VERIFIED; do not claim MCU edition equivalence.")
out=ROOT/"corpus/offline_corpus_audit.json"
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
if report["errors"]:
    print("\nOFFLINE CORPUS GATE: FAILED",file=sys.stderr)
    sys.exit(1)
print("\nOFFLINE CORPUS GATE: PASSED")
