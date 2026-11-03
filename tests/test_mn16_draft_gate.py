"""MN16 strict unreviewed-draft QA tests, using synthetic Pāli fixtures."""
import csv,hashlib,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import validate_mn16_editorial_draft as gate

class TestMN16DraftGate(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.csv=root/"working.csv"
        self.original=root/"source.json"
        ids=sorted(gate.ABBREVIATION_IDS)+[f"mn16:synthetic-{i}" for i in range(74)]
        self.source={sid:("Pāli …pe…" if sid in gate.ABBREVIATION_IDS else "Pāli source "+sid) for sid in ids}
        self.rows=[]
        for sid,pali in self.source.items():
            abbreviated=sid in gate.ABBREVIATION_IDS
            self.rows.append([sid,"mn16",pali,
              "အတိုချုံးပါဠိ [မချဲ့ရသေး]" if abbreviated else "မြန်မာမူကြမ်း",
              "မြန်မာရှင်းလင်းချက်","Section","Topic","AI_DRAFT_UNREVIEWED",
              "SOURCE_ELLIPSIS_UNEXPANDED" if abbreviated else "SEGMENT_ALIGNED_AI_DRAFT",
              hashlib.sha256(pali.encode()).hexdigest(),gate.EXPECTED_SOURCE,"a"*40,
              self.blob(),"0","","https://example.org/source"])
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def blob(self):
        b=json.dumps(self.source,ensure_ascii=False,indent=2).encode()
        return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
    def save(self):
        self.original.write_text(json.dumps(self.source,ensure_ascii=False),encoding="utf8")
        with self.csv.open("w",encoding="utf-8-sig",newline="") as f:
            w=csv.writer(f);w.writerow(gate.FIELDS);w.writerows(self.rows)
    def check(self):
        with patch.object(gate,"EXPECTED_BLOB",self.blob()):
            return gate.validate(self.csv,self.original)
    def test_83_source_linked_draft_rows(self):
        self.assertEqual(self.check()["source_segments"],83)
        self.assertEqual(self.check()["scholar_approved"],0)
    def test_false_scholar_approval_fails(self):
        self.rows[0][13]="1";self.save()
        with self.assertRaisesRegex(ValueError,"auto-approved"):self.check()
    def test_modified_pali_hash_fails(self):
        self.rows[0][9]="0"*64;self.save()
        with self.assertRaisesRegex(ValueError,"SHA mismatch"):self.check()
    def test_missing_translation_fails(self):
        self.rows[0][3]="";self.save()
        with self.assertRaisesRegex(ValueError,"Missing Burmese"):self.check()
    def test_unexpanded_source_requires_explicit_flag(self):
        self.rows[0][8]="SEGMENT_ALIGNED_AI_DRAFT";self.save()
        with self.assertRaisesRegex(ValueError,"visible review flag"):self.check()
    def test_missing_row_fails(self):
        self.rows.pop();self.save()
        with self.assertRaisesRegex(ValueError,"83 working draft rows"):self.check()
    def test_source_blob_fails(self):
        self.source["mn16:synthetic-0"]="tampered original"
        self.save()
        with self.assertRaisesRegex(ValueError,"Git blob SHA mismatch"):
            with patch.object(gate,"EXPECTED_BLOB","0"*40):
                gate.validate(self.csv,self.original)
    def test_source_abbreviation_inventory_fails(self):
        r=next(r for r in self.rows if r[0]=="mn16:synthetic-1")
        r[2]="added …pe…";r[9]=hashlib.sha256(r[2].encode()).hexdigest()
        self.source[r[0]]=r[2]
        for row in self.rows:row[12]=self.blob()
        self.save()
        with self.assertRaisesRegex(ValueError,"abbreviation inventory changed"):self.check()

if __name__=="__main__":unittest.main()
