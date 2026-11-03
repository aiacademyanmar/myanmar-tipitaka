#!/usr/bin/env python3
"""V2.3.9.3: Apadana/Patthana MCU structural crosswalk, UNVERIFIED.

Accepts the existing V2.3.9.1 and V2.3.9.2 GitHub pipeline schemas.
No assertion of source license, MCU paragraph equivalence or APK readiness.
"""
import argparse, collections, hashlib, json, re, sqlite3
from pathlib import Path

APADANA="https://www.buddhaparisa.org/apadana.php"
PATTHANA="https://www.buddhaparisa.org/patthana.php"

def boundary(pool, uid):
    if pool=="32|33":
        m=re.fullmatch(r"tha-ap(\d+)",uid)
        if m:
            n=int(m.group(1))
            if not 1<=n<=563: raise ValueError(uid)
            return (32 if n<=412 else 33),None
        if re.fullmatch(r"thi-ap\d+",uid): return 33,None
        raise ValueError(f"Unknown Apadana source UID: {uid}")
    if pool=="40|41|42|43|44|45":
        m=re.fullmatch(r"patthana(\d+)\..+",uid)
        if not m: raise ValueError(f"Unknown Patthana source UID: {uid}")
        n=int(m.group(1))
        if n==1:return None,"40|41"
        if n==2:return None,"42|43"
        if 3<=n<=6:return 44,None
        if 7<=n<=24:return 45,None
        raise ValueError(f"Unexpected Patthana group: {uid}")
    raise ValueError(f"Unexpected input pool: {pool}")

def run(candidates, previous, pali_source, output, report):
    if output.exists():raise FileExistsError(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    c=sqlite3.connect(f"file:{candidates.resolve()}?mode=ro",uri=True)
    s=sqlite3.connect(f"file:{previous.resolve()}?mode=ro",uri=True)
    p=sqlite3.connect(f"file:{pali_source.resolve()}?mode=ro",uri=True)
    o=sqlite3.connect(output)
    try:
        o.executescript("""
         CREATE TABLE segment_boundary_review(segment_id TEXT PRIMARY KEY,text_uid TEXT,
          source_pool TEXT,proposed_mcu_volume INTEGER,remaining_pool TEXT,
          review_status TEXT NOT NULL,sha256 TEXT NOT NULL,source_path TEXT NOT NULL,
          source_commit TEXT NOT NULL,pali TEXT NOT NULL,
          mcu_paragraph_verified INTEGER NOT NULL DEFAULT 0 CHECK(mcu_paragraph_verified=0));
         CREATE INDEX ix_review_status ON segment_boundary_review(review_status,proposed_mcu_volume);
         CREATE TABLE evidence(reference TEXT PRIMARY KEY,url TEXT NOT NULL,
          evidence_level TEXT NOT NULL);
         CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        """)
        for k,url in [("APADANA_PARTS",APADANA),("PATTHANA_PARTS",PATTHANA)]:
            o.execute("INSERT INTO evidence VALUES(?,?,'STRUCTURAL_NOT_PARAGRAPH_VERIFIED')",(k,url))
        counts=collections.Counter()
        additions=collections.Counter()
        remaining=collections.Counter()
        pending=[]
        rows=s.execute("""SELECT segment_id,text_uid,source_pool,source_sha256 FROM
          split_candidates WHERE mapping_status='REVIEW_REQUIRED' ORDER BY segment_id""")
        for segment,uid,pool,sha in rows:
            assigned,unresolved=boundary(pool,uid)
            info=p.execute("SELECT sha256,source_path,source_commit,pali FROM segments WHERE segment_id=?",(segment,)).fetchone()
            if not info or sha!=info[0] or hashlib.sha256(info[3].encode("utf-8")).hexdigest()!=sha:
                raise ValueError(f"Missing/mismatched Pali source: {segment}")
            status="STRUCTURAL_CANDIDATE" if assigned is not None else "MCU_BOUNDARY_REVIEW_REQUIRED"
            counts[status]+=1
            if assigned is not None:additions[assigned]+=1
            else:remaining[unresolved]+=1
            pending.append((segment,uid,pool,assigned,unresolved,status,sha,info[1],info[2],info[3]))
            if len(pending)>=1000:
                o.executemany("INSERT INTO segment_boundary_review VALUES(?,?,?,?,?,?,?,?,?,?,0)",pending)
                pending=[]
        if pending:o.executemany("INSERT INTO segment_boundary_review VALUES(?,?,?,?,?,?,?,?,?,?,0)",pending)
        total=o.execute("SELECT count(*) FROM segment_boundary_review").fetchone()[0]
        assert total==sum(counts.values()) and total>0
        assert o.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        direct=c.execute("SELECT count(*) FROM mapping_candidates WHERE status='CANDIDATE_ONLY'").fetchone()[0]
        earlier=s.execute("SELECT count(*) FROM split_candidates WHERE mapping_status='SOURCE_ALIGNED_CANDIDATE'").fetchone()[0]
        o.executemany("INSERT INTO metadata VALUES(?,?)",[
           ("verified_mcu_volumes","0"),("release_ready","NO"),
           ("mcu_edition_paragraph_mapping","UNVERIFIED"),("license_check","PENDING")])
        o.commit()
        audit={"version":"2.3.9.3","prior_candidates":direct+earlier,
          "new_source_structure_candidates":counts["STRUCTURAL_CANDIDATE"],
          "total_structure_candidates":direct+earlier+counts["STRUCTURAL_CANDIDATE"],
          "remaining_boundary_review":counts["MCU_BOUNDARY_REVIEW_REQUIRED"],
          "per_volume_additions":dict(additions),"unresolved_pools":dict(remaining),
          "verified_mcu_volumes":0,"source_hashes_checked":total,
          "sqlite_integrity":"ok","status":"CANDIDATE_ONLY_NOT_RELEASE_READY"}
        report.parent.mkdir(parents=True,exist_ok=True)
        report.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(audit,ensure_ascii=False,indent=2))
    except Exception:
        o.close();output.unlink(missing_ok=True);raise
    finally:
        c.close();s.close();p.close();o.close()

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for k in ("candidate-db","prior-split-db","pali-db","out","report"):
        ap.add_argument("--"+k,type=Path,required=True)
    a=ap.parse_args()
    run(a.candidate_db,a.prior_split_db,a.pali_db,a.out,a.report)
