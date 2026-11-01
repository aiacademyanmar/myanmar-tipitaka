#!/usr/bin/env python3
"""Fail-closed validation for all 45 editorial volume-to-source mappings."""
import csv,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=root/"corpus/45_volume_crosswalk.csv"
rows=list(csv.DictReader(p.open(encoding="utf-8-sig",newline="")))
errors=[];valid=0;assigned=set();ids=[]
if len(rows)!=45:errors.append(f"Expected 45 rows; found {len(rows)}")
for i,r in enumerate(rows,1):
    try:n=int(r.get("volume_id",""))
    except Exception:n=-1
    ids.append(n)
    if n!=i:errors.append(f"Volume order mismatch at row {i}")
    status=(r.get("mapping_status") or "").strip().upper()
    prefix=(r.get("source_file_prefix") or "").strip()
    reviewer=(r.get("reviewer_reference") or "").strip()
    if status!="VERIFIED":
        errors.append(f"Volume {i} is {status or 'UNMARKED'}, not VERIFIED")
        continue
    if not prefix:errors.append(f"Verified volume {i} has no source_file_prefix");continue
    if not reviewer:errors.append(f"Verified volume {i} has no reviewer_reference");continue
    if prefix in assigned:errors.append(f"Repeated source_file_prefix: {prefix}");continue
    assigned.add(prefix);valid+=1
if len(set(ids))!=45:errors.append("volume_id values are not unique")
print(f"Editorially verified mappings: {valid}/45")
if valid!=45:errors.append("All 45 mappings must be VERIFIED before release.")
if errors:
    print("\n".join(errors),file=sys.stderr)
    sys.exit(1)
print("45-volume editorial crosswalk: PASSED")
