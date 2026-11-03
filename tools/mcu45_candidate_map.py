#!/usr/bin/env python3
"""MCU 45-book provisional crosswalk from Bilara Roman Pāli source SQLite.

Conservative candidate mapping only. Never mark MCU volumes verified here.
Usage: python tools/mcu45_candidate_map.py source.sqlite review_candidates.sqlite
"""
import re
import sqlite3
import sys
import json
from collections import Counter
from pathlib import Path

def classify(uid, basket):
    if basket == "vinaya":
        if uid.startswith("pli-tv-bu-vb-"): return "1|2", "SPLIT_REQUIRED"
        if uid.startswith("pli-tv-bi-vb-"): return "3", "CANDIDATE_ONLY"
        m = re.fullmatch(r"pli-tv-kd(\d+)", uid)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 10: return "4|5", "SPLIT_REQUIRED"
            if 11 <= n <= 22: return "6|7", "SPLIT_REQUIRED"
        if uid.startswith("pli-tv-pvr"): return "8", "CANDIDATE_ONLY"
        if uid in ("pli-tv-bu-pm", "pli-tv-bi-pm"): return "", "SUPPLEMENTARY"
        return "", "UNMATCHED"

    family = (re.match(r"^[a-z-]+", uid) or [None])[0]
    if basket == "sutta":
        m = re.match(r"^(dn|mn|sn|an)(\d+)(?:\.|-|$)", uid)
        if m:
            f, n = m.group(1), int(m.group(2))
            if f == "dn": v = 9 if n <= 13 else 10 if n <= 23 else 11 if n <= 34 else None
            elif f == "mn": v = 12 if n <= 50 else 13 if n <= 100 else 14 if n <= 152 else None
            elif f == "sn": v = 15 if n <= 11 else 16 if n <= 21 else 17 if n <= 34 else 18 if n <= 44 else 19 if n <= 56 else None
            else: v = 20 if n <= 3 else 21 if n == 4 else 22 if n <= 6 else 23 if n <= 9 else 24 if n <= 11 else None
            if v: return str(v), "CANDIDATE_ONLY"
        groups = {25: {"kp","dhp","ud","iti","snp"},26: {"vv","pv","thag","thig"},29: {"mnd"},30: {"cnd"},31: {"ps"},33: {"bv","cp"}}
        for v, names in groups.items():
            if family in names: return str(v), "CANDIDATE_ONLY"
        if family == "ja": return "27|28", "SPLIT_REQUIRED"
        if family in ("tha-ap","thi-ap"): return "32|33", "SPLIT_REQUIRED"
        if family in ("mil","ne","pe"): return "", "OUTSIDE_MCU45"
        return "", "UNMATCHED"

    if basket == "abhidhamma":
        groups = {"ds":34,"vb":35,"dt":36,"pp":36,"kv":37}
        if family in groups: return str(groups[family]), "CANDIDATE_ONLY"
        if family == "ya": return "38|39", "SPLIT_REQUIRED"
        if family == "patthana": return "40|41|42|43|44|45", "SPLIT_REQUIRED"
    return "", "UNMATCHED"

def run(source, output):
    source, output = Path(source), Path(output)
    if output.exists(): raise FileExistsError(output)
    db = sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)
    out = sqlite3.connect(output)
    try:
        out.executescript("""
          CREATE TABLE mapping_candidates(
            segment_id TEXT PRIMARY KEY, text_uid TEXT, basket TEXT,
            volumes TEXT NOT NULL, status TEXT NOT NULL, sha256 TEXT NOT NULL);
          CREATE INDEX ix_map_volumes ON mapping_candidates(volumes);
          CREATE INDEX ix_map_status ON mapping_candidates(status);
        """)
        counts=Counter()
        buf=[]
        for sid,uid,basket,digest in db.execute("SELECT segment_id,text_uid,basket,sha256 FROM segments"):
            volumes,status=classify(uid,basket)
            buf.append((sid,uid,basket,volumes,status,digest))
            counts[status]+=1
            if len(buf)>=10000:
                out.executemany("INSERT INTO mapping_candidates VALUES(?,?,?,?,?,?)",buf)
                buf.clear()
        if buf: out.executemany("INSERT INTO mapping_candidates VALUES(?,?,?,?,?,?)",buf)
        out.commit()
        assert out.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
        assert out.execute("SELECT count(*) FROM mapping_candidates").fetchone()[0]==sum(counts.values())
        return {"segments":sum(counts.values()),"status_counts":dict(counts),
                "verified_MCU45_volumes":0,"release_ready":False}
    finally:
        db.close()
        out.close()

if __name__=="__main__":
    if len(sys.argv)!=3:raise SystemExit("usage: mcu45_candidate_map.py source.sqlite output.sqlite")
    print(json.dumps(run(sys.argv[1],sys.argv[2]),indent=2))
