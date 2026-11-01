package asia.aaii.myanmartipitaka;
import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import java.io.File;

/** Offline Dhammapada: 423 Pali verses / 26 chapters. Myanmar draft labels never claim review. */
public final class DhammapadaYamakavaggaActivity extends Activity {
  private SQLiteDatabase db;
  private LinearLayout list;
  private Spinner chapters;
  private int chapter=1;
  private boolean destroyed=false;
  private static final int GREEN=0xff144638,CREAM=0xfffaf6eb;
  private final String[] names={"ယမကဝဂ်","အပ္ပမာဒဝဂ်","စိတ္တဝဂ်","ပုပ္ဖဝဂ်","ဗာလဝဂ်","ပဏ္ဍိတဝဂ်","အရဟန္တဝဂ်","သဟဿဝဂ်","ပါပဝဂ်","ဒဏ္ဍဝဂ်","ဇရာဝဂ်","အတ္တဝဂ်","လောကဝဂ်","ဗုဒ္ဓဝဂ်","သုခဝဂ်","ပိယဝဂ်","ကောဓဝဂ်","မလဝဂ်","ဓမ္မဋ္ဌဝဂ်","မဂ္ဂဝဂ်","ပကိဏ္ဏကဝဂ်","နိရယဝဂ်","နာဂဝဂ်","တဏှာဝဂ်","ဘိက္ခုဝဂ်","ဗြာဟ္မဏဝဂ်"};
  private int dp(int x){return (int)(x*getResources().getDisplayMetrics().density+.5f);}
  private TextView label(String s,int sp){TextView t=new TextView(this);t.setText(s);t.setTextSize(sp);t.setTextColor(GREEN);t.setPadding(dp(16),dp(12),dp(16),dp(12));return t;}
  @Override public void onCreate(Bundle b){
    super.onCreate(b);getWindow().setStatusBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(CREAM);
    TextView head=label("☸ ဓမ္မပဒ — ၂၆ ဝဂ်",22);head.setBackgroundColor(GREEN);head.setTextColor(Color.WHITE);root.addView(head);
    root.addView(label("Dhammapada · 423 Pāli verses · Offline Reader",15));
    chapters=new Spinner(this);chapters.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,names));root.addView(chapters);
    chapters.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
      public void onNothingSelected(android.widget.AdapterView<?> p){}
      public void onItemSelected(android.widget.AdapterView<?> p,View v,int position,long id){chapter=position+1;if(db!=null)showChapter();}
    });
    ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TextView back=label("‹ ပြန်ရန်",16);back.setTextColor(Color.WHITE);back.setBackgroundColor(GREEN);root.addView(back);back.setOnClickListener(v->finish());
    setContentView(root);list.addView(label("Offline ကျမ်းစာဒေတာကို ဖွင့်နေပါသည်…",17));
    new Thread(()->{
      SQLiteDatabase opened=null;
      try{
        File f=OfflineCorpusInstaller.prepare(getApplicationContext());
        opened=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        try(Cursor c=opened.rawQuery("SELECT COUNT(*),COUNT(DISTINCT chapter) FROM dhammapada_verses",null)){
          if(!c.moveToFirst()||c.getInt(0)!=423||c.getInt(1)!=26)throw new IllegalStateException("423 verses / 26 chapters incomplete");
        }
        if(destroyed){opened.close();return;}
        db=opened;runOnUiThread(()->{if(!destroyed)showChapter();});
      }catch(Exception e){
        if(opened!=null&&opened!=db)opened.close();
        final String msg=e.getMessage();
        runOnUiThread(()->{if(!destroyed){list.removeAllViews();list.addView(label("စာသားဖွင့်မရပါ — "+msg,17));}});
      }
    },"dhp-offline-init").start();
  }
  private void showChapter(){
    if(db==null||destroyed)return;
    list.removeAllViews();
    list.addView(label("ဝဂ် "+chapter+" — "+names[chapter-1],19));
    try(Cursor c=db.rawQuery("SELECT verse,pali_text,my_draft FROM dhammapada_verses WHERE chapter=? ORDER BY verse",new String[]{Integer.toString(chapter)})){
      while(c.moveToNext()){
        final String verse=c.getString(0),pali=c.getString(1),draft=c.getString(2);
        TextView row=label("ဂါထာ "+verse+"\n\n"+pali,21);
        row.setBackgroundColor(Color.WHITE);
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(10),dp(5),dp(10),dp(5));list.addView(row,lp);
        row.setOnClickListener(v->popup(verse,pali,draft));
      }
    }catch(Exception e){list.addView(label("ကျမ်းစာ SQL ဖတ်၍မရပါ — "+e.getMessage(),17));}
  }
  private void popup(String verse,String pali,String draft){
    ScrollView scroll=new ScrollView(this);
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(1);panel.setPadding(dp(14),dp(14),dp(14),dp(14));
    panel.addView(label("ပါဠိမူရင်း\n"+pali,19));
    TextView state=label(draft==null?"မြန်မာဘာသာပြန် မရှိသေးပါ":"မြန်မာဘာသာပြန် Draft · မစိစစ်ရသေးပါ",14);
    state.setTextColor(0xffa25b21);panel.addView(state);
    panel.addView(label(draft==null?"ဤဂါထာအတွက် မြန်မာဘာသာပြန် မရရှိသေးပါ။":draft,19));
    panel.addView(label("ဘာသာပြန်မူကြမ်းများသည် ပါဠိပညာရှင် အတည်ပြုချက်မရသေးပါ။",13));
    scroll.addView(panel);
    new AlertDialog.Builder(this).setTitle("ဓမ္မပဒ ဂါထာ "+verse).setView(scroll).setPositiveButton("ပိတ်မည်",null).show();
  }
  @Override protected void onDestroy(){destroyed=true;if(db!=null)db.close();super.onDestroy();}
}
