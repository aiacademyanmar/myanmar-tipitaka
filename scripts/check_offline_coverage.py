#!/usr/bin/env python3
"""Verify a real, licensed 45-volume corpus, producing a truthful offline coverage report.
Optional database input: app/src/main/assets/tipitaka_offline.sqlite
Expected tables: paragraphs(id,volume,body,source_ref);
 paragraph_explanations(paragraph_id,language,explanation_my,source_ref,provenance,reviewed).
"""
from pathlib import Path
import sqlite3, json, sys
base=Path(__file__).resolve().parents[1]
path=base/"app/src/main/assets/tipitaka_offline.sqlite"
report={"corpus_present":path.exists(),"volumes_total":45,"volumes_with_text":0,"paragraphs":0,"reviewed_myanmar_explanations":0,"complete":False}
if path.exists():
  con=sqlite3.connect(f"file:{path}?mode=ro",uri=True)
  try:
    report["volumes_with_text"]=con.execute("SELECT COUNT(DISTINCT volume) FROM paragraphs WHERE length(trim(body))>0 AND length(trim(source_ref))>0").fetchone()[0]
    report["paragraphs"]=con.execute("SELECT COUNT(*) FROM paragraphs WHERE length(trim(body))>0 AND length(trim(source_ref))>0").fetchone()[0]
    report["reviewed_myanmar_explanations"]=con.execute("SELECT COUNT(*) FROM paragraph_explanations WHERE language='my' AND reviewed=1 AND length(trim(explanation_my))>0 AND length(trim(source_ref))>0").fetchone()[0]
    report["complete"]=report["volumes_with_text"]==45 and report["paragraphs"]>0 and report["reviewed_myanmar_explanations"]>=report["paragraphs"]
  finally:con.close()
(base/"offline_coverage_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
if not report["complete"]:print("INCOMPLETE OFFLINE FULL LIBRARY: do not advertise complete 45-volume paragraph explanations.")
