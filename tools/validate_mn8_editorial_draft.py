#!/usr/bin/env python3
"""MN8 Sallekhasutta: fail-closed audit of source-aligned Myanmar AI drafts.
No claim of reviewed translation, MCU Pali equivalence, or offline APK readiness.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
EXPECTED={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203,"mn6":51,"mn7":147,"mn8":170}
ELLIPSES={"mn8:13.3","mn8:15.2"}
LONG={"mn8:14.3","mn8:14.4","mn8:14.5"}
HEADERS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
"draft_status","translation_method","source_sha256","source_path","source_commit",
"approved","reviewer","source_url"]
def audit(csv_path,source_json,combined_db=None,prior_db=None):
 original=json.loads(Path(source_json).read_text(encoding="utf-8-sig"))
 if not isinstance(original,dict) or len(original)!=170 or not all(k.startswith("mn8:") for k in original):
  raise ValueError("Wrong original MN8 source inventory")
 with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=HEADERS:raise ValueError("Wrong editorial CSV column structure")
  rows=list(reader)
 if len(rows)!=170:raise ValueError("Expected 170 MN8 editorial draft rows")
 seen=set()
 for r in rows:
  sid=r["segment_id"];pali=r["pali"]
  if sid in seen or sid not in original or r["sutta_uid"]!="mn8":
   raise ValueError("Duplicate or invalid source ID")
  seen.add(sid)
  if pali!=original[sid] or hashlib.sha256(pali.encode()).hexdigest()!=r["source_sha256"]:
   raise ValueError("MN8 source text or hash mismatch: "+sid)
  if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
   raise ValueError("Empty Myanmar draft: "+sid)
  if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
   raise ValueError("Draft translation cannot be auto-approved")
  if ("…pe…" in pali)!=(sid in ELLIPSES):
   raise ValueError("Source ellipsis list mismatch: "+sid)
  if sid in ELLIPSES and r["translation_method"]!="SOURCE_ELLIPSIS_UNEXPANDED":
   raise ValueError("Unexpanded Pali must be explicitly flagged: "+sid)
  if sid in LONG and r["translation_method"]!="LONG_PASSAGE_NEEDS_LITERAL_REVIEW":
   raise ValueError("Long paraphrase needs detail review: "+sid)
  if not r["source_path"].endswith("mn8_root-pli-ms.json") or len(r["source_commit"])!=40:
   raise ValueError("Missing Mahasangiti source provenance")
 if seen!=set(original):raise ValueError("Incomplete MN8 source coverage")
 if combined_db:
  c=sqlite3.connect("file:"+str(Path(combined_db).resolve())+"?mode=ro",uri=True)
  try:
   if c.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite corrupt")
   if dict(c.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))!=EXPECTED:
    raise ValueError("Expected 1323 rows across MN1 to MN8")
   if c.execute("SELECT count(*) FROM pali_myanmar WHERE approved<>0").fetchone()[0]:
    raise ValueError("Unreviewed texts cannot be marked approved")
   for r in rows:
    found=c.execute("SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?",(r["segment_id"],)).fetchone()
    if found!=(r["pali"],r["translation_draft"],r["explanation_draft"],r["source_sha256"]):
     raise ValueError("MN8 CSV and SQLite disagree: "+r["segment_id"])
   if prior_db:
    p=sqlite3.connect("file:"+str(Path(prior_db).resolve())+"?mode=ro",uri=True)
    try:
     if c.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn8'").fetchall()!=p.execute("SELECT * FROM pali_myanmar").fetchall():
      raise ValueError("Previous 1153 drafts unexpectedly changed")
    finally:p.close()
  finally:c.close()
 return {"MN8_segments":170,"translated_draft_rows":170,"explanation_draft_rows":170,
  "ellipsis_source_unexpanded":2,"long_review_passages":3,
  "combined_draft_rows":1323 if combined_db else None,
  "approved":0,"MCU_verified_volumes":0,"APK_release_ready":False}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--csv",required=True);p.add_argument("--source-json",required=True)
 p.add_argument("--combined-db");p.add_argument("--prior-db")
 a=p.parse_args();print(json.dumps(audit(a.csv,a.source_json,a.combined_db,a.prior_db),indent=2))
