# V2.3.9.7 — MCU Original Pāli 45-Volume Acquisition

## Confirmed primary target

- Edition: `MCU_PALI_1996` — Mahācuḷā Pāli Tipiṭaka, Thai script, Thailand, 1996.
- Tipitaka Hall lists the MC archive as 45 volumes and 17,463 pages: https://www.tipitakahall.org/archive
- tipitaka.cloud distinguishes MCU *Thai-language translation* from its *Siam Rath Thai-script Pāli* edition: https://tipitaka.cloud/sources
- Do **not** substitute Siam Rath, 40-volume Mahāsaṅgīti or MCU Thai translation for 45-volume MCU Pāli original.

## Implemented

- `tools/ingest_mcu45_original_v2397.py` — accepts only independently acquired MCU_PALI_1996 original Thai-script Pāli source JSON; checks volume inventory, exact edition, SHA-256, text script, page number and unique paragraph IDs.
- `tests/test_mcu45_original_v2397.py` — checks 45-volume registry, partial acquisition, edition mismatch, tampered SHA and duplicate paragraphs.
- Output marks every acquired source `UNREVIEWED`; never grants 45/45 completion or license approval.

## Source data status

- 45-volume target catalogue identified: **45/45**.
- Real MCU 1996 original Pāli files downloaded: **0/45**.
- MCU original Pāli segments ingested: **0**.
- Independently verified MCU full books: **0/45**.
- Existing 444,701 Mahāsaṅgīti Roman Pāli segments and 425,953 structural MCU-volume candidates are a **different edition** and cannot fill these zeros.

Direct authorized archive download links and redistribution permission for MCU-1996 Pāli have not been confirmed. Archive access alone does not establish a bulk text license.

## Import schema

Manifest `{"edition":"MCU_PALI_1996","volumes":[{"volume":1,"title":"...","source_status":"PENDING"}, ...]}` must contain exactly 45 numbered volumes. To acquire a volume set `source_status=ACQUIRED`, `source_file=mcu_01.json`, `file_sha256` to the actual file SHA-256, and `source_url` to the verified direct source.

Source JSON:
```json
{"edition":"MCU_PALI_1996","volume":1,"script":"Thai","language":"pli","paragraphs":[{"paragraph_id":"SOURCE_ORIGINAL_ID","pali":"ORIGINAL_THAI_SCRIPT_PALI","page":1}]}
```
The illustrative text above is a schema placeholder, **not** canonical Pāli.

## NEXT

- **V2.3.9.8:** acquire source-authorized original MCU Pāli files; verify page and paragraph anchors and rights.
- **V2.3.9.9:** compare independent MCU Pāli vs Mahāsaṅgīti using a reviewed one-to-many paragraph crosswalk; record missing/extra accurately.
- **V2.4.0:** approved-only 45-volume SQLite release gate.
- **V2.4.1:** offline Android reader tests in airplane mode.
- **V2.4.2:** final APK build, install and signing QA.
