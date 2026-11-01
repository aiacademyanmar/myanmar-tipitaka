package asia.aaii.myanmartipitaka;

import android.content.Context;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

/**
 * Durable user-owned Myanmar content overlay.
 * Kept separate from the packaged Pali corpus so app upgrades do not erase
 * locally published translations and explanations.
 */
public final class MyanmarContentStore extends SQLiteOpenHelper {
  public static final String DB_NAME="myanmar_publisher_content.db";
  public static final String TABLE="paragraph_myanmar_content";

  public MyanmarContentStore(Context context){
    super(context.getApplicationContext(),DB_NAME,null,1);
    setWriteAheadLoggingEnabled(true);
  }

  @Override public void onCreate(SQLiteDatabase db){
    db.execSQL("CREATE TABLE paragraph_myanmar_content("+
      "paragraph_id INTEGER NOT NULL,"+
      "segment_id TEXT NOT NULL,"+
      "content_type TEXT NOT NULL CHECK(content_type IN ('translation','explanation')),"+
      "text_my TEXT NOT NULL,"+
      "source_ref TEXT NOT NULL,"+
      "rights_evidence TEXT NOT NULL,"+
      "reviewer_1 TEXT NOT NULL,"+
      "reviewer_2 TEXT NOT NULL,"+
      "review_reference TEXT NOT NULL,"+
      "reviewed_at TEXT NOT NULL,"+
      "source_pali_sha256 TEXT NOT NULL,"+
      "reviewed INTEGER NOT NULL CHECK(reviewed=1),"+
      "publisher_name TEXT NOT NULL,"+
      "published_at TEXT NOT NULL,"+
      "PRIMARY KEY(paragraph_id,content_type))");
    db.execSQL("CREATE INDEX idx_local_myanmar_segment ON paragraph_myanmar_content(segment_id,content_type)");
    db.execSQL("CREATE TABLE publisher_import_log("+
      "id INTEGER PRIMARY KEY AUTOINCREMENT,"+
      "source_type TEXT NOT NULL,"+
      "source_name TEXT NOT NULL,"+
      "publisher_name TEXT NOT NULL,"+
      "imported_at TEXT NOT NULL,"+
      "translation_rows INTEGER NOT NULL,"+
      "explanation_rows INTEGER NOT NULL)");
  }

  @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){
    // Versioned migrations will be added here; preserve all published records.
  }
}
