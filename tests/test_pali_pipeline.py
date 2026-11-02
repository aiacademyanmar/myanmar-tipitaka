"""Offline pipeline smoke test using synthetic fixtures only (NOT canonical Tipiṭaka)."""
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAKE_SHA = "a" * 40

class PipelineTest(unittest.TestCase):
    def test_import_review_and_export(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "root"
            source.mkdir()
            (source/"mn1.json").write_text(json.dumps({"mn1:1.1":"synthetic test segment"}), encoding="utf-8")
            mapping = base/"mapping.json"
            mapping.write_text('{"mn1":1}', encoding="utf-8")
            staged = base/"staging.sqlite"
            approved = base/"approved.sqlite"
            subprocess.run([sys.executable,str(ROOT/"tools/import_bilara_pali.py"),
                "--root",str(source),"--mapping",str(mapping),
                "--out",str(staged),"--source-commit",FAKE_SHA],
                check=True,capture_output=True,text=True)
            con=sqlite3.connect(staged)
            self.assertEqual(con.execute("SELECT review_status FROM pali_segments").fetchone()[0],"pending")
            # Explicitly simulate a human review in this isolated test fixture.
            con.execute("UPDATE pali_segments SET review_status='verified' WHERE segment_id='mn1:1.1'")
            con.commit()
            con.close()
            subprocess.run([sys.executable,str(ROOT/"tools/export_verified_pali.py"),
                "--staging",str(staged),"--out",str(approved)],
                check=True,capture_output=True,text=True)
            con=sqlite3.connect(approved)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM approved_pali").fetchone()[0],1)
            self.assertEqual(con.execute("SELECT value FROM content_manifest WHERE key='fully_verified_volumes'").fetchone()[0],"0")
            con.close()

    def test_unapproved_never_exported(self):
        with tempfile.TemporaryDirectory() as td:
            base=Path(td); root=base/"root"; root.mkdir()
            (root/"mn1.json").write_text('{"mn1:1.1":"test"}',encoding="utf-8")
            mp=base/"mapping.json"; mp.write_text('{"mn1":1}',encoding="utf-8")
            stage=base/"stage.sqlite"
            subprocess.run([sys.executable,str(ROOT/"tools/import_bilara_pali.py"),
                "--root",str(root),"--mapping",str(mp),"--out",str(stage),
                "--source-commit",FAKE_SHA],check=True,capture_output=True)
            out=base/"out.sqlite"
            subprocess.run([sys.executable,str(ROOT/"tools/export_verified_pali.py"),
                "--staging",str(stage),"--out",str(out)],check=True,capture_output=True)
            con=sqlite3.connect(out)
            self.assertEqual(con.execute("SELECT COUNT(*) FROM approved_pali").fetchone()[0],0)
            con.close()

if __name__=="__main__":
    unittest.main()
