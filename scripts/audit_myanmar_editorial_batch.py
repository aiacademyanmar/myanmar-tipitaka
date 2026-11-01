#!/usr/bin/env python3
"""Audit the Myanmar editorial import batch without modifying any database.

Drafts are never treated as approved. The importer remains the only writer,
and requires two distinct reviewers, rights evidence and matching Pali hash.
"""
import argparse,csv,hashlib,json,pathlib,re,sqlite3,sys
REQUIRED={"segment_id","content_type","text_my","source_ref","rights_evidence",
          "reviewer_1","reviewer_2","review_reference","reviewed_at","source_pali_sha256"}
KINDS={"translation","explanation"}
def main():
 ap=argparse.ArgumentParser()
 ap.add_argument("--database",type=pathlib.Path,default=pathlib.Path("app/src/main/assets/tipitaka_offline.sqlite"))
 ap.add_argument("--reviewed",type=pathlib.Path,default=pathlib.Path("corpus/reviewed_myanmar.csv"))
 ap.add_argument("--report",type=pathlib.Path,default=pathlib.Path("corpus/myanmar_editorial_batch_audit.json"))
 a=ap.parse_args()
 report={"database":str(a.database),"batch":str(a.reviewed),"rows":0,"valid_rows":0,
         "translations":0,"explanations":0,"unique_segments":0,"ready_for_import":False,"errors":[]}
 if not a.database.is_file():report["errors"].append("Native offline SQLite is missing.")
 if not a.reviewed.is_file():report["errors"].append("Reviewed Myanmar CSV is missing.")
 if report["errors"]:return finish(a.report,report,1)
 db=sqlite3.connect(f"file:{a.database.resolve()}?mode=ro",uri=True)
 try:
  tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
  if "paragraphs" not in tables:raise ValueError("paragraphs table missing")
  cols={x[1] for x in db.execute("PRAGMA table_info(paragraphs)")}
  if not {"id","body"}.issubset(cols):raise ValueError("paragraphs requires id and body")
  if "segment_id" not in cols:raise ValueError("paragraphs.segment_id is missing; generate native SQLite first")
  seen=set()
  with a.reviewed.open(encoding="utf-8-sig",newline="") as f:
   reader=csv.DictReader(f)
   missing=REQUIRED-set(reader.fieldnames or [])
   if missing:raise ValueError("CSV missing columns: "+", ".join(sorted(missing)))
   for line,row in enumerate(reader,2):
    report["rows"]+=1
    v={k:(row.get(k) or "").strip() for k in REQUIRED}
    if any(not x for x in v.values()):raise ValueError(f"Row {line}: blank required field")
    if v["content_type"] not in KINDS:raise ValueError(f"Row {line}: invalid content_type")
    if not re.search(r"[က-႟]",v["text_my"]):raise ValueError(f"Row {line}: text_my has no Myanmar script")
    if v["reviewer_1"].casefold()==v["reviewer_2"].casefold():raise ValueError(f"Row {line}: reviewers must be distinct")
    if not re.fullmatch(r"[0-9a-fA-F]{64}",v["source_pali_sha256"]):raise ValueError(f"Row {line}: invalid SHA-256")
    key=(v["segment_id"],v["content_type"])
    if key in seen:raise ValueError(f"Row {line}: duplicate segment_id/content_type")
    seen.add(key)
    try:sqlite3.Date if False else None
    except Exception:pass
    import datetime
    try:d=datetime.date.fromisoformat(v["reviewed_at"])
    except ValueError:raise ValueError(f"Row {line}: reviewed_at must be YYYY-MM-DD")
    if d>datetime.date.today():raise ValueError(f"Row {line}: review date is in the future")
    p=db.execute("SELECT body FROM paragraphs WHERE segment_id=?",(v["segment_id"],)).fetchone()
    if not p:raise ValueError(f"Row {line}: segment_id not found in native Pali database")
    actual=hashlib.sha256(p[0].encode("utf-8")).hexdigest()
    if actual!=v["source_pali_sha256"].lower():raise ValueError(f"Row {line}: Pali SHA-256 mismatch")
    report["valid_rows"]+=1;report["translations"]+=v["content_type"]=="translation";report["explanations"]+=v["content_type"]=="explanation"
  report["unique_segments"]=len({x[0] for x in seen})
  report["ready_for_import"]=report["rows"]>0 and report["valid_rows"]==report["rows"]
  report["status"]="READY_FOR_IMPORT" if report["ready_for_import"] else "EMPTY_BATCH_NO_CONTENT_IMPORTED"
 except Exception as e:report["errors"].append(str(e))
 finally:db.close()
 return finish(a.report,report,1 if report["errors"] else 0)
def finish(path,report,code):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return code
if __name__=="__main__":sys.exit(main())
