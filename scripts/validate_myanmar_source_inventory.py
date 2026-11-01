#!/usr/bin/env python3
"""Validate the V2.3.5.4 source inventory without upgrading candidates to approved sources."""
import csv,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
inv=ROOT/"corpus/myanmar_translation_source_inventory.csv"
cov=ROOT/"corpus/45_volume_myanmar_source_coverage.csv"
required={"source_id","publisher","source_title","source_type","language","coverage_scope","available_format","source_url","rights_status","reuse_decision","technical_notes","next_action"}
with inv.open(encoding="utf-8-sig",newline="") as f:
 rows=list(csv.DictReader(f))
if len(rows)<8:sys.exit(f"Expected at least 8 source candidates; found {len(rows)}")
if not required.issubset(rows[0]):sys.exit("Source inventory schema incomplete")
ids=[r["source_id"] for r in rows]
if len(ids)!=len(set(ids)):sys.exit("Duplicate source_id")
for r in rows:
 if not r["source_url"].startswith("https://"):sys.exit("Non-HTTPS source URL: "+r["source_id"])
 if not r["rights_status"].strip() or not r["reuse_decision"].strip():sys.exit("Missing rights gate: "+r["source_id"])
 if r["reuse_decision"] not in {"CATALOG_ONLY_PERMISSION_REQUIRED","ONLINE_REFERENCE_ONLY_PERMISSION_REQUIRED","PDF_REFERENCE_ONLY_PERMISSION_REQUIRED","LINK_ONLY_PERMISSION_REQUIRED","DISCOVERY_ONLY_PERMISSION_REQUIRED","REFERENCE_METADATA_ONLY","REFERENCE_ONLY_CONTACT_LIBRARY","AI_DRAFT_REFERENCE_ONLY","PALI_REFERENCE_ONLY","PALI_IMAGE_REFERENCE_ONLY"}:
  sys.exit("Unrecognized reuse decision: "+r["source_id"])
with cov.open(encoding="utf-8-sig",newline="") as f: volumes=list(csv.DictReader(f))
if len(volumes)!=45:sys.exit(f"Expected 45 volume source rows; found {len(volumes)}")
if [int(r["volume_id"]) for r in volumes]!=list(range(1,46)):sys.exit("Volume source map must be ordered 1..45")
if any(r["coverage_status"]!="CATEGORY_CANDIDATE_ONLY" for r in volumes):sys.exit("Do not promote source category candidates to verified book coverage")
print(f"PASS: {len(rows)} source candidates; {len(volumes)} volume mapping rows; rights gates preserved; no source promoted to verified.")
