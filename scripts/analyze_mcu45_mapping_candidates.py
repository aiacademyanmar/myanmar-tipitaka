#!/usr/bin/env python3
"""Create a human-reviewable Bilara-to-MCU volume mapping dossier.

Candidate source families are discovery hints only. The script never marks a
volume verified and never creates the Android 45-volume reader database.
"""
import argparse,csv,json,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser()
ap.add_argument("database",type=pathlib.Path,help="pali_root_source.sqlite from V2.3.4.9.1")
ap.add_argument("--candidates",type=pathlib.Path,default=ROOT/"corpus/45_volume_source_candidates.csv")
ap.add_argument("--out",type=pathlib.Path,default=ROOT/"corpus/mcu45_mapping_review")
a=ap.parse_args()
if not a.database.is_file():sys.exit("Missing Bilara source staging SQLite")
con=sqlite3.connect(f"file:{a.database.resolve()}?mode=ro",uri=True)
if con.execute("PRAGMA integrity_check").fetchone()[0]!="ok":sys.exit("Source SQLite integrity check failed")
source={}
for name,n,first,last in con.execute("SELECT source_file,COUNT(*),MIN(segment_id),MAX(segment_id) FROM source_segments GROUP BY source_file"):
    source[name]=(n,first,last)
con.close()
with a.candidates.open(encoding="utf-8-sig",newline="") as f: candidates=list(csv.DictReader(f))
if len(candidates)!=45:sys.exit(f"Expected 45 candidate rows, found {len(candidates)}")
a.out.mkdir(parents=True,exist_ok=True)
rows=[];volumes=[];prefix_usage={}
for row in candidates:
    vid=int(row["volume_id"]); prefixes=[x.strip().rstrip("/") for x in row["candidate_bilara_prefix"].split("|") if x.strip()]
    volume_files=set();total=0;missing=[]
    for prefix in prefixes:
        matches=sorted(x for x in source if x.startswith(prefix+"/") or x.startswith(prefix+"_"))
        if not matches:missing.append(prefix)
        for name in matches:
            n,first,last=source[name];volume_files.add(name);total+=n
            prefix_usage.setdefault(prefix,set()).add(vid)
            rows.append({"volume_id":vid,"candidate_prefix":prefix,"source_file":name,"segments":n,
                         "first_segment_id":first,"last_segment_id":last,
                         "candidate_only":"YES","editorial_status":"UNVERIFIED"})
    volumes.append({"volume_id":vid,"candidate_prefixes":prefixes,"matched_source_files":len(volume_files),
                    "candidate_segment_assignments":total,"missing_prefixes":missing,
                    "unique_source_segments_not_deduplicated":None,
                    "editorial_mapping":"UNVERIFIED","release_eligible":False})
with (a.out/"volume_candidate_files.csv").open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=["volume_id","candidate_prefix","source_file","segments","first_segment_id","last_segment_id","candidate_only","editorial_status"]);w.writeheader();w.writerows(rows)
overlap=[{"candidate_prefix":p,"volume_ids":sorted(v),"volume_count":len(v)} for p,v in sorted(prefix_usage.items()) if len(v)>1]
report={"source_files":len(source),"source_segments":sum(x[0] for x in source.values()),
        "candidate_volume_rows":len(volumes),"candidate_prefixes":len(prefix_usage),
        "overlapping_prefixes":len(overlap),"overlap_details":overlap,
        "volumes_with_all_candidate_families_present":sum(not x["missing_prefixes"] for x in volumes),
        "editorially_verified_volumes":0,"approved_45_volume_mapping":False,
        "native_reader_database_generated":False,
        "volume_candidates":volumes,
        "required_evidence":["MCU edition title/printing and source licence","exact printed-volume first and last Pali reference",
          "independent page/paragraph cross-check","reviewer identity and signed review reference",
          "resolved overlaps and duplicate segment policy"]}
(a.out/"mapping_review_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({k:v for k,v in report.items() if k not in ("volume_candidates","overlap_details")},ensure_ascii=False,indent=2))
