package asia.aaii.myanmartipitaka;

import android.content.Context;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;

/** Installs a versioned offline SQLite asset atomically, off the UI thread. */
public final class OfflineCorpusInstaller {
  private static final String FILE="tipitaka_offline.sqlite";
  private static final String PREFS="tipitaka_offline_asset_installer";
  private OfflineCorpusInstaller(){}
  public static synchronized File prepare(Context context) throws Exception {
    File target=new File(context.getFilesDir(),FILE);
    long version=context.getPackageManager().getPackageInfo(context.getPackageName(),0).lastUpdateTime;
    long oldVersion=context.getSharedPreferences(PREFS,Context.MODE_PRIVATE).getLong("apk_update",-1L);
    if(target.isFile() && target.length()>4096 && oldVersion==version)return target;
    File temp=new File(context.getFilesDir(),FILE+".part");
    if(temp.exists()&&!temp.delete())throw new IllegalStateException("Cannot remove temporary corpus");
    try(InputStream in=context.getAssets().open(FILE);
        OutputStream out=new FileOutputStream(temp)){
      byte[] buf=new byte[65536];int n;
      while((n=in.read(buf))!=-1){if(n>0)out.write(buf,0,n);}
    }catch(Exception e){temp.delete();throw e;}
    if(temp.length()<4096){temp.delete();throw new IllegalStateException("Corpus is too small");}
    // Use atomic rename when possible and never claim installed before success.
    if(target.isFile()&&!target.delete())throw new IllegalStateException("Unable to replace old corpus");
    if(!temp.renameTo(target))throw new IllegalStateException("Unable to move staged corpus");
    context.getSharedPreferences(PREFS,Context.MODE_PRIVATE).edit().putLong("apk_update",version).apply();
    return target;
  }
}
