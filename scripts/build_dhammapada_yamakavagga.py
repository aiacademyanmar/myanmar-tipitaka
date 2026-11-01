#!/usr/bin/env python3
"""Build independent, explicitly unreviewed Myanmar verse drafts for Dhp 1–20.
Never add these drafts to the scholar-reviewed translation tables.
"""
import argparse,csv,re,sqlite3,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--database",default="app/src/main/assets/tipitaka_offline.sqlite")
 p.add_argument("--drafts",default=str(ROOT/"corpus/dhammapada_yamakavagga_my_drafts.csv"))
 a=p.parse_args()
 con=sqlite3.connect(a.database)
 con.execute("""CREATE TABLE IF NOT EXISTS dhammapada_yamakavagga(
 verse INTEGER PRIMARY KEY, pali_text TEXT NOT NULL, my_draft TEXT NOT NULL,
 source_ref TEXT NOT NULL, translation_status TEXT NOT NULL
 CHECK(translation_status='ai_draft_unreviewed'))""")
 draft={}
 with open(a.drafts,encoding="utf-8",newline="") as f:
  for r in csv.DictReader(f):
   n=int(r["verse"])
   assert n in range(1,21) and n not in draft and r["status"]=="ai_draft_unreviewed" and r["translation_my"].strip()
   draft[n]=r["translation_my"].strip()
 assert len(draft)==20
 raw=list(con.execute("""SELECT segment_id,body,source_file
 FROM paragraphs WHERE volume=25 AND source_file LIKE 'sutta/kn/dhp/dhp1-20_%'
 ORDER BY id"""))
 grouped={i:[] for i in range(1,21)}
 for seg,body,file in raw:
  m=re.fullmatch(r"dhp(\d+):(\d+)",seg)
  if m and int(m.group(1)) in grouped and int(m.group(2))>=1:
   grouped[int(m.group(1))].append(body.strip())
 assert all(grouped.values()),"Original Pali for one or more verses missing"
 with con:
  for n in range(1,21):
   con.execute("""INSERT OR REPLACE INTO dhammapada_yamakavagga VALUES(?,?,?,?,'ai_draft_unreviewed')""",
    (n,"\n".join(grouped[n]),draft[n],
     "suttacentral/bilara-data published/root/pli/ms/sutta/kn/dhp/dhp1-20_root-pli-ms.json"))
 count=con.execute("SELECT COUNT(*) FROM dhammapada_yamakavagga").fetchone()[0]
 assert count==20
 con.close()
 print("Verified offline Dhammapada Yamakavagga: 20 verses + 20 labeled unreviewed Myanmar drafts.")
if __name__=="__main__": main()
