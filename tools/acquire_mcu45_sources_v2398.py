#!/usr/bin/env python3
"""V2.3.9.8: MCU-original Pāli intake — DRY RUN by default.

Only approved direct HTTPS URLs from the explicitly allowed host are downloaded.
Requires pinned SHA256, human permission evidence and MCU_PALI_1996 metadata.
Downloading/staging never means a volume is verified or ready for the APK.
"""
import argparse,hashlib,ipaddress,json,re,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
EDITION="MCU_PALI_1996"
SHA256=re.compile(r"^[0-9a-f]{64}$")
THAI=re.compile(r"[\u0e00-\u0e7f]")
MAX_BYTES=80_000_000

class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  raise ValueError("Redirects not permitted for pinned source links")

def check_manifest(doc):
 books=doc.get("volumes")
 if doc.get("edition")!=EDITION or not isinstance(books,list) or len(books)!=45:
  raise ValueError("Expected MCU_PALI_1996 with 45 volume records")
 ids=[b.get("volume") for b in books]
 if any(type(x) is not int for x in ids) or sorted(ids)!=list(range(1,46)):
  raise ValueError("Duplicate/missing volume numbers")
 if not all(isinstance(b.get("title"),str) and b["title"].strip() for b in books):
  raise ValueError("Volume title missing")
 return sorted(books,key=lambda x:x["volume"])

def check_url(url,approved_host):
 if not isinstance(url,str):raise ValueError("Invalid URL")
 u=urllib.parse.urlsplit(url)
 if u.scheme!="https" or not u.hostname or u.username or u.password or u.port not in (None,443):
  raise ValueError("Only HTTPS URLs without user credentials accepted")
 host=u.hostname.lower()
 if not approved_host or host!=approved_host.lower():
  raise ValueError("Source host is not explicitly approved")
 if host in ("localhost","localhost.localdomain") or host.endswith((".local",".internal",".localhost")):
  raise ValueError("Private host forbidden")
 try:
  ip=ipaddress.ip_address(host)
 except ValueError:
  pass
 else:
  if not ip.is_global:raise ValueError("Private IP forbidden")
 return url

def validate_json_bytes(raw,volume):
 try:obj=json.loads(raw.decode("utf-8-sig"))
 except (UnicodeError,json.JSONDecodeError) as e:raise ValueError("Invalid UTF-8 JSON") from e
 if (obj.get("edition")!=EDITION or obj.get("volume")!=volume
     or obj.get("language")!="pli" or obj.get("script")!="Thai"):
  raise ValueError("Source edition/language/script mismatch")
 rows=obj.get("paragraphs")
 if not isinstance(rows,list) or not rows:raise ValueError("No source paragraphs")
 ids=set()
 for p in rows:
  if not isinstance(p,dict):raise ValueError("Invalid paragraph object")
  pid,txt,page=p.get("paragraph_id"),p.get("pali"),p.get("page")
  if not isinstance(pid,str) or not pid.strip() or pid in ids:raise ValueError("Duplicate/missing ID")
  if not isinstance(txt,str) or not txt.strip() or not THAI.search(txt):raise ValueError("Missing Thai-script Pali")
  if page is not None and (type(page) is not int or page<1):raise ValueError("Invalid page")
  ids.add(pid)
 return len(rows)

def readiness(book,allowed_host):
 if book.get("source_status")=="ACQUIRED" and book.get("source_file"):
  return "LOCAL_SOURCE_ALREADY_DECLARED"
 if book.get("rights_status")!="REVIEWED_PERMITTED":return "RIGHTS_NOT_APPROVED"
 if not book.get("rights_reviewer") or not book.get("rights_evidence_url"):
  return "RIGHTS_EVIDENCE_MISSING"
 if not SHA256.fullmatch(book.get("file_sha256") or ""):
  return "MISSING_PINNED_SHA256"
 try:check_url(book.get("direct_download_url"),allowed_host)
 except ValueError:return "UNAPPROVED_DIRECT_SOURCE_URL"
 return "ELIGIBLE_FOR_MANUAL_FETCH"

def run(manifest_path,out_dir,report_path,allow_host="",execute=False):
 books=check_manifest(json.loads(Path(manifest_path).read_text(encoding="utf-8")))
 if execute and not allow_host:raise ValueError("--fetch requires --allow-host")
 out_dir=Path(out_dir);out_dir.mkdir(parents=True,exist_ok=True)
 acquired=paragraphs=0;records=[]
 opener=urllib.request.build_opener(NoRedirect)
 for book in books:
  v=book["volume"];status=readiness(book,allow_host);size=count=0;digest=""
  if status=="ELIGIBLE_FOR_MANUAL_FETCH" and execute:
   url=check_url(book["direct_download_url"],allow_host)
   request=urllib.request.Request(url,headers={"User-Agent":"Tipitaka-MCU-Source-Intake/2.3.9.8","Accept":"application/json"})
   with opener.open(request,timeout=35) as response:
    sizeh=response.headers.get("Content-Length")
    if sizeh and int(sizeh)>MAX_BYTES:raise ValueError("Source too large")
    raw=response.read(MAX_BYTES+1)
   if len(raw)>MAX_BYTES:raise ValueError("Source too large")
   size=len(raw);digest=hashlib.sha256(raw).hexdigest()
   if digest!=book["file_sha256"]:raise ValueError(f"Volume {v} SHA mismatch")
   count=validate_json_bytes(raw,v)
   path=out_dir/f"mcu_{v:02d}.json"
   if path.exists():raise FileExistsError(path)
   temp=path.with_suffix(".partial")
   try:temp.write_bytes(raw);temp.replace(path)
   finally:temp.unlink(missing_ok=True)
   acquired+=1;paragraphs+=count;status="ACQUIRED_UNREVIEWED"
  elif status=="ELIGIBLE_FOR_MANUAL_FETCH":
   status="ELIGIBLE_NOT_FETCHED"
  records.append({"volume":v,"title":book["title"],"status":status,"bytes":size,"sha256":digest,
                   "paragraphs":count,"rights_status":book.get("rights_status","PENDING")})
 report={"version":"2.3.9.8","edition":EDITION,"catalog_volumes":45,
         "new_files_acquired":acquired,"new_paragraphs_acquired":paragraphs,
         "verified_mcu_volumes":0,"release_ready":False,
         "mode":"EXPLICIT_FETCH" if execute else "DRY_RUN",
         "rights_policy":"Explicit human permission and pinned SHA required",
         "records":records,"created_utc":datetime.now(timezone.utc).isoformat()}
 report_path=Path(report_path);report_path.parent.mkdir(parents=True,exist_ok=True)
 report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 return report

if __name__=="__main__":
 p=argparse.ArgumentParser()
 for arg in ("manifest","output-dir","report"):p.add_argument("--"+arg,required=True)
 p.add_argument("--allow-host",default="");p.add_argument("--fetch",action="store_true")
 a=p.parse_args()
 print(json.dumps(run(a.manifest,a.output_dir,a.report,a.allow_host,a.fetch),ensure_ascii=False,indent=2))
