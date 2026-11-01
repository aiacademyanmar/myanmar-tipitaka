#!/usr/bin/env python3
"""Validate all 45 editorial mapping rows. Fail on conflicts, duplicated prefixes or missing citations."""
import csv,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=root/"corpus/45_volume_crosswalk.csv"
rows=list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
errors=[];valid=0;assigned=set()
if len(rows)!=45:errors.append("Expected 45 rows")
for i,r in enumerate(rows,1):
 try:n=int(r["volume_id"])
 except Exception:n=-1
 if n!=i:errors.append(f"Volume order mismatch at row {i}")
 if r["mapping_status"]=="VERIFIED":
  prefix=r["source_file_prefix"].strip()
  if not prefix or not r["reviewer_reference"].strip():errors.append(f"Unsubstantiated verified mapping {i}")
  elif prefix in assigned:errors.append(f"Repeated source prefix {prefix}")
  else:assigned.add(prefix);valid+=1
 elif r["mapping_status"]!="UNVERIFIED":errors.append(f"Invalid mapping status row {i}")
print(f"Editorially verified mappings: {valid}/45")
if errors:sys.exit("\n".join(errors))
