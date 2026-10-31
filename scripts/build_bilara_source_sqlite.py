#!/usr/bin/env python3
"""Build a provenance-preserving OFFLINE SQLite from published Bilara Pali root JSON.
Does NOT equate Bilara collections with the edition-specific 45-volume catalog.
Source redistribution must be separately approved before shipping APK.
"""
import argparse, hashlib, json, pathlib, sqlite3, sys
p=argparse.ArgumentParser()
p.add_argument("root",type=pathlib.Path,help="checked-out bilara-data/root/pli/ms")
p.add_argument("--output",type=pathlib.Path,default=pathlib.Path("pali_root_source.sqlite"))
p.add_argument("--source-commit",required=True)
a=p.parse_args()
if not a.root.is_dir():sys.exit("Missing source root")
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.unlink(missing_ok=True)
conn=sqlite3.connect(a.output)
conn.executescript("""
CREATE TABLE source_segments (
 segment_id TEXT PRIMARY KEY, body TEXT NOT NULL, source_file TEXT NOT NULL,
 source_commit TEXT NOT NULL, sha256 TEXT NOT NULL
);
CREATE INDEX idx_source_file ON source_segments(source_file);
CREATE TABLE build_info (name TEXT PRIMARY KEY, value TEXT NOT NULL);
""")
files=0;segments=0
for f in sorted(a.root.rglob("*.json")):
 src=f.relative_to(a.root).as_posix()
 obj=json.loads(f.read_text(encoding="utf-8"))
 if not isinstance(obj,dict):continue
 files+=1
 for key,value in obj.items():
  if not isinstance(key,str) or not isinstance(value,str) or not value.strip():continue
  digest=hashlib.sha256(value.encode("utf-8")).hexdigest()
  try:conn.execute("INSERT INTO source_segments VALUES (?,?,?,?,?)",(key,value,src,a.source_commit,digest))
  except sqlite3.IntegrityError:sys.exit("Conflicting segment ID: "+key)
  segments+=1
conn.execute("INSERT INTO build_info VALUES ('source','suttacentral/bilara-data published root/pli/ms')")
conn.execute("INSERT INTO build_info VALUES ('commit',?)",(a.source_commit,))
conn.execute("INSERT INTO build_info VALUES ('catalog_mapping','NOT VERIFIED — 45 volume catalog NOT mapped')")
conn.commit();conn.close()
print(json.dumps({"source_files":files,"pali_segments":segments,"sqlite_bytes":a.output.stat().st_size,"mapped_45_volumes":0,"complete_45":False}))
if not segments:sys.exit("No source segments imported")
