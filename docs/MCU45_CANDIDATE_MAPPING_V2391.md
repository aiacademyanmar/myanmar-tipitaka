# Myanmar Tipitaka — V2.3.9.1 Candidate Mapping Report

Source: Bilara Mahāsaṅgīti Pāli JSON (Roman script), pinned commit b9c23ceb354289eca89b7ef80a51046f7a33732e.
MCU 45-volume catalog: https://tipitaka.cloud/library/

Audited source rows: **444701** (one classification per source segment).
- Single-volume **candidates**: 266610
- Multiple-volume splits to review: 159343
- Possibly outside MCU 45-title list: 17048 (Milinda, Netti, Peṭakopadesa)
- Supplementary Pātimokkha sources: 1700

**Verified full MCU volumes: 0/45.**
**Production APK release: NOT READY.**
**Source reuse permissions: Not audited.**

Single-volume candidates still need explicit first/last MCU passage matching, edition review and sign-off. No claim that chapter-range groupings prove paragraph parity. Split-required pools must not be arbitrarily assigned to volumes.

Major unresolved boundaries:
- Vinaya: vols 1–2, 4–5 and 6–7
- Jātaka: vols 27–28
- Apadāna: vols 32–33
- Yamaka: vols 38–39
- Paṭṭhāna: vols 40–45

Run locally against the successful Pāli Full Source Export SQLite:
```bash
python tools/mcu45_candidate_map.py pali_source_unreviewed.sqlite mcu45_candidates.sqlite
```
Source: https://github.com/suttacentral/bilara-data/tree/published/root/pli/ms

Do not market the resulting database as approved MCU full text or approved Myanmar translation.
