#!/usr/bin/env python3
"""Regression tests for the reviewed Myanmar corpus importer."""
import csv
import hashlib
import importlib.util
import pathlib
import sqlite3
import tempfile
import unittest
from datetime import date

ROOT=pathlib.Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("merge_verified_myanmar",ROOT/"scripts/merge_verified_myanmar.py")
MODULE=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class ReviewedMyanmarImporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=pathlib.Path(self.tmp.name)
        self.db=sqlite3.connect(self.root/"test.sqlite")
        self.db.executescript("""
          CREATE TABLE paragraphs(id INTEGER PRIMARY KEY,segment_id TEXT UNIQUE,body TEXT);
          CREATE TABLE paragraph_explanations(
            paragraph_id INTEGER,language TEXT,explanation_my TEXT,source_ref TEXT,
            provenance TEXT,reviewed INTEGER,PRIMARY KEY(paragraph_id,language));
          INSERT INTO paragraphs VALUES(1,'dn1:1.1','Evaṃ me sutaṃ.');
        """)
        self.csv=self.root/"reviewed.csv"
        self.row={
          "segment_id":"dn1:1.1","content_type":"translation",
          "text_my":"ဤသို့ ကျွန်ုပ် ကြားနာခဲ့ရ၏။",
          "source_ref":"Rights-cleared Myanmar edition, page 1",
          "rights_evidence":"Written redistribution permission REF-001",
          "reviewer_1":"Reviewer A","reviewer_2":"Reviewer B",
          "review_reference":"Review record REV-001","reviewed_at":date.today().isoformat(),
          "source_pali_sha256":hashlib.sha256("Evaṃ me sutaṃ.".encode()).hexdigest()
        }
    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()
    def write(self,row):
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(MODULE.COLUMNS));w.writeheader();w.writerow(row)
    def test_imports_translation_and_explanation_separately(self):
        MODULE.create_table(self.db)
        self.write(self.row)
        self.assertEqual(MODULE.import_rows(self.db,self.csv),{"translation":1,"explanation":0})
        row=dict(self.row,content_type="explanation",text_my="ဤစာပိုဒ်၏ အနက်ကို ရှင်းလင်းဖော်ပြသည်။",
                 review_reference="Review record REV-002")
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.DictWriter(f,fieldnames=list(MODULE.COLUMNS));w.writeheader();w.writerow(row)
        self.assertEqual(MODULE.import_rows(self.db,self.csv),{"translation":0,"explanation":1})
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM paragraph_myanmar_content WHERE reviewed=1").fetchone()[0],2)
        self.assertEqual(self.db.execute("SELECT reviewed FROM paragraph_explanations").fetchone()[0],1)
    def test_rejects_wrong_pali_hash(self):
        MODULE.create_table(self.db)
        row=dict(self.row,source_pali_sha256="0"*64)
        self.write(row)
        with self.assertRaisesRegex(ValueError,"Pali SHA-256 mismatch"):
            MODULE.import_rows(self.db,self.csv)
    def test_rejects_same_reviewer(self):
        MODULE.create_table(self.db)
        row=dict(self.row,reviewer_2="Reviewer A")
        self.write(row)
        with self.assertRaisesRegex(ValueError,"two distinct reviewers"):
            MODULE.import_rows(self.db,self.csv)
    def test_rejects_invalid_hash_format(self):
        MODULE.create_table(self.db)
        row=dict(self.row,source_pali_sha256="not-a-hash")
        self.write(row)
        with self.assertRaisesRegex(ValueError,"64-character SHA-256"):
            MODULE.import_rows(self.db,self.csv)
    def test_rejects_missing_rights_evidence(self):
        MODULE.create_table(self.db)
        row=dict(self.row,rights_evidence="")
        self.write(row)
        with self.assertRaisesRegex(ValueError,"missing required review, rights, text or source field"):
            MODULE.import_rows(self.db,self.csv)

if __name__=="__main__":
    unittest.main(verbosity=2)
