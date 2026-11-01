#!/usr/bin/env python3
"""Build a standalone Maṅgala Sutta book into the bundled offline Tipitaka SQLite."""
import argparse,json,pathlib,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
def build(dbpath,data_path):
 data=json.loads(data_path.read_text(encoding="utf-8"))
 groups=data["groups"]; stanzas=data["pali_stanzas"]
 items=[(g["group"],g["title"],g["stanza"],x) for g in groups for x in g["items"]]
 if len(items)!=38 or [x[3]["number"] for x in items]!=list(range(1,39)):
  raise ValueError("Expected exactly 38 sequential Mangala blessings")
 if len(stanzas)!=13 or any(not s["segments"] for s in stanzas):
  raise ValueError("Expected 13 complete Pali stanzas")
 with sqlite3.connect(dbpath) as db:
  db.executescript("""
  CREATE TABLE IF NOT EXISTS mangala_sutta_info(
   id INTEGER PRIMARY KEY CHECK(id=1),title_my TEXT NOT NULL,source_ref TEXT NOT NULL,
   source_url TEXT NOT NULL,pali_source TEXT NOT NULL,blessing_count INTEGER NOT NULL);
  CREATE TABLE IF NOT EXISTS mangala_pali_stanzas(
   stanza INTEGER PRIMARY KEY CHECK(stanza BETWEEN 1 AND 13),
   pali_text TEXT NOT NULL,source_segments TEXT NOT NULL);
  CREATE TABLE IF NOT EXISTS mangala_blessings(
   number INTEGER PRIMARY KEY CHECK(number BETWEEN 1 AND 38),
   group_no INTEGER NOT NULL,group_title_my TEXT NOT NULL,
   stanza_ref TEXT NOT NULL,title_my TEXT NOT NULL,explanation_my TEXT NOT NULL,
   translation_status TEXT NOT NULL CHECK(translation_status='ai_draft_unreviewed'),
   source_ref TEXT NOT NULL);
  """)
  with db:
   db.execute("DELETE FROM mangala_blessings");db.execute("DELETE FROM mangala_pali_stanzas");db.execute("DELETE FROM mangala_sutta_info")
   db.execute("INSERT INTO mangala_sutta_info VALUES(1,?,?,?,?,?)",(data["title"],data["source"],data["source_url"],data["pali_source"],38))
   for s in stanzas:
    db.execute("INSERT INTO mangala_pali_stanzas VALUES(?,?,?)",(s["stanza"],"".join(x["text"] for x in s["segments"]),json.dumps([x["segment"] for x in s["segments"]],ensure_ascii=False)))
   for group,title,stanza,item in items:
    db.execute("INSERT INTO mangala_blessings VALUES(?,?,?,?,?,?,?,?)",(item["number"],group,title,stanza,item["title"],item["explanation"],item["status"],"Sutta Nipata 2.4 / "+stanza))
  counts=db.execute("SELECT COUNT(*),COUNT(DISTINCT group_no) FROM mangala_blessings").fetchone()
  pcount=db.execute("SELECT COUNT(*) FROM mangala_pali_stanzas").fetchone()[0]
  if counts!=(38,10) or pcount!=13:raise ValueError((counts,pcount))
 return {"blessings":38,"groups":10,"pali_stanzas":13}
def main():
 p=argparse.ArgumentParser();p.add_argument("--database",type=pathlib.Path,default=ROOT/"app/src/main/assets/tipitaka_offline.sqlite");p.add_argument("--source",type=pathlib.Path,default=ROOT/"corpus/mangala_sutta_38_my_drafts.json");a=p.parse_args()
 if not a.database.is_file():sys.exit("Offline Tipitaka SQLite not found")
 print(json.dumps(build(a.database,a.source),ensure_ascii=False))
if __name__=="__main__":main()
