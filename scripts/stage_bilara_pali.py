#!/usr/bin/env python3
"""Stage SuttaCentral Bilara Pali root JSON into a traceable PARTIAL corpus CSV.

Usage:
 python scripts/stage_bilara_pali.py /path/to/bilara-data/root/pli/ms
Does NOT assert full 45-volume correspondence. Data is NOT auto-bundled.
This is a staging step; check source licence and verify editorial mapping before import.
"""
import argparse,csv,json,pathlib,re,sys
p=argparse.ArgumentParser();p.add_argument("root",type=pathlib.Path);p.add_argument("--output",type=pathlib.Path,default=pathlib.Path("corpus/bilara_pali_staging.csv"));args=p.parse_args()
root=args.root.resolve()
if not root.is_dir():sys.exit("Bilara Pali root directory not found")
rows=[];seen=set()
for path in sorted(root.rglob("*.json")):
 try: content=json.loads(path.read_text(encoding="utf-8"))
 except (ValueError,UnicodeError) as e:sys.exit(f"Invalid source JSON: {path}: {e}")
 if not isinstance(content,dict):continue
 for segment,body in content.items():
  if not isinstance(segment,str) or not isinstance(body,str) or not body.strip():continue
  key=(str(path.relative_to(root)),segment)
  if key in seen:sys.exit(f"Duplicate source segment: {key}")
  seen.add(key)
  rows.append((str(path.relative_to(root)),segment,body.strip(),"https://github.com/suttacentral/bilara-data/tree/published/root/pli/ms/"+str(path.relative_to(root)).replace("\\","/")))
args.output.parent.mkdir(parents=True,exist_ok=True)
with args.output.open("w",encoding="utf-8",newline="") as f:
 writer=csv.writer(f);writer.writerow(["source_file","segment_id","pali_body","source_ref"]);writer.writerows(rows)
print(f"Staged {len(rows)} Pali segments from {len(set(x[0] for x in rows))} files to {args.output}.")
print("STAGING ONLY: no 45-volume mapping and no Myanmar explanations. NOT a full APK corpus.")
