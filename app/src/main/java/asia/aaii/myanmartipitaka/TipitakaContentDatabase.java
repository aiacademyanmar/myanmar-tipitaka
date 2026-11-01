package asia.aaii.myanmartipitaka;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

/**
 * Versioned offline content foundation. Canonical Pāli, Myanmar translations and
 * explanations are stored separately. Reader queries expose APPROVED Myanmar
 * content only; drafts remain available to reviewer/admin workflows.
 */
public final class TipitakaContentDatabase extends SQLiteOpenHelper {
  private static final String DB_NAME="myanmar_tipitaka_content_v1.db";
  private static final int DB_VERSION=1;
  public TipitakaContentDatabase(Context context){super(context,DB_NAME,null,DB_VERSION);}
  @Override public void onConfigure(SQLiteDatabase db){super.onConfigure(db);db.setForeignKeyConstraintsEnabled(true);}
  @Override public void onCreate(SQLiteDatabase db){
    db.execSQL("CREATE TABLE source_refs(source_id TEXT PRIMARY KEY,collection TEXT NOT NULL,book_code TEXT,reference TEXT NOT NULL,edition TEXT,source_uri TEXT,license_note TEXT)");
    db.execSQL("CREATE TABLE passages(passage_id TEXT PRIMARY KEY,source_id TEXT NOT NULL,sequence_no INTEGER NOT NULL,pali_text TEXT NOT NULL,chapter_title TEXT,verse_no TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(source_id) REFERENCES source_refs(source_id),UNIQUE(source_id,sequence_no))");
    db.execSQL("CREATE TABLE passage_translations(translation_id INTEGER PRIMARY KEY AUTOINCREMENT,passage_id TEXT NOT NULL,language_code TEXT NOT NULL DEFAULT 'my-MM',translation_text TEXT NOT NULL,translation_kind TEXT NOT NULL DEFAULT 'LITERAL',review_status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','PENDING_REVIEW','APPROVED','REJECTED')),reviewer_name TEXT,reviewed_at TEXT,source_note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE)");
    db.execSQL("CREATE TABLE passage_explanations(explanation_id INTEGER PRIMARY KEY AUTOINCREMENT,passage_id TEXT NOT NULL,language_code TEXT NOT NULL DEFAULT 'my-MM',explanation_text TEXT NOT NULL,explanation_kind TEXT NOT NULL DEFAULT 'STUDY_NOTE',review_status TEXT NOT NULL DEFAULT 'DRAFT' CHECK(review_status IN ('DRAFT','PENDING_REVIEW','APPROVED','REJECTED')),reviewer_name TEXT,reviewed_at TEXT,source_note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE)");
    db.execSQL("CREATE TABLE content_review_events(event_id INTEGER PRIMARY KEY AUTOINCREMENT,entity_type TEXT NOT NULL,entity_id TEXT NOT NULL,old_status TEXT,new_status TEXT NOT NULL,reviewer_name TEXT NOT NULL,review_note TEXT,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)");
    db.execSQL("CREATE TABLE reader_bookmarks(passage_id TEXT PRIMARY KEY,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(passage_id) REFERENCES passages(passage_id) ON DELETE CASCADE)");
    db.execSQL("CREATE TABLE reader_notes(note_id INTEGER PRIMARY KEY AUTOINCREMENT,passage_id TEXT,note_text TEXT NOT NULL,updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(passage_id) REFERENCES passages(passage_id) ON DELETE SET NULL)");
    db.execSQL("CREATE TABLE reader_progress(book_code TEXT PRIMARY KEY,last_passage_id TEXT,last_sequence INTEGER NOT NULL DEFAULT 0,progress_percent REAL NOT NULL DEFAULT 0,last_read_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)");
    db.execSQL("CREATE INDEX idx_passages_source_sequence ON passages(source_id,sequence_no)");
    db.execSQL("CREATE INDEX idx_translations_passage_status ON passage_translations(passage_id,review_status)");
    db.execSQL("CREATE INDEX idx_explanations_passage_status ON passage_explanations(passage_id,review_status)");
    db.execSQL("CREATE INDEX idx_passages_pali ON passages(pali_text)");
  }
  @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){}
  public long addPassage(String id,String sourceId,int sequence,String pali,String chapter,String verse){
    ContentValues v=new ContentValues();v.put("passage_id",id);v.put("source_id",sourceId);v.put("sequence_no",sequence);v.put("pali_text",pali);v.put("chapter_title",chapter);v.put("verse_no",verse);
    return getWritableDatabase().insertWithOnConflict("passages",null,v,SQLiteDatabase.CONFLICT_REPLACE);
  }
  public long addTranslationDraft(String passageId,String text,String kind,String sourceNote){
    ContentValues v=new ContentValues();v.put("passage_id",passageId);v.put("translation_text",text);v.put("translation_kind",kind);v.put("source_note",sourceNote);v.put("review_status","DRAFT");
    return getWritableDatabase().insert("passage_translations",null,v);
  }
  public long addExplanationDraft(String passageId,String text,String kind,String sourceNote){
    ContentValues v=new ContentValues();v.put("passage_id",passageId);v.put("explanation_text",text);v.put("explanation_kind",kind);v.put("source_note",sourceNote);v.put("review_status","DRAFT");
    return getWritableDatabase().insert("passage_explanations",null,v);
  }
  /** Only scholar-approved Myanmar translations are returned to the public reader. */
  public Cursor approvedTranslations(String passageId){
    return getReadableDatabase().rawQuery("SELECT translation_text,translation_kind,reviewer_name,reviewed_at FROM passage_translations WHERE passage_id=? AND language_code='my-MM' AND review_status='APPROVED' ORDER BY translation_id DESC",new String[]{passageId});
  }
  /** Only scholar-approved Myanmar explanations are returned to the public reader. */
  public Cursor approvedExplanations(String passageId){
    return getReadableDatabase().rawQuery("SELECT explanation_text,explanation_kind,reviewer_name,reviewed_at FROM passage_explanations WHERE passage_id=? AND language_code='my-MM' AND review_status='APPROVED' ORDER BY explanation_id DESC",new String[]{passageId});
  }
  public boolean integrityOk(){
    try(Cursor c=getReadableDatabase().rawQuery("PRAGMA integrity_check",null)){return c.moveToFirst()&&"ok".equalsIgnoreCase(c.getString(0));}
  }
  public boolean foreignKeysOk(){
    try(Cursor c=getReadableDatabase().rawQuery("PRAGMA foreign_key_check",null)){return !c.moveToFirst();}
  }
}
