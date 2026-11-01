#!/usr/bin/env python3
"""List real source-file and segment-ID endpoints for each 45-volume *candidate*.

Do not treat lexicographic or filename endpoints as edition-specific volume
boundaries. Manuscript/editorial review is required before 45-volume APK bundling.
"""
import argparse
import collections
import csv
import json
import pathlib
import re
import sqlite3

def natural_key(value):
    return [int(part) if part.isdigit() else part.lower()
            for part in re.split(r"(\d+)", value)]

ap = argparse.ArgumentParser()
ap.add_argument("database", type=pathlib.Path)
ap.add_argument("--details", default="bilara_source_boundaries.csv")
ap.add_argument("--manifest", default="bilara_source_file_manifest.csv")
ap.add_argument("--report", default="bilara_mapping_review.json")
args = ap.parse_args()
db = sqlite3.connect("file:" + str(args.database.resolve()) + "?mode=ro", uri=True)
source_files = list(db.execute(
    "SELECT source_file, COUNT(*), MIN(segment_id), MAX(segment_id) "
    "FROM source_segments GROUP BY source_file"
))
file_data = {name:(count,low,high) for name,count,low,high in source_files}
with open(args.manifest, "w", newline="", encoding="utf-8") as out:
    w=csv.writer(out)
    w.writerow(["source_file","segments","lexical_first_segment_id","lexical_last_segment_id"])
    for file in sorted(file_data, key=natural_key):
        w.writerow([file,*file_data[file]])
root=pathlib.Path(__file__).resolve().parents[1]
with (root/"corpus/45_volume_source_candidates.csv").open(encoding="utf-8") as fh:
    candidates=list(csv.DictReader(fh))
assert len(candidates)==45,"Expected exactly 45 numbered volume candidates"
uses=collections.defaultdict(list)
expanded=[]
for row in candidates:
    volume=int(row["volume_id"])
    prefixes=[p.strip().rstrip("/") for p in row["candidate_bilara_prefix"].split("|") if p.strip()]
    expanded.append((volume,prefixes))
    for pre in prefixes:
        uses[pre].append(volume)
with open(args.details,"w",newline="",encoding="utf-8") as out:
    w=csv.writer(out)
    w.writerow(["volume_id","source_prefix","source_files","source_segments",
                "first_source_file","first_source_segment_lexical",
                "last_source_file","last_source_segment_lexical",
                "other_volumes_using_same_prefix","status"])
    valid_volumes=0
    missing=[]
    for volume,prefixes in expanded:
        all_present=bool(prefixes)
        for prefix in prefixes:
            # Exact family path match: no SQL LIKE wildcard ambiguity.
            matched=sorted((x for x in file_data if x.startswith(prefix+"/")
                            or x.startswith(prefix+"_")),key=natural_key)
            if not matched:
                missing.append([volume,prefix])
                all_present=False
            first,last=(matched[0],matched[-1]) if matched else ("","")
            shared=[x for x in uses[prefix] if x!=volume]
            w.writerow([volume,prefix,len(matched),
                        sum(file_data[f][0] for f in matched),first,
                        file_data[first][1] if first else "",
                        last,file_data[last][2] if last else "",
                        "|".join(str(x) for x in shared),
                        "CANDIDATE_SOURCE_PRESENT" if matched else "MISSING_SOURCE"])
        if all_present:
            valid_volumes+=1
report={
 "source_files":len(file_data),
 "source_segments":sum(v[0] for v in file_data.values()),
 "candidate_volumes":len(candidates),
 "candidate_volumes_with_all_source_families_present":valid_volumes,
 "missing_source_prefixes":missing,
 "verified_edition_volume_boundaries":0,
 "ready_to_bundle_as_45_volume_library":False,
 "note":"Source family matches and file endpoints are NOT printed-edition 45-volume boundaries."
}
pathlib.Path(args.report).write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
