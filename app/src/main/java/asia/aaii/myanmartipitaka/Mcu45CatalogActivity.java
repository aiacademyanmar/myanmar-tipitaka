package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.*;
import java.util.Locale;

/** Printed MCU 45-volume INDEX only; Pali Bilara source-file boundaries are NOT verified against these volumes. */
public final class Mcu45CatalogActivity extends Activity {
    private static final int GREEN=0xff12453a,CREAM=0xfffaf6e7,GOLD=0xffb38b30;
    private SQLiteDatabase catalog;
    private LinearLayout list;
    private final String[] pitakas={"Vinaya","Sutta","Abhidhamma"};
    private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
    private TextView text(String s,int size,int color){
        TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);t.setPadding(dp(12),dp(10),dp(12),dp(10));return t;
    }
    private void add(String s,int size,int color){list.addView(text(s,size,color));}
    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
        LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(CREAM);
        TextView title=text("☸  ပိဋကတ် ၄၅ ကျမ်း — MCU Index",22,Color.WHITE);title.setBackgroundColor(GREEN);root.addView(title);
        ScrollView sc=new ScrollView(this);
        list=new LinearLayout(this);list.setOrientation(1);list.setPadding(dp(8),dp(8),dp(8),dp(15));
        sc.addView(list);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
        TextView close=text("‹  ပြန်ရန်",16,Color.WHITE);close.setBackgroundColor(GREEN);
        root.addView(close);close.setOnClickListener(v->finish());TipitakaFooter.attach(this,root,4);setContentView(root);
        try {
            File dbFile=new File(getCacheDir(),"mcu45_metadata_v1.sqlite");
            if(!dbFile.exists()){
                try(InputStream src=getAssets().open("mcu45_metadata.sqlite");FileOutputStream dst=new FileOutputStream(dbFile)){
                    byte[] b=new byte[16384];int n;while((n=src.read(b))!=-1)dst.write(b,0,n);
                }
            }
            catalog=SQLiteDatabase.openDatabase(dbFile.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
            render();
        } catch(Exception e){add("Offline MCU Index မဖွင့်နိုင်ပါ: "+e.getMessage(),16,Color.RED);}
    }
    private void openSource(String group){
        Intent i=new Intent(this,PaliSourceLibraryActivity.class);
        String prefix="Vinaya".equals(group)?"vinaya/":"Abhidhamma".equals(group)?"abhidhamma/":"sutta/";
        i.putExtra("source_prefix",prefix);
        startActivity(i);
    }
    private void render(){
        add("MCU 45-Volume Catalog (8 Vinaya · 25 Sutta · 12 Abhidhamma)",15,GREEN);
        add("ကျမ်းတစ်ကျမ်းကို နှိပ်ပြီး သက်ဆိုင်ရာ ပိဋကတ်၏ Offline ပါဠိ Source ကို တိုက်ရိုက်ဖတ်နိုင်ပါသည်။",14,GREEN);
        add("သတိ: ၄၅ ကျမ်းအမည်စာရင်းသာ Cross-check ပြုလုပ်ထားသည်။ SuttaCentral/Bilara ပါဠိစာပိုဒ်များကို MCU စာအုပ်အလိုက် အတိအကျ Mapping မပြီးသေးပါ။",14,0xff7b4b36);
        add("အတည်ပြု မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက်များ မပါရှိသေးပါ။",14,0xff7b4b36);
        Button pali=new Button(this);pali.setText("📖  Offline ပါဠိမူရင်း 444,701 စာပိုဒ် ဖတ်ရန်");
        list.addView(pali);pali.setOnClickListener(v->startActivity(new Intent(this,PaliSourceLibraryActivity.class)));
        int total=0;
        for(String group:pitakas){
            int count=0;
            add("☸  "+group,20,GREEN);
            try(Cursor cur=catalog.rawQuery("SELECT volume_number,title_myanmar_ui,title_pali_roman FROM volumes WHERE edition=? AND pitaka=? ORDER BY volume_number",new String[]{"TH_MCU_45",group})){
                while(cur.moveToNext()){
                    count++;total++;
                    final int vol=cur.getInt(0);
                    final String name=cur.getString(1);
                    final String en=cur.getString(2);
                    TextView row=text(String.format(Locale.US,"%02d · %s\n%s",vol,name,en),16,GREEN);
                    row.setBackgroundColor(Color.WHITE);
                    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
                    lp.setMargins(dp(3),dp(4),dp(3),dp(4));list.addView(row,lp);
                    row.setOnClickListener(v->new android.app.AlertDialog.Builder(this)
                        .setTitle(String.format(Locale.US,"MCU %02d — %s",vol,name))
                        .setMessage("ဤကျမ်း၏ Bilara Source-file/Paragraph Mapping မစစ်ဆေးရသေးပါ။ မမှန်ကန်သော ကျမ်းစာတစ်ခုသို့ အလိုအလျောက် မချိတ်ပေးပါ။ မူရင်းပါဠိစာများကို Source Category အလိုက် ဖတ်နိုင်ပါသည်။")
                        .setPositiveButton("သက်ဆိုင်ရာ ပိဋကတ် Source ဖွင့်ရန်",(d,w)->openSource(group))
                        .setNegativeButton("ပိတ်ရန်",null).show());
                }
            }
            add(group+" စာရင်း: "+count+" ကျမ်း",13,GOLD);
        }
        if(total!=45)add("WARNING: Expected 45 volume index, found "+total,14,Color.RED);
        else add("Catalog Integrity: 45/45 indexed. Paragraph crosswalk: 0/45 approved.",13,GOLD);
    }
    @Override protected void onDestroy(){if(catalog!=null)catalog.close();super.onDestroy();}
}
