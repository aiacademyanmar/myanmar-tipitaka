# MCU exact-edition comparison input

Source: Mahācuḷā Pāḷi Tepiṭakaṃ, 45-volume MCU edition.
This folder deliberately contains **no invented MCU scripture**.
Obtain a licensed MCU Pāli transcription, independently reviewed against
the Thai-script original, before claiming exact 45-volume verification.

Required metadata.json:
```json
{
  "edition": "Mahācuḷā Pāḷi Tepiṭakaṃ (MCU)",
  "source_uri": "https://verified-publisher-source.example/reference",
  "source_script": "Pali Roman, independently checked against MCU Thai-script original",
  "transcription_method": "Document the exact transcription and proofing",
  "proofreader_reference": "Evidence of editorial review",
  "rights_basis": "Document the permission/public domain evidence"
}
```
The URI above is *illustrative*, not a real source. Replace only with verifiable data.
Place 01.csv ... 45.csv with columns:
`mcu_page,mcu_item,bilara_segment_id,mcu_pali_roman`.
A match requires exactly one MCU row per SQLite source segment; literal
Unicode NFC comparison must pass in every volume. A segment with different
edition punctuation, segmentation or wording is flagged as a mismatch.
If editions are truly different, the expected result is **NOT VERIFIED**.
No script may silently normalize away lexical differences.

Run `python scripts/compare_mcu_exact_45.py --require-exact`
after generating the 45-volume SQLite.
