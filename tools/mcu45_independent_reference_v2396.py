#!/usr/bin/env python3
"""V2.3.9.6: independent MCU paragraph reference comparison (fail closed).

The existing 45-volume mapping is STRUCTURAL ONLY. This report never approves
an MCU book; reviewer sign-off and edition/rights QA are separate processes.
"""
import argparse, collections, csv, hashlib, json, sqlite3, unicodedata
from pathlib import Path

COLUMNS=["mcu_volume","mcu_paragraph_ref","source_segment_id","target_roman_pali","reference_url","editorial_decision"]

def normal(s):
    return " ".join(unicodedata.normalize("NFC",s).split())

def audit(assignment_db,source_db,reference_csv,manifest_json,report_json):
    meta=json.loads(Path(manifest_json).read_text(encoding="utf-8"))
    entries=meta.get("volumes",[])
    if not isinstance(entries,list) or sorted(v["mcu_volume"] for v in entries)!=list(range(1,46)):
        raise ValueError("Manifest must have all 45 unique MCU volumes")
    manifests={v["mcu_volume"]:v for v in entries}
    references=collections.defaultdict(list)
    refkeys=set()
    used_source=set()
    with Path(reference_csv).open("r",encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=COLUMNS:
            raise ValueError("Independent reference CSV header mismatch")
        for item in reader:
            volume=int(item["mcu_volume"])
            if volume<1 or volume>45 or not item["mcu_paragraph_ref"].strip():
                raise ValueError("Unknown volume / paragraph id")
            key=(volume,item["mcu_paragraph_ref"])
            sid=item["source_segment_id"].strip()
            if key in refkeys or (sid and sid in used_source):
                raise ValueError("Duplicate MCU paragraph / source segment mapping")
            if item["editorial_decision"] not in ("PENDING","MATCH_REVIEWED","MISMATCH_REVIEWED"):
                raise ValueError("Unknown editorial decision")
            refkeys.add(key)
            if sid:used_source.add(sid)
            references[volume].append(item)
    a=sqlite3.connect("file:"+str(Path(assignment_db).resolve())+"?mode=ro",uri=True)
    s=sqlite3.connect("file:"+str(Path(source_db).resolve())+"?mode=ro",uri=True)
    try:
        if any(x.execute("PRAGMA integrity_check").fetchone()[0]!="ok" for x in (a,s)):
            raise ValueError("Database integrity failed")
        results=[]
        for volume,basket,title,count in a.execute("SELECT mcu_volume,basket,title,candidate_segments FROM mcu_volume_review ORDER BY mcu_volume"):
            expected={row[0] for row in a.execute("SELECT segment_id FROM segment_assignment WHERE proposed_mcu_volume=?",(volume,))}
            if len(expected)!=count:
                raise ValueError(f"Volume {volume}: count mismatch")
            manifest=manifests[volume]
            complete=manifest.get("complete_independent_corpus") is True
            if complete and not all(manifest.get(k) for k in ("edition","source_url","source_sha256","reviewer")):
                raise ValueError(f"Volume {volume}: missing independent source metadata")
            matched=set()
            target_unmapped=0
            text_difference=0
            pending=0
            for item in references[volume]:
                sid=item["source_segment_id"].strip()
                if sid not in expected:
                    target_unmapped+=1
                else:
                    source_row=s.execute("SELECT pali,sha256 FROM segments WHERE segment_id=?",(sid,)).fetchone()
                    if not source_row or hashlib.sha256(source_row[0].encode("utf-8")).hexdigest()!=source_row[1]:
                        raise ValueError("Source hash failed for "+sid)
                    matched.add(sid)
                    if item["target_roman_pali"].strip() and normal(item["target_roman_pali"])!=normal(source_row[0]):
                        text_difference+=1
                if item["editorial_decision"]=="PENDING":
                    pending+=1
            # NEVER report zero missing/extra if independent target is absent/partial.
            missing=len(expected-matched) if complete else None
            extra=target_unmapped if complete else None
            if not references[volume]:
                status="NO_INDEPENDENT_MCU_CORPUS"
            elif not complete:
                status="PARTIAL_MCU_REFERENCE"
            elif missing or extra or text_difference or pending:
                status="REQUIRES_EDITORIAL_REVIEW"
            else:
                status="EVIDENCE_READY_NOT_APPROVED"
            results.append({"volume":volume,"basket":basket,"title":title,
                "source_candidate_segments":count,"mcu_reference_rows":len(references[volume]),
                "source_not_in_target":missing,"target_not_in_source":extra,
                "text_differences":text_difference,"status":status,"approved":False})
        if len(results)!=45:
            raise ValueError("Expected 45 book rows")
        report={"version":"2.3.9.6","independent_reference_rows":sum(x["mcu_reference_rows"] for x in results),
            "verified_mcu_books":0,"release_ready":False,"volumes":results}
        out=Path(report_json);out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return report
    finally:
        a.close();s.close()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for arg in ("assignment-db","source-db","reference-csv","manifest","report"):
        p.add_argument("--"+arg,required=True)
    args=p.parse_args()
    x=audit(args.assignment_db,args.source_db,args.reference_csv,args.manifest,args.report)
    print(json.dumps({"verified_books":x["verified_mcu_books"],"independent_refs":x["independent_reference_rows"],"release_ready":x["release_ready"]}))
