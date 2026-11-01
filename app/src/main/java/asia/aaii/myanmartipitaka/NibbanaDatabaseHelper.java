package asia.aaii.myanmartipitaka;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** Local SQLite store for the Nibbāna learning module. Imports only the bundled, versioned asset. */
public final class NibbanaDatabaseHelper extends SQLiteOpenHelper {
  private static final String DB_NAME="myanmar_tipitaka_nibbana.db";
  private static final int DB_VERSION=1;
  private final Context context;
  public NibbanaDatabaseHelper(Context c){super(c,DB_NAME,null,DB_VERSION);context=c.getApplicationContext();}
  @Override public void onConfigure(SQLiteDatabase db){super.onConfigure(db);db.setForeignKeyConstraintsEnabled(true);}
  @Override public void onCreate(SQLiteDatabase db){
    db.execSQL("CREATE TABLE content_meta (key TEXT PRIMARY KEY,value TEXT NOT NULL)");
    db.execSQL("CREATE TABLE nibbana_sources (source_id TEXT PRIMARY KEY,reference TEXT NOT NULL,title TEXT NOT NULL,pali_url TEXT,reference_url TEXT,theme TEXT)");
    db.execSQL("CREATE TABLE nibbana_topics (topic_id TEXT PRIMARY KEY,topic_order INTEGER NOT NULL,title TEXT NOT NULL,study_note_draft TEXT,source_ids TEXT,review_status TEXT NOT NULL)");
    db.execSQL("CREATE TABLE nibbana_excerpts (excerpt_id INTEGER PRIMARY KEY AUTOINCREMENT,source_id TEXT NOT NULL,pali_text TEXT NOT NULL,myanmar_gloss_draft TEXT,review_status TEXT NOT NULL,FOREIGN KEY(source_id) REFERENCES nibbana_sources(source_id))");
    db.execSQL("CREATE TABLE nibbana_bookmarks (topic_id TEXT PRIMARY KEY,created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(topic_id) REFERENCES nibbana_topics(topic_id) ON DELETE CASCADE)");
    db.execSQL("CREATE INDEX idx_nibbana_topics_order ON nibbana_topics(topic_order)");
    db.execSQL("CREATE INDEX idx_nibbana_excerpts_source ON nibbana_excerpts(source_id)");
  }
  @Override public void onUpgrade(SQLiteDatabase db,int oldVersion,int newVersion){}
  private String readAsset() throws Exception {
    try(InputStream in=context.getAssets().open("nibbana_my.json");ByteArrayOutputStream out=new ByteArrayOutputStream()){
      byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);return out.toString("UTF-8");
    }
  }
  public synchronized void ensureImported() throws Exception {
    SQLiteDatabase db=getWritableDatabase();
    try(Cursor c=db.rawQuery("SELECT value FROM content_meta WHERE key='asset_version'",null)){
      if(c.moveToFirst() && "1".equals(c.getString(0)))return;
    }
    JSONObject root=new JSONObject(readAsset());
    JSONArray sources=root.getJSONArray("sources"),topics=root.getJSONArray("topics"),excerpts=root.getJSONArray("pali_excerpts");
    if(topics.length()!=12)throw new IllegalStateException("နိဗ္ဗာန်ခေါင်းစဉ် ၁၂ ခု မပြည့်စုံပါ");
    db.beginTransaction();
    try{
      db.delete("nibbana_excerpts",null,null);db.delete("nibbana_topics",null,null);db.delete("nibbana_sources",null,null);
      for(int i=0;i<sources.length();i++){
        JSONObject x=sources.getJSONObject(i);ContentValues v=new ContentValues();
        v.put("source_id",x.getString("id"));v.put("reference",x.getString("ref"));v.put("title",x.getString("title"));
        v.put("pali_url",x.optString("pali_url",null));v.put("reference_url",x.optString("reference_url",null));v.put("theme",x.optString("theme",null));
        db.insertOrThrow("nibbana_sources",null,v);
      }
      for(int i=0;i<topics.length();i++){
        JSONObject x=topics.getJSONObject(i);ContentValues v=new ContentValues();
        v.put("topic_id",x.getString("topic_id"));v.put("topic_order",x.getInt("order"));v.put("title",x.getString("title"));
        v.put("study_note_draft",x.optString("study_note_draft",""));v.put("source_ids",x.optJSONArray("source_ids")==null?"[]":x.getJSONArray("source_ids").toString());
        v.put("review_status",x.optString("review_status","PENDING_SCHOLAR_REVIEW"));db.insertOrThrow("nibbana_topics",null,v);
      }
      for(int i=0;i<excerpts.length();i++){
        JSONObject x=excerpts.getJSONObject(i);ContentValues v=new ContentValues();
        v.put("source_id",x.getString("source_id"));v.put("pali_text",x.getString("pali"));v.put("myanmar_gloss_draft",x.optString("myanmar_gloss_draft",""));
        v.put("review_status",x.optString("review_status","PENDING_SCHOLAR_REVIEW"));db.insertOrThrow("nibbana_excerpts",null,v);
      }
      ContentValues meta=new ContentValues();meta.put("key","asset_version");meta.put("value","1");db.insertWithOnConflict("content_meta",null,meta,SQLiteDatabase.CONFLICT_REPLACE);
      ContentValues count=new ContentValues();count.put("key","source_topic_count");count.put("value",sources.length()+":"+topics.length());db.insertWithOnConflict("content_meta",null,count,SQLiteDatabase.CONFLICT_REPLACE);
      db.setTransactionSuccessful();
    }finally{db.endTransaction();}
  }
  public Cursor topics(){return getReadableDatabase().rawQuery("SELECT topic_id,topic_order,title,study_note_draft,source_ids,review_status FROM nibbana_topics ORDER BY topic_order",null);}
  public Cursor sourcesFor(String idsJson){
    JSONArray ids;try{ids=new JSONArray(idsJson);}catch(Exception e){ids=new JSONArray();}
    StringBuilder q=new StringBuilder("SELECT source_id,reference,title,pali_url,reference_url,theme FROM nibbana_sources WHERE source_id IN (");
    String[] args=new String[ids.length()];
    for(int i=0;i<ids.length();i++){if(i>0)q.append(',');q.append('?');args[i]=ids.optString(i);}
    q.append(") ORDER BY reference");
    if(args.length==0)return getReadableDatabase().rawQuery("SELECT source_id,reference,title,pali_url,reference_url,theme FROM nibbana_sources WHERE 1=0",null);
    return getReadableDatabase().rawQuery(q.toString(),args);
  }
  public Cursor excerptsFor(String sourceId){return getReadableDatabase().rawQuery("SELECT pali_text,myanmar_gloss_draft,review_status FROM nibbana_excerpts WHERE source_id=? ORDER BY excerpt_id",new String[]{sourceId});}
  public boolean isBookmarked(String id){try(Cursor c=getReadableDatabase().rawQuery("SELECT 1 FROM nibbana_bookmarks WHERE topic_id=?",new String[]{id})){return c.moveToFirst();}}
  public void toggleBookmark(String id){SQLiteDatabase db=getWritableDatabase();if(isBookmarked(id))db.delete("nibbana_bookmarks","topic_id=?",new String[]{id});else{ContentValues v=new ContentValues();v.put("topic_id",id);db.insertWithOnConflict("nibbana_bookmarks",null,v,SQLiteDatabase.CONFLICT_IGNORE);}}
  public int topicCount(){try(Cursor c=getReadableDatabase().rawQuery("SELECT COUNT(*) FROM nibbana_topics",null)){return c.moveToFirst()?c.getInt(0):0;}}
  public int sourceCount(){try(Cursor c=getReadableDatabase().rawQuery("SELECT COUNT(*) FROM nibbana_sources",null)){return c.moveToFirst()?c.getInt(0):0;}}
}
