package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.util.Locale;

/**
 * Honest, live, offline progress report for the BUILT-IN Bilara Pali source.
 * A source segment being in the APK is not evidence that it was individually
 * verified as part of one of the 45 printed Thai MCU volumes.
 *
 * Counts 'published Myanmar' separately from independently human-approved.
 * All queries run off the main thread to avoid ANR during DB installation.
 */
public final class ProjectProgressActivity extends Activity {
    private static final int GREEN=0xff174b3b, GOLD=0xffb4883e, INK=0xff204935;
    private LinearLayout body;
    private volatile boolean closed=false;
    private int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+0.5f);}
    private TextView text(String s,int size,int color,boolean strong){
        TextView t=new TextView(this);
        t.setText(s);t.setTextSize(size);t.setTextColor(color);
        t.setPadding(dp(13),dp(9),dp(13),dp(9));
        if(strong)t.setTypeface(null,Typeface.BOLD);
        return t;
    }
    private void label(String s,int size,boolean bold){body.addView(text(s,size,INK,bold));}
    private void progress(String title,long done,long total,boolean showFraction){
        double ratio=total==0?0.0:(double)done/(double)total;
        double percent=100.0*ratio;
        String details=showFraction?
            String.format(Locale.US,"%,d / %,d (%.2f%%)",done,total,percent):
            String.format(Locale.US,"%.2f%%",percent);
        label(title+" — "+details,14,true);
        ProgressBar b=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
        b.setMax(10000);
        b.setProgress((int)Math.round(10000*Math.min(1.0,Math.max(0.0,ratio))));
        b.setProgressTintList(android.content.res.ColorStateList.valueOf(done==total?0xff308956:GOLD));
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(11));
        p.setMargins(dp(15),0,dp(15),dp(11));body.addView(b,p);
    }
    @Override public void onCreate(Bundle state){
        super.onCreate(state);
        getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
        LinearLayout root=new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(0xfffaf7ed);
        TextView header=text("☸  ပါဠိ / မြန်မာ Progress Report",21,Color.WHITE,true);
        header.setBackgroundColor(GREEN);root.addView(header);
        ScrollView scroll=new ScrollView(this);
        body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(dp(6),dp(10),dp(6),dp(18));
        scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
        TipitakaFooter.attach(this,root,-1);
        setContentView(root);
        label("Offline SQLite Database ကို စစ်ဆေးနေပါသည်…",16,true);
        new Thread(this::readCoverage,"tipitaka-content-audit").start();
    }
    private static int count(SQLiteDatabase db,String sql,String[] args){
        try(Cursor c=db.rawQuery(sql,args)){return c.moveToFirst()?c.getInt(0):0;}
    }
    private static int groupCount(SQLiteDatabase db,String group){
        return count(db,"SELECT COUNT(*) FROM source_segments WHERE source_file LIKE ?",new String[]{group+"/%"});
    }
    private static int groupTranslated(SQLiteDatabase db,String group){
        return count(db,"SELECT COUNT(*) FROM myanmar_published m JOIN source_segments s ON s.segment_id=m.segment_id WHERE s.source_file LIKE ?",new String[]{group+"/%"});
    }
    private static class Coverage {
        int total,paliFiles, headings,myanmar,vinayaDrafts,approvedTranslation,approvedExplanation;
        int[] group=new int[3],translation=new int[3];
        int catalog,verifiedCrosswalk;
        boolean integrity;
        String revision;
    }
    private void readCoverage(){
        try{
            PaliSourceInstaller.Result prepared=PaliSourceInstaller.prepare(this);
            Coverage d=new Coverage();
            try(SQLiteDatabase db=SQLiteDatabase.openDatabase(prepared.file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY)){
                d.total=count(db,"SELECT COUNT(*) FROM source_segments",null);
                d.paliFiles=count(db,"SELECT COUNT(DISTINCT source_file) FROM source_segments",null);
                d.headings=count(db,"SELECT COUNT(*) FROM pali_segment_titles",null);
                d.myanmar=count(db,"SELECT COUNT(*) FROM myanmar_published",null);
                d.vinayaDrafts=count(db,"SELECT COUNT(*) FROM vinaya_myanmar_drafts WHERE editorial_status='AI_DRAFT_UNREVIEWED'",null);
                String[] names={"vinaya","sutta","abhidhamma"};
                for(int i=0;i<3;i++){
                    d.group[i]=groupCount(db,names[i]);
                    d.translation[i]=groupTranslated(db,names[i]);
                }
                d.revision=prepared.revision;
                try(Cursor check=db.rawQuery("PRAGMA quick_check",null)){d.integrity=check.moveToFirst() && "ok".equals(check.getString(0));}
            }
            File seed=new File(getCacheDir(),"mcu45_progress_v2384.sqlite");
            if(!seed.exists()){
                try(InputStream src=getAssets().open("mcu45_metadata.sqlite");FileOutputStream dst=new FileOutputStream(seed)){
                    byte[] buffer=new byte[16384];int n;
                    while((n=src.read(buffer))!=-1)dst.write(buffer,0,n);
                }
            }
            try(SQLiteDatabase db=SQLiteDatabase.openDatabase(seed.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY)){
                d.catalog=count(db,"SELECT COUNT(*) FROM volumes WHERE edition='TH_MCU_45'",null);
                d.verifiedCrosswalk=count(db,"SELECT COUNT(*) FROM ref_crosswalk",null);
                d.approvedTranslation=count(db,"SELECT COUNT(*) FROM entries WHERE status='approved' AND kind='translation'",null);
                d.approvedExplanation=count(db,"SELECT COUNT(*) FROM entries WHERE status='approved' AND kind='explanation'",null);
            }
            if(!closed)runOnUiThread(()->{if(!closed)render(d);});
        }catch(Exception e){
            final String error=e.getMessage()==null?"Unknown offline database error":e.getMessage();
            if(!closed)runOnUiThread(()->{if(!closed){
                body.removeAllViews();
                label("Database ဖွင့်မရပါ: "+error,15,true);
                label("ပါဠိ သို့မဟုတ် မြန်မာ Content ကို ပြည့်စုံသည်ဟု မဖော်ပြနိုင်ပါ။",13,false);
            }});
        }
    }
    private void render(Coverage d){
        body.removeAllViews();
        label("SQLite Database တိုက်ရိုက်စစ်ဆေးချက်",21,true);
        label("ပါဠိ Source Commit: "+d.revision,11,false);
        label("Offline Source Files: "+d.paliFiles+" · SQLite Check: "+(d.integrity?"OK":"NOT VERIFIED"),13,false);
        label("၁။ ပါဠိမူရင်း",18,true);
        progress("လက်ရှိ Bilara Pāli Source Corpus",d.total,d.total,true);
        label("အောက်ပါ 100% သည် APK ထဲပါပြီးသား Bilara Source စာပိုဒ်များအပေါ်သာ အခြေခံသည်။ MCU ပုံနှိပ်ကျမ်း ၄၅ ကျမ်း တစ်ကျမ်းချင်းစီ အတည်ပြုခြင်း မဟုတ်ပါ။",12,false);
        progress("ပါဠိစာပိုဒ်အလိုက် ခေါင်းစဉ်ချိတ်ဆက်ခြင်း",d.headings,d.total,true);
        String[] groupNames={"ဝိနည်းပိဋကတ်","သုတ္တပိဋကတ်","အဘိဓမ္မပိဋကတ်"};
        for(int i=0;i<3;i++)label(groupNames[i]+" — "+String.format(Locale.US,"%,d ပါဠိစာပိုဒ်",d.group[i]),14,false);

        label("၂။ မြန်မာဘာသာပြန်",18,true);
        progress("SuttaCentral Published Myanmar (AAII မစိစစ်ရသေး)",d.myanmar,d.total,true);
        for(int i=0;i<3;i++){
            progress(groupNames[i]+" — မြန်မာဘာသာပြန်",d.translation[i],d.group[i],true);
        }
        label("DN3 နှင့် DN5 ၏ မြန်မာစာပိုဒ်များကို SuttaCentral Published Data အဖြစ် ဖတ်နိုင်သည်။ ကျန်စာပိုဒ်များတွင် ဘာသာပြန်မရှိသေးကြောင်း ဖော်ပြသည်။",12,false);
        label("ဝိနည်းမြန်မာဘာသာပြန် — အထူးဦးစားပေး",18,true);
        progress("ဝိနည်း AI ဘာသာပြန်မူကြမ်း (မစိစစ်ရသေး)",d.vinayaDrafts,d.group[0],true);
        progress("ဝိနည်း မြန်မာစာသား Draft + Published",d.vinayaDrafts+d.translation[0],d.group[0],true);
        label("မူကြမ်းစာပိုဒ်များကို ပညာရှင်အတည်ပြုစာသားများအဖြစ် မသတ်မှတ်ပါ။",12,false);
        progress("AAII သီးခြားအတည်ပြု မြန်မာဘာသာပြန်",d.approvedTranslation,d.total,true);
        progress("AAII သီးခြားအတည်ပြု မြန်မာရှင်းလင်းချက်",d.approvedExplanation,d.total,true);

        label("၃။ ကျမ်း ၄၅ ကျမ်း Mapping",18,true);
        progress("MCU ကျမ်းအမည် Catalog",d.catalog,45,true);
        progress("MCU Exact Paragraph Crosswalk (ကျမ်းအလိုက်)",0,45,true);
        label("Verified Crosswalk Records: "+d.verifiedCrosswalk,12,false);
        label("ထိုင်း MCU ပုံနှိပ် Volume များ၏ စာပိုဒ်စ/ဆုံးကို မအတည်ပြုရသေးပါ။ 45/45 Catalog ≠ 45/45 Full Mapped Books.",12,false);
        TextView note=text("✓ Source corpus offline ရရှိသည်\n✗ မြန်မာဘာသာပြန် ၄၅ ကျမ်းလုံး မပြီးသေးပါ\n✗ MCU ၄၅ ကျမ်း Exact Mapping မပြီးသေးပါ",14,INK,true);
        note.setBackgroundColor(0xffe9efe5);body.addView(note);
    }
    @Override protected void onDestroy(){closed=true;super.onDestroy();}
}
