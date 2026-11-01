#!/usr/bin/env python3
"""Fail-closed validation of 45 editorial crosswalk rows.

Repeated source prefixes are permitted because one Bilara source family can
span multiple printed volumes. Exact non-overlapping boundaries are checked
by build_native_45_sqlite.py.
"""
import csv,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=root/"corpus/45_volume_crosswalk.csv"
rows=list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
errors=[];valid=0;ids=[]
if len(rows)!=45:errors.append(f"Expected 45 rows; found {len(rows)}")
required={"volume_id","source_file_prefix","mapping_status","reviewer_reference","start_segment_id","end_segment_id","rights_evidence"}
if not rows or not required.issubset(rows[0]):
 errors.append("Crosswalk missing required columns: "+", ".join(sorted(required-set(rows[0] if rows else []))))
for i,r in enumerate(rows,1):
 try:n=int(r.get("volume_id",""))
 except Exception:n=-1
 ids.append(n)
 if n!=i:errors.append(f"Volume order mismatch at row {i}")
 for key in ("source_file_prefix","reviewer_reference","start_segment_id","end_segment_id","rights_evidence"):
  if not (r.get(key) or "").strip():errors.append(f"Volume {i} missing {key}")
 if (r.get("mapping_status") or "").strip().upper()!="VERIFIED":
  errors.append(f"Volume {i} is not VERIFIED")
 else:valid+=1
if len(set(ids))!=45:errors.append("volume_id values are not unique")
print(f"Editorially verified mappings: {valid}/45")
if valid!=45:errors.append("All 45 mappings must be VERIFIED before native DB generation.")
if errors:
 print("\n".join(errors),file=sys.stderr);sys.exit(1)
print("45-volume editorial crosswalk: PASSED")
