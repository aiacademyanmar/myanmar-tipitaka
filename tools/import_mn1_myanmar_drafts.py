#!/usr/bin/env python3
"""Import MN1 Burmese AI draft (334 Pāli source IDs) as UNREVIEWED content.

This preserves exact source IDs/SHA-256, never asserts MCU 45-edition
equivalence, and never promotes generated translations to approved status.
Source CSV is delivered separately in the MN1 translation package.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path

FIELDS=["Segment ID","Mahāsaṅgīti Pāli Roman","မြန်မာ AI ဘာသာပြန်မူကြမ်း",
 "မြန်မာ AI ရှင်းလင်းချက်မူကြမ်း","Review Status","Translation Method","Source SHA256","Source Path"]
METHODS={"PRESERVED_PRIOR_AI_DRAFT","TRANSLATED_EXPLICIT_SOURCE",
 "ELLIPSIS_SOURCE_REQUIRES_EXPANSION","SECTION_END_NOTE"}

def build(csvfile,outfile):
 csvfile,outfile=Path(csvfile),Path(outfile)
 if outfile.exists():raise FileExistsError(outfile)
 with csvfile.open("r",encoding="utf-8-sig",newline="") as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError("Wrong MN1 draft CSV header")
  rows=list(reader)
 if len(rows)!=334:raise ValueError("Exactly 334 MN1 source segments expected")
 outfile.parent.mkdir(parents=True,exist_ok=True)
 db=sqlite3.connect(outfile)
 try:
  db.executescript("""
   CREATE TABLE pali_myanmar(
     segment_id TEXT PRIMARY KEY,source_pali_roman TEXT NOT NULL,
     my_translation_draft TEXT NOT NULL,my_explanation_draft TEXT NOT NULL,
     draft_status TEXT NOT NULL CHECK(draft_status='AI_DRAFT_UNREVIEWED'),
     translation_method TEXT NOT NULL,source_sha256 TEXT NOT NULL,
     source_path TEXT NOT NULL,approved INTEGER NOT NULL DEFAULT 0 CHECK(approved=0),
     reviewer TEXT);
   CREATE INDEX ix_translation_method ON pali_myanmar(translation_method);
   CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
  """)
  source_ids=set();ellipsis=0
  for r in rows:
   sid=r["Segment ID"];pali=r["Mahāsaṅgīti Pāli Roman"]
   digest=hashlib.sha256(pali.encode("utf8")).hexdigest()
   if (not sid.startswith("mn1:") or sid in source_ids or
       digest!=r["Source SHA256"] or
       r["Review Status"]!="AI_DRAFT_UNREVIEWED" or
       r["Translation Method"] not in METHODS or
       not r["မြန်မာ AI ဘာသာပြန်မူကြမ်း"].strip() or
       not r["မြန်မာ AI ရှင်းလင်းချက်မူကြမ်း"].strip()):
    raise ValueError("Unverified or malformed draft "+sid)
   source_ids.add(sid)
   if r["Translation Method"]=="ELLIPSIS_SOURCE_REQUIRES_EXPANSION":
    if "…" not in pali:raise ValueError("Ellipsis marker mismatch")
    ellipsis+=1
   db.execute("INSERT INTO pali_myanmar VALUES(?,?,?,?,?,?,?,?,0,NULL)",
    (sid,pali,r["မြန်မာ AI ဘာသာပြန်မူကြမ်း"],
      r["မြန်မာ AI ရှင်းလင်းချက်မူကြမ်း"],"AI_DRAFT_UNREVIEWED",
      r["Translation Method"],digest,r["Source Path"]))
  if ellipsis!=154:raise ValueError("Expected 154 unexpanded source abbreviations")
  db.executemany("INSERT INTO metadata VALUES (?,?)",[
   ("source_edition","Mahāsaṅgīti Roman Pāli"),("translation_status","AI_DRAFT_ONLY"),
   ("mcu45_verified_books","0"),("ai_draft_segments","334"),
   ("source_abbreviations_unexpanded","154"),("human_approved_segments","0"),
   ("approved_for_offline_release","NO")])
  db.commit()
  if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("SQLite integrity failed")
  return {"source_segments":len(rows),"draft_segments":len(rows),
          "unexpanded_source_abbreviations":ellipsis,"approved_segments":0,
          "MCU_45_verified_books":0,"release_ready":False}
 except Exception:
  db.close();outfile.unlink(missing_ok=True);raise
 finally:db.close()

if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--csv",required=True,type=Path)
 p.add_argument("--out",required=True,type=Path)
 a=p.parse_args()
 print(json.dumps(build(a.csv,a.out),ensure_ascii=False,indent=2))
