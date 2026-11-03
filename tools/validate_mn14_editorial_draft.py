#!/usr/bin/env python3
"""MN14 Cūḷadukkhakkhandhasutta: fail-closed source-aligned draft QA.

Does NOT certify Burmese translation quality, MCU edition or offline APK release.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
COLUMNS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','section_id','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
METHODS={'SEGMENT_LEVEL_WORKING_TRANSLATION':130,'SOURCE_ELLIPSIS_UNEXPANDED':13,'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':1}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144}
BLOB='7f38297154a85f06f97980d54b5b65a34f959e1d'
EXPECTED_SOURCE_CHARS=14940
EXPECTED_SOURCE_ROLLING=106229723
def validate(csv_file,original_json,combined_db=None,prior_db=None):
 source=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
 if not isinstance(source,dict) or len(source)!=144 or not all(k.startswith('mn14:') for k in source):
  raise ValueError('Original MN14 source must have 144 IDs')
 s=json.dumps(list(source.items()),ensure_ascii=False,separators=(',',':'))
 check=0
 for char in s:check=(check*131+ord(char))%1000000007
 if (len(s),check)!=(EXPECTED_SOURCE_CHARS,EXPECTED_SOURCE_ROLLING):raise ValueError('Source content checksum mismatch')
 with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=COLUMNS:raise ValueError('CSV schema mismatch')
  rows=list(reader)
 if len(rows)!=144:raise ValueError('MN14 requires exactly 144 records')
 seen=set();methods=Counter()
 for r in rows:
  sid=r['segment_id'];pali=r['pali'];method=r['translation_method']
  if sid not in source or sid in seen or r['sutta_uid']!='mn14':
   raise ValueError('Invalid/duplicate MN14 source segment')
  seen.add(sid)
  if source[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:
   raise ValueError('Pāli source/SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('Empty Myanmar editorial draft '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():
   raise ValueError('Draft cannot be auto-approved '+sid)
  if r['source_path']!='sutta/mn/mn14_root-pli-ms.json' or r['published_source_blob_sha']!=BLOB:
   raise ValueError('Original source provenance mismatch '+sid)
  if ('…' in pali)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
   raise ValueError('Unexpanded original Pāli not flagged '+sid)
  if method=='SOURCE_ELLIPSIS_UNEXPANDED' and 'မချဲ့ရသေး' not in r['translation_draft']:
   raise ValueError('Source abbreviation must remain explicit '+sid)
  if method=='CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW' and sid!='mn14:13.3':
   raise ValueError('Unexpected summary classification '+sid)
  methods[method]+=1
 if seen!=set(source) or dict(methods)!=METHODS:raise ValueError('Review queue 13+1 changed')
 if combined_db:
  conn=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if conn.execute('pragma integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite corrupt')
   if dict(conn.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!=COUNTS:
    raise ValueError('Combined 2,592-row sutta counts mismatch')
   if conn.execute('select count(*) from pali_myanmar where approved!=0').fetchone()[0]:
    raise ValueError('Draft corpus marked approved')
   for r in rows:
    q=conn.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if q!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256']):
     raise ValueError('CSV ↔ SQLite mismatch '+r['segment_id'])
   if prior_db:
    p=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     if p.execute('select * from pali_myanmar order by segment_id').fetchall()!=conn.execute("select * from pali_myanmar where sutta_uid!='mn14' order by segment_id").fetchall():
      raise ValueError('Prior MN1-MN13 rows changed')
    finally:p.close()
  finally:conn.close()
 return {'source_segments':144,'Burmese_translation_drafts':144,'Burmese_explanation_drafts':144,
  'source_abbreviations_unexpanded':13,'long_summaries':1,
  'combined_segments':2592 if combined_db else None,
  'human_approved':0,'MCU_verified':0,'APK_ready':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db');a=p.parse_args()
 print(json.dumps(validate(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
