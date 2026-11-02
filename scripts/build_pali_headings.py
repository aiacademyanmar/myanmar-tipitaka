#!/usr/bin/env python3
"""Attach source-grounded book, division and chapter headings to every Pali segment.

SuttaCentral/Bilara 'root/pli/ms' stores original Pali text per segment.
Its corresponding 'html/pli/ms' files store the hierarchy <h1>, <h2>, etc.
Never invent printed MCU 45-volume paragraph boundaries or translations.
Fallback uses real source metadata or explicit source-file reference.
"""
import argparse
import html as html_lib
import json
import pathlib
import re
import sqlite3

cli=argparse.ArgumentParser()
cli.add_argument("database",type=pathlib.Path)
cli.add_argument("pali_root",type=pathlib.Path)
cli.add_argument("html_root",type=pathlib.Path)
cli.add_argument("--report",type=pathlib.Path,default=pathlib.Path("pali_headings_qa.json"))
args=cli.parse_args()
db=sqlite3.connect(args.database)
db.execute("PRAGMA busy_timeout=60000")
db.executescript("""
CREATE TABLE IF NOT EXISTS pali_source_books(
 source_file TEXT PRIMARY KEY,
 book_title TEXT NOT NULL,
 collection_title TEXT NOT NULL,
 title_origin TEXT NOT NULL,
 heading_markup_available INTEGER NOT NULL CHECK(heading_markup_available IN (0,1))
);
CREATE TABLE IF NOT EXISTS pali_segment_titles(
 segment_id TEXT PRIMARY KEY REFERENCES source_segments(segment_id),
 source_file TEXT NOT NULL,
 book_title TEXT NOT NULL,
 chapter_title TEXT NOT NULL,
 chapter_origin TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pali_titles_source ON pali_segment_titles(source_file);
""")
# Fresh rebuild of immutable APK asset only (does not edit user bookmarks).
db.execute("DELETE FROM pali_segment_titles")
db.execute("DELETE FROM pali_source_books")
rheading=re.compile(r"<h([1-6])(?:\s|>)",re.I)
def clean(s):
    return " ".join(html_lib.unescape(re.sub(r"<[^>]*>","",str(s))).split()).strip()
count_file=0
segments=0
html_files=0
real_headings=0
no_html_files=0
source_only=0
last_file_name=None
for source in sorted(args.pali_root.rglob("*.json")):
    relative=source.relative_to(args.pali_root)
    source_path=relative.as_posix()
    rows=json.loads(source.read_text(encoding="utf8"))
    if not isinstance(rows,dict):continue
    html_path=args.html_root / relative.parent / relative.name.replace("_root-pli-ms.json","_html.json")
    tags={}
    if html_path.exists():
        try:
            tags=json.loads(html_path.read_text(encoding="utf8"))
            if not isinstance(tags,dict):tags={}
            else:html_files+=1
        except ValueError:
            raise RuntimeError("Broken Bilara structural HTML: "+str(html_path))
    else:no_html_files+=1
    meta=[]
    for key,value in rows.items():
        if isinstance(value,str) and re.search(r":0\.[1-9]\d*$",key):
            value=clean(value)
            if value and value not in meta:meta.append(value)
    # Book metadata is given by the source, not a guessed MCU 45-volume index.
    collection=meta[0] if meta else relative.parts[0].title()
    book=" · ".join(meta[:3]) if meta else source_path.replace("_root-pli-ms.json","")
    origin="pali_root_metadata" if meta else "explicit_source_file_reference"
    if not meta:source_only+=1
    if not book.strip() or not collection.strip():raise RuntimeError("Invalid book heading: "+source_path)
    db.execute("INSERT INTO pali_source_books VALUES(?,?,?,?,?)",
      (source_path,book,collection,origin,1 if tags else 0))
    chapter=book
    chapter_origin="book_metadata"
    title_rows=[]
    for segment,value in rows.items():
        if not isinstance(segment,str) or not isinstance(value,str) or not value.strip():continue
        tag=tags.get(segment,"")
        match=rheading.search(tag) if isinstance(tag,str) else None
        if match and int(match.group(1))>=2:
            heading=clean(value)
            if heading:
                chapter=heading
                chapter_origin="bilara_html_h"+match.group(1)
                real_headings+=1
        elif not tags and re.search(r":[1-9]\d*(?:\.\d+)*\.0$",segment) and len(value.strip())<=165:
            # Some Bilara work types do not have an html companion.
            # Preserve actual source text, but mark it as inferred structure.
            chapter=clean(value)
            chapter_origin="pali_source_0_segment"
        if not chapter.strip():raise RuntimeError("Missing chapter heading "+segment)
        title_rows.append((segment,source_path,book,chapter,chapter_origin))
    db.executemany("INSERT INTO pali_segment_titles VALUES(?,?,?,?,?)",title_rows)
    count_file+=1
    segments+=len(title_rows)
    last_file_name=source_path
db.commit()
total=db.execute("SELECT count(*) FROM source_segments").fetchone()[0]
attached=db.execute("SELECT count(*) FROM pali_segment_titles").fetchone()[0]
missing=db.execute("""SELECT count(*) FROM source_segments s
 LEFT JOIN pali_segment_titles t ON t.segment_id=s.segment_id
 WHERE t.segment_id IS NULL""").fetchone()[0]
assert total==attached==segments and missing==0,(total,attached,segments,missing)
assert count_file==db.execute("SELECT count(*) FROM pali_source_books").fetchone()[0]
assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
qa={
 "status":"HEADING_BOUND_TO_EVERY_PALI_SEGMENT",
 "pali_segments":total,
 "segments_with_book_and_chapter_headings":attached,
 "missing_heading_records":missing,
 "source_files":count_file,
 "html_structure_files":html_files,
 "no_html_structure_files":no_html_files,
 "explicit_h2_to_h6_headings":real_headings,
 "files_falling_back_to_source_reference":source_only,
 "mcu_45_exact_printed_mapping_verified":False,
 "source":"suttacentral/bilara-data published root/pli/ms and html/pli/ms",
 "tipitaka_cloud_reference_only":True,
}
args.report.write_text(json.dumps(qa,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(qa,ensure_ascii=False))
db.close()
