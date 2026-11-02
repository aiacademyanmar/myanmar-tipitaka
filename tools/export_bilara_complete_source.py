#!/usr/bin/env python3
"""Export all available Bilara Mahasangiti Roman Pali root JSON to XLSX/DOCX/SQLite.
IMPORTANT: this is NOT an MCU 45-volume crosswalk or a certified 45-book edition.
Use only after checking upstream provenance and license.
"""
import argparse, hashlib, json, sqlite3, zipfile
from collections import Counter
from pathlib import Path
import xlsxwriter
from docx import Document
from docx.shared import Pt, Inches

BASKETS=("vinaya","sutta","abhidhamma")
SOURCE_URL="https://github.com/suttacentral/bilara-data/tree/published/root/pli/ms"

def export(root: Path, output: Path, commit: str):
    if not root.is_dir(): raise ValueError(f"Source unavailable: {root}")
    if len(commit)!=40 or any(c not in "0123456789abcdefABCDEF" for c in commit):
        raise ValueError("Pinned 40-character source commit SHA required")
    if output.exists() and list(output.iterdir()):
        raise ValueError("Output must be an empty directory")
    output.mkdir(parents=True,exist_ok=True)
    (output/"excel").mkdir(exist_ok=True)
    (output/"word").mkdir(exist_ok=True)
    db=sqlite3.connect(output/"pali_source_unreviewed.sqlite")
    db.executescript("""
      CREATE TABLE segments(segment_id TEXT PRIMARY KEY,basket TEXT NOT NULL,
        text_uid TEXT NOT NULL,pali TEXT NOT NULL,source_path TEXT NOT NULL,
        sha256 TEXT NOT NULL,source_commit TEXT NOT NULL,review_status TEXT NOT NULL DEFAULT 'UNREVIEWED');
      CREATE INDEX idx_segments ON segments(basket,text_uid);
    """)
    statistics=Counter()
    output_files=[]
    try:
        for basket in BASKETS:
            sources=sorted((root/basket).rglob("*.json"))
            if not sources: raise ValueError(f"No source files for {basket}")
            excel_idx=word_idx=0
            xl=worksheet=doc=None
            excel_rows=word_rows=0
            last_uid=None

            def open_xl():
                nonlocal xl,worksheet,excel_idx,excel_rows
                excel_idx+=1
                filename=output/"excel"/f"{basket}_pali_source_{excel_idx:03d}.xlsx"
                xl=xlsxwriter.Workbook(str(filename),{"constant_memory":True})
                worksheet=xl.add_worksheet("Pali")
                widths=[16,20,27,95,65,16]
                for col,width in enumerate(widths): worksheet.set_column(col,col,width)
                headerfmt=xl.add_format({"bold":True,"font_color":"#FFFFFF","bg_color":"#14504A"})
                for col,name in enumerate(["Basket","Text UID","Segment ID","Pali Roman","Source path","Review status"]):
                    worksheet.write(0,col,name,headerfmt)
                worksheet.freeze_panes(1,0)
                excel_rows=0
                output_files.append(str(filename.relative_to(output)))

            def close_xl():
                nonlocal xl,worksheet
                if xl:xl.close()
                xl=worksheet=None

            def open_doc():
                nonlocal doc,word_idx,word_rows,last_uid
                word_idx+=1
                doc=Document()
                sec=doc.sections[0]
                sec.top_margin=sec.bottom_margin=Inches(.65)
                normal=doc.styles["Normal"]
                normal.font.name="DejaVu Sans"
                normal.font.size=Pt(10)
                normal.paragraph_format.space_after=Pt(4)
                doc.add_heading(f"{basket.title()} Piṭaka — Source Part {word_idx:03d}",0)
                doc.add_paragraph("Roman Pāli · Mahāsaṅgīti · UNREVIEWED source export — NOT mapped to MCU 45 volumes",style="Subtitle")
                doc.add_paragraph(f"Source: {SOURCE_URL}\nSource commit: {commit}")
                word_rows=0;last_uid=None

            def close_doc():
                nonlocal doc
                if doc:
                    path=output/"word"/f"{basket}_pali_source_{word_idx:03d}.docx"
                    doc.save(path)
                    output_files.append(str(path.relative_to(output)))
                doc=None

            open_xl()
            open_doc()
            for source in sources:
                obj=json.loads(source.read_text(encoding="utf-8-sig"))
                if not isinstance(obj,dict): raise ValueError(f"Non-object JSON: {source}")
                for segment,pali in obj.items():
                    if not isinstance(segment,str) or ":" not in segment or not isinstance(pali,str):
                        raise ValueError(f"Malformed segment in {source}")
                    if not pali.strip(): continue
                    uid=segment.split(":",1)[0]
                    relative=source.relative_to(root).as_posix()
                    digest=hashlib.sha256(pali.encode("utf-8")).hexdigest()
                    db.execute("INSERT INTO segments(segment_id,basket,text_uid,pali,source_path,sha256,source_commit) VALUES(?,?,?,?,?,?,?)",
                        (segment,basket,uid,pali,relative,digest,commit))
                    if excel_rows>=60000:close_xl();open_xl()
                    worksheet.write_row(excel_rows+1,0,[basket,uid,segment,pali,relative,"UNREVIEWED"])
                    excel_rows+=1
                    if word_rows>=1800:close_doc();open_doc()
                    if uid!=last_uid:doc.add_heading(uid,2);last_uid=uid
                    paragraph=doc.add_paragraph()
                    paragraph.add_run(segment+"  ").bold=True
                    paragraph.add_run(pali)
                    word_rows+=1
                    statistics[basket]+=1
                db.commit()
            close_xl();close_doc()
        if db.execute("PRAGMA integrity_check").fetchone()[0]!="ok":
            raise ValueError("SQLite integrity check failed")
    finally: db.close()
    info={"source":SOURCE_URL,"source_commit":commit,
          "edition":"Mahasangiti Roman Pali (40-volume source edition)",
          "mapping_to_MCU_45":"NOT VERIFIED","review_status":"UNREVIEWED",
          "segments_by_pitaka":{b:statistics[b] for b in BASKETS},
          "total_segments":sum(statistics.values()),"files":output_files}
    (output/"manifest.json").write_text(json.dumps(info,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({k:info[k] for k in ["source_commit","segments_by_pitaka","total_segments","mapping_to_MCU_45"]},ensure_ascii=False))
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--source-commit",required=True)
    a=ap.parse_args()
    export(a.root,a.out,a.source_commit)
