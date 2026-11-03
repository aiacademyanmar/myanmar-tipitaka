#!/usr/bin/env python3
"""MN20 Vitakkasaṇṭhānasutta Pāli/Burmese AI-DRAFT gate, not scholar approval."""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path
SOURCE_BLOB='f423bcb2f52610f3a4a19b81b3329a424c19eb7a'
SOURCE_PATH='sutta/mn/mn20_root-pli-ms.json'
FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft','section','topic','draft_status','translation_method','source_sha256','source_path','source_commit','published_source_blob_sha','approved','reviewer','source_url']
ELLIPSES=set()
REVIEW_IDS={'mn20:3.1','mn20:3.5','mn20:4.1','mn20:4.6','mn20:5.6','mn20:6.1','mn20:7.2','mn20:8.1'}
COUNTS={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132,'mn12':372,'mn13':152,'mn14':144,'mn15':263,'mn16':83,'mn17':83,'mn18':150,'mn19':123,'mn20':87}
METHODS={'CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW':8,'SEGMENT_ALIGNED_AI_DRAFT':79}
def check(csv_file,original_json,combined_db=None,prior_db=None):
    source=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
    if not isinstance(source,dict) or len(source)!=87 or any(not x.startswith('mn20:') for x in source):
        raise ValueError('MN20 requires 87 unique original source segment IDs')
    raw=json.dumps(source,ensure_ascii=False,indent=2).encode()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob!=SOURCE_BLOB:raise ValueError('Published MN20 source Git Blob SHA mismatch')
    with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError('Unexpected CSV editorial fields')
        rows=list(reader)
    if len(rows)!=87:raise ValueError('MN20 requires 87 source-linked drafts')
    seen=set();methods=Counter()
    for row in rows:
        sid=row['segment_id'];pali=row['pali'];method=row['translation_method']
        if sid in seen or sid not in source or row['sutta_uid']!='mn20':
            raise ValueError('Duplicate or foreign MN20 segment ID')
        seen.add(sid)
        if source[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=row['source_sha256']:
            raise ValueError('Original Pāli text/SHA256 tampered: '+sid)
        if not row['translation_draft'].strip() or not row['explanation_draft'].strip():
            raise ValueError('Missing Burmese draft text: '+sid)
        if row['draft_status']!='AI_DRAFT_UNREVIEWED' or row['approved']!='0' or row['reviewer'].strip():
            raise ValueError('No AI editorial draft may be auto-approved: '+sid)
        if row['source_path']!=SOURCE_PATH or row['published_source_blob_sha']!=SOURCE_BLOB or len(row['source_commit'])!=40:
            raise ValueError('Missing original source provenance: '+sid)
        if ('…' in pali)!=(sid in ELLIPSES):
            raise ValueError('Unexpected Pāli abbreviation inventory: '+sid)
        if (sid in ELLIPSES)!=(method=='SOURCE_ELLIPSIS_UNEXPANDED'):
            raise ValueError('Pāli ellipsis must remain visibly unexpanded: '+sid)
        if sid in ELLIPSES and 'မချဲ့ရသေး' not in row['translation_draft']:
            raise ValueError('Unexpanded original must be visibly marked in Burmese: '+sid)
        expected_method='CONTEXTUAL_SUMMARY_REQUIRES_LITERAL_REVIEW' if sid in REVIEW_IDS else 'SEGMENT_ALIGNED_AI_DRAFT'
        if method!=expected_method:raise ValueError('MN20 method review flag mismatch: '+sid)
        methods[method]+=1
    if seen!=set(source) or dict(methods)!=METHODS:
        raise ValueError('MN20 79 direct/8 literal-review method inventory mismatch')
    if combined_db:
        combined=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
        try:
            if combined.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('SQLite integrity_check failed')
            if dict(combined.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))!=COUNTS:
                raise ValueError('Expected combined 3381 rows in MN1–MN20')
            if combined.execute('SELECT COUNT(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
                raise ValueError('Scholar-approved flags unexpectedly set')
            for r in rows:
                found=combined.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,draft_status,source_sha256 FROM pali_myanmar WHERE segment_id=?',(r['segment_id'],)).fetchone()
                if found!=(r['pali'],r['translation_draft'],r['explanation_draft'],'AI_DRAFT_UNREVIEWED',r['source_sha256']):
                    raise ValueError('Combined SQLite differs from MN20 CSV: '+r['segment_id'])
            if prior_db:
                previous=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
                try:
                    old=previous.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
                    new=combined.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn20' ORDER BY segment_id").fetchall()
                    if len(old)!=3294 or old!=new:raise ValueError('Prior 3294 records changed')
                finally:previous.close()
        finally:combined.close()
    return {'source_rows':87,'working_translation_drafts':87,'working_explanations':87,'direct_drafts':79,'long_literal_review_required':8,'unexpanded_source_abbreviations':0,'combined_draft_rows':3381 if combined_db else None,'scholar_approved':0,'MCU_45_verified_volumes':0,'signed_native_APK':False}
if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
    p.add_argument('--combined-db');p.add_argument('--prior-db');a=p.parse_args()
    print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
