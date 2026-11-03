# Myanmar Tipitaka V2.3.9.8 — MCU Original Pāli Intake

## Implemented
- `tools/acquire_mcu45_sources_v2398.py`: dry-run inventory by default. Explicit `--fetch` and `--allow-host` permit only a human-reviewed, direct HTTPS source whose exact bytes match a pinned SHA-256.
- `tests/test_acquire_mcu45_v2398.py`: fail-closed tests for edition substitution, duplicate/missing books, wrong Pāli script or language, bad rights evidence, non-HTTPS/private hosts and duplicate paragraphs. CI is already configured to run `test_*.py`.
- 45-slot volume registry and editable rights-review manifest. No original MCU source bytes are included.
- **Original MCU Pāli acquired: 0/45. Verified: 0/45. Release gate: CLOSED.**

## Research and edition distinction
1. [Tipitaka Hall archive](https://www.tipitakahall.org/archive) lists Mahācuḷā Pāli Thai-script (1996), 45 volumes and 17,463 pages. This listing does **not** itself supply confirmed bulk permission or downloadable 45 original files.
2. [tipitaka.cloud sources](https://tipitaka.cloud/sources) identifies MCU **Thai-language translation** separately from Siam Rath Thai-script Pāli. Neither is verified original MCU 1996 Pāli.
3. The [Mahāsaṅgīti Bilara Pāli](https://github.com/suttacentral/bilara-data/tree/published/root/pli/ms) is a separate Roman-script edition with 444,701 source segments; 425,953 structural candidates are not MCU verified passages.

## Required input
`mcu45_v2398_source_manifest.json` contains exactly 45 entries. Each genuine acquisition must specify:
- `edition: MCU_PALI_1996`, integer `volume`, title;
- independently reviewed `rights_status: REVIEWED_PERMITTED`, a named `rights_reviewer`, and `rights_evidence_url`;
- direct HTTPS `direct_download_url`, pinned original `file_sha256`;
- actual JSON `edition: MCU_PALI_1996`, `volume`, `script: Thai`, `language: pli`, and nonempty `paragraphs` entries with unique `paragraph_id`, `pali`, and optional positive `page`.

## How to use
Dry run (does not fetch):
```bash
python tools/acquire_mcu45_sources_v2398.py \
  --manifest mcu45_v2398_source_manifest.json \
  --output-dir build/mcu-original --report build/v2398-intake.json
```
After acquiring explicit editorial rights and direct URLs plus verified SHA-256 checksums:
```bash
python tools/acquire_mcu45_sources_v2398.py \
  --manifest mcu45_v2398_source_manifest.json \
  --output-dir build/mcu-original --report build/v2398-intake.json \
  --fetch --allow-host approved.publisher.example
```
The hostname above is a placeholder, **not** a known original MCU source. No automated third-party scraping or unauthorized redistribution.

## NEXT process and strict acceptance gates
- **V2.3.9.9 — Original MCU acquisition:** independently sourced and licensed 45-volume original Thai-script Pāli with page/paragraph count and publisher verification.
- **V2.4.0 — MCU-to-Mahāsaṅgīti review:** many-to-many segment crosswalk, edition variants, 45 first/last reference checks, missing/extra report; unknown never means zero.
- **V2.4.1 — Approved Pāli SQLite:** reviewer signatures, explicit rights status, 45/45 verified before packaging.
- **V2.4.2 — Native offline APK QA:** Android reader, all 45 books, airplane-mode search, bookmarks, Samsung installation.
- **V2.4.3 — Signed release:** successful build, approved content and rights evidence, and signed APK artifact.

The source integrity pass and GitHub test pass do not imply MCU 45/45 completeness, translation approval, or Android APK readiness.
