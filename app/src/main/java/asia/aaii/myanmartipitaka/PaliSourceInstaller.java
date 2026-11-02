package asia.aaii.myanmartipitaka;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.SystemClock;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Atomic, version-independent installer for the *unmapped* original Pali source.
 * Always run from a background worker. Does not touch user content or bookmarks.
 */
public final class PaliSourceInstaller {
  public static final String DB_FILE="pali_root_source.sqlite";
  private static final String REVISION_ASSET="pali_source_commit.txt";
  private static final String PREFS="pali_source_install_v2";
  public static final class Result {
    public final File file;
    public final boolean copied;
    public final long elapsedMs;
    public final String revision;
    Result(File f,boolean copy,long elapsed,String rev){
      file=f;copied=copy;elapsedMs=elapsed;revision=rev;
    }
  }
  private PaliSourceInstaller(){}
  private static String revision(Context c)throws Exception{
    try(InputStream in=c.getAssets().open(REVISION_ASSET)){
      byte[] bytes=new byte[80];int n=in.read(bytes);
      if(n<=0)throw new IllegalStateException("Pali source revision asset empty");
      String s=new String(bytes,0,n,StandardCharsets.UTF_8).trim();
      if(!s.matches("[0-9a-fA-F]{40}"))throw new IllegalStateException("Invalid pinned Pali revision");
      return s.toLowerCase(java.util.Locale.ROOT);
    }
  }
  private static void verify(File f,String expected)throws Exception {
    if(!f.isFile()||f.length()<4096)throw new IllegalStateException("Offline Pali file missing/empty");
    SQLiteDatabase db=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    try{
      try(Cursor c=db.rawQuery("SELECT value FROM build_info WHERE name='commit'",null)){
        if(!c.moveToFirst()||!expected.equalsIgnoreCase(c.getString(0)))
          throw new IllegalStateException("Pali source revision mismatch");
      }
      try(Cursor c=db.rawQuery("SELECT 1 FROM sqlite_master WHERE type='table' AND name='myanmar_published'",null)){
        if(!c.moveToFirst())throw new IllegalStateException("Burmese table missing in existing Pali DB");
      }
      try(Cursor c=db.rawQuery("SELECT value FROM build_info WHERE name='vinaya_myanmar_draft_pack'",null)){
        if(!c.moveToFirst()||!"aaii.vinaya.translation_drafts.v2_1000".equals(c.getString(0)))
          throw new IllegalStateException("Vinaya Myanmar translation pack is missing");
      }
      try(Cursor c=db.rawQuery("SELECT 1 FROM source_segments LIMIT 1",null)){
        if(!c.moveToFirst())throw new IllegalStateException("Pali source segments empty");
      }
      try(Cursor c=db.rawQuery("PRAGMA quick_check",null)){
        if(!c.moveToFirst()||!"ok".equalsIgnoreCase(c.getString(0)))
          throw new IllegalStateException("Pali SQLite integrity failed");
      }
    }finally{db.close();}
  }
  public static synchronized Result prepare(Context context)throws Exception{
    long start=SystemClock.elapsedRealtime();
    Context app=context.getApplicationContext();
    String rev=revision(app);
    File dest=new File(app.getFilesDir(),DB_FILE);
    String installedRev=app.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getString("revision","");
    if(dest.isFile()&&rev.equals(installedRev)){
      // Revision already verified on this installation; recheck schema quickly.
      try(SQLiteDatabase db=SQLiteDatabase.openDatabase(dest.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY)){
        try(Cursor c=db.rawQuery("SELECT value FROM build_info WHERE name='commit'",null)){
          if(c.moveToFirst()&&rev.equalsIgnoreCase(c.getString(0))){
            try(Cursor cc=db.rawQuery("SELECT value FROM build_info WHERE name='vinaya_myanmar_draft_pack'",null)){
              if(cc.moveToFirst() && "aaii.vinaya.translation_drafts.v2_1000".equals(cc.getString(0)))
                return new Result(dest,false,SystemClock.elapsedRealtime()-start,rev);
            }
          }
        }
      }catch(Exception ignored){/* recopy from immutable APK asset */}
    }
    // An app upgrade may reuse the existing source even when the legacy reader
    // did not store our revision preference.
    if(dest.isFile()){
      try{
        verify(dest,rev);
        app.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("revision",rev).apply();
        return new Result(dest,false,SystemClock.elapsedRealtime()-start,rev);
      }catch(Exception ignored){/* new revision or damaged local copy */}
    }
    File temp=new File(app.getFilesDir(),DB_FILE+".part");
    File previous=new File(app.getFilesDir(),DB_FILE+".previous");
    if(temp.exists()&&!temp.delete())throw new IllegalStateException("Cannot remove stale partial database");
    try(InputStream input=app.getAssets().open(DB_FILE);
        FileOutputStream output=new FileOutputStream(temp)){
      byte[] buf=new byte[65536];int n;
      while((n=input.read(buf))!=-1)if(n>0)output.write(buf,0,n);
      output.flush();output.getFD().sync();
    }catch(Exception error){temp.delete();throw error;}
    try{verify(temp,rev);}catch(Exception error){temp.delete();throw error;}
    if(previous.exists()&&!previous.delete()){temp.delete();throw new IllegalStateException("Cannot clear source backup");}
    boolean moved=false;
    if(dest.exists()){
      if(!dest.renameTo(previous)){temp.delete();throw new IllegalStateException("Cannot preserve previous source");}
      moved=true;
    }
    if(!temp.renameTo(dest)){
      if(moved)previous.renameTo(dest);
      temp.delete();
      throw new IllegalStateException("Cannot install new Pali source");
    }
    if(!app.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putString("revision",rev).commit()){
      dest.delete();if(moved)previous.renameTo(dest);
      throw new IllegalStateException("Cannot save Pali revision");
    }
    if(previous.exists())previous.delete();
    return new Result(dest,true,SystemClock.elapsedRealtime()-start,rev);
  }
}
