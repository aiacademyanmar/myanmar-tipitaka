#!/usr/bin/env python3
"""Import SuttaCentral *published* CC0 Burmese texts into existing Bilara Pali SQLite.
Only exact segment-ID matches are imported. Never labels these as AAII human-approved
or treats Thai MCU 45 volume index as a verified paragraph crosswalk.
"""
import argparse, sqlite3, json, hashlib, pathlib
parser=argparse.ArgumentParser()
parser.add_argument("pali_db",type=pathlib.Path)
parser.add_argument("translation_dir",type=pathlib.Path)
parser.add_argument("--source-commit",required=True)
parser.add_argument("--report",type=pathlib.Path,default=pathlib.Path("myanmar_import_report.json"))
a=parser.parse_args()
assert a.pali_db.is_file(),a.pali_db
assert a.translation_dir.is_dir(),a.translation_dir
db=sqlite3.connect(a.pali_db)
db.execute("""CREATE TABLE IF NOT EXISTS myanmar_published (
  segment_id TEXT PRIMARY KEY,
  body TEXT NOT NULL,
  source_file TEXT NOT NULL,
  source_commit TEXT NOT NULL,
  author TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status='SUTTACENTRAL_PUBLISHED_CC0_AAII_UNREVIEWED'),
  sha256 TEXT NOT NULL
)""")
db.execute("DELETE FROM myanmar_published")
input_files=0;nonempty=0;matched=0;missing=0
per_file={}
for f in sorted(a.translation_dir.rglob("*_translation-my-myteam.json")):
    records=json.loads(f.read_text(encoding="utf-8"))
    assert isinstance(records,dict)
    input_files+=1
    count=0
    for segment,body in records.items():
        if not isinstance(body,str) or not body.strip():continue
        nonempty+=1
        exists=db.execute("SELECT 1 FROM source_segments WHERE segment_id=? LIMIT 1",(segment,)).fetchone()
        if not exists:
            missing+=1
            continue
        relative=f.relative_to(a.translation_dir).as_posix()
        sha=hashlib.sha256(body.encode('utf-8')).hexdigest()
        db.execute("INSERT INTO myanmar_published VALUES(?,?,?,?,?,?,?)",(
          segment,body,relative,a.source_commit,"SuttaCentral myteam",
          "SUTTACENTRAL_PUBLISHED_CC0_AAII_UNREVIEWED",sha))
        matched+=1;count+=1
    per_file[f.name]=count
db.execute("INSERT OR REPLACE INTO build_info VALUES(?,?)",("myanmar_license","SuttaCentral/Bilara CC0; published Burmese by myteam"))
db.execute("INSERT OR REPLACE INTO build_info VALUES(?,?)",("myanmar_approval","Published source; AAII independent review NOT COMPLETE"))
db.commit()
pali_count=db.execute("SELECT count(*) FROM source_segments").fetchone()[0]
assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
assert matched>0 and input_files>0, "No published Myanmar translation segment matches"
assert db.execute("SELECT count(*) FROM myanmar_published").fetchone()[0]==matched
report={"status":"PALI_FULL_BILARA_SOURCE_PLUS_PARTIAL_PUBLISHED_BURMESE",
 "pali_source_segments":pali_count,"myanmar_input_files":input_files,
 "myanmar_nonempty_segments":nonempty,"myanmar_exact_id_matches":matched,
 "myanmar_unmatched":missing,"per_file":per_file,
 "independent_reviewer_approval":0,"approved_explanations":0,
 "verified_mcu_45_paragraph_crosswalk":0,
 "is_complete_45_volume_myanmar":False,
 "burmese_source":"suttacentral/bilara-data published translation/my/myteam",
 "license":"CC0","source_commit":a.source_commit}
a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False))
db.close()
