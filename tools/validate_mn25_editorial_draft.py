#!/usr/bin/env python3
"""MN25 Nivāpasutta fail-closed source and Burmese AI draft integrity gate.

Structural quality only. It neither approves a Burmese translation nor verifies
MCU 45-volume equivalence, and does not compile or sign an Android APK.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
from collections import Counter
BLOB='ff7913513ea8f067e37f926b528ac032c2c4a5c5'
SOURCE_PATH='sutta/mn/mn25_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':162,'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':12,'SOURCE_ELLIPSIS_UNEXPANDED':25}
COUNTS=[334,125,128,165,203,51,147,170,234,235,132,372,152,144,263,83,83,150,123,87,227,359,104,139,199]
def check(csv_path,source_json,combined_db=None,prior_db=None):
 original=json.loads(Path(source_json).read_text(encoding='utf-8-sig'))
 if not isinstance(original,dict) or len(original)!=199 or any(not k.startswith('mn25:') for k in original):
  raise ValueError('MN25 requires exactly 199 source IDs')
 raw=json.dumps(original,ensure_ascii=False,indent=2).encode()
 if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=BLOB:
  raise ValueError('Original MN25 published Git blob mismatch')
 if sum('…' in x for x in original.values())!=25:
  raise ValueError('Original 25 Pāli source ellipses changed')
 with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:
  rd=csv.DictReader(f)
  if rd.fieldnames!=FIELDS:raise ValueError('Unexpected editorial CSV schema')
  rows=list(rd)
 if len(rows)!=199:raise ValueError('Expected 199 MN25 AI working drafts')
 seen=set();counts=Counter()
 for r in rows:
  sid=r['segment_id'];p=r['pali'];method=r['translation_method']
  if sid in seen or sid not in original or r['sutta_uid']!='mn25':
   raise ValueError('Duplicate/foreign source segment '+sid)
  seen.add(sid)
  if p!=original[sid] or hashlib.sha256(p.encode()).hexdigest()!=r['source_sha256']:
   raise ValueError('Pāli source text/SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('Missing Myanmar AI working draft '+sid)
  if r['approved']!='0' or r['reviewer'].strip() or r['draft_status']!='AI_DRAFT_UNREVIEWED':
   raise ValueError('False human approval '+sid)
  if r['source_path']!=SOURCE_PATH or r['published_source_blob_sha']!=BLOB:
   raise ValueError('Missing source provenance '+sid)
  if ('…' in p)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
   raise ValueError('Pāli source ellipsis classification incorrect '+sid)
  if method=='SOURCE_ELLIPSIS_UNEXPANDED' and 'မချဲ့ရသေး' not in r['translation_draft']:
   raise ValueError('Source ellipsis requires visible warning '+sid)
  if method=='CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' and not r['translation_draft'].startswith('အဓိပ္ပာယ်အနှစ်ချုပ်'):
   raise ValueError('Contextual summary requires visible warning '+sid)
  counts[method]+=1
 if seen!=set(original) or dict(counts)!=METHODS:
  raise ValueError('MN25 classification must be 162+12+25')
 if combined_db:
  db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('pragma integrity_check').fetchone()[0]!='ok':raise ValueError('Combined SQLite corrupt')
   if dict(db.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!={f'mn{i}':v for i,v in enumerate(COUNTS,1)}:
    raise ValueError('Combined MN1–MN25 4409 records missing or duplicated')
   if db.execute('select count(*) from pali_myanmar where approved!=0').fetchone()[0]:
    raise ValueError('Unapproved corpus contains approved records')
   for r in rows:
    x=db.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if x!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256']):
     raise ValueError('CSV vs SQLite mismatch '+r['segment_id'])
   if prior_db:
    pre=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     if pre.execute('select * from pali_myanmar order by segment_id').fetchall()!=db.execute("select * from pali_myanmar where sutta_uid!='mn25' order by segment_id").fetchall():
      raise ValueError('Prior MN1–MN24 rows were modified')
    finally:pre.close()
  finally:db.close()
 return {'source_segments':199,'direct_AI_drafts':162,'contextual_summaries':12,
  'source_ellipses_unexpanded':25,'total_drafts':4409 if combined_db else None,
  'scholar_approved':0,'MCU_45_original_volumes_verified':0,'native_APK_built':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--source-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args();print(json.dumps(check(a.csv,a.source_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
