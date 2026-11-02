#!/usr/bin/env python3
"""Export *reviewed* Pāli passages from staging SQLite for an offline Android reader.

Strict requirements: independently reviewed source segments, known MCU mapping, 
source provenance. This tool does NOT certify completeness of any volume.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

def export(staging, output):
    if Path(output).exists():
        raise ValueError("Refusing to overwrite existing reader database")
    source = sqlite3.connect(f"file:{Path(staging).resolve()}?mode=ro", uri=True)
    target = None
    try:
        if source.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("Staging integrity check failed")
        target = sqlite3.connect(output)
        target.executescript("""
        CREATE TABLE approved_pali (
           segment_id TEXT PRIMARY KEY,
           text_uid TEXT NOT NULL,
           mcu_volume INTEGER NOT NULL CHECK(mcu_volume BETWEEN 1 AND 45),
           pali TEXT NOT NULL,
           source_commit TEXT NOT NULL,
           source_path TEXT NOT NULL,
           sha256 TEXT NOT NULL
        );
        CREATE INDEX ix_approved_pali_volume ON approved_pali(mcu_volume, text_uid);
        CREATE TABLE content_manifest (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        count = 0
        volumes = set()
        for row in source.execute("""
            SELECT segment_id, text_uid, mcu_volume, pali, source_commit,
                   source_path, sha256
            FROM pali_segments WHERE review_status='verified'
            ORDER BY segment_id
        """):
            sid,uid,vol,pali,commit,path,digest = row
            if not isinstance(vol,int) or not 1 <= vol <= 45:
                raise ValueError(f"Verified segment {sid}: MCU mapping missing/invalid")
            if not isinstance(pali,str) or not pali.strip() or hashlib.sha256(pali.encode("utf-8")).hexdigest()!=digest:
                raise ValueError(f"Verified segment {sid}: hash mismatch")
            if not all((sid,uid,commit,path)) or not sid.startswith(uid+":"):
                raise ValueError(f"Verified segment {sid}: provenance/UID invalid")
            target.execute("INSERT INTO approved_pali VALUES(?,?,?,?,?,?,?)",row)
            count += 1
            volumes.add(vol)
        for key,value in {
            "approved_segments":str(count),
            "volumes_with_approved_segments":str(len(volumes)),
            "fully_verified_volumes":"0",
            "release_status":"PARTIAL_NOT_FULL_TEXT",
            "content_note":"Volume coverage is not volume completeness or licensing approval."
        }.items():
            target.execute("INSERT INTO content_manifest VALUES(?,?)",(key,value))
        target.commit()
        if target.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("Output integrity check failed")
        return {"approved_segments":count,"volumes_with_approved_segments":len(volumes),
                "fully_verified_volumes":0,"status":"PARTIAL_NOT_FULL_TEXT"}
    except Exception:
        if target: target.close()
        Path(output).unlink(missing_ok=True)
        raise
    finally:
        source.close()
        if target: target.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--staging",required=True)
    p.add_argument("--out",required=True)
    args=p.parse_args()
    print(json.dumps(export(args.staging,args.out),ensure_ascii=False))
