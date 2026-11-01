-- Myanmar Tipitaka V2.3.4
-- SQLite schema foundation. No canonical scripture or translation text is fabricated here.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tipitaka_books (
  book_id TEXT PRIMARY KEY,
  collection_code TEXT NOT NULL CHECK(collection_code IN ('VINAYA','SUTTA','ABHIDHAMMA')),
  book_order INTEGER NOT NULL,
  pali_title TEXT NOT NULL,
  myanmar_title TEXT,
  source_code TEXT NOT NULL DEFAULT 'MCU',
  source_uri TEXT,
  is_enabled INTEGER NOT NULL DEFAULT 1 CHECK(is_enabled IN (0,1)),
  UNIQUE(collection_code, book_order)
);

CREATE TABLE IF NOT EXISTS passages (
  passage_id TEXT PRIMARY KEY,
  book_id TEXT NOT NULL REFERENCES tipitaka_books(book_id) ON DELETE CASCADE,
  parent_passage_id TEXT REFERENCES passages(passage_id),
  sequence_no INTEGER NOT NULL,
  section_path TEXT,
  paragraph_ref TEXT,
  pali_text TEXT NOT NULL,
  text_hash TEXT NOT NULL,
  source_code TEXT NOT NULL,
  source_uri TEXT,
  UNIQUE(book_id, sequence_no),
  UNIQUE(book_id, paragraph_ref)
);

CREATE TABLE IF NOT EXISTS passage_translations (
  translation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
  locale TEXT NOT NULL DEFAULT 'my-MM',
  translation_text TEXT NOT NULL,
  translation_version INTEGER NOT NULL DEFAULT 1,
  review_status TEXT NOT NULL DEFAULT 'DRAFT'
    CHECK(review_status IN ('DRAFT','IN_REVIEW','APPROVED','REJECTED')),
  translator_name TEXT,
  reviewer_name TEXT,
  reviewed_at TEXT,
  approval_note TEXT,
  source_reference TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(passage_id, locale, translation_version)
);

CREATE TABLE IF NOT EXISTS passage_explanations (
  explanation_id INTEGER PRIMARY KEY AUTOINCREMENT,
  passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
  locale TEXT NOT NULL DEFAULT 'my-MM',
  explanation_text TEXT NOT NULL,
  explanation_version INTEGER NOT NULL DEFAULT 1,
  review_status TEXT NOT NULL DEFAULT 'DRAFT'
    CHECK(review_status IN ('DRAFT','IN_REVIEW','APPROVED','REJECTED')),
  author_name TEXT,
  reviewer_name TEXT,
  reviewed_at TEXT,
  doctrinal_scope TEXT,
  source_reference TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(passage_id, locale, explanation_version)
);

CREATE TABLE IF NOT EXISTS content_sources (
  source_id TEXT PRIMARY KEY,
  source_name TEXT NOT NULL,
  source_uri TEXT,
  edition_or_version TEXT,
  license_note TEXT,
  attribution_text TEXT,
  accessed_at TEXT
);

CREATE TABLE IF NOT EXISTS content_review_events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  passage_id TEXT NOT NULL REFERENCES passages(passage_id) ON DELETE CASCADE,
  content_type TEXT NOT NULL CHECK(content_type IN ('TRANSLATION','EXPLANATION')),
  content_row_id INTEGER NOT NULL,
  action TEXT NOT NULL CHECK(action IN ('SUBMITTED','APPROVED','REJECTED','REVISED')),
  reviewer_name TEXT NOT NULL,
  note TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS offline_content_meta (
  meta_key TEXT PRIMARY KEY,
  meta_value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_passages_book_sequence
  ON passages(book_id, sequence_no);
CREATE INDEX IF NOT EXISTS idx_passages_parent
  ON passages(parent_passage_id);
CREATE INDEX IF NOT EXISTS idx_translation_lookup
  ON passage_translations(passage_id, locale, review_status);
CREATE INDEX IF NOT EXISTS idx_explanation_lookup
  ON passage_explanations(passage_id, locale, review_status);
CREATE INDEX IF NOT EXISTS idx_review_events_passage
  ON content_review_events(passage_id, created_at);

-- Reader must show APPROVED Myanmar content only. Missing approved content is
-- represented as unavailable; never silently substitute AI-generated text.
-- Example:
-- SELECT p.passage_id, p.pali_text, t.translation_text, e.explanation_text
-- FROM passages p
-- LEFT JOIN passage_translations t ON t.passage_id=p.passage_id
--   AND t.locale='my-MM' AND t.review_status='APPROVED'
-- LEFT JOIN passage_explanations e ON e.passage_id=p.passage_id
--   AND e.locale='my-MM' AND e.review_status='APPROVED'
-- WHERE p.book_id=? ORDER BY p.sequence_no;
