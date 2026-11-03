"""V2.3.9.8 MCU Pāli rights-gated intake regression tests."""
import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from acquire_mcu45_sources_v2398 import check_url,validate_json_bytes,readiness,run

class TestMCUAcquisition(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.volumes=[{"volume":i,"title":f"MCU {i}","rights_status":"PENDING","source_status":"PENDING"} for i in range(1,46)]
  self.manifest=self.root/"manifest.json"
 def tearDown(self):self.temp.cleanup()
 def save(self,edition="MCU_PALI_1996"):
  self.manifest.write_text(json.dumps({"edition":edition,"volumes":self.volumes}))
 def dry(self):
  return run(self.manifest,self.root/"out",self.root/"audit.json")
 def test_all_45_rights_pending_blocked(self):
  self.save();result=self.dry()
  self.assertEqual(result["new_files_acquired"],0)
  self.assertEqual(result["verified_mcu_volumes"],0)
  self.assertFalse(result["release_ready"])
  self.assertTrue(all(r["status"]=="RIGHTS_NOT_APPROVED" for r in result["records"]))
 def test_duplicate_volume_blocked(self):
  self.volumes[-1]["volume"]=44;self.save()
  with self.assertRaises(ValueError):self.dry()
 def test_wrong_edition_blocked(self):
  self.save("SIAMRATH_PALI_1928")
  with self.assertRaises(ValueError):self.dry()
 def test_private_host_blocked(self):
  for url,host in [("https://127.0.0.1/data","127.0.0.1"),("https://localhost/data","localhost")]:
   with self.subTest(url=url):
    with self.assertRaises(ValueError):check_url(url,host)
 def test_insecure_protocol_blocked(self):
  with self.assertRaises(ValueError):check_url("http://example.org/file","example.org")
 def test_unpinned_checksum_blocked(self):
  self.volumes[0].update(rights_status="REVIEWED_PERMITTED",rights_reviewer="Editor",
    rights_evidence_url="https://example.org/license",direct_download_url="https://example.org/book")
  self.assertEqual(readiness(self.volumes[0],"example.org"),"MISSING_PINNED_SHA256")
 def test_non_thai_or_wrong_edition_blocked(self):
  sample={"edition":"MCU_PALI_1996","volume":1,"script":"Thai","language":"pli",
          "paragraphs":[{"paragraph_id":"1","pali":"นโม ตสฺส","page":1}]}
  b=json.dumps(sample,ensure_ascii=False).encode()
  self.assertEqual(validate_json_bytes(b,1),1)
  with self.assertRaises(ValueError):validate_json_bytes(b,2)
  sample["script"]="Roman"
  with self.assertRaises(ValueError):validate_json_bytes(json.dumps(sample,ensure_ascii=False).encode(),1)
 def test_duplicate_paragraph_rejected(self):
  sample={"edition":"MCU_PALI_1996","volume":1,"script":"Thai","language":"pli",
    "paragraphs":[{"paragraph_id":"1","pali":"นโม"},{"paragraph_id":"1","pali":"ตสฺส"}]}
  with self.assertRaises(ValueError):validate_json_bytes(json.dumps(sample,ensure_ascii=False).encode(),1)
 def test_fetch_requires_approved_host(self):
  self.save()
  with self.assertRaises(ValueError):run(self.manifest,self.root/"out",self.root/"audit.json",execute=True)

if __name__=="__main__":unittest.main()
