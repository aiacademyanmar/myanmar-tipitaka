#!/usr/bin/env python3
"""Audit a completed human mapping worksheet against pinned source segments.

Evidence checks are mechanical only; human sign-offs still require independent
verification. This script NEVER writes or approves the canonical crosswalk.
"""
import argparse,csv,hashlib,json,pathlib,re,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def load(path):
 with path.open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def audit(database,sheet):
 rows=load(sheet)
 errors=[];warnings=[];ranges=[];source_commit=""
 report={"version":"2.3.6.6","status":"BLOCKED","rows":len(rows),"technically_valid_rows":0,"human_verified_volumes":0,"canonical_crosswalk_modified":False,"errors":errors,"warnings":warnings}
 if len(rows)!=45:errors.append("Exactly 45 editorial review rows required")
 if not database.is_file():errors.append("Pinned Pali source SQLite missing");return report
 db=sqlite3.connect(f"file:{database.resolve()}?mode=ro",uri=True)
 try:
  source_commit=dict(db.execute("SELECT name,value FROM build_info")).get("commit","")
  if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":errors.append("Source SQLite corruption detected")
  for n,row in enumerate(rows,1):
   if row.get("volume_id")!=str(n):errors.append(f"Volume {n}: sequential ID mismatch");continue
   fields=["reviewed_source_file","first_segment_id","last_segment_id","exact_edition_source","printed_page_start","printed_page_end","independent_reference","rights_evidence","reviewer_1","reviewer_2","reviewer_reference","first_sha256","last_sha256"]
   missing=[k for k in fields if not (row.get(k) or "").strip()]
   if missing:errors.append(f"Volume {n}: missing {', '.join(missing)}");continue
   a=row["reviewer_1"].strip().casefold();b=row["reviewer_2"].strip().casefold()
   if a==b:errors.append(f"Volume {n}: independent reviewer names identical");continue
   if row.get("mapping_status","").strip().upper()!="VERIFIED":
    errors.append(f"Volume {n}: human editorial approval not recorded");continue
   source_file=row["reviewed_source_file"]
   ends=db.execute("SELECT rowid,segment_id,sha256,source_commit FROM source_segments WHERE source_file=? AND segment_id IN (?,?)",(source_file,row["first_segment_id"],row["last_segment_id"])).fetchall()
   if len(ends)!=2 or any(e[3]!=source_commit for e in ends):
    errors.append(f"Volume {n}: missing pinned source endpoint");continue
   first=next((x for x in ends if x[1]==row["first_segment_id"]),None)
   last=next((x for x in ends if x[1]==row["last_segment_id"]),None)
   if first is None or last is None or first[0]>last[0]:
    errors.append(f"Volume {n}: reversed or duplicate endpoints");continue
   if first[2].lower()!=row["first_sha256"].lower() or last[2].lower()!=row["last_sha256"].lower():
    errors.append(f"Volume {n}: endpoint hash mismatch");continue
   count=db.execute("SELECT COUNT(*) FROM source_segments WHERE source_file=? AND rowid BETWEEN ? AND ?",(source_file,first[0],last[0])).fetchone()[0]
   if count<=0:errors.append(f"Volume {n}: empty source range");continue
   ranges.append((n,source_file,first[0],last[0]))
   report["technically_valid_rows"]+=1
  for i,(v,f,s,e) in enumerate(ranges):
   for w,g,a,b in ranges[i+1:]:
    if f==g and s<=b and a<=e:errors.append(f"Volumes {v}/{w}: overlapping source ranges in {f}")
  report["human_verified_volumes"]=0
  if not errors:
   report["status"]="TECHNICAL_AUDIT_PASSED_HUMAN_EDITORIAL_SIGNOFF_REQUIRED"
   warnings.append("Self-entered reviewer names and evidence are not authenticated. Independent scholarly validation still required before promoting canonical mapping.")
 finally:db.close()
 return report
def main():
 p=argparse.ArgumentParser()
 p.add_argument("database",type=pathlib.Path)
 p.add_argument("--sheet",type=pathlib.Path,required=True)
 p.add_argument("--report",type=pathlib.Path,default=pathlib.Path("mapping_editorial_audit.json"))
 args=p.parse_args()
 try:result=audit(args.database,args.sheet)
 except Exception as e:result={"status":"BLOCKED","errors":[str(e)]}
 args.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0 if result["status"]=="TECHNICAL_AUDIT_PASSED_HUMAN_EDITORIAL_SIGNOFF_REQUIRED" else 1
if __name__=="__main__":sys.exit(main())
