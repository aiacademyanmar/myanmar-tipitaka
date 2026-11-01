package asia.aaii.myanmartipitaka;
import android.app.*;
import android.database.*;
import android.database.sqlite.*;
import android.graphics.*;
import android.os.*;
import android.view.*;
import android.widget.*;
import java.io.*;

/** Distraction-free offline Dhammapada Yamakavagga reader: Pali first, optional Myanmar draft popup. */
public final class DhammapadaYamakavaggaActivity extends Activity {
  private SQLiteDatabase db; private LinearLayout list;
  private final int GREEN=0xff144638,CREAM=0xfffaf6eb;
  private volatile boolean closed=false;
  private int dp(int x){return (int)(x*getResources().getDisplayMetrics().density+.5f);}
  private TextView text(String s,int sp){TextView t=new TextView(this);t.setText(s);t.setTextSize(sp);t.setTextColor(GREEN);
    t.setPadding(dp(16),dp(13),dp(16),dp(13));return t;}
  private void note(String s){list.addView(text(s,17));}
  @Override public void onCreate(Bundle b){
    super.onCreate(b);getWindow().setStatusBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(CREAM);
    TextView header=text("☸ ဓမ္မပဒ — ယမကဝဂ်",22);header.setTextColor(-1);header.setBackgroundColor(GREEN);root.addView(header);
    TextView description=text("Dhammapada • Yamakavagga • ဂါထာ ၁–၂၀\nပါဠိမူရင်းကိုဖတ်ရန် • ဂါထာကိုနှိပ်လျှင် မြန်မာဘာသာပြန် Draft Popup",15);
    root.addView(description);
    ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);
    scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TextView close=text("‹ ပြန်ရန်",16);close.setTextColor(-1);close.setBackgroundColor(GREEN);
    root.addView(close);close.setOnClickListener(v->finish());setContentView(root);
    note("Offline ကျမ်းစာကို ဖွင့်နေပါသည်…");
    new Thread(()->{
      SQLiteDatabase opened=null;
      try{
        File f=OfflineCorpusInstaller.prepare(getApplicationContext());
        opened=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        final java.util.ArrayList<String[]> verses=new java.util.ArrayList<>();
        try(Cursor c=opened.rawQuery("SELECT verse,pali_text,my_draft,translation_status FROM dhammapada_yamakavagga ORDER BY verse",null)){
          while(c.moveToNext())verses.add(new String[]{c.getString(0),c.getString(1),c.getString(2),c.getString(3)});
        }
        if(verses.size()!=20)throw new IOException("Incomplete Yamakavagga");
        db=opened;
        runOnUiThread(()->{if(closed)return;list.removeAllViews();
          for(String[] verse:verses){
            TextView t=text("ဂါထာ "+verse[0]+"\n\n"+verse[1],21);
            t.setBackgroundColor(-1);LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
            lp.setMargins(dp(10),dp(5),dp(10),dp(5));list.addView(t,lp);
            t.setOnClickListener(v->popup(verse));
          }
        });
      }catch(Exception e){
        if(opened!=null && opened!=db)opened.close();
        String msg=e.getMessage();
        runOnUiThread(()->{if(!closed){list.removeAllViews();note("စာသားဖွင့်မရပါ — "+msg);}});
      }
    },"dhammapada-offline-reader").start();
  }
  private void popup(String[] verse){
    ScrollView scroll=new ScrollView(this);
    LinearLayout body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(12),dp(12),dp(12),dp(18));
    body.addView(text("ပါဠိမူရင်း\n"+verse[1],19));
    TextView status=text("အတည်မပြုရသေးသော မြန်မာဘာသာပြန် Draft",14);status.setTextColor(0xffa15b20);body.addView(status);
    body.addView(text(verse[2],19));
    body.addView(text("ဤဘာသာပြန်သည် လေ့လာရေးမူကြမ်းဖြစ်သည်။ ဆရာတော်/ပါဠိပညာရှင်များ အတည်မပြုရသေးပါ။",14));
    scroll.addView(body);
    new AlertDialog.Builder(this).setTitle("ဓမ္မပဒ — ဂါထာ "+verse[0]).setView(scroll)
       .setPositiveButton("ပိတ်မည်",null).show();
  }
  @Override protected void onDestroy(){closed=true;if(db!=null)db.close();super.onDestroy();}
}
