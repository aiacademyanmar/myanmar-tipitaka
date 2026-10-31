-- Offline Tipitaka corpus schema (only load legally redistributable, verified data).
-- Do NOT mark explanations as canonical translations.
CREATE TABLE IF NOT EXISTS paragraphs (
  id INTEGER PRIMARY KEY,
  volume INTEGER NOT NULL CHECK(volume BETWEEN 1 AND 45),
  body TEXT NOT NULL,
  source_ref TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_paragraph_volume ON paragraphs(volume,id);
CREATE TABLE IF NOT EXISTS paragraph_explanations (
  paragraph_id INTEGER NOT NULL,
  language TEXT NOT NULL DEFAULT 'my',
  explanation_my TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  provenance TEXT NOT NULL CHECK(provenance IN ('approved_translation','editorial_explanation')),
  reviewed INTEGER NOT NULL DEFAULT 0 CHECK(reviewed IN (0,1)),
  PRIMARY KEY(paragraph_id,language),
  FOREIGN KEY(paragraph_id) REFERENCES paragraphs(id)
);
-- Import pipeline must reject paragraphs without source_ref and unreviewed explanations.
