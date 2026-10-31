#!/usr/bin/env python3
"""Import a licensed, reviewed 45-volume Tipitaka corpus from CSV into Android SQLite.
Inputs: corpus/paragraphs.csv (volume,paragraph_id,body,source_ref)
        corpus/explanations_my.csv (paragraph_id,explanation_my,source_ref,provenance,reviewed)
Review and redistribution permissions are mandatory. Does not generate translations.
"""
import csv, sqlite3, sys, json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
paragraphs=root/"corpus/paragraphs.csv"
explanations=root/"corpus/explanations_my.csv"
licensefile=root/"corpus/LICENSE_AND_SOURCES.md"
out=root/"app/src/main/assets/tipitaka_offline.sqlite"
if not all(p.exists() for p in (paragraphs,explanations,licensefile)):
    print("No complete licensed corpus supplied; no offline scripture database generated.")
    sys.exit(0)
lic=licensefile.read_text(encoding="utf-8")
if "REDISTRIBUTION_APPROVED: YES" not in lic:
    sys.exit("Corpus redistribution not approved. Aborting.")
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():out.unlink()
con=sqlite3.connect(out)
schema=(root/"database/offline_tipitaka_explanations_schema.sql").read_text(encoding="utf-8")
con.executescript(schema)
seen=set()
with paragraphs.open(encoding="utf-8-sig",newline="") as f:
 for row in csv.DictReader(f):
  v=int(row["volume"]); pid=int(row["paragraph_id"])
  body=row["body"].strip(); source=row["source_ref"].strip()
  if not 1<=v<=45 or not body or not source or pid in seen:sys.exit("Invalid or duplicate paragraph: "+str(pid))
  con.execute("INSERT INTO paragraphs(id,volume,body,source_ref) VALUES(?,?,?,?)",(pid,v,body,source));seen.add(pid)
with explanations.open(encoding="utf-8-sig",newline="") as f:
 for row in csv.DictReader(f):
  pid=int(row["paragraph_id"])
  if pid not in seen or row["reviewed"].strip()!="1" or not row["explanation_my"].strip() or not row["source_ref"].strip():
   sys.exit("Missing source or unreviewed explanation: "+str(pid))
  if row["provenance"] not in ("approved_translation","editorial_explanation"):sys.exit("Invalid provenance")
  con.execute("INSERT INTO paragraph_explanations VALUES(?,?,?,?,?,1)",(pid,"my",row["explanation_my"].strip(),row["source_ref"].strip(),row["provenance"]))
con.commit()
v=con.execute("SELECT count(DISTINCT volume) FROM paragraphs").fetchone()[0]
p=con.execute("SELECT count(*) FROM paragraphs").fetchone()[0]
e=con.execute("SELECT count(*) FROM paragraph_explanations").fetchone()[0]
con.close()
if v!=45 or e!=p:
 out.unlink(missing_ok=True);sys.exit(f"Incomplete corpus: volumes={v}/45, explanations={e}/{p}")
print(f"Verified 45-volume offline corpus: {p} scripture paragraphs and {e} reviewed Myanmar explanations.")
