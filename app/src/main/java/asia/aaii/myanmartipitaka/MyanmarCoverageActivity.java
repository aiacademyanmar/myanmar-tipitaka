package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.File;

/** Offline editorial coverage dashboard. Counts only rows imported as reviewed=1. */
public final class MyanmarCoverageActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6eb, GOLD=0xffb88730;
  private LinearLayout body;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private TextView label(String value,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(14),dp(12),dp(14),dp(12));return t;
  }
  private void card(String title,String value,String detail){
    LinearLayout c=new LinearLayout(this);c.setOrientation(1);
    GradientDrawable bg=new GradientDrawable();bg.setColor(Color.WHITE);bg.setCornerRadius(dp(16));c.setBackground(bg);
    c.addView(label(title,15,GREEN,true));c.addView(label(value,26,GOLD,true));c.addView(label(detail,13,0xff665b49,false));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(4),dp(5),dp(4),dp(5));body.addView(c,lp);
  }
  private long count(SQLiteDatabase db,String sql){
    try(Cursor c=db.rawQuery(sql,null)){return c.moveToFirst()?c.getLong(0):0;}
  }
  private void load(){
    body.removeAllViews();
    File file;
    try{file=OfflineCorpusInstaller.prepare(this);}catch(Exception e){body.addView(label("Offline Database ဖွင့်မရပါ။",17,GREEN,true));return;}
    try(SQLiteDatabase db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY)){
      long pali=count(db,"SELECT COUNT(*) FROM paragraphs");
      long volumes=count(db,"SELECT COUNT(DISTINCT volume) FROM paragraphs");
      boolean has=false;
      try(Cursor c=db.rawQuery("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paragraph_myanmar_content'",null)){has=c.moveToFirst();}
      long translations=0,explanations=0,both=0;
      if(has){
        translations=count(db,"SELECT COUNT(*) FROM paragraph_myanmar_content WHERE content_type='translation' AND reviewed=1");
        explanations=count(db,"SELECT COUNT(*) FROM paragraph_myanmar_content WHERE content_type='explanation' AND reviewed=1");
        both=count(db,"SELECT COUNT(*) FROM paragraphs p WHERE EXISTS(SELECT 1 FROM paragraph_myanmar_content t WHERE t.segment_id=p.segment_id AND t.content_type='translation' AND t.reviewed=1) AND EXISTS(SELECT 1 FROM paragraph_myanmar_content e WHERE e.segment_id=p.segment_id AND e.content_type='explanation' AND e.reviewed=1)");
      }
      body.addView(label("စိစစ်အတည်ပြုထားသော အကြောင်းအရာများကိုသာ ရေတွက်ထားပါသည်။",14,GREEN,false));
      card("ပါဠိမူရင်းစာပိုဒ်",String.format("%,d",pali),"ကျမ်း "+volumes+" / 45 အုပ်");
      card("မြန်မာအတည်ပြုဘာသာပြန်",String.format("%,d",translations),"reviewed = 1");
      card("မြန်မာအတည်ပြုရှင်းလင်းချက်",String.format("%,d",explanations),"reviewed = 1");
      card("ဘာသာပြန်နှင့် ရှင်းလင်းချက် နှစ်မျိုးလုံးရှိသော စာပိုဒ်",String.format("%,d",both),"စာပိုဒ်တစ်ခုတည်းတွင် နှစ်မျိုးလုံးရှိခြင်း");
      card("ကျန်ရှိနေသော ဘာသာပြန်",String.format("%,d",Math.max(0,pali-translations)),"မစိစစ်ရသေးသော AI စာသားများကို အတည်ပြုစာရင်းထဲ မထည့်ပါ။");
      TextView note=label("မှတ်ချက် — ဤ Dashboard သည် အတည်ပြုဒေတာ၏ အရေအတွက်ကိုသာ ပြသသည်။ Reviewer အမည်၊ ရင်းမြစ်နှင့် အတည်ပြုမှတ်တမ်းကို စာပိုဒ်တစ်ခုချင်းစီ၏ Reader Popup တွင် စစ်ဆေးပါ။",14,0xff665b49,false);
      body.addView(note);
    }catch(Exception e){body.addView(label("Coverage အချက်အလက်ဖတ်၍မရပါ။ Database schema ကို စစ်ဆေးပါ။",16,GREEN,true));}
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(CREAM);
    TextView head=label("☸ Myanmar Translation Coverage",21,Color.WHITE,true);head.setBackgroundColor(GREEN);root.addView(head);
    ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);body.setPadding(dp(14),dp(10),dp(14),dp(20));scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    Button search=new Button(this);search.setText("မြန်မာ / ပါဠိ Offline Search ဖွင့်ရန်");root.addView(search);search.setOnClickListener(v->startActivity(new Intent(this,OfflineSearchActivity.class)));
    Button refresh=new Button(this);refresh.setText("အချက်အလက် ပြန်စစ်မည်");root.addView(refresh);refresh.setOnClickListener(v->load());
    load();
  }
}
