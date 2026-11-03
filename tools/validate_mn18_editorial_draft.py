#!/usr/bin/env python3
"""MN18 Madhupindika editorial draft QA. No MCU-edition, scholar or APK claim."""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
BLOB='086ac27259da3768455d8c793cbc1079ea73c597'
SOURCE='sutta/mn/mn18_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
ELLIPSIS={'mn18:10.5','mn18:11.6','mn18:11.12','mn18:15.3','mn18:16.2','mn18:16.3','mn18:16.4','mn18:16.5','mn18:17.6','mn18:17.7','mn18:17.8','mn18:17.9','mn18:18.6','mn18:18.7','mn18:18.8','mn18:18.9','mn18:19.2','mn18:20.5'}
LONG={'mn18:4.1','mn18:6.11','mn18:8.3','mn18:11.16','mn18:12.3','mn18:16.1','mn18:16.6','mn18:20.11','mn18:20.15'}
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':123,'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':9,'SOURCE_ELLIPSIS_UNEXPANDED':18}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144,'mn15':263,'mn16':83,'mn17':83,'mn18':150}
def validate(csv_file,original_json,combined_db=None,prior_db=None):
 src=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
 if not isinstance(src,dict) or len(src)!=150 or not all(k.startswith('mn18:') for k in src):raise ValueError('150 source segments required')
 raw=json.dumps(src,ensure_ascii=False,indent=2).encode()
 blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if blob!=BLOB:raise ValueError('Pinned original source Git blob mismatch')
 with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError('Draft CSV schema mismatch')
  rows=list(reader)
 if len(rows)!=150:raise ValueError('150 draft records required')
 ids=set();methods=Counter()
 for r in rows:
  sid=r['segment_id'];p=r['pali']
  if sid in ids or sid not in src or r['sutta_uid']!='mn18':raise ValueError('Source ID invalid/duplicate')
  ids.add(sid)
  if p!=src[sid] or hashlib.sha256(p.encode()).hexdigest()!=r['source_sha256']:raise ValueError('Source Pali/hash differs: '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():raise ValueError('Missing Burmese draft: '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():raise ValueError('No auto-approval: '+sid)
  if r['source_path']!=SOURCE or r['published_source_blob_sha']!=BLOB:raise ValueError('Provenance mismatch: '+sid)
  if ('…' in p)!=(sid in ELLIPSIS):raise ValueError('Original abbreviation inventory differs: '+sid)
  m=r['translation_method']
  expected='SOURCE_ELLIPSIS_UNEXPANDED' if sid in ELLIPSIS else 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' if sid in LONG else 'SEGMENT_ALIGNED_AI_DRAFT'
  if m!=expected:raise ValueError('Review classification mismatch: '+sid)
  if sid in ELLIPSIS and 'မချဲ့ရသေး' not in r['translation_draft']:raise ValueError('Abbreviation must stay explicit: '+sid)
  methods[m]+=1
 if ids!=set(src) or dict(methods)!=METHODS:raise ValueError('MN18 123+9+18 count mismatch')
 if combined_db:
  d=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if d.execute('pragma integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite corrupt')
   if dict(d.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!=COUNTS:raise ValueError('MN1-MN18 3171 rows required')
   if d.execute('select count(*) from pali_myanmar where approved!=0').fetchone()[0]:raise ValueError('Unreviewed corpus auto-approved')
   for r in rows:
    x=d.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if x!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256']):raise ValueError('CSV/SQLite mismatch '+r['segment_id'])
   if prior_db:
    p=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     old=p.execute('select * from pali_myanmar order by segment_id').fetchall()
     new=d.execute("select * from pali_myanmar where sutta_uid!='mn18' order by segment_id").fetchall()
     if len(old)!=3021 or old!=new:raise ValueError('Prior MN1-MN17 rows changed')
    finally:p.close()
  finally:d.close()
 return {'MN18_source':150,'Myanmar_draft_rows':150,'source_abbreviations':18,'long_passage_reviews':9,'combined_rows':3171 if combined_db else None,'scholar_approved':0,'MCU_verified_original_books':0,'signed_APK':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db');a=p.parse_args()
 print(json.dumps(validate(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
