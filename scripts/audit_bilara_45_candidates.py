#!/usr/bin/env python3
"""Audit 45 Bilara source-family candidates, including composite volumes and overlap.
Source presence is NOT verification of edition-specific volume boundaries.
"""
import argparse,csv,json,pathlib,sqlite3,collections
p=argparse.ArgumentParser();p.add_argument("database");p.add_argument("--output",default="bilara_candidate_audit.csv");a=p.parse_args()
db=sqlite3.connect("file:"+str(pathlib.Path(a.database).resolve())+"?mode=ro",uri=True)
root=pathlib.Path(__file__).resolve().parents[1]
rows=list(csv.DictReader((root/"corpus/45_volume_source_candidates.csv").open(encoding="utf-8")))
assert len(rows)==45
out=[];used=collections.defaultdict(list)
for row in rows:
 prefixes=[x.strip().rstrip("/") for x in row["candidate_bilara_prefix"].split("|") if x.strip()]
 counts=[]
 for pre in prefixes:
  n=db.execute("SELECT COUNT(*) FROM source_segments WHERE source_file LIKE ?",(pre+"/%",)).fetchone()[0]
  if not n:
   # Some Bilara families consist of a single root file rather than a directory.
   n=db.execute("SELECT COUNT(*) FROM source_segments WHERE source_file LIKE ?",(pre+"_%",)).fetchone()[0]
  counts.append(n)
  used[pre].append(int(row["volume_id"]))
 status="SOURCE_PRESENT" if prefixes and all(x>0 for x in counts) else "SOURCE_NOT_FOUND"
 out.append({"volume_id":row["volume_id"],"candidate_prefixes":"|".join(prefixes),"source_segments":sum(counts),"source_status":status,"edition_mapping_status":"UNVERIFIED","prefix_overlap":"PENDING"})
for r in out:
 prefixes=r["candidate_prefixes"].split("|")
 repeated=sorted(set(v for pre in prefixes for v in used[pre] if str(v)!=r["volume_id"]))
 r["prefix_overlap"]="|".join(map(str,repeated))
with open(a.output,"w",newline="",encoding="utf-8") as f:
 w=csv.DictWriter(f,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
print(json.dumps({"candidate_rows":len(out),"source_candidates_present":sum(x["source_status"]=="SOURCE_PRESENT" for x in out),"with_overlapping_source_families":sum(bool(x["prefix_overlap"]) for x in out),"verified_volume_mappings":0}))
