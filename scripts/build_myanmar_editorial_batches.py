#!/usr/bin/env python3
"""Build per-volume editorial intake batches without inventing Myanmar content.

The generated rows are EMPTY editorial work units. They are not translations,
not explanations, and never count as approved. Templates are produced only
from a native SQLite corpus built from a fully VERIFIED 45-volume crosswalk.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, pathlib, sqlite3, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
CROSSWALK_COLUMNS={"volume_id","book_title_my","pitaka","source_file_prefix","mapping_status"}
BATCH_COLUMNS=[
 "volume_id","book_title_my","paragraph_id","segment_id","content_type",
 "pali_source_ref","pali_preview","source_pali_sha256","text_my","source_ref",
 "rights_evidence","reviewer_1","reviewer_2","review_reference","reviewed_at",
 "editorial_status"
]

def read_csv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        return list(csv.DictReader(f))

def read_crosswalk(path):
    rows=read_csv(path)
    if len(rows)!=45:
        raise ValueError(f"Expected 45 crosswalk rows; found {len(rows)}")
    if not rows or not CROSSWALK_COLUMNS.issubset(rows[0]):
        raise ValueError("Crosswalk is missing required 45-volume fields")
    ids=[int(r["volume_id"]) for r in rows]
    if ids!=list(range(1,46)):
        raise ValueError("Crosswalk volume_id must be unique and ordered 1..45")
    return rows

def sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def write_csv(path, columns, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

def make_plan(database, crosswalk_path, output_dir, manifest_path, report_path, force=False):
    crosswalk=read_crosswalk(crosswalk_path)
    mapping_ok=all(r["mapping_status"].strip().upper()=="VERIFIED" for r in crosswalk)
    report={
      "version":"2.3.5.3",
      "volumes_expected":45,
      "crosswalk_verified":mapping_ok,
      "database_present":database.is_file(),
      "total_paragraphs":0,
      "translation_work_units":0,
      "explanation_work_units":0,
      "approved_translations":0,
      "approved_explanations":0,
      "both_approved":0,
      "batch_files_generated":0,
      "status":"BLOCKED",
      "warnings":[]
    }
    manifest=[]
    for r in crosswalk:
        manifest.append({
          "volume_id":r["volume_id"],
          "book_title_my":r["book_title_my"],
          "pitaka":r["pitaka"],
          "source_file_candidate":r["source_file_prefix"],
          "mapping_status":r["mapping_status"],
          "paragraph_count":"",
          "approved_translation_count":0,
          "approved_explanation_count":0,
          "both_approved_count":0,
          "translation_coverage_percent":"0.00",
          "explanation_coverage_percent":"0.00",
          "translation_source_status":"SOURCE_REQUIRED",
          "explanation_source_status":"SOURCE_REQUIRED",
          "editorial_status":"BLOCKED_UNTIL_SOURCE_AND_CROSSWALK_VERIFIED"
        })
    if not database.is_file():
        report["warnings"].append("Native 45-volume SQLite is not present; no paragraph templates can be generated.")
        report["warnings"].append("Reviewed Myanmar CSV is currently an empty template; no approved translation/explanation content is available.")
        write_csv(manifest_path,list(manifest[0]),manifest)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report
    if not mapping_ok:
        report["warnings"].append("45-volume crosswalk contains unverified rows; source-aligned editorial batches are blocked.")
        write_csv(manifest_path,list(manifest[0]),manifest)
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report
    if output_dir.exists() and any(output_dir.glob("volume_*_editorial_batch.csv")) and not force:
        raise FileExistsError(f"{output_dir} already contains editorial batches; use --force only if regenerating untouched templates.")
    db=sqlite3.connect(f"file:{database.resolve()}?mode=ro",uri=True)
    try:
        tables={x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {"paragraphs","volumes","build_info"}.issubset(tables):
            raise ValueError("Native database must contain paragraphs, volumes and build_info tables")
        pcols={x[1] for x in db.execute("PRAGMA table_info(paragraphs)")}
        if not {"id","volume","body","source_ref","segment_id"}.issubset(pcols):
            raise ValueError("Native paragraphs schema is missing id/volume/body/source_ref/segment_id")
        meta=dict(db.execute("SELECT name,value FROM build_info"))
        if meta.get("edition_mapping")!="45-volume human-reviewed crosswalk":
            report["warnings"].append("Native SQLite metadata does not confirm the approved 45-volume crosswalk.")
            write_csv(manifest_path,list(manifest[0]),manifest)
            report_path.parent.mkdir(parents=True,exist_ok=True)
            report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
            return report
        volumes={int(x[0]):x[1] for x in db.execute("SELECT volume,title_my FROM volumes")}
        actual=sorted(int(x[0]) for x in db.execute("SELECT DISTINCT volume FROM paragraphs"))
        if actual!=list(range(1,46)) or sorted(volumes)!=list(range(1,46)):
            raise ValueError("Native SQLite must contain all 45 non-empty volumes and matching volume metadata")
        content_table="paragraph_myanmar_content" in tables
        if content_table:
            content_cols={x[1] for x in db.execute("PRAGMA table_info(paragraph_myanmar_content)")}
            if not {"paragraph_id","content_type","text_my","reviewed"}.issubset(content_cols):
                raise ValueError("paragraph_myanmar_content schema is incompatible")
        if output_dir.exists() and force:
            output_dir.mkdir(parents=True,exist_ok=True)
        else:
            output_dir.mkdir(parents=True,exist_ok=True)
        total=0
        for r in crosswalk:
            v=int(r["volume_id"])
            rows=db.execute(
              "SELECT id,segment_id,body,source_ref FROM paragraphs WHERE volume=? ORDER BY id",(v,)
            ).fetchall()
            if not rows:
                raise ValueError(f"Volume {v} has no Pali paragraphs")
            n=len(rows);tr=ex=both=0
            if content_table:
                tr=db.execute("SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_myanmar_content WHERE content_type='translation' AND reviewed=1 AND length(trim(text_my))>0 AND paragraph_id IN (SELECT id FROM paragraphs WHERE volume=?)",(v,)).fetchone()[0]
                ex=db.execute("SELECT COUNT(DISTINCT paragraph_id) FROM paragraph_myanmar_content WHERE content_type='explanation' AND reviewed=1 AND length(trim(text_my))>0 AND paragraph_id IN (SELECT id FROM paragraphs WHERE volume=?)",(v,)).fetchone()[0]
                both=db.execute("""SELECT COUNT(*) FROM paragraphs p WHERE p.volume=?
                  AND EXISTS(SELECT 1 FROM paragraph_myanmar_content t WHERE t.paragraph_id=p.id AND t.content_type='translation' AND t.reviewed=1 AND length(trim(t.text_my))>0)
                  AND EXISTS(SELECT 1 FROM paragraph_myanmar_content e WHERE e.paragraph_id=p.id AND e.content_type='explanation' AND e.reviewed=1 AND length(trim(e.text_my))>0)""",(v,)).fetchone()[0]
            batch_path=output_dir/f"volume_{v:02d}_editorial_batch.csv"
            batch_rows=[]
            for pid,segment,body,pali_ref in rows:
                segment=segment or str(pid)
                digest=sha256(body)
                preview=" ".join((body or "").split())[:180]
                for kind in ("translation","explanation"):
                    batch_rows.append({
                      "volume_id":v,"book_title_my":r["book_title_my"],
                      "paragraph_id":pid,"segment_id":segment,"content_type":kind,
                      "pali_source_ref":pali_ref,"pali_preview":preview,
                      "source_pali_sha256":digest,"text_my":"","source_ref":"",
                      "rights_evidence":"","reviewer_1":"","reviewer_2":"",
                      "review_reference":"","reviewed_at":"","editorial_status":"NOT_STARTED"
                    })
            write_csv(batch_path,BATCH_COLUMNS,batch_rows)
            total+=n
            status="COMPLETE" if tr==n and ex==n else ("IN_PROGRESS" if tr or ex else "NOT_STARTED")
            manifest[v-1].update({
              "book_title_my":volumes[v] or r["book_title_my"],
              "paragraph_count":n,
              "approved_translation_count":tr,
              "approved_explanation_count":ex,
              "both_approved_count":both,
              "translation_coverage_percent":f"{100*tr/n:.2f}",
              "explanation_coverage_percent":f"{100*ex/n:.2f}",
              "translation_source_status":"PARTIAL_OR_REVIEWED" if tr else "SOURCE_REQUIRED",
              "explanation_source_status":"PARTIAL_OR_REVIEWED" if ex else "SOURCE_REQUIRED",
              "editorial_status":status
            })
            report["batch_files_generated"]+=1
        report["total_paragraphs"]=total
        report["translation_work_units"]=total
        report["explanation_work_units"]=total
        report["approved_translations"]=sum(int(x["approved_translation_count"]) for x in manifest)
        report["approved_explanations"]=sum(int(x["approved_explanation_count"]) for x in manifest)
        report["both_approved"]=sum(int(x["both_approved_count"]) for x in manifest)
        report["status"]="CONTENT_IN_PROGRESS" if report["approved_translations"] or report["approved_explanations"] else "READY_FOR_EDITORIAL_INTAKE"
        report["work_unit_note"]="Each Pali paragraph requires two separate editorial records: translation and explanation."
    finally:
        db.close()
    write_csv(manifest_path,list(manifest[0]),manifest)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--database",type=pathlib.Path,default=ROOT/"app/src/main/assets/tipitaka_offline.sqlite")
    ap.add_argument("--crosswalk",type=pathlib.Path,default=ROOT/"corpus/45_volume_crosswalk.csv")
    ap.add_argument("--output-dir",type=pathlib.Path,default=ROOT/"corpus/generated_editorial_batches")
    ap.add_argument("--manifest",type=pathlib.Path,default=ROOT/"corpus/45_volume_editorial_manifest.csv")
    ap.add_argument("--report",type=pathlib.Path,default=ROOT/"corpus/myanmar_editorial_batch_plan.json")
    ap.add_argument("--force",action="store_true")
    a=ap.parse_args()
    try:
        report=make_plan(a.database,a.crosswalk,a.output_dir,a.manifest,a.report,a.force)
    except Exception as e:
        print(f"Editorial batch generation refused: {e}",file=sys.stderr)
        sys.exit(1)
    print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
