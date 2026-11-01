#!/usr/bin/env python3
"""Build native 45-volume SQLite only from a fully evidenced, approved crosswalk.

Input CSV columns:
volume_id,book_title_my,pitaka,source_file_prefix,start_segment_id,end_segment_id,
mapping_status,reviewer_reference,rights_evidence

Every volume must be VERIFIED with exact inclusive endpoints, reviewer reference
and rights evidence. Every selected Bilara segment must map to exactly one
printed volume. No candidate-only fallback is allowed.
"""
import argparse,csv,hashlib,json,pathlib,sqlite3,sys
p=argparse.ArgumentParser()
p.add_argument("source_db",type=pathlib.Path)
p.add_argument("--crosswalk",type=pathlib.Path,default=pathlib.Path("corpus/45_volume_crosswalk.csv"))
p.add_argument("--output",type=pathlib.Path,default=pathlib.Path("tipitaka_offline.sqlite"))
p.add_argument("--report",type=pathlib.Path,default=pathlib.Path("native_corpus_report.json"))
a=p.parse_args()
if not a.source_db.is_file():sys.exit("Pali source staging SQLite missing")
rows=list(csv.DictReader(a.crosswalk.open(encoding="utf-8-sig",newline="")))
required={"volume_id","book_title_my","pitaka","source_file_prefix","start_segment_id","end_segment_id","mapping_status","reviewer_reference","rights_evidence"}
if len(rows)!=45:sys.exit(f"Expected exactly 45 crosswalk rows, found {len(rows)}")
if not required.issubset(set(rows[0] if rows else [])):sys.exit("Crosswalk missing required edition evidence columns: "+", ".join(sorted(required-set(rows[0] if rows else []))))
for n,r in enumerate(rows,1):
 if int(r["volume_id"])!=n:sys.exit(f"Crosswalk row {n}: volume_id/order mismatch")
 for k in ("source_file_prefix","start_segment_id","end_segment_id","reviewer_reference","rights_evidence"):
  if not r[k].strip():sys.exit(f"Volume {n}: missing {k}")
 if r["mapping_status"].strip().upper()!="VERIFIED":sys.exit(f"Volume {n}: mapping is not VERIFIED")
src=sqlite3.connect(f"file:{a.source_db.resolve()}?mode=ro",uri=True)
if src.execute("PRAGMA integrity_check").fetchone()[0]!="ok":sys.exit("Source SQLite integrity_check failed")
source_commit=src.execute("SELECT value FROM build_info WHERE name='commit'").fetchone()
if not source_commit:sys.exit("Pinned upstream source commit missing")
source_commit=source_commit[0]
out=a.output
out.parent.mkdir(parents=True,exist_ok=True)
tmp=out.with_suffix(out.suffix+".part")
tmp.unlink(missing_ok=True)
dst=sqlite3.connect(tmp)
dst.executescript("""
PRAGMA foreign_keys=ON;
CREATE TABLE volumes(volume INTEGER PRIMARY KEY,title_my TEXT NOT NULL,pitaka TEXT NOT NULL,source_file_prefix TEXT NOT NULL,reviewer_reference TEXT NOT NULL,rights_evidence TEXT NOT NULL);
CREATE TABLE paragraphs(id INTEGER PRIMARY KEY,volume INTEGER NOT NULL REFERENCES volumes(volume),body TEXT NOT NULL,source_ref TEXT NOT NULL,segment_id TEXT NOT NULL UNIQUE,source_sha256 TEXT NOT NULL);
CREATE INDEX idx_paragraphs_volume_id ON paragraphs(volume,id);
CREATE INDEX idx_paragraphs_segment ON paragraphs(segment_id);
CREATE TABLE paragraph_explanations(paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),language TEXT NOT NULL,explanation_my TEXT NOT NULL,source_ref TEXT NOT NULL,provenance TEXT NOT NULL,reviewed INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(paragraph_id,language));
CREATE TABLE paragraph_myanmar_content(paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),segment_id TEXT NOT NULL,content_type TEXT NOT NULL CHECK(content_type IN ('translation','explanation')),text_my TEXT NOT NULL,source_ref TEXT NOT NULL,rights_evidence TEXT NOT NULL,reviewer_1 TEXT NOT NULL,reviewer_2 TEXT NOT NULL,review_reference TEXT NOT NULL,reviewed_at TEXT NOT NULL,source_pali_sha256 TEXT NOT NULL,reviewed INTEGER NOT NULL CHECK(reviewed=1),PRIMARY KEY(paragraph_id,content_type));
CREATE INDEX idx_myanmar_segment_type ON paragraph_myanmar_content(segment_id,content_type,reviewed);
CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT NOT NULL);
""")
used=set();counts=[];total=0
try:
 for r in rows:
  v=int(r["volume_id"]);prefix=r["source_file_prefix"].strip().rstrip("/")
  start=r["start_segment_id"].strip();end=r["end_segment_id"].strip()
  # Require both endpoint segments to be inside the same exact source file.
  endpoints=src.execute("SELECT rowid,segment_id,source_file FROM source_segments WHERE segment_id IN (?,?)",(start,end)).fetchall()
  if len(endpoints)!=2 or endpoints[0][2]!=endpoints[1][2]:raise ValueError(f"Volume {v}: endpoints missing or not in same source file")
  source_file=endpoints[0][2]
  endpoint_rows={x[1]:x[0] for x in endpoints}
  start_row,end_row=endpoint_rows[start],endpoint_rows[end]
  if start_row>end_row:raise ValueError(f"Volume {v}: start endpoint follows end endpoint in source order")
  if not (source_file.startswith(prefix+"/") or source_file.startswith(prefix+"_")):raise ValueError(f"Volume {v}: endpoint source file does not match approved prefix")
  ordered=src.execute("SELECT segment_id,body,source_file,sha256 FROM source_segments WHERE source_file=? AND rowid BETWEEN ? AND ? ORDER BY rowid",(source_file,start_row,end_row)).fetchall()
  ids=[x[0] for x in ordered]
  if not ids or ids[0]!=start or ids[-1]!=end:raise ValueError(f"Volume {v}: exact inclusive boundaries cannot be resolved")
  duplicate=used.intersection(ids)
  if duplicate:raise ValueError(f"Volume {v}: {len(duplicate)} source segments already assigned to another volume")
  used.update(ids)
  dst.execute("INSERT INTO volumes VALUES(?,?,?,?,?,?)",(v,r["book_title_my"],r["pitaka"],prefix,r["reviewer_reference"],r["rights_evidence"]))
  for sid,body,sfile,digest in ordered:
   dst.execute("INSERT INTO paragraphs(volume,body,source_ref,segment_id,source_sha256) VALUES(?,?,?,?,?)",(v,body,f"Bilara:{sfile}#{sid}@{source_commit}",sid,digest))
  counts.append({"volume":v,"source_file":source_file,"paragraphs":len(ids),"first_segment_id":start,"last_segment_id":end})
  total+=len(ids)
 dst.execute("INSERT INTO build_info VALUES('source','SuttaCentral Bilara Pali root/pli/ms')")
 dst.execute("INSERT INTO build_info VALUES('source_commit',?)",(source_commit,))
 dst.execute("INSERT INTO build_info VALUES('edition_mapping','45-volume human-reviewed crosswalk')")
 dst.execute("INSERT INTO build_info VALUES('pali_paragraph_count',?)",(str(total),))
 dst.commit()
 if dst.execute("PRAGMA integrity_check").fetchone()[0]!="ok":raise ValueError("Native SQLite integrity_check failed")
 if dst.execute("SELECT COUNT(DISTINCT volume) FROM paragraphs").fetchone()[0]!=45:raise ValueError("Native DB does not contain all 45 volumes")
 if dst.execute("SELECT COUNT(*) FROM paragraphs WHERE trim(body)='' OR trim(source_ref)=''").fetchone()[0]:raise ValueError("Empty paragraph/source reference found")
 dst.close();src.close();tmp.replace(out)
 report={"source_commit":source_commit,"volumes":45,"paragraphs":total,"translation_rows":0,"explanation_rows":0,"paragraphs_with_both":0,"volume_counts":counts,"sqlite_integrity":"ok","mapping_reviewed":True,"myanmar_content_approved":False,"release_status":"PALI_ONLY_PENDING_MYANMAR_EDITORIAL_IMPORT"}
 a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print(json.dumps(report,ensure_ascii=False,indent=2))
except Exception as e:
 try:dst.close()
 except Exception:pass
 try:src.close()
 except Exception:pass
 tmp.unlink(missing_ok=True)
 sys.exit("Native SQLite generation refused: "+str(e))
