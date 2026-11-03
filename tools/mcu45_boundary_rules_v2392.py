#!/usr/bin/env python3
"""V2.3.9.2 source-aligned MCU volume split candidates.

Inputs: V2.3.9.1 candidate_map SQLite. Output: a *provisional* split
database + JSON report. Never marks edition matches or 45 volumes verified.
"""
import argparse, collections, json, re, sqlite3
from pathlib import Path

EVIDENCE={
 "VINAYA12":("1|2","https://dhammapanya.org/tipitaka?pitaka=vinaya"),
 "VINAYA45":("4|5","https://ptb.tptk.org/part-4-tipitaka-digest/vinaya-pitaka/vol-06"),
 "VINAYA67":("6|7","https://ptb.tptk.org/part-4-tipitaka-digest/vinaya-pitaka/vol-06"),
 "JATAKA":("27|28","https://ptb.tptk.org/part-4-tipitaka-digest/sutta-pitaka/khuddaka-nikaya/vol-27"),
 "YAMAKA":("38|39","https://tipitaka.cloud/library/"),
 "APADANA_PENDING":("32|33","https://tipitaka.cloud/library/"),
 "PATTHANA_PENDING":("40|41|42|43|44|45","https://tipitaka.cloud/library/"),
}
def decide(pool,uid):
 if pool=="1|2":
  x=re.fullmatch(r"pli-tv-bu-vb-([a-z]+)\d+",uid)
  if x and x.group(1) in ("pj","ss","ay"): return 1,"VINAYA12"
  if x and x.group(1) in ("np","pc","pd","sk","as"): return 2,"VINAYA12"
 elif pool in ("4|5","6|7"):
  x=re.fullmatch(r"pli-tv-kd(\d+)",uid)
  if x:
   k=int(x.group(1))
   if pool=="4|5" and 1<=k<=10: return (4 if k<=4 else 5),"VINAYA45"
   if pool=="6|7" and 11<=k<=22: return (6 if k<=14 else 7),"VINAYA67"
 elif pool=="27|28":
  x=re.fullmatch(r"ja(\d+)",uid)
  if x and 1<=int(x.group(1))<=547: return (27 if int(x.group(1))<=525 else 28),"JATAKA"
 elif pool=="38|39":
  x=re.match(r"ya(\d+)(?:\.|$)",uid)
  if x and 1<=int(x.group(1))<=10: return (38 if int(x.group(1))<=7 else 39),"YAMAKA"
 return None, "APADANA_PENDING" if pool=="32|33" else "PATTHANA_PENDING" if pool=="40|41|42|43|44|45" else "OTHER_PENDING"

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--candidate-db",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--report",type=Path,required=True)
 a=p.parse_args()
 if a.out.exists():p.error("Refusing to overwrite existing review DB")
 a.out.parent.mkdir(parents=True,exist_ok=True)
 src=sqlite3.connect("file:"+str(a.candidate_db.resolve())+"?mode=ro",uri=True)
 dst=sqlite3.connect(a.out)
 try:
  dst.executescript("""
    CREATE TABLE split_candidates(segment_id TEXT PRIMARY KEY,text_uid TEXT,
      source_pool TEXT,proposed_mcu_volume INTEGER,mapping_status TEXT,
      evidence_id TEXT,source_sha256 TEXT);
    CREATE INDEX ix_proposed ON split_candidates(proposed_mcu_volume);
    CREATE TABLE evidence(evidence_id TEXT PRIMARY KEY,source_pool TEXT,reference_url TEXT,
      evidence_level TEXT NOT NULL);
    CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  """)
  for evidence,(pool,url) in EVIDENCE.items():
   dst.execute("INSERT INTO evidence VALUES(?,?,?,?)",
     (evidence,pool,url,"SOURCE_STRUCTURE_ONLY_NOT_PARAGRAPH_VERIFIED"))
  dst.execute("INSERT INTO evidence VALUES(?,?,?,?)",("OTHER_PENDING","",
      "https://tipitaka.cloud/library/","NOT_VERIFIED"))
  counts=collections.Counter(); per_volume=collections.Counter(); buff=[]
  tables={r[0] for r in src.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if "candidate_map" in tables:
   table,pool_col,hash_col,status_col="candidate_map","volume_candidates","source_sha256","mapping_status"
  elif "mapping_candidates" in tables:
   table,pool_col,hash_col,status_col="mapping_candidates","volumes","sha256","status"
  else:
   raise ValueError("No recognized candidate mapping table")
  rows=src.execute(f"""SELECT segment_id,text_uid,{pool_col},{hash_col}
    FROM {table} WHERE {status_col}='SPLIT_REQUIRED' ORDER BY segment_id""")
  for seg,uid,pool,digest in rows:
   volume,evidence=decide(pool,uid)
   status="SOURCE_ALIGNED_CANDIDATE" if volume is not None else "REVIEW_REQUIRED"
   counts[(pool,status)]+=1
   if volume is not None:per_volume[volume]+=1
   buff.append((seg,uid,pool,volume,status,evidence,digest))
   if len(buff)>=10000:dst.executemany("INSERT INTO split_candidates VALUES(?,?,?,?,?,?,?)",buff);buff=[]
  if buff:dst.executemany("INSERT INTO split_candidates VALUES(?,?,?,?,?,?,?)",buff)
  total=src.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
  expected=src.execute(f"SELECT count(*) FROM {table} WHERE {status_col}='SPLIT_REQUIRED'").fetchone()[0]
  actual=dst.execute("SELECT count(*) FROM split_candidates").fetchone()[0]
  approved=dst.execute("SELECT count(*) FROM split_candidates WHERE mapping_status='SOURCE_ALIGNED_CANDIDATE'").fetchone()[0]
  assert total==444701 and expected==actual and dst.execute("pragma integrity_check").fetchone()[0]=="ok"
  dst.executemany("INSERT INTO metadata VALUES (?,?)",[
    ("verified_mcu_volumes","0"),("release_ready","NO"),("license_check","PENDING"),
    ("edition_crosswalk_status","CANDIDATE_ONLY"),("upstream_total",str(total))])
  dst.commit()
  data={"version":"2.3.9.2","total_source_segments":total,"previous_split_pool":expected,
        "new_source_aligned_candidates":approved,"remaining_unresolved":actual-approved,
        "verified_mcu_volumes":0,
        "counts":[{"pool":pool,"status":status,"segments":count}
                  for (pool,status),count in sorted(counts.items())],
        "per_volume_split_candidate_counts":dict(per_volume),
        "license_review":"PENDING",
        "notice":"Source-UID candidates only; no proof of MCU edition paragraph-level match."}
  a.report.parent.mkdir(parents=True,exist_ok=True)
  a.report.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
  print(json.dumps(data,indent=2))
 except Exception:
  dst.close();a.out.unlink(missing_ok=True);raise
 finally:src.close();dst.close()
if __name__=="__main__":main()
