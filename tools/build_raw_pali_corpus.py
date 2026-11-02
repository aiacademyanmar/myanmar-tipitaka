#!/usr/bin/env python3
"""Build an UNREVIEWED SQLite source corpus from Bilara root/pli/ms JSON.

This preserves all three Pāli baskets and source references. It does NOT
assign Thai MCU 45-volume numbers, claim 45-volume completeness, or package
the data as approved Android content.
"""
import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path

BASKETS = ("vinaya", "sutta", "abhidhamma")
SCHEMA = """
PRAGMA journal_mode=DELETE;
CREATE TABLE source_segments(
  segment_id TEXT PRIMARY KEY,
  basket TEXT NOT NULL CHECK(basket IN ('vinaya','sutta','abhidhamma')),
  text_uid TEXT NOT NULL,
  source_file TEXT NOT NULL,
  pali TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  source_commit TEXT NOT NULL,
  review_status TEXT NOT NULL DEFAULT 'unreviewed'
    CHECK(review_status = 'unreviewed')
);
CREATE INDEX ix_source_basket ON source_segments(basket,text_uid,segment_id);
CREATE TABLE source_files(
  path TEXT PRIMARY KEY,
  basket TEXT NOT NULL,
  file_sha256 TEXT NOT NULL,
  segment_count INTEGER NOT NULL
);
CREATE TABLE source_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
"""

def build(root: Path, out: Path, source_commit: str):
    if len(source_commit) != 40 or any(c not in "0123456789abcdefABCDEF" for c in source_commit):
        raise ValueError("Exact 40-character upstream Git commit required")
    if not root.is_dir() or out.exists():
        raise ValueError("Root must exist and output must not exist")
    out.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(out)
    files = Counter()
    counts = Counter()
    try:
        db.executescript(SCHEMA)
        for basket in BASKETS:
            folder = root / basket
            if not folder.is_dir():
                raise ValueError(f"Required basket directory is missing: {folder}")
            for file in sorted(folder.rglob("*.json")):
                original = file.read_bytes()
                data = json.loads(original.decode("utf-8-sig"))
                if not isinstance(data, dict):
                    raise ValueError(f"Expected JSON object in {file}")
                n = 0
                for sid, pali in data.items():
                    if not isinstance(sid, str) or ":" not in sid or not sid.split(":",1)[0]:
                        raise ValueError(f"Bad segment id {sid!r} in {file}")
                    # Some Bilara JSON records are empty layout placeholders.
                    if not isinstance(pali, str):
                        raise ValueError(f"Bad text for {sid} in {file}")
                    if not pali.strip():
                        counts["empty_layout_records"] += 1
                        continue
                    uid = sid.split(":", 1)[0]
                    try:
                        db.execute("""INSERT INTO source_segments
                          (segment_id,basket,text_uid,source_file,pali,text_sha256,source_commit)
                          VALUES(?,?,?,?,?,?,?)""",
                          (sid,basket,uid,file.relative_to(root).as_posix(),pali,
                           hashlib.sha256(pali.encode("utf-8")).hexdigest(),source_commit))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError(f"Duplicate segment ID {sid} in {file}") from exc
                    n += 1
                db.execute("INSERT INTO source_files VALUES (?,?,?,?)",
                           (file.relative_to(root).as_posix(),basket,
                            hashlib.sha256(original).hexdigest(),n))
                files[basket] += 1
                counts[basket] += n
        if any(files[k] == 0 or counts[k] == 0 for k in BASKETS):
            raise ValueError("Every Pāli basket requires nonempty source JSON")
        metadata = {
            "source_repo":"https://github.com/suttacentral/bilara-data",
            "source_branch":"published",
            "source_edition":"Mahasangiti (ms)",
            "source_commit":source_commit,
            "verification":"UNREVIEWED",
            "mcu_45_volume_mapping":"NOT_VERIFIED",
            "full_mcu_volumes_verified":"0",
        }
        db.executemany("INSERT INTO source_metadata VALUES (?,?)", metadata.items())
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ValueError("SQLite integrity failed")
        report = {
            "status":"SOURCE_STAGED_UNREVIEWED",
            "source_commit":source_commit,
            "files_by_basket":dict(files),
            "segments_by_basket":{k:counts[k] for k in BASKETS},
            "empty_layout_records":counts["empty_layout_records"],
            "segments_total":sum(counts[k] for k in BASKETS),
            "mcu_45_volumes_verified":0,
        }
        return report
    except Exception:
        db.close()
        out.unlink(missing_ok=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--source-commit",required=True)
    p.add_argument("--report",type=Path)
    args=p.parse_args()
    report=build(args.root,args.out,args.source_commit)
    if args.report:
        args.report.parent.mkdir(parents=True,exist_ok=True)
        args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
