#!/usr/bin/env python3
"""MN7 Vatthasutta editorial-draft validation; no human approval or MCU verification."""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
N=147
ELLIPSES={"mn7:9.1","mn7:14.1","mn7:15.1"}
COLUMNS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
"draft_status","translation_method","source_sha256","source_path","source_commit",
"approved","reviewer","source_url"]

def check(csv_path,source_json,combined_db=None):
 src=json.loads(Path(source_json).read_text(encoding="utf-8-sig"))
 if not isinstance(src,dict) or len(src)!=N or any(not k.startswith("mn7:") for k in src):
  raise ValueError("Wrong MN7 source inventory")
 with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=COLUMNS:raise ValueError("Wrong source CSV columns")
  rows=list(reader)
 if len(rows)!=N:raise ValueError("MN7 must have 147 rows")
 seen=set()
 for r in rows:
  sid=r["segment_id"]
  if sid in seen or sid not in src or r["sutta_uid"]!="mn7":
   raise ValueError("Duplicate or missing MN7 segment")
  seen.add(sid)
  if r["pali"]!=src[sid] or hashlib.sha256(r["pali"].encode("utf-8")).hexdigest()!=r["source_sha256"]:
   raise ValueError("Pāli source/hash mismatch: "+sid)
  if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
   raise ValueError("Missing Burmese draft: "+sid)
  if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
   raise ValueError("No draft may be auto approved: "+sid)
  if ("…pe…" in r["pali"])!=(sid in ELLIPSES):
   raise ValueError("Source ellipsis inventory mismatch: "+sid)
  if sid in ELLIPSES and r["translation_method"]!="SOURCE_ELLIPSIS_UNEXPANDED":
   raise ValueError("Unexpanded source not flagged: "+sid)
  if not r["source_path"].endswith("mn7_root-pli-ms.json") or len(r["source_commit"])!=40:
   raise ValueError("Missing source provenance")
 if seen!=set(src):raise ValueError("Unmapped source segments")
 if combined_db:
  c=sqlite3.connect("file:"+str(Path(combined_db).resolve())+"?mode=ro",uri=True)
  try:
   if c.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite integrity failure")
   expected={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203,"mn6":51,"mn7":147}
   if dict(c.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))!=expected:
    raise ValueError("Combined source count mismatch")
   if c.execute("SELECT count(*) FROM pali_myanmar WHERE approved!=0").fetchone()[0]:
    raise ValueError("Draft-only DB cannot contain approved text")
   for r in rows:
    rec=c.execute("SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?",(r["segment_id"],)).fetchone()
    if rec!=(r["pali"],r["translation_draft"],r["explanation_draft"],r["source_sha256"]):
     raise ValueError("CSV SQLite source mismatch: "+r["segment_id"])
  finally:c.close()
 return {"source_segments":147,"translation_drafts":147,"explanation_drafts":147,
 "source_ellipses_unexpanded":3,"combined_draft_segments":1153 if combined_db else None,
 "scholar_approved_segments":0,"verified_mcu_volumes":0,"release_ready":False}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 for k in ("csv","source-json"):p.add_argument("--"+k,required=True)
 p.add_argument("--combined-db")
 a=p.parse_args()
 print(json.dumps(check(a.csv,a.source_json,a.combined_db),indent=2))
