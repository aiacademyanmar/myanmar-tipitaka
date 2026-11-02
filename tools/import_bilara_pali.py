#!/usr/bin/env python3
"""Import published Bilara Pāli root JSON into a staging SQLite DB.

Usage:
 python tools/import_bilara_pali.py --root bilara-data/root/pli/ms --mapping data/bilara_mcu_mapping.json --out build/pali_staging.sqlite --source-commit <40-character-sha>

Mapping format: {"mn1": 10, "dn1": 9} (illustrative ONLY; IDs must be researched).
IMPORTANT: does not assert that any of the 45 volumes is verified.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

UID = re.compile(r"^[a-z0-9][a-z0-9_-]*$", re.I)

def run():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--mapping", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-commit", required=True)
    args = ap.parse_args()
    if not re.fullmatch(r"[a-fA-F0-9]{40}", args.source_commit):
        ap.error("--source-commit must be an exact 40-character Git commit SHA")
    if not args.root.is_dir() or not args.mapping.is_file():
        ap.error("Root directory and mapping JSON must exist")
    mapping = json.loads(args.mapping.read_text(encoding="utf-8"))
    if not isinstance(mapping, dict) or any(not isinstance(v, int) or isinstance(v,bool) or not 1 <= v <= 45 for v in mapping.values()):
        ap.error("Mapping must be {text_uid: MCU_volume_1_to_45}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.out.exists():
        ap.error("Output exists; refuse to overwrite verified or prior data")
    db = sqlite3.connect(args.out)
    try:
        db.executescript("""
        CREATE TABLE pali_segments(
          segment_id TEXT PRIMARY KEY, text_uid TEXT NOT NULL,
          mcu_volume INTEGER, pali TEXT NOT NULL, sha256 TEXT NOT NULL,
          source_commit TEXT NOT NULL, source_path TEXT NOT NULL,
          review_status TEXT NOT NULL DEFAULT 'pending'
          CHECK(review_status IN ('pending','verified','rejected'))
        );
        CREATE INDEX ix_pali_mcu ON pali_segments(mcu_volume, text_uid);
        CREATE TABLE import_summary(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        total = 0
        uids = set()
        unmapped = set()
        for fp in sorted(args.root.rglob("*.json")):
            data = json.loads(fp.read_text(encoding="utf-8-sig"))
            if not isinstance(data, dict):
                raise ValueError(f"JSON object required: {fp}")
            for sid, pali in data.items():
                if not isinstance(sid,str) or not isinstance(pali,str) or not pali.strip():
                    raise ValueError(f"Invalid segment in {fp}: {sid}")
                uid = sid.split(":",1)[0]
                if not UID.fullmatch(uid):
                    raise ValueError(f"Invalid text UID {uid}")
                vol = mapping.get(uid)
                uids.add(uid)
                if vol is None:
                    unmapped.add(uid)
                db.execute("INSERT INTO pali_segments(segment_id,text_uid,mcu_volume,pali,sha256,source_commit,source_path) VALUES (?,?,?,?,?,?,?)",
                  (sid,uid,vol,pali,hashlib.sha256(pali.encode("utf-8")).hexdigest(),args.source_commit,str(fp.relative_to(args.root))))
                total += 1
        if not total:
            raise ValueError("No segments imported")
        for k,v in {"segments":total,"text_uids":len(uids),"unmapped_uids":len(unmapped),"verified_segments":0,"verified_volumes":0,"source_commit":args.source_commit}.items():
            db.execute("INSERT INTO import_summary VALUES (?,?)",(k,str(v)))
        db.commit()
        print(json.dumps({"imported_segments":total,"unmapped_text_uids":sorted(unmapped),"verified_volumes":0},ensure_ascii=False))
        print("STAGING ONLY: reviewer approval, license/edition check and MCU crosswalk audit required.")
    except Exception:
        db.close()
        args.out.unlink(missing_ok=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
