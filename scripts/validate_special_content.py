#!/usr/bin/env python3
"""Audit special-study datasets without treating drafts as approved translations."""
import csv,json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
errors=[];report={}
# Dhammapada draft coverage: only count explicit AI draft rows, never call them approved.
draft_files=[
 "corpus/dhammapada_yamakavagga_my_drafts.csv",
 "corpus/dhammapada_draft_21_99.csv",
 "corpus/dhammapada_draft_100_145.csv",
 "corpus/dhammapada_draft_146_196.csv",
 "corpus/dhammapada_draft_197_234.csv",
 "corpus/dhammapada_draft_235_305.csv",
 "corpus/dhammapada_draft_306_359.csv",
 "corpus/dhammapada_draft_360_423.csv"]
verses={}
for name in draft_files:
 p=ROOT/name
 if not p.is_file():continue
 with p.open(encoding="utf-8-sig",newline="") as f:
  for line,row in enumerate(csv.DictReader(f),2):
   try:n=int(row["verse"])
   except Exception:errors.append(f"{name}:{line}: invalid verse");continue
   if n<1 or n>423 or n in verses:errors.append(f"{name}:{line}: invalid or duplicate verse {n}");continue
   if row.get("status")!="ai_draft_unreviewed" or not row.get("translation_my","").strip():
    errors.append(f"{name}:{line}: draft status/text missing")
   verses[n]=name
report["dhammapada"]={"expected_verses":423,"expected_vaggas":26,"draft_translation_rows":len(verses),
 "verses_without_draft":423-len(verses),"drafts_approved":0,"status":"DRAFT_ONLY"}
# Maṅgala content: count all 38 draft items and 13 source stanzas.
p=ROOT/"corpus/mangala_sutta_38_my_drafts.json"
if p.is_file():
 data=json.loads(p.read_text(encoding="utf-8"))
 items=[x for g in data.get("groups",[]) for x in g.get("items",[])]
 stanzas=data.get("pali_stanzas",[])
 nums=[x.get("number") for x in items]
 if len(items)!=38 or nums!=list(range(1,39)):errors.append("Maṅgala: expected blessings 1..38 exactly once")
 if len(stanzas)!=13 or [x.get("stanza") for x in stanzas]!=list(range(1,14)):errors.append("Maṅgala: expected Pāli stanzas 1..13")
 report["mangala"]={"blessings":len(items),"pali_stanzas":len(stanzas),"groups":len(data.get("groups",[])),
  "translation_status":"DRAFT","explanation_status":"DRAFT","approved_count":0}
else:errors.append("Missing Maṅgala source JSON")
# Nibbāna: manifest is study-topic catalog, not a full Pāli passage corpus.
p=ROOT/"app/src/main/assets/nibbana_my.json"
if p.is_file():
 data=json.loads(p.read_text(encoding="utf-8"))
 topics=data.get("topics",[])
 if len(topics)!=12:errors.append("Nibbāna: expected 12 study topics")
 report["nibbana"]={"topics":len(topics),"sources":len(data.get("sources",[])),
  "translation_status":"NOT_REVIEWED","explanation_status":"DRAFT","offline_passage_corpus":"NOT_COMPLETE"}
else:errors.append("Missing Nibbāna study JSON")
# Satipaṭṭhāna catalogue placeholder explicitly states source requirements; no fabricated content.
p=ROOT/"content/satipatthana_manifest.json"
if p.is_file():
 data=json.loads(p.read_text(encoding="utf-8"))
 report["satipatthana"]={"catalogue_status":data.get("content_status"),"source_refs":data.get("source_refs",[]),
  "translation_status":data.get("translation_status"),"explanation_status":data.get("explanation_status")}
else:errors.append("Missing Satipaṭṭhāna manifest")
report["errors"]=errors
out=ROOT/"content/special_content_audit.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report,ensure_ascii=False,indent=2))
if errors:sys.exit(1)
