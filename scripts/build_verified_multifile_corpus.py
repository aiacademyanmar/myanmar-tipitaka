#!/usr/bin/env python3
"""V2.3.6.7: fail-closed 45-volume Pali SQLite builder with multiple source spans.

Input is a human-reviewed 45-volume crosswalk PLUS an independently reviewed
source-file span manifest. No AI/candidate data is automatically approved.
This script checks syntax, source commit, SHA-256, bounds and overlap. It
cannot independently authenticate the people named in reviewer fields or
establish legal redistribution rights; those require off-line review.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,pathlib,re,sqlite3,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
REQUIRED_CROSSWALK={"volume_id","book_title_my","pitaka","source_file_prefix","mapping_status","reviewer_reference","rights_evidence"}
REQUIRED_SPANS={"volume_id","span_order","source_file","start_segment_id","end_segment_id","first_sha256","last_sha256","mapping_status","reviewer_reference","rights_evidence","independent_reference"}
HEXDIGEST=re.compile(r"^[0-9a-fA-F]{64}$")
COMMIT=re.compile(r"^[0-9a-fA-F]{40}$")
def table(path):
    with path.open("r",encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        rows=list(reader)
        return set(reader.fieldnames or []),rows
def sha(s):return hashlib.sha256(s.encode("utf-8")).hexdigest()
def require(condition,message):
    if not condition:raise ValueError(message)
def build(source_db,crosswalk,spans_csv,output,report):
    require(source_db.is_file(),"Pinned upstream Pali SQLite is missing.")
    require(crosswalk.is_file(),"Approved 45-volume crosswalk is missing.")
    require(spans_csv.is_file(),"Separate reviewed multi-file span manifest is missing.")
    cw_fields,cw=table(crosswalk);span_fields,spans=table(spans_csv)
    require(REQUIRED_CROSSWALK<=cw_fields,"Crosswalk missing "+str(sorted(REQUIRED_CROSSWALK-cw_fields)))
    require(REQUIRED_SPANS<=span_fields,"Span manifest missing "+str(sorted(REQUIRED_SPANS-span_fields)))
    require(len(cw)==45,"Crosswalk must have exactly 45 books.")
    require(len(spans)>=45,"Every one of 45 books needs at least one approved span.")
    books={}
    for i,row in enumerate(cw,1):
        require(row["volume_id"]==str(i),f"Volume {i}: volume_id must be ordered 1..45")
        require(row["mapping_status"].strip().upper()=="VERIFIED",f"Volume {i}: crosswalk not approved.")
        for f in ("book_title_my","pitaka","source_file_prefix","reviewer_reference","rights_evidence"):
            require(row[f].strip(),f"Volume {i}: missing {f}")
        require(row["pitaka"] in ("vinaya","sutta","abhidhamma"),f"Volume {i}: unsupported pitaka")
        books[i]=row
    by_volume={v:[] for v in range(1,46)}
    seen_keys=set()
    for row in spans:
        try:v=int(row["volume_id"]);sequence=int(row["span_order"])
        except (TypeError,ValueError):raise ValueError("Volume/span order must be integers")
        require(1<=v<=45 and sequence>0,f"Volume {v}: invalid span order")
        key=(v,sequence)
        require(key not in seen_keys,f"Duplicate volume/span order {key}")
        seen_keys.add(key)
        for f in ("source_file","start_segment_id","end_segment_id","first_sha256","last_sha256","reviewer_reference","rights_evidence","independent_reference"):
            require(row[f].strip(),f"Volume {v} span {sequence}: missing {f}")
        require(row["mapping_status"].strip().upper()=="VERIFIED",f"Volume {v} span {sequence}: not approved")
        require(HEXDIGEST.fullmatch(row["first_sha256"]) is not None and HEXDIGEST.fullmatch(row["last_sha256"]) is not None,
                f"Volume {v} span {sequence}: invalid source SHA-256")
        require(row["reviewer_reference"]==books[v]["reviewer_reference"],
                f"Volume {v} span {sequence}: conflicting reviewer evidence")
        require(row["rights_evidence"]==books[v]["rights_evidence"],
                f"Volume {v} span {sequence}: conflicting rights evidence")
        by_volume[v].append((sequence,row))
    for v,items in by_volume.items():
        items.sort(key=lambda x:x[0])
        require([n for n,_ in items]==list(range(1,len(items)+1)),
                f"Volume {v}: spans must be ordered 1..N with no gap")
    source=sqlite3.connect(f"file:{source_db.resolve()}?mode=ro",uri=True)
    output.parent.mkdir(parents=True,exist_ok=True)
    report.parent.mkdir(parents=True,exist_ok=True)
    temp=output.with_suffix(output.suffix+".part")
    temp.unlink(missing_ok=True)
    dest=None
    try:
        require(source.execute("PRAGMA integrity_check").fetchone()[0]=="ok","Source SQLite integrity failed")
        tables={r[0] for r in source.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({"source_segments","build_info"}<=tables,"Invalid source SQLite schema")
        info=dict(source.execute("SELECT name,value FROM build_info"))
        source_commit=info.get("commit","")
        require(COMMIT.fullmatch(source_commit) is not None,"Source commit must be 40 hexadecimal characters")
        columns={x[1] for x in source.execute("PRAGMA table_info(source_segments)")}
        require({"segment_id","body","source_file","source_commit","sha256"}<=columns,"Invalid source segment columns")
        dest=sqlite3.connect(temp)
        dest.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE volumes(volume INTEGER PRIMARY KEY,title_my TEXT NOT NULL,pitaka TEXT NOT NULL,source_file_prefix TEXT NOT NULL,reviewer_reference TEXT NOT NULL,rights_evidence TEXT NOT NULL);
        CREATE TABLE paragraphs(id INTEGER PRIMARY KEY,volume INTEGER NOT NULL REFERENCES volumes(volume),body TEXT NOT NULL,source_ref TEXT NOT NULL,segment_id TEXT NOT NULL UNIQUE,source_sha256 TEXT NOT NULL);
        CREATE INDEX idx_paragraphs_volume_id ON paragraphs(volume,id);
        CREATE INDEX idx_paragraphs_segment ON paragraphs(segment_id);
        CREATE TABLE paragraph_explanations(paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),language TEXT NOT NULL,explanation_my TEXT NOT NULL,source_ref TEXT NOT NULL,provenance TEXT NOT NULL,reviewed INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(paragraph_id,language));
        CREATE TABLE paragraph_myanmar_content(paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id),segment_id TEXT NOT NULL,content_type TEXT NOT NULL CHECK(content_type IN ('translation','explanation')),text_my TEXT NOT NULL,source_ref TEXT NOT NULL,rights_evidence TEXT NOT NULL,reviewer_1 TEXT NOT NULL,reviewer_2 TEXT NOT NULL,review_reference TEXT NOT NULL,reviewed_at TEXT NOT NULL,source_pali_sha256 TEXT NOT NULL,reviewed INTEGER NOT NULL CHECK(reviewed=1),PRIMARY KEY(paragraph_id,content_type));
        CREATE INDEX idx_myanmar_segment_type ON paragraph_myanmar_content(segment_id,content_type,reviewed);
        CREATE TABLE build_info(name TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE volume_source_spans(volume INTEGER NOT NULL REFERENCES volumes(volume),span_order INTEGER NOT NULL,source_file TEXT NOT NULL,start_segment_id TEXT NOT NULL,end_segment_id TEXT NOT NULL,segment_count INTEGER NOT NULL,first_sha256 TEXT NOT NULL,last_sha256 TEXT NOT NULL,independent_reference TEXT NOT NULL,PRIMARY KEY(volume,span_order));
        """)
        used=set();volume_counts=[];total=0
        for v in range(1,46):
            book=books[v]
            dest.execute("INSERT INTO volumes VALUES(?,?,?,?,?,?)",
                (v,book["book_title_my"],book["pitaka"],book["source_file_prefix"],book["reviewer_reference"],book["rights_evidence"]))
            volume_count=0
            family_prefixes=[s.strip().rstrip("/") for s in book["source_file_prefix"].split("|") if s.strip()]
            for sequence,span in by_volume[v]:
                path=span["source_file"]
                require(any(path.startswith(fam+"/") or path.startswith(fam+"_") for fam in family_prefixes),
                        f"Volume {v} span {sequence}: source path does not match approved source family")
                # rowid is the actual input insertion order within this *same* source file.
                endpoints=source.execute(
                    "SELECT rowid,segment_id,body,sha256,source_commit FROM source_segments WHERE source_file=? AND segment_id IN (?,?)",
                    (path,span["start_segment_id"],span["end_segment_id"])).fetchall()
                require(len(endpoints) in (1,2),f"Volume {v} span {sequence}: endpoints not found")
                end_by_id={r[1]:r for r in endpoints}
                start=end_by_id.get(span["start_segment_id"]);end=end_by_id.get(span["end_segment_id"])
                require(start is not None and end is not None,f"Volume {v} span {sequence}: endpoints missing")
                require(start[0]<=end[0],f"Volume {v} span {sequence}: reversed source row order")
                require(start[3].lower()==span["first_sha256"].lower() and end[3].lower()==span["last_sha256"].lower(),
                        f"Volume {v} span {sequence}: endpoint hash evidence mismatch")
                require(start[4]==source_commit and end[4]==source_commit,
                        f"Volume {v} span {sequence}: endpoint commit mismatch")
                items=source.execute(
                    "SELECT segment_id,body,source_file,sha256,source_commit FROM source_segments WHERE source_file=? AND rowid BETWEEN ? AND ? ORDER BY rowid",
                    (path,start[0],end[0])).fetchall()
                require(items and items[0][0]==start[1] and items[-1][0]==end[1],
                        f"Volume {v} span {sequence}: exact range not reproducible")
                for sid,body,sfile,digest,commit in items:
                    require(sid not in used,f"Volume {v} span {sequence}: segment overlaps an earlier volume/span: {sid}")
                    require(body and digest and sha(body)==digest.lower() and commit==source_commit,
                            f"Volume {v} span {sequence}: source SHA or commit mismatch: {sid}")
                    used.add(sid)
                    dest.execute("INSERT INTO paragraphs(volume,body,source_ref,segment_id,source_sha256) VALUES(?,?,?,?,?)",
                        (v,body,f"Bilara:{sfile}#{sid}@{source_commit}",sid,digest))
                dest.execute("INSERT INTO volume_source_spans VALUES(?,?,?,?,?,?,?,?,?)",
                    (v,sequence,path,span["start_segment_id"],span["end_segment_id"],len(items),
                     span["first_sha256"].lower(),span["last_sha256"].lower(),span["independent_reference"]))
                volume_count+=len(items)
            require(volume_count>0,f"Volume {v} has no mapped Pali segments")
            volume_counts.append({"volume":v,"spans":len(by_volume[v]),"paragraphs":volume_count})
            total+=volume_count
        for key,value in (("source","SuttaCentral Bilara Pali root/pli/ms"),
                          ("source_commit",source_commit),("edition_mapping","45-volume human-reviewed crosswalk with approved multifile spans"),
                          ("pali_paragraph_count",str(total)),("crosswalk_spans",str(len(spans)))):
            dest.execute("INSERT INTO build_info(name,value) VALUES(?,?)",(key,value))
        dest.commit()
        require(dest.execute("PRAGMA integrity_check").fetchone()[0]=="ok","Output SQLite integrity failed")
        require(not dest.execute("PRAGMA foreign_key_check").fetchall(),"Output SQLite foreign key violation")
        require(dest.execute("SELECT COUNT(DISTINCT volume) FROM paragraphs").fetchone()[0]==45,
                "Output does not contain 45 populated volumes")
        require(dest.execute("SELECT COUNT(*) FROM paragraphs").fetchone()[0]==total,
                "Output paragraph count mismatch")
        dest.close();dest=None
        temp.replace(output)
        payload={"version":"2.3.6.7","status":"VERIFIED_PALI_SQLITE_BUILT_MYANMAR_CONTENT_PENDING",
                 "source_commit":source_commit,"volumes":45,"spans":len(spans),"pali_paragraphs":total,
                 "approved_translations":0,"approved_explanations":0,
                 "sqlite_integrity":"ok","volume_counts":volume_counts,
                 "warning":"Technical checks do not authenticate human reviewer identities or redistribution rights."}
        report.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        return payload
    except Exception:
        if dest is not None:dest.close()
        temp.unlink(missing_ok=True)
        raise
    finally:source.close()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("source_db",type=pathlib.Path)
    ap.add_argument("--crosswalk",type=pathlib.Path,default=ROOT/"corpus/45_volume_crosswalk.csv")
    ap.add_argument("--spans",type=pathlib.Path,default=ROOT/"corpus/45_volume_verified_source_spans.csv")
    ap.add_argument("--output",type=pathlib.Path,default=pathlib.Path("tipitaka_offline.sqlite"))
    ap.add_argument("--report",type=pathlib.Path,default=pathlib.Path("native_corpus_report.json"))
    args=ap.parse_args()
    try:result=build(args.source_db,args.crosswalk,args.spans,args.output,args.report)
    except Exception as exc:
        print("Verified 45-book multi-file SQLite build BLOCKED: "+str(exc),file=sys.stderr)
        return 1
    print(json.dumps(result,ensure_ascii=False,indent=2));return 0
if __name__=="__main__":sys.exit(main())
