# Myanmar Tipitaka V2.3.9.6 — Independent MCU Paragraph QA

## Implemented
- `tools/mcu45_independent_reference_v2396.py`: read-only candidate/source SQLite comparison against an independent MCU paragraph CSV and a 45-volume source manifest.
- `tests/test_mcu45_independent_v2396.py`: fail-closed tests. Existing CI workflow runs `test_*.py`.
- All source IDs are *candidates*; 0 MCU books auto-approved.
- Missing / extra remains **UNKNOWN** when an independent complete target has not been supplied; it is never treated as zero.
- Independent source edition, SHA-256 provenance, reviewer and content are mandatory for a completeness claim.
- A zero-difference comparison still requires a separate reviewer approval and APK content gate.

## Required reference data
CSV columns in this order:
`mcu_volume,mcu_paragraph_ref,source_segment_id,target_roman_pali,reference_url,editorial_decision`
The candidate source IDs are Bilara IDs, **not** MCU printed paragraph IDs. The crosswalk must be reviewed. Different paragraph segmentation may require a many-to-many editorial reconciliation beyond the simple comparison.

Manifest: `{"volumes": [{"mcu_volume": 1, "complete_independent_corpus": false, "edition": "", "source_url": "", "source_sha256": "", "reviewer": ""}, ...]}` with 45 distinct volume records.

## Actual baseline
- Bilara Mahāsaṅgīti Pāli: 444,701 source segments
- MCU 45-volume structural candidate assignments: 425,953
- Independent MCU target segments imported into this stage: **0**
- Fully verified MCU volumes: **0/45**
- Android 45-book offline APK QA: not passed

## NEXT process & release acceptance
| Version | Process | Acceptance evidence |
|---|---|---|
| V2.3.9.7 | Acquire *independent* original MCU Pāli 45-book paragraph corpus | Source references, complete 45-book inventory, licensing/provenance |
| V2.3.9.8 | Align Roman/Thai/Myanmar scripts and paragraph split/merge structure | Bidirectional reviewed edition crosswalk |
| V2.3.9.9 | Audit complete missing/extra/text differences and source start/end | Reviewed exceptions and per-volume 45/45 QA |
| V2.4.0 | Publish approved-only offline SQLite database | Approved content manifest and hash, human reviewer |
| V2.4.1 | Integrate native Android offline reader + QA | Airplane-mode, 45-book navigation/search tests |
| V2.4.2 | Final APK build & release approval | Signed APK, Samsung install report, 45/45 accepted |

## Edition caveat
MCU Thai translation, original MCU Pāli edition, 40-volume Mahāsaṅgīti and Siam Rath Pāli are different source/edition objects; don't substitute them without explicit parallel-text evidence. Source catalog: https://tipitaka.cloud/library/ ; content origins: https://tipitaka.cloud/sources .
