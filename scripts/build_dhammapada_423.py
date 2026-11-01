#!/usr/bin/env python3
"""Build all 423 Dhammapada verses grouped in 26 chapters from the licensed
Bilara Pali source already bundled in the 45-volume offline SQLite.
Independent Myanmar drafts are optional and NEVER labeled human reviewed.
"""
import argparse,csv,pathlib,re,sqlite3
ROOT=pathlib.Path(__file__).resolve().parents[1]

# Inclusive verse ranges: Dhammapada's traditional 26 vaggas.
CHAPTERS=[
 ("Yamakavagga","ယမကဝဂ်",1,20),
 ("Appamādavagga","အပ္ပမာဒဝဂ်",21,32),
 ("Cittavagga","စိတ္တဝဂ်",33,43),
 ("Pupphavagga","ပုပ္ဖဝဂ်",44,59),
 ("Bālavagga","ဗာလဝဂ်",60,75),
 ("Paṇḍitavagga","ပဏ္ဍိတဝဂ်",76,89),
 ("Arahantavagga","အရဟန္တဝဂ်",90,99),
 ("Sahassavagga","သဟဿဝဂ်",100,115),
 ("Pāpavagga","ပါပဝဂ်",116,128),
 ("Daṇḍavagga","ဒဏ္ဍဝဂ်",129,145),
 ("Jarāvagga","ဇရာဝဂ်",146,156),
 ("Attavagga","အတ္တဝဂ်",157,166),
 ("Lokavagga","လောကဝဂ်",167,178),
 ("Buddhavagga","ဗုဒ္ဓဝဂ်",179,196),
 ("Sukhavagga","သုခဝဂ်",197,208),
 ("Piyavagga","ပိယဝဂ်",209,220),
 ("Kodhavagga","ကောဓဝဂ်",221,234),
 ("Malavagga","မလဝဂ်",235,255),
 ("Dhammaṭṭhavagga","ဓမ္မဋ္ဌဝဂ်",256,272),
 ("Maggavagga","မဂ္ဂဝဂ်",273,289),
 ("Pakiṇṇakavagga","ပကိဏ္ဏကဝဂ်",290,305),
 ("Nirayavagga","နိရယဝဂ်",306,319),
 ("Nāgavagga","နာဂဝဂ်",320,333),
 ("Taṇhāvagga","တဏှာဝဂ်",334,359),
 ("Bhikkhuvagga","ဘိက္ခုဝဂ်",360,382),
 ("Brāhmaṇavagga","ဗြာဟ္မဏဝဂ်",383,423),
]
def load_drafts(path):
 drafts={}
 if not path.is_file():return drafts
 with path.open(encoding="utf-8-sig",newline="") as h:
  for r in csv.DictReader(h):
   n=int(r["verse"])
   if not (1<=n<=423) or n in drafts or not r["translation_my"].strip() or r["status"]!="ai_draft_unreviewed":
    raise ValueError("Invalid Myanmar draft row: "+str(n))
   drafts[n]=r["translation_my"].strip()
 return drafts

def build(db,drafts):
 mapping={}
 for chapter,(roman,my,first,last) in enumerate(CHAPTERS,1):
  for n in range(first,last+1):
   if n in mapping:raise ValueError("Overlapping verse "+str(n))
   mapping[n]=(chapter,roman,my)
 if set(mapping)!=set(range(1,424)):raise ValueError("Incomplete chapter mapping")
 rows=db.execute("""SELECT segment_id,body,source_file FROM paragraphs
  WHERE volume=25 AND source_file LIKE 'sutta/kn/dhp/%' ORDER BY id""")
 verses={n:[] for n in range(1,424)}
 sources={}
 for segment,body,source_file in rows:
  m=re.fullmatch(r"dhp(\d+):(\d+)",segment)
  if m:
   n,line=int(m.group(1)),int(m.group(2))
   if 1<=n<=423 and line>=1:
    verses[n].append((line,body.strip()))
    sources[n]=source_file
 missing=[n for n,parts in verses.items() if not parts]
 if missing:raise ValueError("Pali source lacks Dhammapada verses: "+str(missing))
 db.execute("""CREATE TABLE IF NOT EXISTS dhammapada_verses(
   verse INTEGER PRIMARY KEY CHECK(verse BETWEEN 1 AND 423),
   chapter INTEGER NOT NULL CHECK(chapter BETWEEN 1 AND 26),
   chapter_roman TEXT NOT NULL,chapter_my TEXT NOT NULL,
   pali_text TEXT NOT NULL,my_draft TEXT,
   translation_status TEXT NOT NULL CHECK(translation_status IN ('ai_draft_unreviewed','not_available')),
   source_ref TEXT NOT NULL)""")
 with db:
  db.execute("DELETE FROM dhammapada_verses")
  for n in range(1,424):
   chapter,roman,my=mapping[n]
   lines=sorted(verses[n])
   if len({line for line,_ in lines})!=len(lines):raise ValueError("Duplicate verse lines "+str(n))
   pali="\n".join(body for _,body in lines)
   draft=drafts.get(n)
   db.execute("INSERT INTO dhammapada_verses VALUES(?,?,?,?,?,?,?,?)",
     (n,chapter,roman,my,pali,draft,
      "ai_draft_unreviewed" if draft else "not_available",
      "suttacentral/bilara-data published/root/pli/ms/"+sources[n]))
 total=db.execute("SELECT COUNT(*),COUNT(DISTINCT chapter) FROM dhammapada_verses").fetchone()
 if total!=(423,26):raise ValueError("Expected 423 verses in 26 chapters")
 return len(drafts)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--database",type=pathlib.Path,default=ROOT/"app/src/main/assets/tipitaka_offline.sqlite")
 p.add_argument("--drafts",type=pathlib.Path,default=ROOT/"corpus/dhammapada_yamakavagga_my_drafts.csv")
 a=p.parse_args()
 if not a.database.is_file():raise SystemExit("Offline Pali SQLite must be built first")
 drafts=load_drafts(a.drafts)
 extra=load_drafts(ROOT/"corpus/dhammapada_draft_21_99.csv")
 if set(drafts)&set(extra):raise ValueError("Overlapping Myanmar draft verse numbers")
 drafts.update(extra)
 next_batch=load_drafts(ROOT/"corpus/dhammapada_draft_100_145.csv")
 if set(drafts)&set(next_batch):raise ValueError("Overlapping Myanmar draft numbers")
 drafts.update(next_batch)
 batch_146_196=load_drafts(ROOT/"corpus/dhammapada_draft_146_196.csv")
 if set(drafts)&set(batch_146_196):raise ValueError("Overlapping Myanmar drafts 146-196")
 drafts.update(batch_146_196)
 batch_197_234=load_drafts(ROOT/"corpus/dhammapada_draft_197_234.csv")
 if set(drafts)&set(batch_197_234):raise ValueError("Overlapping Myanmar drafts 197-234")
 drafts.update(batch_197_234)
 with sqlite3.connect(a.database) as db:
  draft_count=build(db,drafts)
 print(f"Dhammapada: 423 original Pali verses / 26 chapters; {draft_count} unreviewed Myanmar draft translations; {423-draft_count} without translations")
if __name__=="__main__":main()
