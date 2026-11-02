package asia.aaii.myanmartipitaka;

import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;

/** Optional, strictly approved Pāli content asset. No data => empty results. */
public final class ApprovedPaliStore {
    private static final String ASSET = "approved_pali.sqlite";
    public static final class Passage {
        public final String id, pali;
        Passage(String id, String pali) { this.id=id; this.pali=pali; }
    }
    private final Context context;
    public ApprovedPaliStore(Context context) { this.context=context.getApplicationContext(); }
    public List<Passage> get(int volume, int limit) throws Exception {
        if(volume<1 || volume>45) throw new IllegalArgumentException("Invalid MCU volume");
        List<Passage> result=new ArrayList<>();
        boolean found=false;
        for(String f:context.getAssets().list("")) if(ASSET.equals(f)) found=true;
        if(!found) return result;
        File target = context.getDatabasePath(ASSET);
        File parent=target.getParentFile();
        if(parent!=null && !parent.exists() && !parent.mkdirs()) throw new IllegalStateException("Cannot create DB folder");
        if(!target.exists()) {
            File tmp=new File(target.getAbsolutePath()+".tmp");
            try(InputStream in=context.getAssets().open(ASSET);FileOutputStream out=new FileOutputStream(tmp)) {
                byte[] buf=new byte[32768];int n;
                while((n=in.read(buf))!=-1)out.write(buf,0,n);
                out.getFD().sync();
            }
            if(!tmp.renameTo(target)) {tmp.delete();throw new IllegalStateException("Cannot install approved DB");}
        }
        SQLiteDatabase db=SQLiteDatabase.openDatabase(target.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        try {
            try(Cursor c=db.rawQuery("SELECT segment_id,pali FROM approved_pali WHERE mcu_volume=? ORDER BY segment_id LIMIT ?",
                    new String[]{String.valueOf(volume),String.valueOf(Math.max(1,Math.min(limit,500)))})) {
                while(c.moveToNext()) result.add(new Passage(c.getString(0),c.getString(1)));
            }
        } finally {db.close();}
        return result;
    }
}
