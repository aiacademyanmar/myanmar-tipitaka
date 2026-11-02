#!/usr/bin/env python3
"""Validate that a native Android APK really bundles the pinned Pali SQLite.

Rejects an unbundled shell APK, broken SQLites, or a source revision mismatch.
Never reports 45-volume edition mapping or Myanmar translations as approved.
"""
from __future__ import annotations
import argparse,hashlib,json,pathlib,sqlite3,tempfile,zipfile,sys

def inspect(apk: pathlib.Path,reference: pathlib.Path, output: pathlib.Path):
    if not apk.is_file():raise ValueError("APK output does not exist")
    if not reference.is_file():raise ValueError("Source SQLite does not exist")
    with zipfile.ZipFile(apk) as z:
        entries={n for n in z.namelist()}
        name="assets/pali_root_source.sqlite"
        if name not in entries:raise ValueError("APK does not bundle the original Pali SQLite")
        if "assets/upstream_LICENSE.md" not in entries:
            raise ValueError("APK missing upstream SuttaCentral license notice")
        with tempfile.TemporaryDirectory() as directory:
            extracted=pathlib.Path(directory)/"pali_root_source.sqlite"
            digest=hashlib.sha256()
            with z.open(name) as src,extracted.open("wb") as dst:
                while chunk:=src.read(1024*1024):
                    dst.write(chunk);digest.update(chunk)
            db=sqlite3.connect(f"file:{extracted.resolve()}?mode=ro",uri=True)
            expected=sqlite3.connect(f"file:{reference.resolve()}?mode=ro",uri=True)
            try:
                if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
                    raise ValueError("Packaged Pali SQLite integrity_check failed")
                count=db.execute("SELECT COUNT(*) FROM source_segments").fetchone()[0]
                files=db.execute("SELECT COUNT(DISTINCT source_file) FROM source_segments").fetchone()[0]
                metadata=dict(db.execute("SELECT name,value FROM build_info"))
                expected_meta=dict(expected.execute("SELECT name,value FROM build_info"))
                expected_count=expected.execute("SELECT COUNT(*) FROM source_segments").fetchone()[0]
                if count<=0 or files<=0 or count!=expected_count:
                    raise ValueError("Packaged source paragraph count mismatch")
                if metadata.get("commit")!=expected_meta.get("commit"):
                    raise ValueError("Packaged source pinned commit mismatch")
                if metadata.get("catalog_mapping") is None or "NOT VERIFIED" not in metadata["catalog_mapping"]:
                    raise ValueError("Unverified 45-volume edition status is missing")
                data={"version":"2.3.6.9","status":"PALI_SOURCE_OFFLINE_PREVIEW",
                      "pali_source_bundled":True,"source_segments":count,
                      "source_files":files,"source_commit":metadata["commit"],
                      "sqlite_sha256":digest.hexdigest(),
                      "packaged_database_bytes":extracted.stat().st_size,
                      "mcu_45_books_verified":0,"approved_myanmar_translations":0,
                      "approved_myanmar_explanations":0,
                      "is_final_45_volume_release":False}
            finally:db.close();expected.close()
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return data

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--apk",type=pathlib.Path,required=True)
    parser.add_argument("--source-db",type=pathlib.Path,required=True)
    parser.add_argument("--report",type=pathlib.Path,default=pathlib.Path("bundled_pali_apk_qa.json"))
    a=parser.parse_args()
    try:print(json.dumps(inspect(a.apk,a.source_db,a.report),ensure_ascii=False,indent=2))
    except Exception as error:
        print("Bundled Pali preview APK gate FAILED: "+str(error),file=sys.stderr)
        sys.exit(1)
