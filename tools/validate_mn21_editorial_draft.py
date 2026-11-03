#!/usr/bin/env python3
"""MN21 Kakacupamasutta source-aligned Burmese AI editorial draft gate.

This tests row/provenance integrity, NOT translation quality, human approval,
MCU edition equivalence, or a signed APK.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
BLOB='8388da261c4b895776318e7c9caf64c2ec63f7f5'
PATH='sutta/mn/mn21_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
ELLIPSES={'mn21:15.1','mn21:17.1'}
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':225,'SOURCE_ELLIPSIS_UNEXPANDED':2}
EXPECTED={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144,'mn15':263,'mn16':83,'mn17':83,'mn18':150,'mn19':123,'mn20':87,'mn21':227}
def validate(csv_path,original_json,combined_db=None,prior_db=None):
 source=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
 if not isinstance(source,dict) or len(source)!=227 or any(not sid.startswith('mn21:') for sid in source):
  raise ValueError('MN21 original inventory requires 227 source segment IDs')
 raw=json.dumps(source,ensure_ascii=False,indent=2).encode()
 source_sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if source_sha!=BLOB:raise ValueError('Published MN21 Git source blob mismatch')
 with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=FIELDS:raise ValueError('MN21 editorial CSV fields altered')
  rows=list(rd)
 if len(rows)!=227:raise ValueError('MN21 working draft needs exactly 227 rows')
 seen=set();methods=Counter()
 for r in rows:
  sid=r['segment_id'];pali=r['pali'];method=r['translation_method']
  if sid in seen or sid not in source or r['sutta_uid']!='mn21':
   raise ValueError('Duplicate or invalid MN21 segment '+sid)
  seen.add(sid)
  if pali!=source[sid] or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:
   raise ValueError('Original Pali text/SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('MN21 Burmese draft missing '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():
   raise ValueError('Draft must never be auto-approved '+sid)
  if r['source_path']!=PATH or r['published_source_blob_sha']!=BLOB or len(r['source_commit'])!=40:
   raise ValueError('Published source provenance missing '+sid)
  if ('…' in pali)!=(sid in ELLIPSES):
   raise ValueError('Original abbreviation inventory changed '+sid)
  if (sid in ELLIPSES)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
   raise ValueError('Source ellipsis requires explicit flag '+sid)
  if sid in ELLIPSES and 'မချဲ့ရသေး' not in r['translation_draft']:
   raise ValueError('Source abbreviation must not be falsely expanded '+sid)
  methods[method]+=1
 if seen!=set(source) or dict(methods)!=METHODS:
  raise ValueError('MN21 method count / coverage changed')
 if combined_db:
  db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failed')
   counts=dict(db.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))
   if counts!=EXPECTED:raise ValueError('MN1–MN21 3608-row inventory mismatch')
   if db.execute('SELECT COUNT(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
    raise ValueError('Unreviewed merged corpus has approved records')
   for r in rows:
    found=db.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,draft_status,source_sha256 FROM pali_myanmar WHERE segment_id=?',(r['segment_id'],)).fetchone()
    if found!=(r['pali'],r['translation_draft'],r['explanation_draft'],'AI_DRAFT_UNREVIEWED',r['source_sha256']):
     raise ValueError('MN21 CSV/SQLite mismatch '+r['segment_id'])
   if prior_db:
    prev=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     a=prev.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
     b=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn21' ORDER BY segment_id").fetchall()
     if len(a)!=3381 or a!=b:raise ValueError('Previous 3381 rows changed')
    finally:prev.close()
  finally:db.close()
 return {'source_rows':227,'Burmese_working_drafts':227,'Burmese_explanations':227,'source_abbreviations_unexpanded':2,'combined_drafts':3608 if combined_db else None,'human_approved':0,'verified_MCU45':0,'signed_APK':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args()
 print(json.dumps(validate(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
