#!/usr/bin/env python3
"""Import human-reviewed Myanmar translation or explanation into existing Pali SQLite.

Never auto-approve. Require two distinct named reviewers, dated review evidence,
rights reference, and SHA256 of the exact Pali original segment.
Translation and explanation are stored separately; batches can be incremental.
"""
import argparse,csv,datetime,hashlib,json,pathlib,sqlite3,sys

COLUMNS = {
    "segment_id","content_type","text_my","source_ref","rights_evidence",
    "reviewer_1","reviewer_2","review_reference","reviewed_at",
    "source_pali_sha256"
}
KINDS={"translation","explanation"}
def digest(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()
def create_table(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS paragraph_myanmar_content(
      segment_id TEXT NOT NULL,
      content_type TEXT NOT NULL CHECK(content_type IN ('translation','explanation')),
      text_my TEXT NOT NULL,
      source_ref TEXT NOT NULL,
      rights_evidence TEXT NOT NULL,
      reviewer_1 TEXT NOT NULL,
      reviewer_2 TEXT NOT NULL,
      review_reference TEXT NOT NULL,
      reviewed_at TEXT NOT NULL,
      source_pali_sha256 TEXT NOT NULL,
      reviewed INTEGER NOT NULL CHECK(reviewed=1),
      PRIMARY KEY(segment_id,content_type)
    );
    CREATE INDEX IF NOT EXISTS idx_pmc_type ON paragraph_myanmar_content(content_type,segment_id);
    """)
def import_rows(db,csv_path):
    count={"translation":0,"explanation":0}
    if not csv_path.is_file():
        return count
    with csv_path.open("r",encoding="utf-8-sig",newline="") as fh:
        reader=csv.DictReader(fh)
        missing=COLUMNS-set(reader.fieldnames or [])
        if missing:raise ValueError("Missing reviewed CSV columns: "+",".join(sorted(missing)))
        seen=set()
        for n,r in enumerate(reader,2):
            vals={x:(r.get(x) or "").strip() for x in COLUMNS}
            if any(not x for x in vals.values()):
                raise ValueError(f"Row {n}: incomplete review, rights, Pali hash or source")
            if vals["content_type"] not in KINDS:raise ValueError(f"Row {n}: invalid content_type")
            if vals["reviewer_1"].casefold()==vals["reviewer_2"].casefold():
                raise ValueError(f"Row {n}: two distinct reviewers required")
            try:d=datetime.date.fromisoformat(vals["reviewed_at"])
            except ValueError:raise ValueError(f"Row {n}: invalid date, ISO YYYY-MM-DD required")
            if d>datetime.date.today():raise ValueError(f"Row {n}: future approval date")
            key=(vals["segment_id"],vals["content_type"])
            if key in seen:raise ValueError(f"Row {n}: duplicate segment/type")
            seen.add(key)
            row=db.execute("SELECT id,body FROM paragraphs WHERE segment_id=?",(vals["segment_id"],)).fetchone()
            if row is None:raise ValueError(f"Row {n}: Pali segment missing from SQLite: {vals['segment_id']}")
            pid,pali=row
            if digest(pali)!=vals["source_pali_sha256"].lower():
                raise ValueError(f"Row {n}: original Pali has changed since review: {vals['segment_id']}")
            db.execute("""INSERT INTO paragraph_myanmar_content VALUES(?,?,?,?,?,?,?,?,?,?,1)
                 ON CONFLICT(segment_id,content_type) DO UPDATE SET
                 text_my=excluded.text_my,source_ref=excluded.source_ref,
                 rights_evidence=excluded.rights_evidence,
                 reviewer_1=excluded.reviewer_1,reviewer_2=excluded.reviewer_2,
                 review_reference=excluded.review_reference,
                 reviewed_at=excluded.reviewed_at,
                 source_pali_sha256=excluded.source_pali_sha256,reviewed=1""",
                 (vals["segment_id"],vals["content_type"],vals["text_my"],
                  vals["source_ref"],vals["rights_evidence"],
                  vals["reviewer_1"],vals["reviewer_2"],
                  vals["review_reference"],vals["reviewed_at"],
                  vals["source_pali_sha256"]))
            if vals["content_type"]=="explanation":
                db.execute("""INSERT INTO paragraph_explanations(
                  paragraph_id,language,explanation_my,source_ref,provenance,reviewed)
                  VALUES (?,'my',?,?,'editorial_explanation',1)
                  ON CONFLICT(paragraph_id,language) DO UPDATE SET
                  explanation_my=excluded.explanation_my,source_ref=excluded.source_ref,
                  provenance=excluded.provenance,reviewed=1""",
                  (pid,vals["text_my"],vals["source_ref"]))
            count[vals["content_type"]]+=1
    return count
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database",type=pathlib.Path,default=pathlib.Path("app/src/main/assets/tipitaka_offline.sqlite"))
    p.add_argument("--reviewed",type=pathlib.Path,default=pathlib.Path("corpus/reviewed_myanmar.csv"))
    p.add_argument("--report",type=pathlib.Path,default=pathlib.Path("myanmar_review_coverage.json"))
    a=p.parse_args()
    if not a.database.is_file():sys.exit("Offline Pali database must be built before Myanmar merge")
    db=sqlite3.connect(a.database)
    try:
        create_table(db)
        with db:
            imported=import_rows(db,a.reviewed)
        total=db.execute("SELECT count(*) FROM paragraphs").fetchone()[0]
        stats=dict(db.execute("SELECT content_type,COUNT(*) FROM paragraph_myanmar_content WHERE reviewed=1 GROUP BY content_type"))
        with_both=db.execute("""
         SELECT COUNT(*) FROM paragraphs p
         WHERE EXISTS(SELECT 1 FROM paragraph_myanmar_content x WHERE x.segment_id=p.segment_id AND x.content_type='translation' AND x.reviewed=1)
         AND EXISTS(SELECT 1 FROM paragraph_myanmar_content y WHERE y.segment_id=p.segment_id AND y.content_type='explanation' AND y.reviewed=1)
        """).fetchone()[0]
        report={
         "pali_segments_total":total,
         "reviewed_myanmar_translations":stats.get("translation",0),
         "reviewed_myanmar_explanations":stats.get("explanation",0),
         "segments_with_both":with_both,
         "reviewed_import_file_supplied":a.reviewed.is_file(),
         "imported_this_build":imported,
         "all_pali_segments_explained":stats.get("explanation",0)==total,
         "review_requirement":"2 separate human reviewers + rights reference + review document + original Pali SHA256"
        }
        a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        print(json.dumps(report,ensure_ascii=False))
    finally:
        db.close()
if __name__=="__main__":main()
