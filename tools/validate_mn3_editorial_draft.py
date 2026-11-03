#!/usr/bin/env python3
"""MN3 editorial-draft QA gate; validates downloaded CSV + combined draft DB.

NEVER upgrades a translation to approved or treats MCU 45 original as verified.
Run: python tools/validate_mn3_editorial_draft.py --csv FILE --combined-db FILE
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
COUNT=128
COLUMNS=["Segment ID","Roman Pāli","မြန်မာဘာသာပြန်မူကြမ်း","မြန်မာရှင်းလင်းချက်မူကြမ်း","Section","Review Status","Method","Source SHA256","Source Path","Source Commit"]
def check(csv_path,db_path):
 with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=COLUMNS:raise ValueError("Editorial CSV schema changed")
  rows=list(reader)
 if len(rows)!=COUNT:raise ValueError("MN3 source must have exactly 128 segments")
 ids=set()
 short=0
 for row in rows:
  sid=row["Segment ID"]
  if not sid.startswith("mn3:") or sid in ids:raise ValueError("Missing/duplicate MN3 ID")
  ids.add(sid)
  pali=row["Roman Pāli"]
  if hashlib.sha256(pali.encode("utf-8")).hexdigest()!=row["Source SHA256"]:
   raise ValueError("Pāli hash mismatch: "+sid)
  if not row["မြန်မာဘာသာပြန်မူကြမ်း"].strip() or not row["မြန်မာရှင်းလင်းချက်မူကြမ်း"].strip():
   raise ValueError("Empty Burmese draft: "+sid)
  if row["Review Status"]!="AI_DRAFT_UNREVIEWED":raise ValueError("Unapproved content marked reviewed: "+sid)
  if "…" in pali:short+=1
 if short!=3:raise ValueError("Source abbreviation counts changed")
 con=sqlite3.connect("file:"+str(Path(db_path).resolve())+"?mode=ro",uri=True)
 try:
  if con.execute("pragma integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite corruption")
  for uid,n in [("mn1",334),("mn2",125),("mn3",128)]:
   k=con.execute("select count(*) from pali_myanmar where sutta_uid=?",(uid,)).fetchone()[0]
   if k!=n:raise ValueError("Combined database count mismatch for "+uid)
  if con.execute("select count(*) from pali_myanmar where approved<>0").fetchone()[0]:
   raise ValueError("Unreviewed texts cannot be automatically approved")
  if con.execute("select count(*) from pali_myanmar").fetchone()[0]!=587:
   raise ValueError("Combined database contains non-specified suttas")
  for row in rows:
   found=con.execute("select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 from pali_myanmar where segment_id=?",(row["Segment ID"],)).fetchone()
   if not found or list(found)!=[row["Roman Pāli"],row["မြန်မာဘာသာပြန်မူကြမ်း"],row["မြန်မာရှင်းလင်းချက်မူကြမ်း"],row["Source SHA256"]]:
    raise ValueError("MN3 source and combined SQLite disagreement: "+row["Segment ID"])
 finally:con.close()
 return {"status":"DRAFT_QA_PASSED","mn3_rows":128,"combined_rows":587,"abbreviated":3,"human_approved":0,"mcu45_verified":0,"release_ready":False}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--csv",required=True)
 p.add_argument("--combined-db",required=True)
 a=p.parse_args()
 print(json.dumps(check(a.csv,a.combined_db),indent=2))
