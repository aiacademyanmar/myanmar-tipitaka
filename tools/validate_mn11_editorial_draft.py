#!/usr/bin/env python3
"""MN11 Culasihanada source-aligned UNREVIEWED Myanmar editorial draft gate.

This checks structural/data integrity only. It cannot certify Burmese translation
meaning, independent MCU 45-volume edition equivalence, rights, or APK release.
"""
import argparse,csv,hashlib,json,sqlite3
from pathlib import Path

HEADERS=['segment_id','sutta_uid','pali','translation_draft','explanation_draft',
'section','topic','draft_status','translation_method','source_sha256',
'source_path','source_commit','approved','reviewer','source_url']
EXPECTED={'mn1':334,'mn2':125,'mn3':128,'mn4':165,'mn5':203,'mn6':51,
          'mn7':147,'mn8':170,'mn9':234,'mn10':235,'mn11':132}
DIRECT='SEGMENT_ALIGNED_AI_TRANSLATION_DRAFT'
LONG='LONG_PASSAGE_NEEDS_LITERAL_REVIEW'
METHODS={DIRECT:131,LONG:1}

def audit(csv_file,original_json,combined_db=None,prior_db=None):
    source=json.loads(Path(original_json).read_text(encoding='utf-8-sig'))
    if not isinstance(source,dict) or len(source)!=132 or any(not k.startswith('mn11:') for k in source):
        raise ValueError('MN11 expected original source has 132 segment IDs')
    with Path(csv_file).open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=HEADERS:raise ValueError('MN11 draft CSV schema mismatch')
        rows=list(reader)
    if len(rows)!=132:raise ValueError('MN11 requires exactly 132 draft rows')
    seen=set();methods={DIRECT:0,LONG:0}
    for row in rows:
        sid=row['segment_id'];pali=row['pali']
        if sid in seen or sid not in source or row['sutta_uid']!='mn11':
            raise ValueError('Duplicate or invalid MN11 source ID '+sid)
        seen.add(sid)
        if source[sid]!=pali or hashlib.sha256(pali.encode()).hexdigest()!=row['source_sha256']:
            raise ValueError('MN11 source content/SHA mismatch '+sid)
        if not row['translation_draft'].strip() or not row['explanation_draft'].strip():
            raise ValueError('Missing Burmese draft text '+sid)
        if row['draft_status']!='AI_DRAFT_UNREVIEWED' or row['approved']!='0' or row['reviewer'].strip():
            raise ValueError('Draft must never be auto-approved '+sid)
        if '…' in pali:raise ValueError('Unexpected original source abbreviation '+sid)
        method=row['translation_method']
        if method not in methods:raise ValueError('Unknown draft method')
        methods[method]+=1
        if method==LONG and len(pali.strip())<280:
            raise ValueError('False long-passage flag '+sid)
        if method==DIRECT and len(pali.strip())>=280:
            raise ValueError('Long-passage review flag missing '+sid)
        if not row['source_path'].endswith('mn11_root-pli-ms.json') or len(row['source_commit'])!=40:
            raise ValueError('Unpinned Mahasangiti original source '+sid)
    if seen!=set(source) or methods!=METHODS:
        raise ValueError('MN11 paragraph or manual review inventory mismatch')
    if combined_db:
        db=sqlite3.connect('file:'+str(Path(combined_db).resolve())+'?mode=ro',uri=True)
        try:
            if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise ValueError('MN1-MN11 combined SQLite corruption')
            counts=dict(db.execute('SELECT sutta_uid,count(*) FROM pali_myanmar GROUP BY sutta_uid'))
            if counts!=EXPECTED:raise ValueError('MN1-MN11 combined count mismatch')
            if db.execute('SELECT count(*) FROM pali_myanmar WHERE approved!=0').fetchone()[0]:
                raise ValueError('Combined unreviewed corpus has approved entries')
            for row in rows:
                found=db.execute('SELECT source_pali_roman,my_translation_draft,my_explanation_draft,source_sha256,draft_status FROM pali_myanmar WHERE segment_id=?',
                  (row['segment_id'],)).fetchone()
                if found!=(row['pali'],row['translation_draft'],row['explanation_draft'],
                          row['source_sha256'],'AI_DRAFT_UNREVIEWED'):
                    raise ValueError('MN11 CSV and SQLite disagree: '+row['segment_id'])
            if prior_db:
                prior=sqlite3.connect('file:'+str(Path(prior_db).resolve())+'?mode=ro',uri=True)
                try:
                    before=prior.execute('SELECT * FROM pali_myanmar ORDER BY segment_id').fetchall()
                    after=db.execute("SELECT * FROM pali_myanmar WHERE sutta_uid!='mn11' ORDER BY segment_id").fetchall()
                    if before!=after:raise ValueError('Previous MN1-MN10 1792 rows were changed')
                finally:prior.close()
        finally:db.close()
    return {'sutta':'mn11','Pali_source_rows':132,
            'Burmese_translation_drafts':132,'Burmese_explanation_drafts':132,
            'original_source_abbreviations':0,'long_passage_review_flags':1,
            'combined_draft_rows':1924 if combined_db else None,
            'human_approved_rows':0,'MCU_45_original_verified_volumes':0,
            'final_APK_release_ready':False}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--csv',required=True)
    p.add_argument('--original-json',required=True)
    p.add_argument('--combined-db')
    p.add_argument('--prior-db')
    a=p.parse_args()
    print(json.dumps(audit(a.csv,a.original_json,a.combined_db,a.prior_db),ensure_ascii=False,indent=2))
