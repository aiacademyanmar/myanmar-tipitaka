package asia.aaii.myanmartipitaka;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.File;
import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashSet;
import java.util.Set;

/** Installs a versioned offline SQLite asset only after validating the staged database. */
public final class OfflineCorpusInstaller {
  private static final String FILE="tipitaka_offline.sqlite";
  private static final String PREFS="tipitaka_offline_asset_installer";
  private OfflineCorpusInstaller(){}

  public static synchronized File prepare(Context context)throws Exception{
    File target=new File(context.getFilesDir(),FILE);
    File backup=new File(context.getFilesDir(),FILE+".previous");
    long version=context.getPackageManager().getPackageInfo(context.getPackageName(),0).lastUpdateTime;
    long installed=context.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("apk_update",-1L);
    if(target.isFile()&&installed==version){
      try{validate(target);return target;}catch(Exception corrupt){/* reinstall from packaged asset below */}
    }

    File temp=new File(context.getFilesDir(),FILE+".part");
    if(temp.exists()&&!temp.delete())throw new IllegalStateException("Cannot remove stale temporary corpus");
    try(InputStream in=context.getAssets().open(FILE);
        FileOutputStream out=new FileOutputStream(temp)){
      byte[] buffer=new byte[65536];int n;
      while((n=in.read(buffer))!=-1)if(n>0)out.write(buffer,0,n);
      out.flush();FileDescriptor fd=out.getFD();fd.sync();
    }catch(Exception e){temp.delete();throw e;}

    try{validate(temp);}catch(Exception invalid){temp.delete();throw new IllegalStateException("Packaged offline SQLite failed validation: "+invalid.getMessage(),invalid);}

    // Preserve the previous database until the staged database is in place.
    if(backup.exists()&&!backup.delete())throw new IllegalStateException("Cannot clear previous corpus backup");
    boolean movedOld=false;
    if(target.exists()){
      if(!target.renameTo(backup)){temp.delete();throw new IllegalStateException("Cannot preserve previous offline database");}
      movedOld=true;
    }
    if(!temp.renameTo(target)){
      if(movedOld&&!backup.renameTo(target))throw new IllegalStateException("Install failed and previous database rollback failed");
      throw new IllegalStateException("Cannot atomically install staged offline database");
    }
    try{
      validate(target);
      if(!context.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong("apk_update",version).commit())
        throw new IllegalStateException("Cannot persist offline database install version");
    }catch(Exception failure){
      if(target.exists())target.delete();
      if(movedOld&&!backup.renameTo(target))throw new IllegalStateException("New database rejected and rollback failed",failure);
      throw failure;
    }
    if(backup.exists())backup.delete();
    return target;
  }

  private static void validate(File file)throws Exception{
    if(!file.isFile()||file.length()<4096)throw new IllegalStateException("SQLite file missing or too small");
    SQLiteDatabase db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    try{
      try(Cursor c=db.rawQuery("PRAGMA quick_check",null)){
        if(!c.moveToFirst()||!"ok".equalsIgnoreCase(c.getString(0)))
          throw new IllegalStateException("SQLite quick_check failed");
      }
      Set<String> tables=new HashSet<>();
      try(Cursor c=db.rawQuery("SELECT name FROM sqlite_master WHERE type='table'",null)){
        while(c.moveToNext())tables.add(c.getString(0));
      }
      if(!tables.contains("paragraphs")||!tables.contains("paragraph_explanations"))
        throw new IllegalStateException("Required offline reader tables are missing");
      Set<String> cols=new HashSet<>();
      try(Cursor c=db.rawQuery("PRAGMA table_info(paragraphs)",null)){while(c.moveToNext())cols.add(c.getString(1));}
      if(!cols.contains("id")||!cols.contains("volume")||!cols.contains("body")||!cols.contains("source_ref"))
        throw new IllegalStateException("Paragraph schema is incompatible");
      long volumes,count;
      try(Cursor c=db.rawQuery("SELECT COUNT(DISTINCT volume),COUNT(*) FROM paragraphs",null)){
        if(!c.moveToFirst())throw new IllegalStateException("Cannot count offline paragraphs");
        volumes=c.getLong(0);count=c.getLong(1);
      }
      if(volumes!=45)throw new IllegalStateException("Expected 45 volumes; found "+volumes);
      if(count<=0)throw new IllegalStateException("Offline corpus has no paragraphs");
      if(!tables.contains("volumes")||!tables.contains("build_info"))
        throw new IllegalStateException("Native 45-volume corpus metadata is missing");
      try(Cursor meta=db.rawQuery("SELECT value FROM build_info WHERE name='pali_paragraph_count'",null)){
        if(!meta.moveToFirst()||Long.parseLong(meta.getString(0))!=count)
          throw new IllegalStateException("Corpus paragraph count metadata mismatch");
      }
      try(Cursor meta=db.rawQuery("SELECT value FROM build_info WHERE name='edition_mapping'",null)){
        if(!meta.moveToFirst()||!"45-volume human-reviewed crosswalk".equals(meta.getString(0)))
          throw new IllegalStateException("Edition mapping is not approved");
      }
      try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM paragraphs WHERE body IS NULL OR trim(body)='' OR source_ref IS NULL OR trim(source_ref)=''",null)){
        if(!c.moveToFirst()||c.getLong(0)!=0)throw new IllegalStateException("Empty or unreferenced paragraphs exist");
      }
      for(int v=1;v<=45;v++){
        try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM paragraphs WHERE volume=?",new String[]{Integer.toString(v)})){
          if(!c.moveToFirst()||c.getLong(0)==0)throw new IllegalStateException("Volume "+v+" is empty");
        }
      }
    }finally{db.close();}
  }
}
