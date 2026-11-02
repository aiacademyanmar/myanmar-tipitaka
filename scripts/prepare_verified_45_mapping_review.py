#!/usr/bin/env python3
"""Produce reproducible, *unapproved* 45-volume editorial review packets.

This tool inspects a genuine pinned Bilara Pali source SQLite. It uses SQLite
rowid insertion order for endpoint previews (NOT lexical min/max segment IDs)
and never edits authoritative 45_volume_crosswalk.csv or issues approvals.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
FIELDS=("volume_id","book_title_my","candidate_prefix","source_file","source_segments",
        "first_segment_id","last_segment_id","first_sha256","last_sha256",
        "first_pali_preview","last_pali_preview","shared_candidate_prefix",
        "review_status")
REV_FIELDS=("volume_id","book_title_my","pitaka","mapping_status",
 "proposed_source_prefix","reviewed_source_file","first_segment_id",
 "last_segment_id","exact_edition_source","printed_page_start","printed_page_end",
 "independent_reference","rights_evidence","reviewer_reference","review_notes")

def load_csv(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write_csv(path,cols,rows):
 path.parent.mkdir(parents=True,exist_ok=True)
 with path.open("w",encoding="utf-8-sig",newline="") as f:
  w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore");w.writeheader();w.writerows(rows)
def digest(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()

def generate(database,crosswalk,candidates,out):
 if not database.is_file():raise ValueError("Pinned source SQLite artifact is missing")
 cw=load_csv(crosswalk);ca=load_csv(candidates)
 if len(cw)!=45 or len(ca)!=45:raise ValueError("Both crosswalk and candidate inventories must contain 45 rows")
 if [r.get("volume_id") for r in cw]!=[str(n) for n in range(1,46)]:
  raise ValueError("Crosswalk volume IDs are not sequential 1..45")
 if [r.get("volume_id") for r in ca]!=[str(n) for n in range(1,46)]:
  raise ValueError("Candidate volume IDs are not sequential 1..45")
 db=sqlite3.connect(f"file:{database.resolve()}?mode=ro",uri=True)
 try:
  if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Source SQLite integrity_check failed")
  tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if not {"source_segments","build_info"}.issubset(tables):
   raise ValueError("Not an authenticated source_segments staging database")
  metadata=dict(db.execute("SELECT name,value FROM build_info"))
  source_commit=metadata.get("commit","")
  if len(source_commit)!=40 or any(c not in "0123456789abcdefABCDEF" for c in source_commit):
   raise ValueError("Pinned source commit must be a 40-digit SHA-1")
  groups=db.execute("SELECT source_file,COUNT(*),MIN(rowid),MAX(rowid) FROM source_segments GROUP BY source_file").fetchall()
  files={}
  for path,count,low,high in groups:
   first=db.execute("SELECT segment_id,body,sha256,source_commit FROM source_segments WHERE rowid=?",(low,)).fetchone()
   last=db.execute("SELECT segment_id,body,sha256,source_commit FROM source_segments WHERE rowid=?",(high,)).fetchone()
   for segment in (first,last):
    if segment is None or segment[3]!=source_commit or digest(segment[1])!=segment[2].lower():
     raise ValueError(f"Source provenance/hash mismatch: {path}")
   files[path]=(count,first,last)
  n=db.execute("SELECT COUNT(*) FROM source_segments").fetchone()[0]
  if n<=0 or sum(x[0] for x in files.values())!=n:raise ValueError("Source segment counts inconsistent")
  # Verify ALL segment hashes, not only the sampled endpoints, before providing review packets.
  failed=0
  for body,sha,commit in db.execute("SELECT body,sha256,source_commit FROM source_segments"):
   if digest(body)!=(sha or "").lower() or commit!=source_commit:failed+=1
  if failed:raise ValueError(f"Failed complete source SHA-256/provenance audit ({failed} rows)")
 finally:db.close()
 prefix_usage={}
 for row in ca:
  for prefix in row.get("candidate_bilara_prefix","").split("|"):
   prefix=prefix.strip().rstrip("/")
   if prefix:prefix_usage.setdefault(prefix,[]).append(int(row["volume_id"]))
 file_rows=[];volume_review=[];missing=[]
 for original,candidate in zip(cw,ca):
  vid=int(original["volume_id"])
  prefixes=[x.strip().rstrip("/") for x in candidate.get("candidate_bilara_prefix","").split("|") if x.strip()]
  volume_review.append({"volume_id":vid,"book_title_my":original.get("book_title_my",""),
     "pitaka":original.get("pitaka",""),"mapping_status":"UNVERIFIED",
     "proposed_source_prefix":" | ".join(prefixes),
     "reviewed_source_file":"","first_segment_id":"","last_segment_id":"",
     "exact_edition_source":"","printed_page_start":"","printed_page_end":"",
     "independent_reference":"","rights_evidence":"","reviewer_reference":"","review_notes":""})
  for prefix in prefixes:
   matched=sorted(path for path in files if path.startswith(prefix+"/") or path.startswith(prefix+"_"))
   if not matched:missing.append({"volume_id":vid,"missing_candidate_prefix":prefix})
   for path in matched:
    count,first,last=files[path]
    file_rows.append({
     "volume_id":vid,"book_title_my":original.get("book_title_my",""),
     "candidate_prefix":prefix,"source_file":path,"source_segments":count,
     "first_segment_id":first[0],"last_segment_id":last[0],
     "first_sha256":first[2],"last_sha256":last[2],
     "first_pali_preview":" ".join(first[1].split())[:140],
     "last_pali_preview":" ".join(last[1].split())[:140],
     "shared_candidate_prefix":"YES" if len(prefix_usage[prefix])>1 else "NO",
     "review_status":"CANDIDATE_ONLY"})
 out.mkdir(parents=True,exist_ok=True)
 write_csv(out/"candidate_source_file_boundaries.csv",FIELDS,file_rows)
 write_csv(out/"45_volume_human_review_sheet.csv",REV_FIELDS,volume_review)
 report={"version":"2.3.6.5","source_commit":source_commit,
  "source_files":len(files),"source_segments":n,
  "candidate_rows":45,"candidate_file_assignments":len(file_rows),
  "missing_candidate_families":missing,
  "shared_candidate_families":{p:vs for p,vs in prefix_usage.items() if len(vs)>1},
  "human_verified_45_volume_mappings":0,"approved_final_corpus":False,
  "ready_to_generate_45_volume_sqlite":False,
  "warning":"File endpoints are literal Bilara file endpoints, NOT verified printed-edition 45-book boundaries.",
  "next_review":"Compare printed MCU title, exact first/last source segment, multi-file spans, rights evidence, and independent reviewer sign-off."}
 (out/"mapping_review_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report

def main():
 p=argparse.ArgumentParser()
 p.add_argument("database",type=pathlib.Path)
 p.add_argument("--crosswalk",type=pathlib.Path,default=ROOT/"corpus/45_volume_crosswalk.csv")
 p.add_argument("--candidates",type=pathlib.Path,default=ROOT/"corpus/45_volume_source_candidates.csv")
 p.add_argument("--out",type=pathlib.Path,default=pathlib.Path("mapping-review-v2-3-6-5"))
 a=p.parse_args()
 try:r=generate(a.database,a.crosswalk,a.candidates,a.out)
 except Exception as e:print("Mapping dossier generation failed: "+str(e),file=sys.stderr);return 1
 print(json.dumps(r,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":sys.exit(main())
