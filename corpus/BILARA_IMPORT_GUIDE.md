# Bilara Pāli source staging — not yet bundled

Use the published SuttaCentral Bilara data repository as a candidate source:
https://github.com/suttacentral/bilara-data

1. Verify the exact licence and attribution for **each source directory** before redistributing.
2. Download the published data, then run:
   `python scripts/stage_bilara_pali.py /path/to/bilara-data/root/pli/ms`
3. Review `corpus/bilara_pali_staging.csv` and create an **editorially verified** segment-to-45-volume crosswalk.
4. Do not use segment IDs as numerical volume IDs. Do not invent explanations or claim 45-volume completeness.
5. To bundle a corpus, provide approved `corpus/paragraphs.csv`, `corpus/explanations_my.csv` and `corpus/LICENSE_AND_SOURCES.md`, then run `scripts/import_reviewed_corpus.py`.

A separate `tipitaka_offline.sqlite` cannot honestly be produced until the complete approved data and mapping are present.
