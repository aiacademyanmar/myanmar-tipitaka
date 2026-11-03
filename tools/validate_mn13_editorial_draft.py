#!/usr/bin/env python3
"""MN13 Mahādukkhakkhandhasutta editorial-draft QA (not scholar-approved).

Confirms 152 source-aligned Roman Pāli records, source abbreviations,
Burmese working drafts and unchanged MN1–MN12 SQLite rows (when provided).
This NEVER certifies MCU 45-edition equivalence or semantic translation quality.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft',
'section','topic','draft_status','translation_method','source_sha256',
'source_path','source_blob_sha','approved','reviewer','source_url']
METHOD_COUNTS={
 'SEGMENT_LEVEL_WORKING_TRANSLATION':125,
 'CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW':22,
 'SOURCE_ELLIPSIS_UNEXPANDED':5}
EXPECTED={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,
 'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152}
BLOB='20a35bbc3f7e38ff9f48a3c5d9aa86ca012e6bbc'
SOURCE='sutta/mn/mn13_root-pli-ms.json'
CHECKSUM=157404040
def audit(csv_path,original_path,combined=None,prior=None):
 original=json.loads(Path(original_path).read_text(encoding='utf-8-sig'))
 if not isinstance(original,dict) or len(original)!=152 or not all(k.startswith('mn13:') for k in original):
  raise ValueError('MN13 source inventory must have exactly 152 source segment IDs')
 ordered=json.dumps(list(original.items()),ensure_ascii=False,separators=(',',':'))
 h=0
 for ch in ordered:h=(h*131+ord(ch))%1000000007
 if len(ordered)!=17585 or h!=CHECKSUM:raise ValueError('Published source text-checksum mismatch')
 with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError('Unexpected MN13 editorial CSV schema')
  rows=list(reader)
 if len(rows)!=152:raise ValueError('Expected 152 MN13 editorial records')
 seen=set();counts=Counter()
 for r in rows:
  sid=r['segment_id']
  if sid in seen or sid not in original or r['sutta_uid']!='mn13':
   raise ValueError('Duplicate or foreign MN13 segment ID')
  seen.add(sid);pali=r['pali']
  if pali!=original[sid] or hashlib.sha256(pali.encode('utf8')).hexdigest()!=r['source_sha256']:
   raise ValueError('Source Pāli changed or SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('Missing Myanmar working draft '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():
   raise ValueError('Cannot auto approve unreviewed Burmese draft '+sid)
  if r['source_path']!=SOURCE or r['source_blob_sha']!=BLOB:
   raise ValueError('Pinned SuttaCentral/Bilara source provenance missing '+sid)
  method=r['translation_method']
  counts[method]+=1
  if ('…' in pali)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
   raise ValueError('Unexpanded source must be flagged '+sid)
 if seen!=set(original) or dict(counts)!=METHOD_COUNTS:
  raise ValueError('MN13 editorial coverage/review method inventory changed')
 if combined:
  db=sqlite3.connect('file:'+str(Path(combined).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('pragma integrity_check').fetchone()[0]!='ok':
    raise ValueError('Combined SQLite corrupt')
   if dict(db.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!=EXPECTED:
    raise ValueError('Expected 2448 rows across MN1–MN13')
   if db.execute('select count(*) from pali_myanmar where approved<>0').fetchone()[0]:
    raise ValueError('Approved flag cannot be set in unreviewed draft corpus')
   for r in rows:
    found=db.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,draft_status from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if found!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256'],'AI_DRAFT_UNREVIEWED'):
     raise ValueError('CSV ↔ SQLite mismatch for '+r['segment_id'])
   if prior:
    pre=sqlite3.connect('file:'+str(Path(prior).resolve())+'?mode=ro',uri=True)
    try:
     a=pre.execute('select * from pali_myanmar order by segment_id').fetchall()
     b=db.execute("select * from pali_myanmar where sutta_uid!='mn13' order by segment_id").fetchall()
     if a!=b:raise ValueError('Earlier MN1–MN12 2296 rows modified')
    finally:pre.close()
  finally:db.close()
 return {'status':'MN13_DRAFT_QA_PASSED','source_segments':152,
  'working_translation_draft_rows':152,'working_explanation_rows':152,
  'direct_working_drafts':125,'contextual_summaries_need_full_translation':22,
  'original_abbreviations_unexpanded':5,'combined_draft_rows':2448 if combined else None,
  'scholar_approved_rows':0,'independent_MCU_original_volumes_verified':0,
  'release_ready':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args()
 print(json.dumps(audit(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
