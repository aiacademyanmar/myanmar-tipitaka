#!/usr/bin/env python3
"""MN12: 372 Mahasangiti Pali source-aligned, UNREVIEWED Myanmar draft gate.

The gate verifies source IDs, original hashes, review classification, and
optional combined SQLite structure. It does NOT certify Burmese semantic
accuracy, MCU-45 edition, source licensing, or production APK readiness.
"""
import argparse, csv, hashlib, json, sqlite3
from collections import Counter
from pathlib import Path
COLS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft',
      'section','topic','draft_status','translation_method','source_sha256',
      'source_path','source_commit','approved','reviewer','source_url']
EXPECTED={'SEGMENT_LEVEL_WORKING_TRANSLATION':256,
          'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':104,
          'SOURCE_ELLIPSIS_UNEXPANDED':12}
PRIOR={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,
       'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132}

def audit(csvfile,source_json,combined_db=None):
    source=json.loads(Path(source_json).read_text(encoding='utf-8-sig'))
    if not isinstance(source,dict) or len(source)!=372 or any(not k.startswith('mn12:') for k in source):
        raise ValueError('MN12 source must have exactly 372 segment IDs')
    with Path(csvfile).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=COLS:raise ValueError('Unexpected CSV columns')
        rows=list(reader)
    if len(rows)!=372:raise ValueError('Expected 372 Myanmar draft records')
    seen=set();methods=Counter();ellipses=0
    for r in rows:
        sid=r['segment_id'];pali=r['pali']
        if sid not in source or sid in seen or r['sutta_uid']!='mn12':
            raise ValueError('Wrong/duplicate source segment ID: '+sid)
        seen.add(sid)
        if pali!=source[sid] or hashlib.sha256(pali.encode()).hexdigest()!=r['source_sha256']:
            raise ValueError('Original Pali/hash mismatch: '+sid)
        if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
            raise ValueError('Missing Myanmar draft/explanation: '+sid)
        if r['draft_status']!='AI_DRAFT_UNREVIEWED' or r['approved']!='0' or r['reviewer'].strip():
            raise ValueError('No draft content can be auto-approved: '+sid)
        if not r['source_path'].endswith('mn12_root-pli-ms.json') or len(r['source_commit'])!=40:
            raise ValueError('Unpinned source provenance: '+sid)
        methods[r['translation_method']]+=1
        if '…' in pali:ellipses+=1
        if ('…' in pali)!=(r['translation_method']=='SOURCE_ELLIPSIS_UNEXPANDED'):
            raise ValueError('Unexpanded Pali source not flagged: '+sid)
    if seen!=set(source) or dict(methods)!=EXPECTED or ellipses!=12:
        raise ValueError('Editorial method counts or source inventory changed')
    if combined_db:
        c=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
        try:
            if c.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('Combined SQLite damaged')
            counts=dict(c.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))
            if counts!={**PRIOR,'mn12':372}:raise ValueError('MN1-MN12 count mismatch')
            if c.execute('SELECT count(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
                raise ValueError('Combined unreviewed draft has approved rows')
            for r in rows:
                found=c.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?',(r['segment_id'],)).fetchone()
                if found!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256']):
                    raise ValueError('CSV/SQLite mismatch: '+r['segment_id'])
        finally:c.close()
    return {'MN12_source':372,'working_translations':256,
            'contextual_summaries_not_literal':104,'original_abbreviations_unexpanded':12,
            'combined_draft_records':2296 if combined_db else None,'human_approved':0,
            'independently_verified_MCU_volumes':0,'release_ready':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',required=True)
    p.add_argument('--source-json',required=True)
    p.add_argument('--combined-db')
    args=p.parse_args()
    print(json.dumps(audit(args.csv,args.source_json,args.combined_db),indent=2))
