#!/usr/bin/env python3
"""Inventory Bilara source-file family prefixes for an EDITORIAL 45-volume crosswalk.
This is an audit report, not a verified volume assignment.
"""
import argparse,collections,csv,pathlib,sqlite3
p=argparse.ArgumentParser();p.add_argument("database",type=pathlib.Path);p.add_argument("--output",type=pathlib.Path,default=pathlib.Path("bilara_collection_inventory.csv"));a=p.parse_args()
conn=sqlite3.connect("file:"+str(a.database.resolve())+"?mode=ro",uri=True)
counts=collections.Counter()
for path,n in conn.execute("SELECT source_file,COUNT(*) FROM source_segments GROUP BY source_file"):
 parts=pathlib.PurePosixPath(path).parts
 family=parts[0] if parts else "(unknown)"
 subgroup=parts[1] if len(parts)>1 else "(root)"
 counts[(family,subgroup)]+=n
a.output.parent.mkdir(parents=True,exist_ok=True)
with a.output.open("w",encoding="utf-8",newline="") as f:
 writer=csv.writer(f);writer.writerow(["bilara_family","bilara_subgroup","source_segments","verified_45_volume","mapping_status"])
 for (family,subgroup),n in sorted(counts.items()):writer.writerow([family,subgroup,n,"","EDITORIAL_MAPPING_REQUIRED"])
print("Inventory families/subgroups:",len(counts),"total segments:",sum(counts.values()))
print("No 45-volume edition mapping claimed.")
