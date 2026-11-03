"""V2.3.9.7 MCU original source acquisition safety regression tests."""
import hashlib,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from ingest_mcu45_original_v2397 import build

class TestMCUOriginalIngest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.p=Path(self.tmp.name)
        self.books=[{"volume":i,"title":f"MCU Volume {i}","source_status":"PENDING"}
                    for i in range(1,46)]
        self.manifest=self.p/"manifest.json"
        self.db=self.p/"staged.sqlite"
        self.report=self.p/"report.json"
    def tearDown(self):self.tmp.cleanup()
    def save(self,edition="MCU_PALI_1996"):
        self.manifest.write_text(json.dumps({"edition":edition,"volumes":self.books}),encoding="utf-8")
    def acquire_first(self,rows):
        doc={"edition":"MCU_PALI_1996","volume":1,"script":"Thai","language":"pli","paragraphs":rows}
        binary=json.dumps(doc,ensure_ascii=False).encode("utf-8")
        (self.p/"mcu_01.json").write_bytes(binary)
        self.books[0].update(source_status="ACQUIRED",source_file="mcu_01.json",
                              source_url="https://example.org/original-mcu",
                              file_sha256=hashlib.sha256(binary).hexdigest())
        self.save()
    def test_empty_reference_is_registry_only(self):
        self.save()
        summary=build(self.manifest,self.p,self.db,self.report)
        self.assertEqual(summary["catalog_volumes"],45)
        self.assertEqual(summary["acquired_mcu_original_volumes"],0)
        self.assertEqual(summary["staged_mcu_paragraphs"],0)
        self.assertFalse(summary["release_ready"])
    def test_one_authorized_source_stages_unreviewed_only(self):
        self.acquire_first([{"paragraph_id":"1","pali":"นโม ตสฺส","page":1}])
        r=build(self.manifest,self.p,self.db,self.report)
        self.assertEqual(r["acquired_mcu_original_volumes"],1)
        self.assertEqual(r["staged_mcu_paragraphs"],1)
        self.assertEqual(r["verified_full_volumes"],0)
    def test_hash_mismatch_rejected(self):
        self.acquire_first([{"paragraph_id":"1","pali":"นโม","page":1}])
        self.books[0]["file_sha256"]="f"*64
        self.save()
        with self.assertRaises(ValueError):build(self.manifest,self.p,self.db,self.report)
    def test_wrong_edition_rejected(self):
        self.save("SIAMRATH_PALI_1928")
        with self.assertRaises(ValueError):build(self.manifest,self.p,self.db,self.report)
    def test_duplicate_paragraph_rejected(self):
        self.acquire_first([{"paragraph_id":"1","pali":"นโม","page":1},
                            {"paragraph_id":"1","pali":"ตสฺส","page":1}])
        with self.assertRaises(ValueError):build(self.manifest,self.p,self.db,self.report)

if __name__=="__main__":unittest.main()
