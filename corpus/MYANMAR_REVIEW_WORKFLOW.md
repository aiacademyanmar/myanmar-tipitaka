# Myanmar Pali paragraph translation and explanation review

The 45-volume offline Pali SQLite currently has **425,953** source-aligned
paragraphs. **No human-reviewed per-paragraph Myanmar translations or explanations**
have yet been provided. Do not present generic notes as canonically reviewed text.

A preliminary Burmese translation is present in public Bilara in two DN files
(`translation/my/myteam/sutta/dn/dn3_translation-my-myteam.json`,
`dn5_translation-my-myteam.json`). Its publication metadata says
`is_published: false`. It is **candidate material only**, not a signed-off
translation/explanation corpus. The SuttaCentral publication entry describes
CC0 but also says its process adapted an existing Myanmar publication. Rights
and review of the actual input must be confirmed separately.

The reviewed import file is `corpus/reviewed_myanmar.csv` with columns:

`segment_id,content_type,text_my,source_ref,rights_evidence,reviewer_1,reviewer_2,review_reference,reviewed_at,source_pali_sha256`

- `content_type` = `translation` or `explanation`; keep them separate.
- `reviewer_1` and `reviewer_2` must be real, different persons with documented approval.
- `source_pali_sha256` must hash the exact UTF-8 paragraph text in SQLite.
- `reviewed_at` is ISO YYYY-MM-DD.
- Never fabricate reviewers or approvals.
- Source credit, licence evidence and the original reference are mandatory.
- The importer fails on mismatched Pali text or missing references.
- Popups should only show reviewed content, and display a missing-data message otherwise.

Run `python scripts/merge_verified_myanmar.py` on the built SQLite.
Coverage is recorded in `myanmar_review_coverage.json`.

**Translation** = conveying the Pali sentence in Myanmar.
**Explanation** = a separate careful interpretation; it must never be passed
off as a word-for-word canonical translation.

Full 425,953/425,953 human review is a substantial editorial undertaking.
