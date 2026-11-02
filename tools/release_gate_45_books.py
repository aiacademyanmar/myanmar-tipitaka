#!/usr/bin/env python3
"""Fail-closed MCU 45-volume offline content release gate.

Requires independently audited expected segment IDs for every MCU volume.
A volume is NOT complete merely because it contains one or more segments.
"""
import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

def check(database, manifest):
    m=json.loads(Path(manifest).read_text(encoding="utf-8"))
    expected=m.get("volumes",{})
    if set(expected)!={str(i) for i in range(1,46)}:
        raise ValueError("Manifest must independently specify all 45 MCU volumes")
    if m.get("crosswalk_reviewed") is not True or m.get("license_reviewed") is not True:
        raise ValueError("Crosswalk and source license review must be signed off")
    db=sqlite3.connect(f"file:{Path(database).resolve()}?mode=ro",uri=True)
    try:
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("SQLite integrity check failed")
        per_volume={}
        for number in range(1,46):
            entry=expected[str(number)]
            ids=entry.get("expected_segment_ids",[])
            if not ids or len(ids)!=len(set(ids)):
                raise ValueError(f"Volume {number}: expected IDs missing or duplicated")
            if entry.get("source_edition") is None or not entry.get("reviewer"):
                raise ValueError(f"Volume {number}: edition or reviewer missing")
            rows=db.execute("SELECT segment_id,pali,sha256 FROM approved_pali WHERE mcu_volume=?",(number,)).fetchall()
            actual_ids={r[0] for r in rows}
            if len(rows)!=len(actual_ids) or actual_ids!=set(ids):
                raise ValueError(f"Volume {number}: missing, extra or duplicate segments ({len(rows)} / {len(ids)})")
            for sid,pali,digest in rows:
                if not pali or hashlib.sha256(pali.encode("utf-8")).hexdigest()!=digest:
                    raise ValueError(f"Volume {number}: invalid hash for {sid}")
            per_volume[str(number)]=len(rows)
        return {"release_ready":True,"full_volumes":45,"segments_by_volume":per_volume}
    finally:
        db.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    p.add_argument("--manifest",required=True)
    args=p.parse_args()
    try:
        report=check(args.db,args.manifest)
        print(json.dumps(report,ensure_ascii=False,indent=2))
    except Exception as exc:
        print(json.dumps({"release_ready":False,"error":str(exc)},ensure_ascii=False))
        raise SystemExit(1)
