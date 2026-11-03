#!/usr/bin/env python3
"""MN17 Vanapatthasutta source-linked Burmese AI draft gate, NOT release approval."""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
BLOB="5fa0b1e2bc116f0ef3fe4398212d0a446827793d"
PATH="sutta/mn/mn17_root-pli-ms.json"
FIELDS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft","section","topic","draft_status","translation_method","source_sha256","source_path","source_commit","published_source_blob_sha","approved","reviewer","source_url"]
ELLIPSIS={"mn17:4.7","mn17:5.7","mn17:7-10.1","mn17:11-14.1","mn17:15-18.1","mn17:19-22.1","mn17:24.7","mn17:25.7"}
COUNTS={"mn1":334,"mn2":125,"mn3":128,"mn4":165,"mn5":203,"mn6":51,"mn7":147,"mn8":170,"mn9":234,"mn10":235,"mn11":132,"mn12":372,"mn13":152,"mn14":144,"mn15":263,"mn16":83,"mn17":83}
METHODS={"SEGMENT_ALIGNED_AI_DRAFT":75,"SOURCE_ELLIPSIS_UNEXPANDED":8}
def check(csv_path,source_json,combined=None,prior=None):
 src=json.loads(Path(source_json).read_text(encoding="utf-8-sig"))
 if not isinstance(src,dict) or len(src)!=83 or any(not k.startswith("mn17:") for k in src):
  raise ValueError("MN17 source needs exactly 83 source IDs")
 b=json.dumps(src,ensure_ascii=False,indent=2).encode()
 if hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()!=BLOB:
  raise ValueError("MN17 published Git blob mismatch")
 with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError("MN17 draft columns mismatch")
  rows=list(reader)
 if len(rows)!=83:raise ValueError("MN17 requires exactly 83 draft records")
 seen=set();methods=Counter()
 for r in rows:
  sid=r["segment_id"];pali=r["pali"]
  if sid in seen or sid not in src or r["sutta_uid"]!="mn17":
   raise ValueError("Foreign/duplicate MN17 segment ID")
  seen.add(sid)
  if src[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=r["source_sha256"]:
   raise ValueError("Pāli source text/SHA mismatch "+sid)
  if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
   raise ValueError("Empty Burmese draft "+sid)
  if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
   raise ValueError("Never auto approve editorial working draft "+sid)
  if r["source_path"]!=PATH or r["published_source_blob_sha"]!=BLOB or len(r["source_commit"])!=40:
   raise ValueError("Source provenance missing "+sid)
  if ("…" in pali)!=(sid in ELLIPSIS):
   raise ValueError("Source ellipsis ID mismatch "+sid)
  if (sid in ELLIPSIS)!=(r["translation_method"]=="SOURCE_ELLIPSIS_UNEXPANDED"):
   raise ValueError("Source abbreviation must be unexpanded "+sid)
  if sid in ELLIPSIS and "မချဲ့ရသေး" not in r["translation_draft"]:
   raise ValueError("Missing explicit source abbreviation warning "+sid)
  methods[r["translation_method"]]+=1
 if seen!=set(src) or dict(methods)!=METHODS:raise ValueError("MN17 coverage/review counts mismatch")
 if combined:
  c=sqlite3.connect("file:"+str(Path(combined).resolve())+"?mode=ro",uri=True)
  try:
   if c.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite corrupt")
   if dict(c.execute("SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid"))!=COUNTS:
    raise ValueError("MN1-MN17 3021 row count mismatch")
   if c.execute("SELECT count(*) FROM pali_myanmar WHERE approved!=0").fetchone()[0]:
    raise ValueError("Unreviewed draft illegally approved")
   for r in rows:
    x=c.execute("SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?",(r["segment_id"],)).fetchone()
    if x!=(r["pali"],r["translation_draft"],r["explanation_draft"],r["source_sha256"]):
     raise ValueError("CSV/SQLite mismatch "+r["segment_id"])
   if prior:
    p=sqlite3.connect("file:"+str(Path(prior).resolve())+"?mode=ro",uri=True)
    try:
     old=p.execute("SELECT * FROM pali_myanmar ORDER BY segment_id").fetchall()
     new=c.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn17' ORDER BY segment_id").fetchall()
     if len(old)!=2938 or old!=new:raise ValueError("Previous MN1-MN16 2938 rows changed")
    finally:p.close()
  finally:c.close()
 return {"source_pali":83,"Burmese_working_drafts":83,"explanations":83,"unexpanded_source":8,"combined_rows":3021 if combined else None,"scholar_approved":0,"MCU_45_verified":0,"signed_APK":False}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--csv",required=True);p.add_argument("--original-json",required=True)
 p.add_argument("--combined-db");p.add_argument("--prior-db")
 a=p.parse_args()
 print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
