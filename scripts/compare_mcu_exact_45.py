#!/usr/bin/env python3
"""Compare all 45 MCU-origin Pāli reference volumes to the APK's Bilara-based SQLite.

No automatic claim of MCU identity is made without complete, licensed,
edition-specific, segment-aligned reference files in Roman Pali transcription.

Expected: reference_dir/metadata.json and 01.csv through 45.csv.
CSV columns: mcu_page,mcu_item,bilara_segment_id,mcu_pali_roman
Every SQLite segment MUST have exactly one matching reference row in its
claimed volume. Any missing/extra/unmatched/different segment FAILS.
"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unicodedata

def normalize(text):
    # Conservatively normalize Unicode only, not words, spelling, or punctuation.
    return unicodedata.normalize("NFC", text).replace("\r\n","\n").replace("\r","\n")

def check(db_path,ref_dir):
    report={
        "reference_edition":"Mahācuḷā Pāḷi Tepiṭakaṃ (MCU), 45 volumes",
        "comparison_target":"Bilara Mahāsaṅgīti Pāli app SQLite",
        "reference_available":False,
        "compared_volumes":0,
        "matched_segments":0,
        "different_segments":0,
        "wrong_volume":0,
        "missing_in_source":0,
        "unreferenced_source_segments":0,
        "reference_duplicate_ids":0,
        "missing_reference_volumes":[],
        "volume_results":{},
        "verified_exact_mcu_45":False,
        "note":"MCU exact-edition identity cannot be inferred from matching book titles."
    }
    if not db_path.exists():
        report["error"]="App SQLite database not available"
        return report
    conn=sqlite3.connect(f"file:{db_path.resolve()}?mode=ro",uri=True)
    try:
        sqlite_count=conn.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]
        report["sqlite_segments"]=sqlite_count
        metadata_file=ref_dir/"metadata.json"
        if not metadata_file.exists():
            report["error"]="Licensed, segment-aligned MCU reference metadata.json unavailable"
            report["missing_reference_volumes"]=list(range(1,46))
            return report
        meta=json.loads(metadata_file.read_text(encoding="utf-8"))
        report["reference_available"]=True
        required=("edition","source_uri","source_script","transcription_method",
                  "proofreader_reference","rights_basis")
        if any(not str(meta.get(k,"")).strip() for k in required):
            report["error"]="Incomplete original MCU source metadata"
            return report
        if meta["edition"]!="Mahācuḷā Pāḷi Tepiṭakaṃ (MCU)":
            report["error"]="Reference is not the MCU Pali edition"
            return report
        if meta["source_script"]!="Pali Roman, independently checked against MCU Thai-script original":
            report["error"]="Reference script not sufficiently verified for literal comparison"
            return report
        total_referenced_ids=set()
        all_good=True
        source_counts=dict(conn.execute("SELECT volume, COUNT(*) FROM paragraphs GROUP BY volume"))
        for v in range(1,46):
            file=ref_dir/f"{v:02d}.csv"
            local={"reference_rows":0,"matched":0,"different":0,"wrong_volume":0,
                   "absent_in_bilara":0,"duplicate_ids":0,
                   "unreferenced_in_bilara":source_counts.get(v,0),
                   "first_differences":[],"reference_sha256":None}
            if not file.is_file():
                report["missing_reference_volumes"].append(v)
                all_good=False
                report["volume_results"][str(v)]=local
                continue
            local["reference_sha256"]=hashlib.sha256(file.read_bytes()).hexdigest()
            seen=set()
            with file.open(encoding="utf-8-sig",newline="") as fh:
                rdr=csv.DictReader(fh)
                needed={"mcu_page","mcu_item","bilara_segment_id","mcu_pali_roman"}
                if not needed.issubset(rdr.fieldnames or []):
                    report["error"]=f"Missing columns in {file.name}: {sorted(needed-set(rdr.fieldnames or []))}"
                    return report
                for row in rdr:
                    local["reference_rows"]+=1
                    sid=row["bilara_segment_id"].strip()
                    pali=row["mcu_pali_roman"]
                    if not sid or not row["mcu_page"].strip() or not row["mcu_item"].strip() or not pali.strip():
                        report["error"]=f"Missing MCU page/item/id/text at {file.name} row {local['reference_rows']}"
                        return report
                    if sid in seen or sid in total_referenced_ids:
                        local["duplicate_ids"]+=1
                        all_good=False
                        continue
                    seen.add(sid);total_referenced_ids.add(sid)
                    result=conn.execute("SELECT volume,body FROM paragraphs WHERE segment_id=?",(sid,)).fetchone()
                    if result is None:
                        local["absent_in_bilara"]+=1
                        all_good=False
                        if len(local["first_differences"])<10:
                            local["first_differences"].append({"segment_id":sid,"reason":"Missing from SQLite"})
                    elif int(result[0])!=v:
                        local["wrong_volume"]+=1
                        all_good=False
                        if len(local["first_differences"])<10:
                            local["first_differences"].append({"segment_id":sid,"reason":f"Mapped to volume {result[0]}"})
                    elif normalize(result[1])!=normalize(pali):
                        local["different"]+=1
                        all_good=False
                        if len(local["first_differences"])<10:
                            local["first_differences"].append({"segment_id":sid,"reason":"Text differs from MCU reference","mcu_page":row["mcu_page"]})
                    else:
                        local["matched"]+=1
            local["unreferenced_in_bilara"]=source_counts.get(v,0)-(
                local["matched"]+local["different"]+local["wrong_volume"])
            if local["unreferenced_in_bilara"]<0:local["unreferenced_in_bilara"]=0
            if local["unreferenced_in_bilara"] or not local["reference_rows"]:
                all_good=False
            for key,global_key in (("matched","matched_segments"),("different","different_segments"),
                ("wrong_volume","wrong_volume"),("absent_in_bilara","missing_in_source"),
                ("duplicate_ids","reference_duplicate_ids"),("unreferenced_in_bilara","unreferenced_source_segments")):
                report[global_key]+=local[key]
            report["volume_results"][str(v)]=local
            report["compared_volumes"]+=1
        report["verified_exact_mcu_45"]=bool(all_good and report["compared_volumes"]==45
            and len(total_referenced_ids)==sqlite_count and
            report["matched_segments"]==sqlite_count)
        report["note"]=("All supplied MCU reference segments match" if report["verified_exact_mcu_45"]
            else "NOT VERIFIED: MCU original reference text is missing, incomplete or differs")
        return report
    finally:
        conn.close()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database",type=Path,default=Path("app/src/main/assets/tipitaka_offline.sqlite"))
    p.add_argument("--reference-dir",type=Path,default=Path("corpus/mcu_reference"))
    p.add_argument("--out",type=Path,default=Path("mcu_45_exact_comparison.json"))
    p.add_argument("--require-exact",action="store_true")
    a=p.parse_args()
    result=check(a.database,a.reference_dir)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="volume_results"},ensure_ascii=False))
    if a.require_exact and not result["verified_exact_mcu_45"]:
        sys.exit("MCU 45-volume literal Pali text and boundaries NOT VERIFIED")

if __name__=="__main__":
    main()
