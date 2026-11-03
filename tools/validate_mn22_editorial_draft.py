#!/usr/bin/env python3
"""MN22 Alagaddūpamasutta editorial QA; structural only, no scholar approval."""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path
from collections import Counter
SOURCE_BLOB='07e7677d245aa40846239954aaf6acde8dd3e618'
SOURCE_PATH='sutta/mn/mn22_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
METHODS={'SEGMENT_ALIGNED_AI_DRAFT':329,'SOURCE_ELLIPSIS_UNEXPANDED':30}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144,'mn15':263,'mn16':83,'mn17':83,'mn18':150,'mn19':123,'mn20':87,'mn21':227,'mn22':359}
def check(csv_file,original_json,combined_db=None,prior_db=None):
 src=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
 if not isinstance(src,dict) or len(src)!=359 or any(not sid.startswith('mn22:') for sid in src):
  raise ValueError('MN22 source needs exactly 359 segment IDs')
 raw=json.dumps(src,ensure_ascii=False,indent=2).encode()
 blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if blob!=SOURCE_BLOB:raise ValueError('MN22 published Pāli source Git Blob SHA mismatch')
 if sum('…' in pali for pali in src.values())!=30:raise ValueError('MN22 30 abbreviations changed')
 with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  if reader.fieldnames!=FIELDS:raise ValueError('MN22 CSV schema changed')
  rows=list(reader)
 if len(rows)!=359:raise ValueError('MN22 needs 359 Burmese drafts')
 seen=set();methods=Counter()
 for r in rows:
  sid=r['segment_id'];pali=r['pali']
  if sid in seen or sid not in src or r['sutta_uid']!='mn22':
   raise ValueError('Duplicate/foreign source segment '+sid)
  seen.add(sid)
  if pali!=src[sid] or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:
   raise ValueError('Pāli source text/SHA mismatch '+sid)
  if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
   raise ValueError('Missing Burmese editorial draft '+sid)
  if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():
   raise ValueError('No false approval of unreviewed draft '+sid)
  if r['source_path']!=SOURCE_PATH or r['published_source_blob_sha']!=SOURCE_BLOB:
   raise ValueError('Source provenance changed '+sid)
  method=r['translation_method']
  if ('…' in pali)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
   raise ValueError('Source ellipsis flag wrong '+sid)
  if method=='SOURCE_ELLIPSIS_UNEXPANDED' and 'မချဲ့ရသေး' not in r['translation_draft']:
   raise ValueError('Source ellipse must show review warning '+sid)
  methods[method]+=1
 if seen!=set(src) or dict(methods)!=METHODS:
  raise ValueError('MN22 editorial review inventory changed')
 if combined_db:
  db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
  try:
   if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity failure')
   if dict(db.execute('select sutta_uid,count(*) from pali_myanmar group by sutta_uid'))!=COUNTS:
    raise ValueError('MN1-MN22 3967 combined corpus counts changed')
   if db.execute('select count(*) from pali_myanmar where approved!=0').fetchone()[0]:
    raise ValueError('Unreviewed corpus contains approved entries')
   for r in rows:
    v=db.execute('select source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,translation_method from pali_myanmar where segment_id=?',(r['segment_id'],)).fetchone()
    if v!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256'],r['translation_method']):
     raise ValueError('CSV to SQLite mismatch '+r['segment_id'])
   if prior_db:
    pre=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
    try:
     old=pre.execute('select * from pali_myanmar order by segment_id').fetchall()
     new=db.execute("select * from pali_myanmar where sutta_uid!='mn22' order by segment_id").fetchall()
     if len(old)!=3608 or old!=new:raise ValueError('Previous 3608 records changed')
    finally:pre.close()
  finally:db.close()
 return {'MN22_source_rows':359,'Burmese_AI_draft_rows':359,'direct_drafts':329,
  'original_ellipses_unexpanded':30,'combined_rows':3967 if combined_db else None,
  'human_approved':0,'MCU_45_original_verified':0,'signed_APK_ready':False}
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
 p.add_argument('--combined-db');p.add_argument('--prior-db')
 a=p.parse_args()
 print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
