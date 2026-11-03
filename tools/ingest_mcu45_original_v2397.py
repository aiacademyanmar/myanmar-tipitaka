#!/usr/bin/env python3
"""V2.3.9.7: stage independently sourced MCU-1996 Thai-script Pāli volumes.

Input is an authorized, separately obtained 45-volume manifest plus JSON files.
This script DOES NOT download from web pages or infer that Thai translations,
Siam Rath or Mahasangiti texts are MCU original Pāli.
All output is UNREVIEWED. An acquired volume is NOT a verified volume.
"""
import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path

EDITION="MCU_PALI_1996"
ACQUIRED="ACQUIRED"
PENDING="PENDING"
THAI=re.compile(r"[\u0e00-\u0e7f]")

def build(manifest_path, source_dir, output_path, report_path):
    manifest_path=Path(manifest_path)
    source_dir=Path(source_dir)
    output_path=Path(output_path)
    report_path=Path(report_path)
    if output_path.exists():
        raise FileExistsError(output_path)
    data=json.loads(manifest_path.read_text(encoding="utf-8"))
    books=data.get("volumes")
    if not isinstance(books,list) or len(books)!=45:
        raise ValueError("Exactly 45 MCU volume registry entries required")
    indices=[b.get("volume") for b in books]
    if sorted(indices)!=list(range(1,46)):
        raise ValueError("Duplicate, absent or invalid MCU volume")
    if data.get("edition")!=EDITION:
        raise ValueError("Wrong Pāli edition; only MCU_PALI_1996 can enter MCU registry")
    source_dir=source_dir.resolve()
    output_path.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(output_path)
    try:
        db.executescript("""
        CREATE TABLE volume_registry(
          volume INTEGER PRIMARY KEY CHECK(volume BETWEEN 1 AND 45),
          edition TEXT NOT NULL, title TEXT NOT NULL,
          source_url TEXT, source_file TEXT, file_sha256 TEXT,
          source_status TEXT NOT NULL CHECK(source_status IN ('PENDING','ACQUIRED')),
          paragraph_count INTEGER NOT NULL,
          independent_corpus_complete INTEGER NOT NULL DEFAULT 0 CHECK(independent_corpus_complete=0),
          reviewer TEXT, rights_status TEXT NOT NULL DEFAULT 'PENDING'
        );
        CREATE TABLE mcu_reference_paragraphs(
          volume INTEGER NOT NULL, paragraph_id TEXT NOT NULL,
          pali_thai TEXT NOT NULL, page_no INTEGER,
          source_file TEXT NOT NULL,
          PRIMARY KEY(volume,paragraph_id),
          FOREIGN KEY(volume) REFERENCES volume_registry(volume)
        );
        CREATE INDEX ix_mcu_page ON mcu_reference_paragraphs(volume,page_no);
        CREATE TABLE source_metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        """)
        acquired=0
        paragraphs=0
        for book in sorted(books,key=lambda item:item["volume"]):
            vol=book["volume"]
            title=book.get("title")
            if not isinstance(title,str) or not title.strip():
                raise ValueError(f"MCU volume {vol}: title required")
            if book.get("edition") not in (None,EDITION):
                raise ValueError(f"MCU volume {vol}: edition mismatch")
            status=book.get("source_status","PENDING")
            if status not in (PENDING,ACQUIRED):
                raise ValueError(f"MCU volume {vol}: invalid source status")
            filename=f"mcu_{vol:02d}.json"
            count=0
            digest=""
            if status==ACQUIRED:
                if book.get("source_file")!=filename:
                    raise ValueError(f"MCU volume {vol}: unexpected file name")
                uri=book.get("source_url","")
                if not isinstance(uri,str) or not uri.startswith("https://"):
                    raise ValueError(f"MCU volume {vol}: source URL required")
                path=source_dir/filename
                if not path.is_file():
                    raise ValueError(f"MCU volume {vol}: file missing")
                binary=path.read_bytes()
                digest=hashlib.sha256(binary).hexdigest()
                if digest!=book.get("file_sha256"):
                    raise ValueError(f"MCU volume {vol}: file hash mismatch")
                doc=json.loads(binary.decode("utf-8-sig"))
                if (doc.get("edition")!=EDITION or doc.get("volume")!=vol or
                    doc.get("script")!="Thai" or doc.get("language")!="pli"):
                    raise ValueError(f"MCU volume {vol}: source JSON edition, language or script mismatch")
                rows=doc.get("paragraphs")
                if not isinstance(rows,list) or not rows:
                    raise ValueError(f"MCU volume {vol}: no text paragraphs")
                for p in rows:
                    pid=p.get("paragraph_id")
                    text=p.get("pali")
                    page=p.get("page")
                    if (not isinstance(pid,str) or not pid.strip() or
                        not isinstance(text,str) or not text.strip() or not THAI.search(text)):
                        raise ValueError(f"MCU volume {vol}: invalid Thai Pāli paragraph")
                    if page is not None and (type(page) is not int or page<1):
                        raise ValueError(f"MCU volume {vol}: invalid page")
                    try:
                        db.execute("INSERT INTO mcu_reference_paragraphs VALUES(?,?,?,?,?)",
                                   (vol,pid,text,page,filename))
                    except sqlite3.IntegrityError as exc:
                        raise ValueError(f"MCU volume {vol}: duplicate paragraph ID {pid}") from exc
                count=len(rows)
                acquired+=1
                paragraphs+=count
            else:
                if book.get("source_file") or book.get("file_sha256"):
                    raise ValueError(f"MCU volume {vol}: PENDING source must not declare file/hash")
            db.execute("INSERT INTO volume_registry VALUES(?,?,?,?,?,?,?,?,0,?,?)",
                       (vol,EDITION,title,book.get("source_url") or None,
                        filename if status==ACQUIRED else None,digest or None,status,
                        count,book.get("reviewer") or None,book.get("rights_status","PENDING")))
        db.executemany("INSERT INTO source_metadata VALUES(?,?)",[
            ("edition",EDITION),("source_mode","INDEPENDENT_REFERENCE_STAGING"),
            ("verified_mcu_volumes","0"),("release_ready","NO"),
            ("source_rights","REVIEW_REQUIRED"),
            ("full_45_volume_reference_ready","NO")])
        db.commit()
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("SQLite integrity failed")
        if db.execute("SELECT COUNT(*) FROM volume_registry").fetchone()[0]!=45:
            raise ValueError("Expected 45 registry volumes")
        if db.execute("SELECT COUNT(*) FROM mcu_reference_paragraphs").fetchone()[0]!=paragraphs:
            raise ValueError("Paragraph count mismatch")
        summary={"version":"2.3.9.7","edition":EDITION,"catalog_volumes":45,
                 "acquired_mcu_original_volumes":acquired,
                 "staged_mcu_paragraphs":paragraphs,
                 "verified_full_volumes":0,"release_ready":False,
                 "note":"Staged MCU original references require full edition and rights review"}
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return summary
    except Exception:
        db.close()
        output_path.unlink(missing_ok=True)
        raise
    finally:
        db.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build(a.manifest,a.source_dir,a.out,a.report),indent=2))
