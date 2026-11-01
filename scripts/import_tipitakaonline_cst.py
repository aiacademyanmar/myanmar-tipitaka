#!/usr/bin/env python3
"""Import CST Pali paragraphs, CST/PTS references and any server-rendered
Burmese AI translation from tipitakaonline.org into the offline SQLite.

The site's developer page currently labels its REST examples as placeholders.
This importer probes the documented example, then uses the site's public,
server-rendered Vinaya/Sutta/Abhidhamma pages. It never invents API responses.

Only exact normalized Pali matches are linked to existing Bilara segment IDs
and 45-volume numbers. Unmatched CST paragraphs remain in the separate CST
table; no speculative 45-volume assignment is made.

AI translations are stored as AI-generated/unreviewed, never as scholar-
approved translations or doctrinal explanations.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import html
from html.parser import HTMLParser
import json
import re
import sqlite3
import sys
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen

BASE="https://tipitakaonline.org"
ROOTS=[BASE+"/vinaya",BASE+"/sutta",BASE+"/abhidhamma"]
ALLOWED=("/vinaya","/sutta","/abhidhamma")
MYANMAR_RE=re.compile(r"[\u1000-\u109f]")
CST_RE=re.compile(r"\bCST\s+([0-9]+\.[0-9]+)\b",re.I)
PTS_RE=re.compile(r"\bPTS\s+([0-9]+\.[0-9]+)\b",re.I)
PARA_RE=re.compile(r"^\s*(\d{1,5})\s*[\.\)]\s*(.*?)\s*$",re.S)

def clean(s):
    return re.sub(r"\s+"," ",html.unescape(s or "")).strip()

def norm_pali(s):
    s=unicodedata.normalize("NFC",s or "")
    s=re.sub(r"^\s*\d{1,5}\s*[\.\)]\s*","",s)
    return re.sub(r"\s+"," ",s).strip()

def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class PageParser(HTMLParser):
    """Extract server-rendered paragraph blocks and canonical internal links."""
    BLOCK_TAGS={"p","li"}
    TITLE_TAGS={"h1","title"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links=[]
        self.blocks=[]
        self.title=""
        self._capture=None
        self._depth=0
        self._title_capture=False
        self._title_depth=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in self.BLOCK_TAGS and self._capture is None:
            self._capture=[tag,[]];self._depth=1
        elif self._capture is not None:
            self._depth+=1
        if tag in self.TITLE_TAGS and not self._title_capture:
            self._title_capture=True;self._title_depth=1
        elif self._title_capture:
            self._title_depth+=1
    def handle_endtag(self,tag):
        if self._capture is not None:
            self._depth-=1
            if self._depth<=0:
                text=clean(" ".join(self._capture[1]))
                if text:self.blocks.append(text)
                self._capture=None;self._depth=0
        if self._title_capture:
            self._title_depth-=1
            if self._title_depth<=0:self._title_capture=False
    def handle_data(self,data):
        if self._capture is not None:self._capture[1].append(data)
        if self._title_capture:self.title+=data

def fetch(url,timeout=25):
    req=Request(url,headers={"User-Agent":"MyanmarTipitakaOfflineResearch/1.0 (+https://github.com/aiacademyanmar/myanmar-tipitaka)","Accept":"text/html,application/json;q=0.9,*/*;q=0.8"})
    with urlopen(req,timeout=timeout) as r:
        return r.status,r.headers.get("Content-Type",""),r.read()

def allowed_url(url):
    p=urlparse(url)
    return p.scheme in ("http","https") and p.netloc=="tipitakaonline.org" and any(
        p.path==x or p.path.startswith(x+"/") for x in ALLOWED)

def parse_page(url,raw):
    parser=PageParser()
    parser.feed(raw.decode("utf-8","replace"))
    records=[]
    last=None
    for block in parser.blocks:
        cst=CST_RE.findall(block)
        pts=PTS_RE.findall(block)
        stripped=clean(CST_RE.sub("",PTS_RE.sub("",block)))
        if cst or pts:
            if last is not None:
                if cst:last["cst_ref"]=cst[-1]
                if pts:last["pts_ref"]=pts[-1]
            # Some templates place a ref and paragraph text in the same block.
            if not stripped or len(stripped)<8:continue
        if MYANMAR_RE.search(stripped):
            if last is not None and len(stripped)>8:
                last["my_ai_translation"]=stripped
                last["translation_status"]="ai_generated_unreviewed"
            continue
        if len(stripped)<18:continue
        if stripped.lower().startswith(("browse tipitaka","tipiṭaka library","previous text","next text")):continue
        m=PARA_RE.match(stripped)
        number=int(m.group(1)) if m else None
        pali=clean(m.group(2) if m else stripped)
        if len(pali)<12:continue
        # Exclude common navigation/edition boilerplate.
        if pali.startswith(("The Chaṭṭha Saṅgāyana","Chaṭṭha Saṅgāyana Tipiṭaka")):continue
        rec={"paragraph_number":number,"pali_text":pali,"cst_ref":cst[-1] if cst else None,
             "pts_ref":pts[-1] if pts else None,"my_ai_translation":None,
             "translation_status":None}
        records.append(rec);last=rec
    return parser.title.strip(),parser.links,records

def create_schema(db):
    db.executescript("""
    CREATE TABLE IF NOT EXISTS cst_source_paragraphs(
      id INTEGER PRIMARY KEY,
      source_path TEXT NOT NULL,
      source_url TEXT NOT NULL,
      page_title TEXT NOT NULL,
      page_paragraph_index INTEGER NOT NULL,
      paragraph_number INTEGER,
      pali_text TEXT NOT NULL,
      cst_ref TEXT,
      pts_ref TEXT,
      my_ai_translation TEXT,
      translation_source TEXT,
      translation_status TEXT,
      matched_bilara_segment_id TEXT,
      matched_volume INTEGER,
      content_sha256 TEXT NOT NULL,
      fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(source_path,page_paragraph_index)
    );
    CREATE INDEX IF NOT EXISTS idx_cst_source_path ON cst_source_paragraphs(source_path,page_paragraph_index);
    CREATE INDEX IF NOT EXISTS idx_cst_ref ON cst_source_paragraphs(cst_ref);
    CREATE INDEX IF NOT EXISTS idx_cst_match ON cst_source_paragraphs(matched_bilara_segment_id);
    CREATE TABLE IF NOT EXISTS cst_import_pages(
      source_path TEXT PRIMARY KEY,
      source_url TEXT NOT NULL,
      page_title TEXT NOT NULL,
      http_status INTEGER NOT NULL,
      paragraph_count INTEGER NOT NULL,
      page_sha256 TEXT NOT NULL,
      fetched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS cst_import_metadata(
      name TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
    """)

def probe_api():
    url=BASE+"/api/v1/text/sutta/dn/silakkhandha-vagga/dn1"
    try:
        status,ctype,body=fetch(url,timeout=12)
        return {"url":url,"status":status,"content_type":ctype,
                "json_response":("json" in ctype.lower()),"bytes":len(body)}
    except HTTPError as e:
        return {"url":url,"status":e.code,"available":False,"note":"Documented example is not currently a usable API response"}
    except Exception as e:
        return {"url":url,"status":None,"available":False,"error":str(e)[:250]}

def build_bilara_index(db):
    index=collections.defaultdict(list)
    try:
        rows=db.execute("SELECT segment_id,volume,body FROM paragraphs")
    except sqlite3.Error:
        return index
    for segment_id,volume,body in rows:
        key=sha(norm_pali(body))
        index[key].append((segment_id,int(volume)))
    return index

def import_pages(database,max_pages,sleep_seconds,timeout,report_path):
    db=sqlite3.connect(database)
    db.row_factory=sqlite3.Row
    create_schema(db)
    index=build_bilara_index(db)
    queue=collections.deque(ROOTS)
    seen=set()
    counts=collections.Counter()
    api=probe_api()
    errors=[]
    while queue and len(seen)<max_pages:
        url=queue.popleft()
        url=urldefrag(url)[0]
        parsed=urlparse(url)
        url=parsed.scheme+"://"+parsed.netloc+parsed.path
        if not allowed_url(url) or url in seen:continue
        seen.add(url)
        try:
            status,ctype,raw=fetch(url,timeout)
            if status!=200 or "html" not in ctype.lower():
                counts["non_html_or_bad_status"]+=1
                continue
            title,links,records=parse_page(url,raw)
            path=urlparse(url).path
            counts["pages_fetched"]+=1
            counts["paragraphs_found"]+=len(records)
            for href in links:
                target=urljoin(url,href)
                target=urldefrag(target)[0]
                if allowed_url(target) and target not in seen:queue.append(target)
            for i,r in enumerate(records,1):
                matched=index.get(sha(norm_pali(r["pali_text"])),[])
                segment_id=matched[0][0] if len(matched)==1 else None
                volume=matched[0][1] if len(matched)==1 else None
                if len(matched)==1:counts["exact_bilara_matches"]+=1
                elif len(matched)>1:counts["ambiguous_bilara_matches"]+=1
                if r["my_ai_translation"]:counts["myanmar_ai_translations_found"]+=1
                db.execute("""INSERT INTO cst_source_paragraphs(
                    source_path,source_url,page_title,page_paragraph_index,paragraph_number,
                    pali_text,cst_ref,pts_ref,my_ai_translation,translation_source,
                    translation_status,matched_bilara_segment_id,matched_volume,content_sha256
                  ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                  ON CONFLICT(source_path,page_paragraph_index) DO UPDATE SET
                    source_url=excluded.source_url,page_title=excluded.page_title,
                    paragraph_number=excluded.paragraph_number,pali_text=excluded.pali_text,
                    cst_ref=excluded.cst_ref,pts_ref=excluded.pts_ref,
                    my_ai_translation=excluded.my_ai_translation,
                    translation_source=excluded.translation_source,
                    translation_status=excluded.translation_status,
                    matched_bilara_segment_id=excluded.matched_bilara_segment_id,
                    matched_volume=excluded.matched_volume,content_sha256=excluded.content_sha256,
                    fetched_at=CURRENT_TIMESTAMP""",
                  (path,url,title,i,r["paragraph_number"],r["pali_text"],r["cst_ref"],r["pts_ref"],
                   r["my_ai_translation"],"tipitakaonline.org" if r["my_ai_translation"] else None,
                   r["translation_status"],segment_id,volume,sha(r["pali_text"])))
            db.execute("""INSERT INTO cst_import_pages(source_path,source_url,page_title,http_status,paragraph_count,page_sha256)
               VALUES(?,?,?,?,?,?) ON CONFLICT(source_path) DO UPDATE SET
               source_url=excluded.source_url,page_title=excluded.page_title,http_status=excluded.http_status,
               paragraph_count=excluded.paragraph_count,page_sha256=excluded.page_sha256,fetched_at=CURRENT_TIMESTAMP""",
               (path,url,title,status,len(records),sha(raw.decode("utf-8","replace"))))
            db.commit()
        except HTTPError as e:
            counts["http_errors"]+=1;errors.append({"url":url,"status":e.code})
        except (URLError,TimeoutError) as e:
            counts["network_errors"]+=1;errors.append({"url":url,"error":str(e)[:180]})
        except Exception as e:
            counts["parse_errors"]+=1;errors.append({"url":url,"error":str(e)[:250]})
        time.sleep(sleep_seconds)
    remaining=len(queue)
    totals=db.execute("""SELECT COUNT(*),COUNT(DISTINCT source_path),
      SUM(CASE WHEN matched_bilara_segment_id IS NOT NULL THEN 1 ELSE 0 END),
      SUM(CASE WHEN my_ai_translation IS NOT NULL THEN 1 ELSE 0 END),
      SUM(CASE WHEN cst_ref IS NOT NULL THEN 1 ELSE 0 END),
      SUM(CASE WHEN pts_ref IS NOT NULL THEN 1 ELSE 0 END)
      FROM cst_source_paragraphs""").fetchone()
    report={
      "source":"https://tipitakaonline.org/",
      "edition":"Chaṭṭha Saṅgāyana (Sixth Council) Tipiṭaka, digitized by VRI",
      "rights":"CC0 1.0 Universal per https://tipitakaonline.org/usage-rights",
      "developer_api_probe":api,
      "api_mode":"REST example is currently a placeholder if probe is unavailable; server-rendered public pages used instead",
      "pages_fetched_this_run":counts["pages_fetched"],
      "paragraphs_found_this_run":counts["paragraphs_found"],
      "database_total_cst_paragraphs":totals[0] or 0,
      "database_pages":totals[1] or 0,
      "exact_matches_to_bilara_segment":totals[2] or 0,
      "cst_reference_count":totals[4] or 0,
      "pts_reference_count":totals[5] or 0,
      "burmese_ai_translation_count":totals[3] or 0,
      "unmatched_or_ambiguous_cst_paragraphs":(totals[0] or 0)-(totals[2] or 0),
      "pages_remaining_in_crawl_queue":remaining,
      "crawl_complete":remaining==0,
      "counts_this_run":dict(counts),
      "errors":errors[:50],
      "important":"Myanmar AI translations are stored as unreviewed. Only exact Pali text matches receive Bilara volume IDs; other CST rows remain separate until crosswalk review."
    }
    db.executemany("INSERT OR REPLACE INTO cst_import_metadata(name,value) VALUES (?,?)",
      [("source",report["source"]),("edition",report["edition"]),("rights",report["rights"]),
       ("developer_api_probe",json.dumps(api,ensure_ascii=False)),
       ("last_import_report",json.dumps(report,ensure_ascii=False))])
    db.commit();db.close()
    report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--database",default="app/src/main/assets/tipitaka_offline.sqlite")
    p.add_argument("--max-pages",type=int,default=1800)
    p.add_argument("--sleep",type=float,default=0.12)
    p.add_argument("--timeout",type=int,default=25)
    p.add_argument("--report",default="tipitakaonline_cst_import_report.json")
    a=p.parse_args()
    if not (0<a.max_pages<=10000):sys.exit("--max-pages must be 1..10000")
    if not __import__("pathlib").Path(a.database).is_file():sys.exit("Offline SQLite must be built before CST import")
    import_pages(a.database,a.max_pages,a.sleep,a.timeout,__import__("pathlib").Path(a.report))

if __name__=="__main__":main()
