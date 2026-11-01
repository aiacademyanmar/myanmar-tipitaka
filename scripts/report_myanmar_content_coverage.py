#!/usr/bin/env python3
"""Read-only per-volume Myanmar translation/explanation coverage report.

Never fabricates content and never marks drafts approved. Missing native
corpus or missing Myanmar table is reported as a blocked/zero-coverage state.
"""
import argparse,json,pathlib,sqlite3,sys
ap=argparse.ArgumentParser()
ap.add_argument("--database",type=pathlib.Path,default=pathlib.Path("app/src/main/assets/tipitaka_offline.sqlite"))
ap.add_argument("--output",type=pathlib.Path,default=pathlib.Path("corpus/myanmar_content_coverage.json"))
a=ap.parse_args()
r={"status":"BLOCKED_NO_NATIVE_CORPUS","database_exists":a.database.is_file(),
   "total_paragraphs":0,"approved_translations":0,"approved_explanations":0,
   "paragraphs_with_both":0,"overall_translation_percent":0.0,
   "overall_explanation_percent":0.0,"volumes":[],"warnings":[]}
if a.database.is_file():
 db=sqlite3.connect(f"file:{a.database.resolve()}?mode=ro",uri=True)
 try:
  tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if not {"paragraphs","volumes"}.issubset(tables):
   r["warnings"].append("Native reader paragraphs/volumes tables are missing.")
  else:
   total=db.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
   r["total_paragraphs"]=total
   if "paragraph_myanmar_content" not in tables:
    r["warnings"].append("Myanmar editorial content table is not present; approved coverage is zero.")
    rows=db.execute("SELECT v.volume,v.title_my,COUNT(p.id) FROM volumes v LEFT JOIN paragraphs p ON p.volume=v.volume GROUP BY v.volume,v.title_my ORDER BY v.volume").fetchall()
    r["volumes"]=[{"volume":v,"title_my":t,"paragraphs":n,"translations":0,"explanations":0,"translation_percent":0.0,"explanation_percent":0.0} for v,t,n in rows]
   else:
    by=db.execute("""
      SELECT v.volume,v.title_my,COUNT(p.id),
       SUM(CASE WHEN EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.paragraph_id=p.id AND m.content_type='translation' AND m.reviewed=1) THEN 1 ELSE 0 END),
       SUM(CASE WHEN EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.paragraph_id=p.id AND m.content_type='explanation' AND m.reviewed=1) THEN 1 ELSE 0 END)
      FROM volumes v LEFT JOIN paragraphs p ON p.volume=v.volume
      GROUP BY v.volume,v.title_my ORDER BY v.volume""").fetchall()
    for v,t,n,tr,ex in by:
     n=n or 0;tr=tr or 0;ex=ex or 0
     r["volumes"].append({"volume":v,"title_my":t,"paragraphs":n,"translations":tr,"explanations":ex,
       "translation_percent":round(100*tr/n,2) if n else 0.0,
       "explanation_percent":round(100*ex/n,2) if n else 0.0})
    r["approved_translations"]=db.execute("SELECT COUNT(*) FROM paragraph_myanmar_content WHERE content_type='translation' AND reviewed=1").fetchone()[0]
    r["approved_explanations"]=db.execute("SELECT COUNT(*) FROM paragraph_myanmar_content WHERE content_type='explanation' AND reviewed=1").fetchone()[0]
    r["paragraphs_with_both"]=db.execute("""
      SELECT COUNT(*) FROM paragraphs p
      WHERE EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.paragraph_id=p.id AND m.content_type='translation' AND m.reviewed=1)
      AND EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.paragraph_id=p.id AND m.content_type='explanation' AND m.reviewed=1)""").fetchone()[0]
   if total:
    r["overall_translation_percent"]=round(100*r["approved_translations"]/total,2)
    r["overall_explanation_percent"]=round(100*r["approved_explanations"]/total,2)
   r["status"]="READY_FOR_EDITORIAL_REVIEW" if total else "BLOCKED_EMPTY_NATIVE_CORPUS"
 finally:db.close()
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(r,ensure_ascii=False,indent=2))
