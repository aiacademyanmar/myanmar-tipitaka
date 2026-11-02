#!/usr/bin/env python3
"""Validate checked-in Bilara MN1 root text and create UNREVIEWED SQLite sample.

This script does not map to MCU 45-volume books or approve passages.
"""
import hashlib, json, sqlite3, argparse
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",default="data/pali_sources/ms/sutta/mn/mn1_root-pli-ms.json")
    p.add_argument("--out",default="build/mn1_unreviewed.sqlite")
    a=p.parse_args()
    source=Path(a.source)
    segments=json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(segments,dict) or not segments or any(not str(k).startswith("mn1:") or not isinstance(v,str) or not v.strip() for k,v in segments.items()):
        raise ValueError("Invalid MN1 JSON")
    output=Path(a.out)
    output.parent.mkdir(parents=True,exist_ok=True)
    if output.exists(): raise ValueError("Refusing to overwrite staging database")
    db=sqlite3.connect(output)
    try:
        db.execute("CREATE TABLE staging_pali(segment_id TEXT PRIMARY KEY,pali TEXT NOT NULL,sha256 TEXT NOT NULL,source_blob_sha TEXT NOT NULL,review_status TEXT NOT NULL CHECK(review_status='pending'))")
        # GitHub blob SHA recorded from the upstream Bilara Published file.
        upstream_blob="096c49f188d43174850a5bfebdc3432789cae836"
        for segment,pali in segments.items():
            db.execute("INSERT INTO staging_pali VALUES(?,?,?,?,?)",(segment,pali,hashlib.sha256(pali.encode('utf-8')).hexdigest(),upstream_blob,"pending"))
        db.commit()
        print(json.dumps({"source_entries":len(segments),"staged":db.execute("SELECT count(*) FROM staging_pali").fetchone()[0],"verified":0,"mcu_volumes_verified":0,"sqlite_integrity":db.execute("PRAGMA integrity_check").fetchone()[0]},indent=2))
    except Exception:
        db.close()
        output.unlink(missing_ok=True)
        raise
    finally:
        db.close()
if __name__=="__main__":
    main()
