#!/usr/bin/env python3
"""MN15 Anumānasutta editorial draft validation, NOT an approved translation.

Validates exact source Git blob, segment Pāli hashes, 263 Burmese working
drafts, 2 long-review flags, and optional MN1-MN15 SQLite preservation.
No independent MCU-edition or Buddhist scholarly sign-off is implied.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
SOURCE_BLOB='436b393d7d456e83fc539301cdcd936b940261d9'
SOURCE_PATH='sutta/mn/mn15_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic',
'draft_status','translation_method','source_sha256','source_path','source_commit',
'published_source_blob_sha','approved','reviewer','source_url']
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':261,'LONG_PASSAGE_NEEDS_LITERAL_REVIEW':2}
LONG_IDS={'mn15:2.2','mn15:4.2'}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,
'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,
'mn13':152,'mn14':144,'mn15':263}
def audit(csv_file,source_json,combined_db=None,prior_db=None):
 source=json.loads(Path(source_json).read_text(encoding='utf-8-sig'))
 if not isinstance(source,dict) or len(source)!=263 or not all(k.startswith('mn15:') for k in source):
  raise ValueError('MN15 source must contain exactly 263 segment IDs')
 original=json.dumps(source,ensure_ascii=False,indent=2).encode('utf-8')
 blob=hashlib.sha1(b'blob '+str(len(original)).encode()+b'\0'+original).hexdigest()
 if blob!=SOURCE_BLOB:raise ValueError('Published MN15 source Git Blob SHA differs')
 with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError('MN15 CSV editorial schema differs')
  rows=list(reader)
 if len(rows)!=263:raise ValueError('Expected 263 MN15 source-linked draft rows')
 ids=set();method_counts=Counter()
 for row in rows:
  sid=row['segment_id'];pali=row['pali']
  if sid in ids or sid not in source or row['sutta_uid']!='mn15':
   raise ValueError('Duplicate or foreign MN15 source ID')
  ids.add(sid)
  if source[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=row['source_sha256']:
   raise ValueError('Pāli source text / SHA mismatch: '+sid)
  if not row['translation_draft'].strip() or not row['explanation_draft'].strip():
   raise ValueError('Myanmar working draft missing: '+sid)
  if row['draft_status']!='AI_DRAFT_UNREVIEWED' or row['approved']!='0' or row['reviewer'].strip():
   raise ValueError('Burmese editorial draft cannot be auto-approved: '+sid)
  if row['source_path']!=SOURCE_PATH or row['published_source_blob_sha']!=SOURCE_BLOB:
   raise ValueError('Missing pinned source provenance: '+sid)
  if '…' in pali:raise ValueError('Unexpected MN15 original ellipsis: '+sid)
  method=row['translation_method']
  if (method=='LONG_PASSAGE_NEEDS_LITERAL_REVIEW')!=(sid in LONG_IDS):
   raise ValueError('MN15 long passage review flag changed: '+sid)
  method_counts[method]+=1
 if ids!=set(source) or dict(method_counts)!=METHODS:
  raise ValueError('MN15 editorial method counts changed')
 if combined_db:
  db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failure')
   if dict(db.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))!=COUNTS:
    raise ValueError('MN1-MN15 2,855-row source inventory mismatch')
   if db.execute('SELECT count(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
    raise ValueError('Draft corpus must not have approved rows')
   for row in rows:
    found=db.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,draft_status FROM pali_myanmar WHERE segment_id=?',(row['segment_id'],)).fetchone()
    if found!=(row['pali'],row['translation_draft'],row['explanation_draft'],row['source_sha256'],'AI_DRAFT_UNREVIEWED'):
     raise ValueError('MN15 CSV/SQLite mismatch: '+row['segment_id'])
   if prior_db:
    prev=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     a=prev.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
     b=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn15' ORDER BY segment_id").fetchall()
     if len(a)!=2592 or a!=b:raise ValueError('Previous MN1-MN14 2592 records changed')
    finally:prev.close()
  finally:db.close()
 return {'status':'MN15_UNREVIEWED_DRAFT_QA_PASS','source_records':263,
 'Burmese_working_drafts':263,'source_abbreviations':0,'long_review_flags':2,
 'combined_draft_rows':2855 if combined_db else None,'human_approved':0,
 'original_MCU_verified_volumes':0,'native_apk_signed':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--source-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args();print(json.dumps(audit(a.csv,a.source_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
