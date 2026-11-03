#!/usr/bin/env python3
"""Validate MN6 Mahasangiti source CSV and UNREVIEWED Myanmar draft records.

Not a certification of translated meaning, MCU edition, or APK-readiness.
"""
import argparse,csv,hashlib,json
from pathlib import Path
HEADERS=["segment_id","sutta_uid","pali","translation_draft","explanation_draft",
 "draft_status","translation_method","source_sha256","source_path","source_commit",
 "approved","reviewer","source_url"]
ELLIPSES={"mn6:7.1","mn6:8.1","mn6:9.1","mn6:10.1","mn6:11.1",
 "mn6:12.1","mn6:13.1","mn6:14.1","mn6:15.1","mn6:16.18","mn6:17.2"}
LONG={"mn6:14.1","mn6:17.1","mn6:18.1"}
def validate(csv_path,original_json):
 original=json.loads(Path(original_json).read_text(encoding="utf-8-sig"))
 if len(original)!=51 or not all(k.startswith("mn6:") for k in original):
  raise ValueError("MN6 must contain exactly 51 published source segments")
 with Path(csv_path).open(encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=HEADERS:raise ValueError("Invalid CSV header")
  rows=list(reader)
 if len(rows)!=51:raise ValueError("MN6 draft must contain 51 rows")
 seen=set()
 for r in rows:
  sid=r["segment_id"]
  if sid in seen or sid not in original or r["sutta_uid"]!="mn6":
   raise ValueError("Invalid/duplicate segment ID "+sid)
  seen.add(sid)
  if r["pali"]!=original[sid] or hashlib.sha256(r["pali"].encode()).hexdigest()!=r["source_sha256"]:
   raise ValueError("Source text/hash mismatch "+sid)
  if not r["translation_draft"].strip() or not r["explanation_draft"].strip():
   raise ValueError("Missing Myanmar draft content "+sid)
  if r["draft_status"]!="AI_DRAFT_UNREVIEWED" or r["approved"]!="0" or r["reviewer"].strip():
   raise ValueError("Draft texts cannot be auto-approved "+sid)
  if not r["source_path"].endswith("mn6_root-pli-ms.json") or not r["source_commit"]:
   raise ValueError("Missing Mahasangiti source provenance "+sid)
  if ("…pe…" in r["pali"])!=(sid in ELLIPSES):
   raise ValueError("Source ellipsis inventory mismatch "+sid)
  if sid in ELLIPSES and r["translation_method"]!="SOURCE_ELLIPSIS_UNEXPANDED":
   raise ValueError("Unexpanded source must be flagged "+sid)
  if sid in LONG-ELLIPSES and r["translation_method"]!="LONG_PASSAGE_NEEDS_LITERAL_REVIEW":
   raise ValueError("Long passage not flagged "+sid)
 return {"source_segments":51,"translation_drafts":51,"explanation_drafts":51,
   "source_abbreviations_unexpanded":11,"long_passages_for_review":3,
   "approved":0,"mcu45_verified_full_books":0,"release_ready":False}
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--csv",required=True);p.add_argument("--original-json",required=True)
 a=p.parse_args();print(json.dumps(validate(a.csv,a.original_json),indent=2))
