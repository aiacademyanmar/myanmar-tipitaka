#!/usr/bin/env python3
"""Audit staged Pāli segments before any offline reader release.

The audit never auto-approves content. Exit nonzero on integrity errors.
"""
import argparse
import json
import sqlite3
from collections import Counter

def audit(path):
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        quick = db.execute("PRAGMA integrity_check").fetchone()[0]
        cols = {r[1] for r in db.execute("PRAGMA table_info(pali_segments)")}
        required = {"segment_id","text_uid","mcu_volume","pali","sha256","source_commit","source_path","review_status"}
        if not required.issubset(cols):
            raise ValueError("Missing columns: "+", ".join(sorted(required-cols)))
        from hashlib import sha256
        totals = Counter()
        vols = set()
        issues = []
        for sid, uid, volume, pali, digest, commit, src, status in db.execute(
          "SELECT segment_id,text_uid,mcu_volume,pali,sha256,source_commit,source_path,review_status FROM pali_segments"):
            totals["segments"] += 1
            if volume is None: totals["unmapped"] += 1
            elif not 1 <= volume <= 45: issues.append(f"Invalid volume for {sid}: {volume}")
            else: vols.add(volume)
            if status == "verified": totals["verified_segments"] += 1
            if status not in {"pending","verified","rejected"}: issues.append(f"Invalid review status: {sid}")
            if not pali or sha256(pali.encode("utf-8")).hexdigest() != digest:
                issues.append(f"Hash mismatch: {sid}")
            if not sid.startswith(uid+":"): issues.append(f"UID mismatch: {sid}")
            if not src or not commit: issues.append(f"Missing provenance: {sid}")
        totals["mapped_volumes"] = len(vols)
        totals["unrepresented_volumes"] = 45-len(vols)
        # A volume with some segments is not a completed, verified book.
        totals["verified_full_volumes"] = 0
        return {"integrity":quick,"counts":dict(totals),"issues":issues[:100],
                "release_gate_pass":False,
                "note":"Full-volume completeness, provenance/license and crosswalk require independent review."}
    finally:
        db.close()

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("database")
    p.add_argument("--report", default="")
    args=p.parse_args()
    try:
        result=audit(args.database)
    except (sqlite3.Error, ValueError, OSError) as e:
        result={"release_gate_pass":False,"error":str(e)}
    out=json.dumps(result,ensure_ascii=False,indent=2)
    if args.report:
        with open(args.report,"w",encoding="utf-8") as f:f.write(out+"\n")
    print(out)
    raise SystemExit(1 if "error" in result or result.get("issues") or result.get("integrity")!="ok" else 0)
