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
    "မဟာဝိဘင်္ဂ ၁","မဟာဝိဘင်္ဂ ၂","ဘိက္ခုနီဝိဘင်္ဂ","မဟာဝဂ္ဂ ၁","မဟာဝဂ္ဂ ၂",
    "စူဠဝဂ္ဂ ၁","စူဠဝဂ္ဂ ၂","ပရိဝါရ",
    "သီလက္ခန္ဓဝဂ္ဂ","မဟာဝဂ္ဂ (ဒီဃ)","ပါထိကဝဂ္ဂ",
    "မူလပဏ္ဏာသ","မဇ္ဈိမပဏ္ဏာသ","ဥပရိပဏ္ဏာသ",
    "သဂါထာဝဂ္ဂ","နိဒါနဝဂ္ဂ","ခန္ဓဝဂ္ဂ","သဠာယတနဝဂ္ဂ","မဟာဝဂ္ဂ (သံယုတ္တ)",
    "အင်္ဂုတ္တရနိကာယ် ၁","အင်္ဂုတ္တရနိကာယ် ၂","အင်္ဂုတ္တရနိကာယ် ၃","အင်္ဂုတ္တရနိကာယ် ၄","အင်္ဂုတ္တရနိကာယ် ၅",
    "ခုဒ္ဒကပါဌ","ဓမ္မပဒ","ဥဒါန","ဣတိဝုတ္တက","သုတ္တနိပါတ","ဝိမာနဝတ္ထု",
    "ပေတဝတ္ထု","ထေရဂါထာ","ထေရီဂါထာ",
    "ဓမ္မသင်္ဂဏီ","ဝိဘင်္ဂ","ဓာတုကထာ","ပုဂ္ဂလပညတ္တိ","ကထာဝတ္ထု","ယမက ၁","ယမက ၂",
    "ပဋ္ဌာန်း ၁","ပဋ္ဌာန်း ၂","ပဋ္ဌာန်း ၃","ပဋ္ဌာန်း ၄","ပဋ္ဌာန်း ၅"
  };
  private SQLiteDatabase db;
  private LinearLayout content;
  private int dp(int v){return (int)(getResources().getDisplayMetrics().density*v+.5);}
  private TextView text(String s,int size){TextView t=new TextView(this);t.setText(s);t.setTextColor(GREEN);t.setTextSize(size);t.setPadding(dp(14),dp(12),dp(14),dp(12));return t;}
  private void row(String title,Runnable fn){
    TextView t=text(title,17);GradientDrawable b=new GradientDrawable();b.setColor(Color.WHITE);b.setCornerRadius(dp(12));t.setBackground(b);
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(dp(12),dp(5),dp(12),dp(5));
    content.addView(t,p);t.setOnClickListener(v->fn.run());
  }
  private boolean openDb(){
    try{
      File file=new File(getFilesDir(),"tipitaka_offline.sqlite");
      if(!file.exists()){
        try(InputStream in=getAssets().open("tipitaka_offline.sqlite");OutputStream out=new FileOutputStream(file)){
          byte[] buf=new byte[8192];int n;while((n=in.read(buf))>0)out.write(buf,0,n);
        }
      }
      db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      try(Cursor c=db.rawQuery("SELECT count(*) FROM paragraphs",null)){if(!c.moveToFirst()||c.getLong(0)==0)throw new IOException("Empty corpus");}
      return true;
    }catch(Exception e){return false;}
  }
  @Override public void onCreate(Bundle b){
    super.onCreate(b);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    TextView header=text("☸  ပိဋကတ်သုံးပုံ · Offline Library",22);header.setTextColor(Color.WHITE);header.setBackgroundColor(GREEN);root.addView(header);
    ScrollView scroll=new ScrollView(this);content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
    scroll.addView(content);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    boolean ready=openDb();
    content.addView(text(ready?"✓ Offline စာသားဒေတာ ရရှိပါပြီ":"၄၅ ကျမ်း စာရင်းနှင့် Offline Reader",19));
    if(ready){
      try {
        long paragraphCount=0,explainedCount=0;int coveredVolumes=0;
        try(Cursor c=db.rawQuery("SELECT COUNT(*),COUNT(DISTINCT volume) FROM paragraphs WHERE LENGTH(TRIM(body))>0",null)){
          if(c.moveToFirst()){paragraphCount=c.getLong(0);coveredVolumes=c.getInt(1);}
        }
        try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM paragraph_explanations WHERE language='my' AND reviewed=1 AND LENGTH(TRIM(explanation_my))>0",null)){
          if(c.moveToFirst())explainedCount=c.getLong(0);
        }
        content.addView(text("Offline Data Coverage  •  ကျမ်း "+coveredVolumes+"/45\\nကျမ်းပိုဒ် "+paragraphCount+" ပိုဒ်\\nစိစစ်ပြီး မြန်မာရှင်းလင်းချက် "+explainedCount+" ပိုဒ်",18));
        if(coveredVolumes<45||explainedCount<paragraphCount)content.addView(text("သတိပြုရန် — ပိဋကတ်တော် Offline Full Library မပြည့်စုံသေးပါ။",16));
      }catch(Exception e){content.addView(text("Database Format / Explanation Coverage စစ်ဆေး၍ မရပါ။",16));}
    }
    if(!ready)content.addView(text("၄၅ ကျမ်း၏ စာအုပ်ခေါင်းစဉ်များကို အင်တာနက်မလိုဘဲ ကြည့်နိုင်ပါသည်။ မူရင်းစာသားဒေတာကို ပြန်လည်ဖြန့်ဝေခွင့်နှင့်တကွ ထည့်သွင်းထားခြင်းမရှိသေးပါ။ ကျမ်းဖတ်လိုပါက မိမိဖုန်းရှိ PDF/EPUB/TXT ဖိုင်ကို ရွေးချယ်နိုင်ပါသည်။",15));
    for(int i=0;i<NAMES.length;i++){
      final int index=i;String group=i<8?"ဝိနည်း":i<33?"သုတ္တန်":"အဘိဓမ္မာ";
      row(String.format(Locale.US,"%02d  %s\n%s",i+1,NAMES[i],group),()->openVolume(index));
    }
    row("📖  မိမိစာအုပ်ဖိုင် ဖွင့်ဖတ်ရန်",()->startActivity(new Intent(this,BookReaderActivity.class)));
    TextView close=text("‹ ပြန်ရန်",17);close.setTextColor(Color.WHITE);close.setBackgroundColor(GREEN);root.addView(close);close.setOnClickListener(v->finish());setContentView(root);
  }
  private void openVolume(int index){
    if(db==null){startActivity(new Intent(this,BookReaderActivity.class));return;}
    Intent popup=new Intent(this,ParagraphExplanationActivity.class);popup.putExtra("volume",index+1);startActivity(popup);return;
  }
  @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
