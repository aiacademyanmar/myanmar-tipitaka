#!/usr/bin/env python3
"""MN24 source-aligned Burmese AI working-draft gate (not expert approval)."""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
BLOB='3be1f90f7c766e4fa07f18da31b7a05038c20e84'
SOURCE_PATH='sutta/mn/mn24_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
ELLIPSES={'mn24:2.5','mn24:10.3','mn24:10.4','mn24:10.5','mn24:10.6','mn24:12.3','mn24:12.4','mn24:12.5','mn24:12.6'}
SUMMARIES={'mn24:2.3','mn24:5.4','mn24:6.2','mn24:15.1','mn24:16.9','mn24:17.12'}
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':124,'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':6,'SOURCE_ELLIPSIS_UNEXPANDED':9}
COUNTS=[334,125,128,165,203,51,147,170,234,235,132,372,152,144,263,83,83,150,123,87,227,359,104,139]
def check(csv_file,source_json,combined_db=None,prior_db=None):
 src=json.loads(Path(source_json).read_text(encoding='utf-8-sig'))
 if not isinstance(src,dict) or len(src)!=139 or any(not x.startswith('mn24:') for x in src):raise ValueError('Expected 139 MN24 Pali source IDs')
 raw=json.dumps(src,ensure_ascii=False,indent=2).encode()
 if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:raise ValueError('Original Pali published Git Blob SHA differs')
 if {k for k,v in src.items() if '…' in v}!=ELLIPSES:raise ValueError('Original 9 Pali abbreviated source segments changed')
 with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError('MN24 editorial CSV schema changed')
  rows=list(reader)
 if len(rows)!=139:raise ValueError('Expected 139 MN24 Burmese working draft rows')
 seen=set();cnt=Counter()
 for r in rows:
  sid=r['segment_id'];pali=r['pali'];method=r['translation_method']
  if sid in seen or sid not in src or r['sutta_uid']!='mn24':raise ValueError('Duplicate or foreign source ID')
  seen.add(sid)
  if src[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:raise ValueError('Pali source SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():raise ValueError('Missing Burmese working draft '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():raise ValueError('False scholarly approval '+sid)
  if r['source_path']!=SOURCE_PATH or r['published_source_blob_sha']!=BLOB:raise ValueError('Original source provenance mismatch '+sid)
  if sid in ELLIPSES:
   if method!='SOURCE_ELLIPSIS_UNEXPANDED' or 'မချဲ့ရသေး' not in r['translation_draft']:raise ValueError('Source ellipsis must be visibly unexpanded '+sid)
  elif sid in SUMMARIES:
   if method!='CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':raise ValueError('Summary requires literal review flag '+sid)
  elif method!='SEGMENT_ALIGNED_AI_DRAFT':raise ValueError('Unexpected editorial classification '+sid)
  cnt[method]+=1
 if seen!=set(src) or dict(cnt)!=METHODS:raise ValueError('MN24 editorial methods changed')
 if combined_db:
  c=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if c.execute('pragma integrity_check').fetchone()[0]!='ok':raise ValueError('Combined SQLite corrupted')
   expected={f'mn{i}':n for i,n in enumerate(COUNTS,1)}
   if dict(c.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!=expected:raise ValueError('MN1-MN24 4210 rows mismatch')
   if c.execute('select count(*) from pali_myanmar where approved!=0').fetchone()[0]:raise ValueError('Unreviewed entries marked approved')
   for r in rows:
    result=c.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,translation_method from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if result!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256'],r['translation_method']):raise ValueError('CSV SQLite drift '+r['segment_id'])
   if prior_db:
    p=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     old=p.execute('select * from pali_myanmar order by segment_id').fetchall()
     new=c.execute("select * from pali_myanmar where sutta_uid!='mn24' order by segment_id").fetchall()
     if len(old)!=4071 or old!=new:raise ValueError('Prior MN1-MN23 4071 rows were changed')
    finally:p.close()
  finally:c.close()
 return {'mn24_source_segments':139,'working_draft_rows':139,'direct_drafts':124,'contextual_summaries':6,'unexpanded_pali':9,'combined_draft_rows':4210 if combined_db else None,'scholar_approved':0,'MCU45_verified':0,'native_release_APK':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db');a=p.parse_args()
 print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
