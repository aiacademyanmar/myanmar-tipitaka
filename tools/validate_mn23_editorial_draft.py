#!/usr/bin/env python3
"""MN23 Vammikasutta source-pinned Pāli/Burmese AI-DRAFT gate.

Checks source IDs and SHA, original 4 ellipses, 5 contextual summaries,
104 unapproved draft records, and optionally combined SQLite preservation.
Does NOT certify semantic translation, MCU volumes, or an Android APK.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
SOURCE_BLOB='57b7bf5f771cff196532a149b8794fd001c8b9a9'
SOURCE_PATH='sutta/mn/mn23_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
ELLIPSES={'mn23:3.6','mn23:4.29','mn23:4.30','mn23:4.31'}
SUMMARIES={'mn23:1.4','mn23:2.44','mn23:3.1','mn23:3.2','mn23:4.1'}
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':95,'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':5,'SOURCE_ELLIPSIS_UNEXPANDED':4}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144,'mn15':263,'mn16':83,'mn17':83,'mn18':150,'mn19':123,'mn20':87,'mn21':227,'mn22':359,'mn23':104}
def check(csv_path,original_json,combined_db=None,prior_db=None):
 src=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
 if not isinstance(src,dict) or len(src)!=104 or any(not k.startswith('mn23:') for k in src):
  raise ValueError('MN23 source must have 104 IDs')
 raw=json.dumps(src,ensure_ascii=False,indent=2).encode()
 blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if blob!=SOURCE_BLOB:raise ValueError('Published MN23 source Git blob SHA mismatch')
 if {k for k,v in src.items() if '…' in v}!=ELLIPSES:
  raise ValueError('Original four source abbreviations changed')
 with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
  rdr=csv.DictReader(f)
  if rdr.fieldnames!=FIELDS:raise ValueError('MN23 editorial CSV schema mismatch')
  rows=list(rdr)
 if len(rows)!=104:raise ValueError('MN23 needs 104 working draft rows')
 seen=set();methods=Counter()
 for r in rows:
  sid=r['segment_id'];pali=r['pali'];method=r['translation_method']
  if sid in seen or sid not in src or r['sutta_uid']!='mn23':
   raise ValueError('Duplicate or foreign MN23 segment '+sid)
  seen.add(sid)
  if src[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:
   raise ValueError('Original Pāli text or SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('Empty Burmese editorial draft '+sid)
  if r['approved']!='0' or r['reviewer'].strip() or r['draft_status']!='AI_DRAFT_UNREVIEWED':
   raise ValueError('Unapproved AI draft marked approved '+sid)
  if r['source_path']!=SOURCE_PATH or r['published_source_blob_sha']!=SOURCE_BLOB or len(r['source_commit'])!=40:
   raise ValueError('Missing published source provenance '+sid)
  if sid in ELLIPSES:
   if method!='SOURCE_ELLIPSIS_UNEXPANDED' or 'မချဲ့ရသေး' not in r['translation_draft']:
    raise ValueError('Source ellipsis silently expanded '+sid)
  elif sid in SUMMARIES:
   if method!='CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':
    raise ValueError('Long contextual passage must retain review flag '+sid)
  elif method!='SEGMENT_ALIGNED_AI_DRAFT':
   raise ValueError('Unexpected direct translation flag '+sid)
  methods[method]+=1
 if seen!=set(src) or dict(methods)!=METHODS:
  raise ValueError('MN23 source coverage or review counts changed')
 if combined_db:
  db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failure')
   if dict(db.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))!=COUNTS:
    raise ValueError('Combined 4071 MN1-MN23 records mismatch')
   if db.execute('SELECT count(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]!=0:
    raise ValueError('Unreviewed SQLite contains approved rows')
   for r in rows:
    v=db.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,translation_method FROM pali_myanmar WHERE segment_id=?',(r['segment_id'],)).fetchone()
    if v!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256'],r['translation_method']):
     raise ValueError('MN23 source CSV vs SQLite mismatch '+r['segment_id'])
   if prior_db:
    p=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     old=p.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
     new=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn23' ORDER BY segment_id").fetchall()
     if len(old)!=3967 or old!=new:raise ValueError('Previous 3967 MN1-MN22 records modified')
    finally:p.close()
  finally:db.close()
 return {'MN23_original_source_segments':104,'Burmese_AI_working_drafts':104,
  'direct_drafts':95,'summaries_need_literal_review':5,'unexpanded_original_ellipses':4,
  'combined_draft_rows':4071 if combined_db else None,'human_approved':0,
  'independently_MCU_45_verified':0,'signed_native_APK':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args()
 print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
