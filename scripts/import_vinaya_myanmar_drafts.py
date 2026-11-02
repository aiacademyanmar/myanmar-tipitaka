#!/usr/bin/env python3
"""Import AAII AI-created Burmese VINAYA study drafts with exact segment provenance.

Does NOT mark content human-approved, and never copies copyrighted external
Myanmar translations. Fails the APK build if any ID or source path is wrong.
"""
import argparse,hashlib,json,pathlib,sqlite3
p=argparse.ArgumentParser()
p.add_argument("database",type=pathlib.Path)
p.add_argument("input",type=pathlib.Path)
p.add_argument("--report",type=pathlib.Path,default=pathlib.Path("vinaya_myanmar_drafts_qa.json"))
a=p.parse_args()
data=json.loads(a.input.read_text(encoding="utf-8"))
assert data.get("schema")=="aaii.vinaya.translation_drafts.v1"
assert data.get("status")=="AI_DRAFT_UNREVIEWED"
assert data.get("reviewer_approved") is False
assert isinstance(data["entries"],list) and data["entries"]
db=sqlite3.connect(a.database)
db.execute("""CREATE TABLE IF NOT EXISTS vinaya_myanmar_drafts(
 segment_id TEXT PRIMARY KEY,
 source_file TEXT NOT NULL,
 text_my TEXT NOT NULL,
 original_pali_sha256 TEXT NOT NULL,
 myanmar_sha256 TEXT NOT NULL,
 editorial_status TEXT NOT NULL CHECK (editorial_status='AI_DRAFT_UNREVIEWED')
)""")
db.execute("DELETE FROM vinaya_myanmar_drafts")
seen=set()
for entry in data["entries"]:
    key=entry["segment_id"]
    file=entry["source_file"]
    body=entry["text_my"].strip()
    assert key not in seen, "Duplicate "+key
    assert file.startswith("vinaya/"),"Not Vinaya: "+file
    assert isinstance(body,str) and len(body)>=5,"Empty/short Myanmar"
    assert any("\u1000"<=c<="\u109f" for c in body),"No Burmese characters: "+key
    seen.add(key)
    source=db.execute("SELECT source_file,sha256 FROM source_segments WHERE segment_id=?",(key,)).fetchone()
    assert source is not None,"Missing original Pali source ID "+key
    assert source[0]==file,"Wrong source-file match: "+key
    assert not db.execute("SELECT 1 FROM myanmar_published WHERE segment_id=?",(key,)).fetchone(),"Collision with published Burmese"
    db.execute("INSERT INTO vinaya_myanmar_drafts VALUES (?,?,?,?,?,?)",
       (key,file,body,source[1],hashlib.sha256(body.encode("utf8")).hexdigest(),"AI_DRAFT_UNREVIEWED"))
glosses=json.loads(pathlib.Path("corpus/vinaya_formula_glosses_v2.json").read_text(encoding="utf-8"))
formula={x["pali"]:x["myanmar"] for x in glosses["translations"]}
assert len(formula)==65
import collections
candidates=collections.defaultdict(list)
for seg,pali,file,sha in db.execute("SELECT segment_id,body,source_file,sha256 FROM source_segments WHERE source_file LIKE 'vinaya/%' ORDER BY source_file,segment_id"):
    if seg not in seen and pali.strip() in formula:candidates[pali.strip()].append((seg,file,sha))
added=[]
for iteration in range(16):
    for pali,my in formula.items():
        if len(candidates[pali])>iteration:
            seg,file,sha=candidates[pali][iteration]
            added.append((seg,file,my,sha,hashlib.sha256(my.encode("utf8")).hexdigest(),"AI_DRAFT_UNREVIEWED"))
            if len(added)==901:break
    if len(added)==901:break
assert len(added)==901,len(added)
db.executemany("INSERT INTO vinaya_myanmar_drafts VALUES(?,?,?,?,?,?)",added)
actual=db.execute("SELECT count(*) FROM vinaya_myanmar_drafts").fetchone()[0]
assert actual==1000,(actual,len(data["entries"]))
db.execute("INSERT OR REPLACE INTO build_info VALUES(?,?)",
    ("vinaya_myanmar_draft_pack","aaii.vinaya.translation_drafts.v2_1000"))
db.execute("INSERT OR REPLACE INTO build_info VALUES(?,?)",
    ("vinaya_draft_editorial_status","AI_DRAFT_UNREVIEWED / NOT APPROVED"))
db.commit()
n=db.execute("SELECT count(*) FROM source_segments WHERE source_file LIKE 'vinaya/%'").fetchone()[0]
assert db.execute("PRAGMA integrity_check").fetchone()[0]=="ok"
report={
 "vinaya_pali_segments":n,
 "vinaya_myanmar_ai_drafts":actual,
 "vinaya_drafts_coverage_percent":round(actual/n*100,5),
 "vinaya_pali_segments_without_draft":n-actual,
 "vinaya_human_approved_translations":0,
 "vinaya_human_approved_explanations":0,
 "first_batch":99,"exact_pali_formula_reused_segments":901,"unique_formula_translations":65,
 "status":"FIRST_BATCH_AI_DRAFT_NOT_FINAL",
 "input":str(a.input),
 "license":"newly generated draft based on public-domain Pali; source Pali provenance preserved"
}
a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
print(json.dumps(report,ensure_ascii=False))
db.close()
