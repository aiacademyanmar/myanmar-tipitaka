#!/usr/bin/env python3
"""Audit candidate source prefixes against actual staged Bilara SQLite files.
Never upgrades a candidate to VERIFIED without edition-specific paragraph bounds.
"""
import csv,sqlite3,argparse,pathlib,json
p=argparse.ArgumentParser();p.add_argument("database");p.add_argument("--output",default="bilara_candidate_audit.csv");a=p.parse_args()
con=sqlite3.connect("file:"+str(pathlib.Path(a.database).resolve())+"?mode=ro",uri=True)
root=pathlib.Path(__file__).resolve().parents[1]
out=[]
with (root/"corpus/45_volume_source_candidates.csv").open(encoding="utf-8") as f:
 for r in csv.DictReader(f):
  prefix=r["candidate_bilara_prefix"]
  n=con.execute("SELECT COUNT(*) FROM source_segments WHERE source_file LIKE ?",(prefix+"/%",)).fetchone()[0]
  out.append((r["volume_id"],prefix,n,"SOURCE_PRESENT" if n else "SOURCE_NOT_FOUND","UNVERIFIED"))
with open(a.output,"w",newline="",encoding="utf-8") as f:
 w=csv.writer(f);w.writerow(["volume_id","candidate_prefix","candidate_segments","source_status","edition_mapping_status"]);w.writerows(out)
print(json.dumps({"candidate_rows":len(out),"source_prefixes_present":sum(x[2]>0 for x in out),"verified_volume_mappings":0}))
