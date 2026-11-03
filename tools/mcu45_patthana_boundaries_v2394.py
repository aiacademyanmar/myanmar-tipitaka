#!/usr/bin/env python3
"""V2.3.9.4 Paṭṭhāna MCU 40–43 provisional source-structure mapper.

Uses the V2.3.9.3 SQLite review artifact. Fail closed: never mark a source
candidate as MCU-verified, licensed or approved for an offline APK.
"""
import argparse, collections, csv, hashlib, json, re, sqlite3
from pathlib import Path

REFERENCES={
 40:"https://84000.org/tipitaka/pitaka_item/m_siri.php?B=40&siri=1",
 41:"https://84000.org/tipitaka/pitaka_item/m_siri.php?B=41&siri=1",
 42:"https://84000.org/tipitaka/pitaka_item/m_siri.php?B=42&siri=1",
 43:"https://84000.org/tipitaka/pitaka_item/m_siri.php?B=43&siri=1",
}
ANCHORS=[
 ("40_LAST","patthana1.6:0.3","Saṅkiliṭṭhattika",40),
 ("41_FIRST","patthana1.7:0.3","Vitakkattika",41),
 ("42_LAST","patthana2.9:0.3","Parāmāsagocchaka",42),
 ("43_FIRST","patthana2.10:1.1","Sārammaṇa",43),
]

def classify(uid,pool):
 m=re.fullmatch(r"patthana([12])\.(\d+)(?:-(\d+))?",uid)
 if not m: raise ValueError("Unrecognized UID: "+uid)
 part,a,b=int(m[1]),int(m[2]),int(m[3] or m[2])
 if part==1 and pool=="40|41" and 1<=a<=b<=23:
  if a<=6<b: raise ValueError("UID crosses boundary: "+uid)
  return 40 if b<=6 else 41
 if part==2 and pool=="42|43" and 1<=a<=b<=13:
  if a<=9<b: raise ValueError("UID crosses boundary: "+uid)
  return 42 if b<=9 else 43
 raise ValueError("Unexpected source group/pool: "+uid+" "+pool)

def run(source_path,output_path,audit_path,csv_path):
 source_path=Path(source_path);output_path=Path(output_path)
 if output_path.exists():raise FileExistsError(output_path)
 if not source_path.is_file():raise FileNotFoundError(source_path)
 output_path.parent.mkdir(parents=True,exist_ok=True)
 src=sqlite3.connect("file:"+str(source_path.resolve())+"?mode=ro",uri=True)
 out=sqlite3.connect(output_path)
 counts=collections.Counter()
 try:
  if src.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
   raise ValueError("Input SQLite corrupt")
  out.executescript("""
   CREATE TABLE patthana_review(
    segment_id TEXT PRIMARY KEY,text_uid TEXT NOT NULL,pali TEXT NOT NULL,
    proposed_mcu_volume INTEGER NOT NULL,source_pool TEXT NOT NULL,
    source_path TEXT NOT NULL,source_sha256 TEXT NOT NULL,source_commit TEXT NOT NULL,
    mapping_status TEXT NOT NULL DEFAULT 'SOURCE_ALIGNED_CANDIDATE',
    mcu_paragraph_verified INTEGER NOT NULL DEFAULT 0 CHECK(mcu_paragraph_verified=0)
   );
   CREATE INDEX ix_patthana ON patthana_review(proposed_mcu_volume,text_uid);
   CREATE TABLE volume_summary(mcu_volume INTEGER PRIMARY KEY,basket TEXT,title TEXT,
    previous_candidate_segments INTEGER,newly_assigned_segments INTEGER,
    total_candidate_segments INTEGER,unresolved_shared_pool INTEGER,
    verified_segments INTEGER NOT NULL DEFAULT 0 CHECK(verified_segments=0),mapping_status TEXT);
   CREATE TABLE source_anchors(label TEXT PRIMARY KEY,segment_id TEXT,heading TEXT,
     proposed_mcu_volume INTEGER,reference_url TEXT,status TEXT);
   CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);
  """)
  for label,sid,expected,volume in ANCHORS:
   row=src.execute("SELECT pali FROM boundary_segments WHERE segment_id=?",(sid,)).fetchone()
   if not row or expected.casefold() not in row[0].casefold():
    raise ValueError("Missing source anchor: "+sid)
   out.execute("INSERT INTO source_anchors VALUES(?,?,?,?,?,'STRUCTURAL_ONLY')",
      (label,sid,row[0].strip(),volume,REFERENCES[volume]))
  batch=[]
  for sid,uid,pool,sha,commit,path,pali in src.execute("""
    SELECT segment_id,text_uid,unresolved_volume_pool,source_sha256,
       source_commit,source_path,pali FROM boundary_segments
    WHERE mapping_status='MCU_BOUNDARY_REVIEW_REQUIRED'
    ORDER BY source_path,segment_id"""):
   volume=classify(uid,pool)
   if not pali.strip() or not commit or not path or hashlib.sha256(pali.encode("utf-8")).hexdigest()!=sha:
    raise ValueError("Source hash/provenance mismatch: "+sid)
   counts[volume]+=1
   batch.append((sid,uid,pali,volume,pool,path,sha,commit))
   if len(batch)>=2000:
    out.executemany("""INSERT INTO patthana_review
      (segment_id,text_uid,pali,proposed_mcu_volume,source_pool,source_path,source_sha256,source_commit)
      VALUES(?,?,?,?,?,?,?,?)""",batch)
    batch.clear()
  if batch:
   out.executemany("""INSERT INTO patthana_review
    (segment_id,text_uid,pali,proposed_mcu_volume,source_pool,source_path,source_sha256,source_commit)
    VALUES(?,?,?,?,?,?,?,?)""",batch)
  original=src.execute("SELECT count(*) FROM boundary_segments WHERE mapping_status='MCU_BOUNDARY_REVIEW_REQUIRED'").fetchone()[0]
  if original!=16114 or sum(counts.values())!=original or set(counts)!={40,41,42,43}:
   raise ValueError("Missing/unexpected unresolved segments")
  previous=0
  for volume,basket,title,prior,added,total,shared,verified,status in src.execute(
       "SELECT * FROM volume_summary ORDER BY mcu_volume"):
   previous+=total
   out.execute("INSERT INTO volume_summary VALUES(?,?,?,?,?,?,?,?,?)",
    (volume,basket,title,total,counts[volume],total+counts[volume],
     0 if volume in counts else shared,0,'SOURCE_ALIGNED_CANDIDATE_NOT_VERIFIED'))
  if out.execute("SELECT count(*) FROM volume_summary").fetchone()[0]!=45:
   raise ValueError("MCU book catalog must have 45 rows")
  out.executemany("INSERT INTO metadata VALUES(?,?)",[
     ("edition_crosswalk","UNVERIFIED"),("verified_mcu_books","0"),
     ("license_review","PENDING"),("apk_approved","NO")])
  out.commit()
  assert out.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
  assert out.execute("SELECT sum(mcu_paragraph_verified) FROM patthana_review").fetchone()[0]==0
  totals=out.execute("SELECT sum(total_candidate_segments) FROM volume_summary").fetchone()[0]
  if totals!=previous+original:raise ValueError("Conservation of source segments failed")
  audit={"version":"2.3.9.4","source_segments":444701,
    "prior_structural_candidates":previous,"new_structural_candidates":original,
    "total_structural_candidates":totals,
    "remaining_patthana_structural_review":0,
    "outside_or_supplementary":444701-totals,
    "counts_by_volume":{str(k):counts[k] for k in sorted(counts)},
    "source_hashes_checked":original,"verified_mcu_volumes":0,
    "mcu_paragraph_verification":"NOT_PERFORMED",
    "source_rights_check":"PENDING","release_ready":False}
  audit_path=Path(audit_path);audit_path.parent.mkdir(parents=True,exist_ok=True)
  audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
  csv_path=Path(csv_path);csv_path.parent.mkdir(parents=True,exist_ok=True)
  with csv_path.open("w",encoding="utf-8-sig",newline="") as f:
   w=csv.writer(f);w.writerow(["segment_id","text_uid","candidate_mcu_volume","pali_excerpt","sha256","source_path","status"])
   for row in out.execute("""SELECT segment_id,text_uid,proposed_mcu_volume,pali,
      source_sha256,source_path,mapping_status FROM patthana_review
      ORDER BY proposed_mcu_volume,source_path,segment_id"""):
    w.writerow([row[0],row[1],row[2],row[3][:240],row[4],row[5],row[6]])
  return audit
 except Exception:
  out.close();output_path.unlink(missing_ok=True);raise
 finally:
  src.close();out.close()

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for arg in ["input","out","audit","csv"]:p.add_argument("--"+arg,required=True)
 args=p.parse_args()
 print(json.dumps(run(args.input,args.out,args.audit,args.csv),indent=2))
