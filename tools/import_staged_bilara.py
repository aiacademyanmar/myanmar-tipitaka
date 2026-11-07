#!/usr/bin/env python3
"""Import SHA256-pinned Bilara root Pali JSON staged in this repo.
Exact source segment strings only. MCU crosswalk and Myanmar approval remain BLOCKED.
"""
import argparse,hashlib,json,pathlib,sqlite3

SCHEMA='''
PRAGMA foreign_keys=ON;
CREATE TABLE corpus_meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE pali_documents(
 sutta_id TEXT PRIMARY KEY,source_path TEXT NOT NULL,
 source_blob_sha1 TEXT NOT NULL,source_sha256 TEXT NOT NULL,segment_count INTEGER NOT NULL
);
CREATE TABLE pali_segments(
 source_segment_id TEXT PRIMARY KEY,
 sutta_id TEXT NOT NULL REFERENCES pali_documents(sutta_id),
 sequence_no INTEGER NOT NULL,pali_original TEXT NOT NULL,pali_sha256 TEXT NOT NULL,
 translation_my_draft TEXT,explanation_my_draft TEXT,
 review_status TEXT NOT NULL DEFAULT 'untranslated'
 CHECK(review_status IN ('untranslated','draft_unapproved')),
 UNIQUE(sutta_id,sequence_no)
);
CREATE VIRTUAL TABLE pali_fts USING fts5(source_segment_id UNINDEXED,pali_original,tokenize='unicode61');
CREATE TABLE mcu_45_volumes(
 volume INTEGER PRIMARY KEY CHECK(volume BETWEEN 1 AND 45),
 division TEXT NOT NULL,verified INTEGER NOT NULL DEFAULT 0 CHECK(verified=0)
);
CREATE INDEX ix_segments_sutta ON pali_segments(sutta_id,sequence_no);
'''

def build(root,sqlite_file,report_file):
 root=pathlib.Path(root);sqlite_file=pathlib.Path(sqlite_file);report_file=pathlib.Path(report_file)
 cursor=json.loads((root/'IMPORT_CURSOR.json').read_text(encoding='utf-8'))
 items=cursor['staged_items']
 if not items or len({x['sutta_id'] for x in items})!=len(items):
  raise ValueError('Bad or duplicate staged source manifest')
 sqlite_file.parent.mkdir(parents=True,exist_ok=True)
 report_file.parent.mkdir(parents=True,exist_ok=True)
 temp=sqlite_file.with_suffix(sqlite_file.suffix+'.partial')
 if temp.exists():temp.unlink()
 db=sqlite3.connect(temp)
 try:
  db.executescript(SCHEMA)
  total=0
  for item in items:
   sid=item['sutta_id'];path=root/(sid+'_root-pli-ms.json')
   raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
   if sha!=item['source_utf8_sha256']:raise ValueError('Source SHA mismatch: '+sid)
   data=json.loads(raw.decode('utf-8-sig'))
   if not isinstance(data,dict) or len(data)!=item['segment_count']:
    raise ValueError('Segment count mismatch: '+sid)
   if any(not x.startswith(sid+':') or not isinstance(v,str) or not v.strip() for x,v in data.items()):
    raise ValueError('Bad source segment: '+sid)
   db.execute('INSERT INTO pali_documents VALUES (?,?,?,?,?)',
    (sid,path.name,item['source_blob_sha1'],sha,len(data)))
   for index,(seg,pali) in enumerate(data.items(),1):
    db.execute('INSERT INTO pali_segments(source_segment_id,sutta_id,sequence_no,pali_original,pali_sha256) VALUES (?,?,?,?,?)',
     (seg,sid,index,pali,hashlib.sha256(pali.encode('utf-8')).hexdigest()))
    db.execute('INSERT INTO pali_fts VALUES(?,?)',(seg,pali))
    total+=1
  if total!=cursor['staged_source_segments']:raise ValueError('Cursor total mismatch')
  for n in range(1,46):
   db.execute('INSERT INTO mcu_45_volumes(volume,division) VALUES (?,?)',
    (n,'vinaya' if n<=8 else 'sutta' if n<=33 else 'abhidhamma'))
  for k,v in {'edition':'SuttaCentral Bilara published Mahasangiti Roman Pali',
   'last_staged_sutta':cursor['last_staged_sutta'],
   'next_unstaged_sutta':cursor['next_unstaged_sutta'],
   'mcu_crosswalk':'UNVERIFIED','rights_review':'PENDING',
   'approved_myanmar_translation':'0','production_release':'BLOCKED'}.items():
   db.execute('INSERT INTO corpus_meta VALUES(?,?)',(k,v))
  db.commit()
  integrity=db.execute('PRAGMA integrity_check').fetchone()[0]
  fk=db.execute('PRAGMA foreign_key_check').fetchall()
  fts=db.execute('SELECT COUNT(*) FROM pali_fts').fetchone()[0]
  docs=db.execute('SELECT COUNT(*) FROM pali_documents').fetchone()[0]
  if integrity!='ok' or fk or fts!=total or docs!=len(items):
   raise RuntimeError('SQLite QA failed')
  db.execute('VACUUM');db.close();temp.replace(sqlite_file)
  report={'source':'GitHub-staged Bilara published exact root Pali','suttas':docs,
   'segments':total,'source_sha256_verified_files':docs,'sqlite_integrity':integrity,
   'foreign_key_errors':0,'fts_segments':fts,'mcu_45_crosswalk_verified':0,
   'approved_myanmar_translations':0,'source_rights_review':'PENDING',
   'production_release':'BLOCKED','sqlite_bytes':sqlite_file.stat().st_size,
   'sqlite_sha256':hashlib.sha256(sqlite_file.read_bytes()).hexdigest()}
  report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  return report
 except BaseException:
  db.close()
  if temp.exists():temp.unlink()
  raise

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--root',required=True)
 p.add_argument('--db',required=True)
 p.add_argument('--report',required=True)
 a=p.parse_args()
 print(json.dumps(build(a.root,a.db,a.report),ensure_ascii=False,indent=2))
