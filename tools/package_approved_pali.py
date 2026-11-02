#!/usr/bin/env python3
"""Package a *fully reviewed* 45-book Pāli DB for the Android assets directory.

Does not download content or claim verification. Requires a passing release gate.
"""
import argparse
import hashlib
import json
import shutil
import sqlite3
from pathlib import Path
from release_gate_45_books import check

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    p.add_argument("--manifest",required=True)
    p.add_argument("--assets",default="app/src/main/assets")
    a=p.parse_args()
    report=check(a.db,a.manifest)  # fail closed
    if not report.get("release_ready") or report.get("full_volumes")!=45:
        raise SystemExit("REJECTED: 45 verified volumes not confirmed")
    source=Path(a.db).resolve()
    output=Path(a.assets)/"approved_pali.sqlite"
    if output.exists(): raise SystemExit("REJECTED: existing asset must be manually reviewed before replacement")
    output.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix(".sqlite.tmp")
    try:
        shutil.copyfile(source,temp)
        db=sqlite3.connect(f"file:{temp.resolve()}?mode=ro",uri=True)
        try:
            if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                raise ValueError("Packaged SQLite integrity check failed")
        finally: db.close()
        temp.replace(output)
    finally: temp.unlink(missing_ok=True)
    summary={"verified_volumes":45,"asset":str(output),"sha256":hashlib.sha256(output.read_bytes()).hexdigest(),"status":"RELEASE_GATE_PASSED"}
    print(json.dumps(summary,indent=2))

if __name__=="__main__":
    main()
