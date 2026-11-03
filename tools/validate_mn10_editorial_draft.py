#!/usr/bin/env python3
"""MN10 Satipatthana source-linked Burmese draft QA, NO scholar/MCU approval.

Inputs:
 --csv the segment draft file (235 source-linked rows)
 --original-json the pinned Mahasangiti Roman Pali source JSON
 --combined-db optional MN1-MN10 combined SQLite
 --prior-db optional MN1-MN9 combined SQLite (must be unchanged)

This script validates provenance, schema, source text, hashes, review flags and
read-only SQLite consistency. It does NOT validate semantic correctness.
"""
import argparse,csv,hashlib,json,sqlite3
from collections import Counter
from pathlib import Path

FIELDS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft',
'foundation','subsection','draft_status','translation_method','source_sha256',
'source_path','source_commit','approved','reviewer','source_url']
METHODS={'DIRECT_EDITORIAL_DRAFT':202,
 'CONTEXTUAL_SUMMARY_NEEDS_LITERAL_REVIEW':8,
 'SOURCE_ELLIPSIS_UNEXPANDED':25}
EXPECTED={'mn1':334,'mn2':125,'mn3':128,'mn4':165,
 'mn5':203,'mn6':51,'mn7':147,'mn8':170,'mn9':234,'mn10':235}
FOUNDATIONS={'intro':15,'kaya':79,'vedana':16,'citta':23,'dhamma':68,'conclusion':34}

def check(csv_file,original_file,combined_db=None,prior_db=None):
    original=json.loads(Path(original_file).read_text(encoding='utf-8-sig'))
    if not isinstance(original,dict) or len(original)!=235 or not all(k.startswith('mn10:') for k in original):
        raise ValueError('Incorrect MN10 original source inventory')
    with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError('MN10 CSV schema mismatch')
        rows=list(reader)
    if len(rows)!=235:raise ValueError('Exactly 235 source-linked draft rows required')
    seen=set();methods=Counter();foundations=Counter();abbreviated=0
    for r in rows:
        sid=r['segment_id']
        if sid in seen or sid not in original or r['sutta_uid']!='mn10':
            raise ValueError('Duplicate or missing MN10 segment ID')
        seen.add(sid)
        if r['pali']!=original[sid] or hashlib.sha256(r['pali'].encode()).hexdigest()!=r['source_sha256']:
            raise ValueError('Original Roman Pali text/hash mismatch: '+sid)
        if not r['translation_draft'].strip() or not r['explanation_draft'].strip():
            raise ValueError('Missing Burmese editorial text: '+sid)
        if r['draft_status']!='AI_DRAFT_UNREVIEWED' or str(r['approved'])!='0' or r['reviewer'].strip():
            raise ValueError('Cannot auto approve editorial drafts: '+sid)
        if r['source_path']!='sutta/mn/mn10_root-pli-ms.json' or len(r['source_commit'])!=40:
            raise ValueError('Missing pinned source provenance: '+sid)
        methods[r['translation_method']]+=1
        foundations[r['foundation']]+=1
        has_ellipsis='…' in r['pali']
        if has_ellipsis:abbreviated+=1
        if has_ellipsis!=(r['translation_method']=='SOURCE_ELLIPSIS_UNEXPANDED'):
            raise ValueError('Source abbreviation must remain unexpanded: '+sid)
    if seen!=set(original) or dict(methods)!=METHODS or dict(foundations)!=FOUNDATIONS or abbreviated!=25:
        raise ValueError('MN10 source or editorial review queue has changed')
    if combined_db:
        db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Combined SQLite corruption')
            found=dict(db.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))
            if found!=EXPECTED:raise ValueError('MN1-MN10 combined count mismatch')
            if db.execute('SELECT count(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
                raise ValueError('Unapproved draft data marked approved')
            for r in rows:
                actual=db.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256 FROM pali_myanmar WHERE segment_id=?',(r['segment_id'],)).fetchone()
                if actual!=(r['pali'],r['translation_draft'],r['explanation_draft'],r['source_sha256']):
                    raise ValueError('CSV-SQLite mismatch: '+r['segment_id'])
            if prior_db:
                pre=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
                try:
                    before=pre.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
                    after=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn10' ORDER BY segment_id").fetchall()
                    if before!=after:raise ValueError('Prior 1,557 rows changed during import')
                finally:pre.close()
        finally:db.close()
    return {'version':'MN10','source_segments':235,'editorial_draft_rows':235,
            'direct_working_drafts':202,'contextual_summaries':8,
            'unexpanded_original_abbreviations':25,
            'combined_drafts':1792 if combined_db else None,
            'human_approved':0,'verified_MCU_books':0,'release_ready':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',required=True);p.add_argument('--original-json',required=True)
    p.add_argument('--combined-db');p.add_argument('--prior-db')
    a=p.parse_args()
    print(json.dumps(check(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
