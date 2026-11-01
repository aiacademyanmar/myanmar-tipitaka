#!/usr/bin/env python3
"""Validate editorial source acquisition and create read-only Android catalog.
Unverified source candidates are never promoted into approved content.
"""
import csv,json,pathlib,re,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
ledger=ROOT/"corpus/45_volume_acquisition_ledger.csv"
sources=ROOT/"corpus/myanmar_translation_source_inventory.csv"
crosswalk=ROOT/"corpus/45_volume_crosswalk.csv"
output=ROOT/"app/src/main/assets/verified_source_acquisition_catalog.json"
report=ROOT/"corpus/verified_source_acquisition_report.json"
def rows(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
a,b,c=rows(ledger),rows(sources),rows(crosswalk)
errors=[]
if len(a)!=45 or len(c)!=45:errors.append("Exactly 45 ledger and crosswalk rows are mandatory")
ids={r["source_id"] for r in b}
entries=[]
for index,book in enumerate(a,1):
 ref=c[index-1] if index<=len(c) else {}
 if book["volume_id"]!=str(index) or book["book_title_my"]!=ref.get("book_title_my"):
  errors.append(f"Volume {index}: title or index does not match authoritative crosswalk")
 sid=book["source_id"].strip()
 if sid and sid not in ids:errors.append(f"Volume {index}: unknown source_id {sid}")
 rights=book["rights_status"].strip()
 match=book["edition_match_status"].strip()
 if rights not in {"NOT_VERIFIED","REDISTRIBUTION_PERMISSION_DOCUMENTED","DENIED"}:errors.append(f"Volume {index}: invalid rights state")
 if match not in {"NOT_VERIFIED","EXACT_VERIFIED"}:errors.append(f"Volume {index}: invalid edition match")
 if match=="EXACT_VERIFIED":
  required=("source_id","source_book_url","source_filename","source_sha256","source_author","source_publisher",
            "edition","license_reference","permission_document","first_pali_segment","last_pali_segment",
            "reviewer_1","reviewer_2","review_reference")
  if rights!="REDISTRIBUTION_PERMISSION_DOCUMENTED" or any(not book[k].strip() for k in required):
   errors.append(f"Volume {index}: missing evidence for exact book mapping")
  if not re.fullmatch("[0-9a-fA-F]{64}",book["source_sha256"]):
   errors.append(f"Volume {index}: bad source SHA256")
  if book["reviewer_1"].strip().casefold()==book["reviewer_2"].strip().casefold():
   errors.append(f"Volume {index}: reviewers must differ")
 # Candidate list is for online references only, not evidence of actual book coverage.
 candidate_ids=[x for x in ref.get("candidate_source_ids","").split(";") if x] if "candidate_source_ids" in ref else []
 entries.append({"volume_id":index,"title_my":book["book_title_my"],"source_id":sid,
   "source_book_url":book["source_book_url"] if book["source_book_url"].startswith("https://") else "",
   "rights_status":rights,"edition_match_status":match,"acquisition_status":book["acquisition_status"],
   "source_verified":match=="EXACT_VERIFIED" and rights=="REDISTRIBUTION_PERMISSION_DOCUMENTED",
   "candidate_source_ids":candidate_ids})
 if book["source_book_url"] and not book["source_book_url"].startswith("https://"):
  errors.append(f"Volume {index}: external source URLs must be HTTPS")
status="BLOCKED" if errors else "CATALOG_READY_PENDING_SOURCE_EVIDENCE"
payload={"schema_version":1,"label":"45-volume Myanmar source acquisition catalog",
 "note":"External discovery references are NOT approved translation sources and do not grant offline redistribution permission.",
 "volumes":entries}
stats={"status":status,"volumes":len(entries),
 "exact_verified_sources":sum(e["source_verified"] for e in entries),
 "pending_source_evidence":sum(not e["source_verified"] for e in entries),"errors":errors}
report.parent.mkdir(parents=True,exist_ok=True)
report.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if errors:
 print(json.dumps(stats,ensure_ascii=False,indent=2));sys.exit(1)
output.parent.mkdir(parents=True,exist_ok=True)
output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(stats,ensure_ascii=False,indent=2))
