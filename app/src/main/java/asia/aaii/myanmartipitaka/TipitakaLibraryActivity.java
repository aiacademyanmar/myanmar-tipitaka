package asia.aaii.myanmartipitaka;
import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.util.*;

/** Read only a verified, actually bundled offline corpus; never invent scripture paragraphs. */
public final class TipitakaLibraryActivity extends Activity {
  private static final int GREEN=Color.rgb(20,66,56),CREAM=Color.rgb(250,245,231);
  private static final String[] NAMES={
    "မဟာဝိဘင်္ဂ ၁",
    "မဟာဝိဘင်္ဂ ၂",
    "ဘိက္ခုနီဝိဘင်္ဂ",
    "မဟာဝဂ္ဂ ၁",
    "မဟာဝဂ္ဂ ၂",
    "စူဠဝဂ္ဂ ၁",
    "စူဠဝဂ္ဂ ၂",
    "ပရိဝါရ",
    "သီလက္ခန္ဓဝဂ္ဂ",
    "မဟာဝဂ္ဂ (ဒီဃ)",
    "ပါထိကဝဂ္ဂ",
    "မူလပဏ္ဏာသ",
    "မဇ္ဈိမပဏ္ဏာသ",
    "ဥပရိပဏ္ဏာသ",
    "သဂါထာဝဂ္ဂ",
    "နိဒါနဝဂ္ဂ",
    "ခန္ဓဝဂ္ဂ",
    "သဠာယတနဝဂ္ဂ",
    "မဟာဝဂ္ဂ (သံယုတ္တ)",
    "ဧက၊ ဒုက၊ တိကနိပါတ",
    "စတုက္ကနိပါတ",
    "ပဉ္စက၊ ဆက္ကနိပါတ",
    "သတ္တက၊ အဋ္ဌက၊ နဝကနိပါတ",
    "ဒသက၊ ဧကာဒသကနိပါတ",
    "ခုဒ္ဒကပါဌ၊ ဓမ္မပဒ၊ ဥဒါန၊ ဣတိဝုတ္တက၊ သုတ္တနိပါတ",
    "ဝိမာနဝတ္ထု၊ ပေတဝတ္ထု၊ ထေရဂါထာ၊ ထေရီဂါထာ",
    "ဇာတက ၁",
    "ဇာတက ၂",
    "မဟာနိဒ္ဒေသ",
    "စူဠနိဒ္ဒေသ",
    "ပဋိသမ္ဘိဒါမဂ္ဂ",
    "အပဒါန် ၁",
    "အပဒါန် ၂၊ ဗုဒ္ဓဝံသ၊ စရိယာပိဋက",
    "ဓမ္မသင်္ဂဏီ",
    "ဝိဘင်္ဂ",
    "ဓာတုကထာ၊ ပုဂ္ဂလပညတ္တိ",
    "ကထာဝတ္ထု",
    "ယမက ၁",
    "ယမက ၂",
    "ပဋ္ဌာန်း ၁",
    "ပဋ္ဌာန်း ၂",
    "ပဋ္ဌာန်း ၃",
    "ပဋ္ဌာန်း ၄",
    "ပဋ္ဌာန်း ၅",
    "ပဋ္ဌာန်း ၆"
  };
  private SQLiteDatabase db;
  private LinearLayout content;\n  private int filterStart=1,filterEnd=45;
  private int dp(int v){return (int)(getResources().getDisplayMetrics().density*v+.5);}
  private TextView text(String s,int size){TextView t=new TextView(this);t.setText(s);t.setTextColor(GREEN);t.setTextSize(size);t.setPadding(dp(14),dp(12),dp(14),dp(12));return t;}
  private void row(String title,Runnable fn){
    TextView t=text(title,17);GradientDrawable b=new GradientDrawable();b.setColor(Color.WHITE);b.setCornerRadius(dp(12));t.setBackground(b);
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(dp(12),dp(5),dp(12),dp(5));
    content.addView(t,p);t.setOnClickListener(v->fn.run());
  }
  private boolean openDb(){
    try{
      File file=OfflineCorpusInstaller.prepare(this);
      db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      try(Cursor c=db.rawQuery("SELECT count(*) FROM paragraphs",null)){
        if(!c.moveToFirst()||c.getLong(0)==0)throw new IOException("Empty corpus");
      }
      return true;
    }catch(Exception e){return false;}
  }
  @Override public void onCreate(Bundle b){
    super.onCreate(b);\n    filterStart=Math.max(1,getIntent().getIntExtra("start_volume",1));\n    filterEnd=Math.min(45,getIntent().getIntExtra("end_volume",45));\n    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    TextView header=text("☸  ပိဋကတ်သုံးပုံ · Offline Library",22);header.setTextColor(Color.WHITE);header.setBackgroundColor(GREEN);root.addView(header);
    ScrollView scroll=new ScrollView(this);content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
    scroll.addView(content);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    content.addView(text("Offline ပါဠိကျမ်းဒေတာကို ဖွင့်နေပါသည်…",18));\n    if(filterStart!=1 || filterEnd!=45) content.addView(text("ရွေးချယ်ထားသော ကျမ်းအုပ်စု • "+filterStart+"–"+filterEnd,16));
    new Thread(()->{
      final boolean ready=openDb();
      long[] counts=new long[3];
      if(ready){
        try(Cursor c=db.rawQuery("SELECT COUNT(*),COUNT(DISTINCT volume) FROM paragraphs WHERE LENGTH(TRIM(body))>0",null)){
          if(c.moveToFirst()){counts[0]=c.getLong(0);counts[1]=c.getLong(1);}
        }catch(Exception ignored){}
      }
      runOnUiThread(()->{
        content.removeViewAt(0);
        content.addView(text(ready?"✓ ပါဠိကျမ်းဒေတာ ဖွင့်ပြီး":"Offline ၄၅ ကျမ်း SQLite မပါသေးပါ",19),0);
        if(ready){
          String summary="Source-aligned Pāli • ကျမ်း "+counts[1]+"/45 • စာပိုဒ် "+counts[0]+"
MCU မူရင်းအုပ်ခွဲတိကျမှု အတည်မပြုရသေးပါ။";
          content.addView(text(summary,16),1);
        }
      });
    },"tipitaka-install").start();
    for(int i=0;i<NAMES.length;i++){
      final int index=i;String group=i<8?"ဝိနည်း":i<33?"သုတ္တန်":"အဘိဓမ္မာ";
      row(String.format(Locale.US,"%02d  %s\n%s",i+1,NAMES[i],group),()->openVolume(index));
    }
    row("🔖  သိမ်းထားသော ကျမ်းပိုဒ် Bookmark များ",()->startActivity(new Intent(this,OfflineBookmarksActivity.class)));
    row("⌕  Offline ကျမ်းပိုဒ် စာသားရှာရန်",()->startActivity(new Intent(this,OfflineSearchActivity.class)));
    row("📚  ပါဠိ Dictionary နှင့် CST / PTS ကျမ်းညွှန်း",()->startActivity(new Intent(this,PaliReferenceActivity.class)));
    row("☸  ပါဠိမူရင်း Source Library (Offline Dataset ရှိပါက)",()->startActivity(new Intent(this,PaliSourceLibraryActivity.class)));
    row("📖  မိမိစာအုပ်ဖိုင် ဖွင့်ဖတ်ရန်",()->startActivity(new Intent(this,BookReaderActivity.class)));
    TextView close=text("‹ ပြန်ရန်",17);close.setTextColor(Color.WHITE);close.setBackgroundColor(GREEN);root.addView(close);close.setOnClickListener(v->finish());setContentView(root);
  }
  private void openVolume(int index){
    if(db==null){new AlertDialog.Builder(this).setTitle("Offline ကျမ်းဒေတာ ပြင်ဆင်နေဆဲ").setMessage("ပါဠိကျမ်းဒေတာကို ဖုန်းထဲသို့ ကူးယူနေဆဲ သို့မဟုတ် မဖွင့်နိုင်သေးပါ။ ခဏစောင့်ပြီး ပြန်စမ်းပါ။").setPositiveButton("ပြန်စစ်မည်",(d,w)->recreate()).setNegativeButton("ပိတ်မည်",null).show();return;}
    Intent popup=new Intent(this,ParagraphExplanationActivity.class);popup.putExtra("volume",index+1);startActivity(popup);return;
  }
  @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
