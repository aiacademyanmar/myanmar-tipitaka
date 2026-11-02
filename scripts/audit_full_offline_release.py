#!/usr/bin/env python3
"""Fail-closed audit of a fully populated, approved Myanmar Tipitaka offline release.

Unlike the normal compile/preflight gate, this gate requires EVERY Pali
paragraph in all 45 verified volumes to have one validated, reviewer-approved
Myanmar translation and one independently labelled explanation.
No approval, translation, volume boundary, or rights assertion is generated here.
"""
from __future__ import annotations
import argparse,csv,datetime,hashlib,json,pathlib,re,sqlite3,sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/"app/src/main/assets/tipitaka_offline.sqlite"
DEFAULT_CROSSWALK=ROOT/"corpus/45_volume_crosswalk.csv"
DEFAULT_REPORT=ROOT/"corpus/full_offline_release_audit.json"
MYANMAR=re.compile(r"[\u1000-\u109f]")
SHA256=re.compile(r"[0-9a-fA-F]{64}")
REQUIRED_TABLES={"paragraphs","volumes","build_info","paragraph_myanmar_content","paragraph_explanations"}
REQUIRED_COLUMNS={
 "paragraphs":{"id","volume","segment_id","body","source_ref","source_sha256"},
 "volumes":{"volume","title_my","pitaka","source_file_prefix","reviewer_reference","rights_evidence"},
 "paragraph_myanmar_content":{"paragraph_id","segment_id","content_type","text_my","source_ref","rights_evidence","reviewer_1","reviewer_2","review_reference","reviewed_at","source_pali_sha256","reviewed"},
}

def audit(database: pathlib.Path,crosswalk: pathlib.Path):
    report={
      "version":"2.3.6.2","release_type":"FULL_PALI_MYANMAR_TRANSLATION_AND_EXPLANATION",
      "status":"BLOCKED","ready_for_final_offline_apk":False,
      "source_database_present":database.is_file(),"crosswalk_present":crosswalk.is_file(),
      "expected_volumes":45,"verified_crosswalk_volumes":0,"pali_paragraphs":0,
      "approved_translations":0,"approved_explanations":0,"paragraphs_with_both":0,
      "translation_coverage_percent":0.0,"explanation_coverage_percent":0.0,
      "volumes":[],"errors":[],"warnings":[]
    }
    errors=report["errors"]
    if not crosswalk.is_file():
        errors.append("Missing 45-volume mapping crosswalk.")
        mappings=[]
    else:
        with crosswalk.open(newline="",encoding="utf-8-sig") as stream:
            reader=csv.DictReader(stream)
            mappings=list(reader)
        if len(mappings)!=45: errors.append(f"Expected 45 crosswalk rows; found {len(mappings)}.")
        for n,row in enumerate(mappings,1):
            if row.get("volume_id")!=str(n):errors.append(f"Crosswalk row {n} is not ordered volume {n}.")
            required=("source_file_prefix","start_segment_id","end_segment_id","reviewer_reference","rights_evidence")
            if any(not (row.get(k) or "").strip() for k in required):
                errors.append(f"Crosswalk volume {n} is missing exact boundary, rights or reviewer evidence.")
            if (row.get("mapping_status") or "").strip().upper()=="VERIFIED" and all((row.get(k) or "").strip() for k in required):
                report["verified_crosswalk_volumes"]+=1
        if report["verified_crosswalk_volumes"]!=45:
            errors.append(f"Crosswalk verified: {report['verified_crosswalk_volumes']}/45; exact review of all volumes is required.")
    if not database.is_file():
        errors.append("Native Android SQLite asset is missing.")
        return report
    db=None
    try:
        db=sqlite3.connect(f"file:{database.resolve()}?mode=ro",uri=True)
        db.row_factory=sqlite3.Row
        integrity=db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity!="ok":errors.append("SQLite integrity_check failed: "+str(integrity))
        violations=db.execute("PRAGMA foreign_key_check").fetchall()
        if violations:errors.append(f"SQLite foreign-key violations: {len(violations)}")
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for table in REQUIRED_TABLES-tables:errors.append("Missing required table: "+table)
        if REQUIRED_TABLES-tables:return report
        for table,cols in REQUIRED_COLUMNS.items():
            actual={r[1] for r in db.execute("PRAGMA table_info("+table+")")}
            for missing in cols-actual:errors.append(f"Missing {table}.{missing}.")
        if errors:return report
        metadata={r[0]:r[1] for r in db.execute("SELECT name,value FROM build_info")}
        if metadata.get("edition_mapping") not in ("45-volume human-reviewed crosswalk","45-volume human-reviewed crosswalk with approved multifile spans"):
            errors.append("No approved edition-mapping metadata.")
        if not metadata.get("source_commit"):errors.append("Missing pinned Pali source commit.")
        volumes=db.execute("SELECT volume,title_my,pitaka,source_file_prefix,reviewer_reference,rights_evidence FROM volumes ORDER BY volume").fetchall()
        if [r["volume"] for r in volumes]!=list(range(1,46)):
            errors.append("Native SQLite must include exactly 45 ordered volumes.")
            return report
        if len(mappings)==45:
            for index,volume in enumerate(volumes):
                row=mappings[index]
                if row.get("source_file_prefix")!=volume["source_file_prefix"]:
                    errors.append(f"Volume {index+1} source family differs from approved crosswalk.")
                if row.get("rights_evidence")!=volume["rights_evidence"]:
                    errors.append(f"Volume {index+1} rights evidence differs from approved crosswalk.")
                actual_endpoints=db.execute(
                  "SELECT segment_id FROM paragraphs WHERE volume=? ORDER BY id",(index+1,)
                ).fetchall()
                if not actual_endpoints:
                    errors.append(f"Volume {index+1} is empty.")
                elif actual_endpoints[0][0]!=row.get("start_segment_id") or actual_endpoints[-1][0]!=row.get("end_segment_id"):
                    errors.append(f"Volume {index+1} Pali segment boundaries differ from the verified mapping.")
        count=int(db.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0])
        report["pali_paragraphs"]=count
        try:expected=int(metadata.get("pali_paragraph_count","-1"))
        except (ValueError,TypeError):expected=-1
        if count<=0 or expected!=count:errors.append(f"Pali paragraph count/metadata mismatch: actual={count}, metadata={expected}.")
        original_hash_fail=0;empty_pali=0
        for row in db.execute("SELECT id,body,source_ref,segment_id,source_sha256 FROM paragraphs"):
            if not all((row[k] or "").strip() for k in ("body","source_ref","segment_id")):empty_pali+=1
            if not SHA256.fullmatch(row["source_sha256"] or "") or hashlib.sha256((row["body"] or "").encode("utf-8")).hexdigest()!=row["source_sha256"].lower():
                original_hash_fail+=1
        if empty_pali:errors.append(f"Empty Pali body/source/segment rows: {empty_pali}.")
        if original_hash_fail:errors.append(f"Pali source SHA-256 mismatch rows: {original_hash_fail}.")
        editorial_errors=[]
        approved={(r["paragraph_id"],r["content_type"]) for r in []}
        approved.clear()
        for row in db.execute("""SELECT m.*,p.id AS pali_id,p.segment_id AS pali_segment,p.body AS pali_body
            FROM paragraph_myanmar_content m
            LEFT JOIN paragraphs p ON p.id=m.paragraph_id
            WHERE m.reviewed=1"""):
            pid=row["paragraph_id"];kind=row["content_type"]
            if row["pali_id"] is None:
                editorial_errors.append(f"Approved {kind} refers to unknown paragraph {pid}.")
                continue
            if kind not in ("translation","explanation"):
                editorial_errors.append(f"Paragraph {pid} has unsupported approved content type {kind}.");continue
            if (pid,kind) in approved:
                editorial_errors.append(f"Paragraph {pid} has duplicate approved {kind}.")
            fields=("text_my","source_ref","rights_evidence","reviewer_1","reviewer_2","review_reference","reviewed_at")
            if any(not (row[f] or "").strip() for f in fields):
                editorial_errors.append(f"Paragraph {pid} {kind} is missing editorial evidence.");continue
            if row["reviewer_1"].strip().casefold()==row["reviewer_2"].strip().casefold():
                editorial_errors.append(f"Paragraph {pid} {kind} lacks two distinct reviewer identities.");continue
            if not MYANMAR.search(row["text_my"]):
                editorial_errors.append(f"Paragraph {pid} {kind} has no Myanmar Unicode.");continue
            try:
                day=datetime.date.fromisoformat(row["reviewed_at"])
                if day>datetime.date.today():raise ValueError()
            except (ValueError,TypeError):
                editorial_errors.append(f"Paragraph {pid} {kind} review date invalid.");continue
            actual=hashlib.sha256(row["pali_body"].encode("utf-8")).hexdigest()
            if row["segment_id"]!=row["pali_segment"] or actual!=(row["source_pali_sha256"] or "").lower():
                editorial_errors.append(f"Paragraph {pid} {kind} source segment/hash mismatch.");continue
            approved.add((pid,kind))
        if editorial_errors:
            errors.extend(editorial_errors[:25])
            if len(editorial_errors)>25:errors.append(f"{len(editorial_errors)-25} additional invalid reviewed rows not listed.")
        tr={pid for pid,kind in approved if kind=="translation"}
        ex={pid for pid,kind in approved if kind=="explanation"}
        both=tr&ex
        report.update(approved_translations=len(tr),approved_explanations=len(ex),paragraphs_with_both=len(both))
        if count:
            report["translation_coverage_percent"]=round(100*len(tr)/count,2)
            report["explanation_coverage_percent"]=round(100*len(ex)/count,2)
        for volume in volumes:
            v=volume["volume"]
            pids={r[0] for r in db.execute("SELECT id FROM paragraphs WHERE volume=?",(v,))}
            n=len(pids)
            vt=len(pids&tr);ve=len(pids&ex);vb=len(pids&both)
            report["volumes"].append({"volume":v,"title_my":volume["title_my"],"pali_paragraphs":n,
              "approved_translations":vt,"approved_explanations":ve,"with_both":vb,
              "translation_percent":round(100*vt/n,2) if n else 0.0,
              "explanation_percent":round(100*ve/n,2) if n else 0.0,
              "ready":n>0 and vt==n and ve==n and vb==n})
        if len(tr)!=count or len(ex)!=count or len(both)!=count:
            errors.append(f"Full Myanmar content missing: {len(tr)}/{count} translations, {len(ex)}/{count} explanations, {len(both)}/{count} with both.")
    except Exception as exc:
        errors.append("SQLite audit failure: "+str(exc))
    finally:
        if db is not None:db.close()
    if not errors:
        report["status"]="VERIFIED_FULL_OFFLINE_RELEASE_READY"
        report["ready_for_final_offline_apk"]=True
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database",type=pathlib.Path,default=DEFAULT_DB)
    p.add_argument("--crosswalk",type=pathlib.Path,default=DEFAULT_CROSSWALK)
    p.add_argument("--report",type=pathlib.Path,default=DEFAULT_REPORT)
    a=p.parse_args()
    result=audit(a.database,a.crosswalk)
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("status","ready_for_final_offline_apk","verified_crosswalk_volumes","pali_paragraphs","approved_translations","approved_explanations","paragraphs_with_both","errors")},ensure_ascii=False,indent=2))
    return 0 if result["ready_for_final_offline_apk"] else 1
if __name__=="__main__":sys.exit(main())
