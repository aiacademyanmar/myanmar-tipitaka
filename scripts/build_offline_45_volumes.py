#!/usr/bin/env python3
"""Build 45 individually readable Pali volumes from public-domain original Bilara segments.

This is a SOURCE-ALIGNED 45-book reader, NOT a verified verbatim MCU Pali edition.
In particular, Patthana's 6 physical-volume breakpoints are PROVISIONAL.
Never claim exact MCU text or boundaries solely from these mapping rules.
"""
import argparse
import collections
import csv
import hashlib
import json
import pathlib
import re
import sqlite3
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]

def source_num(path, expr):
    m=re.search(expr,path)
    return int(m.group(1)) if m else None

def pick_volume(path):
    if path.startswith("vinaya/pli-tv-bu-vb/"):
        if "/pli-tv-bu-vb-pj/" in path or "/pli-tv-bu-vb-ss/" in path or "/pli-tv-bu-vb-ay/" in path:
            return 1
        return 2
    if path.startswith("vinaya/pli-tv-bi-vb/"):
        return 3
    if path.startswith("vinaya/pli-tv-kd/"):
        n=source_num(path,r"pli-tv-kd(\d+)_")
        if n is None: return None
        if n<=4: return 4
        if n<=10: return 5
        if n<=14: return 6
        if n<=22: return 7
        return None
    if path.startswith("vinaya/pli-tv-pvr/") or path.startswith("vinaya/pli-tv-pvr_"):
        return 8
    n=source_num(path,r"^sutta/dn/dn(\d+)_")
    if n is not None:return 9 if n<=13 else 10 if n<=23 else 11 if n<=34 else None
    n=source_num(path,r"^sutta/mn/mn(\d+)_")
    if n is not None:return 12 if n<=50 else 13 if n<=100 else 14 if n<=152 else None
    n=source_num(path,r"^sutta/sn/sn(\d+)/")
    if n is not None:return 15 if n<=11 else 16 if n<=21 else 17 if n<=34 else 18 if n<=44 else 19 if n<=56 else None
    n=source_num(path,r"^sutta/an/an(\d+)/")
    if n is not None:return 20 if n<=3 else 21 if n==4 else 22 if n<=6 else 23 if n<=9 else 24 if n<=11 else None
    for sub in ("kp","dhp","ud","iti","snp"):
        if path.startswith("sutta/kn/"+sub+"/"):return 25
    for sub in ("vv","pv","thag","thig"):
        if path.startswith("sutta/kn/"+sub+"/"):return 26
    n=source_num(path,r"^sutta/kn/ja/ja(\d+)_")
    if n is not None:return 27 if n<=525 else 28 if n<=547 else None
    if path.startswith("sutta/kn/mnd/"):return 29
    if path.startswith("sutta/kn/cnd/"):return 30
    if path.startswith("sutta/kn/ps/"):return 31
    n=source_num(path,r"^sutta/kn/tha-ap/tha-ap(\d+)_")
    if n is not None:return 32 if n<=410 else 33
    if path.startswith("sutta/kn/thi-ap/") or path.startswith("sutta/kn/bv/") or path.startswith("sutta/kn/cp/"):return 33
    if path.startswith("abhidhamma/ds/"):return 34
    if path.startswith("abhidhamma/vb/"):return 35
    if path.startswith("abhidhamma/dt/") or path.startswith("abhidhamma/pp/"):return 36
    if path.startswith("abhidhamma/kv/"):return 37
    n=source_num(path,r"^abhidhamma/ya/ya(\d+)/")
    if n is not None:return 38 if n<=7 else 39 if n<=10 else None
    n=source_num(path,r"^abhidhamma/patthana/patthana(\d+)/")
    if n is not None:
        # Balanced SOURCE GROUPS, not exact printed MCU Paṭṭhāna boundaries.
        return 40+(n-1)//4 if n<=24 else None
    return None

def main():
    p=argparse.ArgumentParser()
    p.add_argument("source",type=pathlib.Path,help="bilara-data/root/pli/ms directory")
    p.add_argument("--output",type=pathlib.Path,default=ROOT/"app/src/main/assets/tipitaka_offline.sqlite")
    p.add_argument("--source-commit",required=True)
    p.add_argument("--report",type=pathlib.Path,default=pathlib.Path("offline_45_volume_mapping_report.json"))
    a=p.parse_args()
    if not a.source.is_dir():sys.exit("Bilara original Pali directory missing")
    with (ROOT/"corpus/45_volume_crosswalk.csv").open(encoding="utf-8") as h:
        catalog=list(csv.DictReader(h))
    if len(catalog)!=45 or [int(x["volume_id"]) for x in catalog]!=list(range(1,46)):
        sys.exit("Invalid 45 volume catalog")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.unlink(missing_ok=True)
    db=sqlite3.connect(a.output)
    db.executescript("""
        PRAGMA synchronous=OFF;
        PRAGMA journal_mode=OFF;
        CREATE TABLE paragraphs(
            id INTEGER PRIMARY KEY,
            volume INTEGER NOT NULL CHECK (volume BETWEEN 1 AND 45),
            body TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            source_file TEXT NOT NULL,
            segment_id TEXT NOT NULL UNIQUE
        );
        CREATE TABLE paragraph_explanations(
            paragraph_id INTEGER NOT NULL,
            language TEXT NOT NULL DEFAULT 'my',
            explanation_my TEXT NOT NULL,
            source_ref TEXT NOT NULL,
            provenance TEXT NOT NULL CHECK(provenance IN ('approved_translation','editorial_explanation')),
            reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
            PRIMARY KEY(paragraph_id,language)
        );
        CREATE TABLE volume_catalog(
            volume INTEGER PRIMARY KEY,
            title_my TEXT NOT NULL,
            source_alignment TEXT NOT NULL,
            source_segments INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT NOT NULL);
    """)
    uncertain={4,5,6,7,32,33,40,41,42,43,44,45}
    for i,row in enumerate(catalog,1):
        quality="PROVISIONAL_PART_SPLIT" if i in uncertain else "SOURCE_CHAPTER_ALIGNED_NOT_TEXT_IDENTICAL"
        db.execute("INSERT INTO volume_catalog(volume,title_my,source_alignment) VALUES (?,?,?)",
                   (i,row["book_title_my"],quality))
    source_files=collections.Counter()
    counts=collections.Counter()
    excluded=collections.Counter()
    ids=set()
    count=0
    for f in sorted(a.source.rglob("*.json")):
        relative=f.relative_to(a.source).as_posix()
        volume=pick_volume(relative)
        data=json.loads(f.read_text(encoding="utf-8"))
        if not isinstance(data,dict):continue
        if volume is None:
            excluded[relative.split("/")[0]]+=sum(isinstance(k,str) and isinstance(v,str) and bool(v.strip()) for k,v in data.items())
            continue
        batch=[]
        for segment,body in data.items():
            if not isinstance(segment,str) or not isinstance(body,str) or not body.strip():continue
            if segment in ids:sys.exit("Duplicated canonical segment: "+segment)
            ids.add(segment)
            count+=1
            batch.append((count,volume,body.strip(),
                          "https://github.com/suttacentral/bilara-data/blob/"+a.source_commit+"/root/pli/ms/"+relative,
                          relative,segment))
        db.executemany("INSERT INTO paragraphs VALUES (?,?,?,?,?,?)",batch)
        source_files[volume]+=1
        counts[volume]+=len(batch)
    db.executemany("UPDATE volume_catalog SET source_segments=? WHERE volume=?",
                   [(counts[i],i) for i in range(1,46)])
    db.executemany("INSERT INTO build_info VALUES (?,?)",
                   [("origin","suttacentral/bilara-data published root/pli/ms"),
                    ("source_commit",a.source_commit),
                    ("edition","Bilara Mahasangiti Pali structured into MCU-named 45 reader volumes"),
                    ("exact_mcu_edition_verified","false"),
                    ("all_45_source_groups_populated","true")])
    db.commit()
    db.executescript("""
        CREATE INDEX idx_paragraph_volume ON paragraphs(volume,id);
        CREATE INDEX idx_paragraph_source ON paragraphs(source_file,id);
        PRAGMA optimize;
    """)
    db.commit()
    db.close()
    missing=[i for i in range(1,46) if counts[i]==0]
    report={
        "source_language":"Pali",
        "pali_segments_in_45_readable_volumes":count,
        "volumes_with_source_text":45-len(missing),
        "volumes_total":45,
        "empty_volumes":missing,
        "source_files_by_volume":{str(i):source_files[i] for i in range(1,46)},
        "segments_by_volume":{str(i):counts[i] for i in range(1,46)},
        "provisional_part_split_volumes":sorted(uncertain),
        "excluded_source_segments_by_family":dict(excluded),
        "exact_mcu_edition_text_verified":False,
        "exact_mcu_volume_boundary_verified":False,
        "myanmar_explanations_included":False,
        "sqlite_bytes":a.output.stat().st_size
    }
    a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k not in ("source_files_by_volume","segments_by_volume")},ensure_ascii=False))
    if missing:
        a.output.unlink(missing_ok=True)
        sys.exit("Refusing incomplete 45-volume corpus: "+str(missing))
    if count<100000:sys.exit("Refusing unexpectedly small source corpus")

if __name__=="__main__":main()
