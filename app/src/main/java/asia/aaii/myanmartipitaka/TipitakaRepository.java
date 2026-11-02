package asia.aaii.myanmartipitaka;
import android.content.Context;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import java.io.*;
import java.util.*;

/** A versioned SQLite metadata seed. Only verified canonical text and approved Myanmar entries can be read. */
public final class TipitakaRepository implements AutoCloseable {
    private static final String ASSET="tipitaka_verified_seed.sqlite",VERSION="2.3.7.7-index";
    private final SQLiteDatabase db;
    public static class Volume {
        public final int number;public final String pitaka,nikaya,title;
        Volume(int n,String p,String k,String t){number=n;pitaka=p;nikaya=k;title=t;}
    }
    public static class Passage {
        public final String ref,pali,translation,explanation;
        Passage(String r,String p,String t,String e){ref=r;pali=p;translation=t;explanation=e;}
    }
    public static class Result {
        public final int volume;public final String ref,excerpt;
        Result(int v,String r,String e){volume=v;ref=r;excerpt=e;}
    }
    public TipitakaRepository(Context ctx)throws IOException {
        File target=ctx.getDatabasePath(ASSET);
        SharedPreferences pref=ctx.getSharedPreferences("tipitaka_seed",Context.MODE_PRIVATE);
        if(!target.exists()||!VERSION.equals(pref.getString("version",""))){
            File parent=target.getParentFile();
            if(parent!=null&&!parent.exists()&&!parent.mkdirs())throw new IOException("Failed to create database directory");
            File tmp=new File(target.getAbsolutePath()+".tmp");
            try(InputStream in=ctx.getAssets().open(ASSET);FileOutputStream out=new FileOutputStream(tmp)){
                byte[] buf=new byte[32768];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);
                out.getFD().sync();
            }
            if(target.exists()&&!target.delete())throw new IOException("Failed to replace seed");
            if(!tmp.renameTo(target))throw new IOException("Failed to install seed");
            pref.edit().putString("version",VERSION).apply();
        }
        db=SQLiteDatabase.openDatabase(target.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    }
    public List<Volume> volumes(String pitaka) {
        List<Volume> list=new ArrayList<>();
        String where=pitaka==null?"":" WHERE pitaka=?";
        String[] args=pitaka==null?null:new String[]{pitaka};
        try(Cursor c=db.rawQuery("SELECT volume_number,pitaka,nikaya,title_myanmar_ui FROM volumes"+where+" ORDER BY volume_number",args)){
            while(c.moveToNext())list.add(new Volume(c.getInt(0),c.getString(1),c.getString(2),c.getString(3)));
        }return list;
    }
    public List<Passage> passages(int v) {
        List<Passage> list=new ArrayList<>();
        String sql="SELECT s.canonical_ref,s.pali_text,"+
          "(SELECT body FROM entries WHERE segment_id=s.segment_id AND kind='translation' AND status='approved' ORDER BY entry_id LIMIT 1),"+
          "(SELECT body FROM entries WHERE segment_id=s.segment_id AND kind='explanation' AND status='approved' ORDER BY entry_id LIMIT 1)"+
          " FROM segments s WHERE s.edition='TH_MCU_45' AND s.volume_number=? AND s.status='verified' ORDER BY s.canonical_ref";
        try(Cursor c=db.rawQuery(sql,new String[]{String.valueOf(v)})){
            while(c.moveToNext())list.add(new Passage(c.getString(0),c.getString(1),c.getString(2),c.getString(3)));
        }return list;
    }
    public List<Result> searchApproved(String term,int max) {
        List<Result> list=new ArrayList<>();
        if(term.trim().isEmpty())return list;
        String q=term.trim().replace("\\","\\\\").replace("%","\\%").replace("_","\\_");
        String sql="SELECT s.volume_number,s.canonical_ref,substr(e.body,1,240)"+
          " FROM entries e JOIN segments s ON s.segment_id=e.segment_id"+
          " WHERE e.status='approved' AND s.status='verified' AND e.body LIKE ? ESCAPE '\\'"+
          " ORDER BY s.volume_number,e.entry_id LIMIT ?";
        try(Cursor c=db.rawQuery(sql,new String[]{"%"+q+"%",String.valueOf(Math.max(1,Math.min(300,max)))})){
            while(c.moveToNext())list.add(new Result(c.getInt(0),c.getString(1),c.getString(2)));
        }return list;
    }
    public int approvedCount(String kind) {
        try(Cursor c=db.rawQuery("SELECT count(*) FROM entries WHERE status='approved' AND kind=?",new String[]{kind})){
            return c.moveToFirst()?c.getInt(0):0;
        }
    }
    @Override public void close(){db.close();}
}