package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.File;

/** Standalone offline Maṅgala Sutta: canonical Pali stanzas + clearly-labelled Myanmar study drafts. */
public final class MangalaSuttaActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6eb, INK=0xff193b30, GOLD=0xff96702b;
  private SQLiteDatabase db;
  private LinearLayout list;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
  private TextView text(String value,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(15),dp(13),dp(15),dp(13));return t;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    TextView header=text("☸  မင်္ဂလသုတ် — မင်္ဂလာ ၃၈ ပါး\nMaṅgala Sutta · Sutta Nipāta 2.4",21,Color.WHITE,true);
    header.setBackgroundColor(GREEN);root.addView(header);
    TextView status=text("ပါဠိမူရင်းနှင့် မြန်မာလေ့လာရေးမူကြမ်း • Offline",14,GOLD,true);root.addView(status);
    ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);list.setPadding(dp(10),dp(6),dp(10),dp(20));scroll.addView(list);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TextView back=text("‹  စာအုပ်တိုက်သို့ ပြန်ရန်",16,Color.WHITE,true);back.setBackgroundColor(GREEN);root.addView(back);back.setOnClickListener(v->finish());
    setContentView(root);
    TextView loading=text("Offline မင်္ဂလသုတ်ကို ဖွင့်နေပါသည်…",18,INK,false);list.addView(loading);
    new Thread(()->openDb(status), "mangala-offline").start();
  }
  private void openDb(TextView status){
    SQLiteDatabase opened=null;
    try{
      File f=OfflineCorpusInstaller.prepare(getApplicationContext());
      opened=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      try(Cursor c=opened.rawQuery("SELECT COUNT(*) FROM mangala_blessings",null)){
        if(!c.moveToFirst()||c.getInt(0)!=38)throw new IllegalStateException("မင်္ဂလာ ၃၈ ပါး ဒေတာ မပြည့်စုံပါ။");
      }
      db=opened;
      runOnUiThread(()->{status.setText("✓ Offline • မင်္ဂလာ ၃၈ ပါး • ပါဠိ ၁၃ ဂါထာ");load();});
    }catch(Exception e){
      if(opened!=null)try{opened.close();}catch(Exception ignored){}
      String msg=e.getMessage()==null?"Offline Database error":e.getMessage();
      runOnUiThread(()->{list.removeAllViews();list.addView(text("မင်္ဂလသုတ်ဒေတာ ဖွင့်မရပါ။\n"+msg,17,INK,false));});
    }
  }
  private void load(){
    if(db==null)return;list.removeAllViews();
    list.addView(text("ဤစာအုပ်တွင် မင်္ဂလာတရား ၃၈ ပါးကို အုပ်စု ၁၀ စုဖြင့် ဖတ်ရှုနိုင်ပါသည်။ အကြောင်းအရာကို နှိပ်၍ ပါဠိမူရင်းနှင့် မြန်မာရှင်းလင်းချက်ကို ဖွင့်ပါ။",16,INK,false));
    int lastGroup=-1;
    try(Cursor c=db.rawQuery("SELECT number,group_no,group_title_my,stanza_ref,title_my,explanation_my,translation_status FROM mangala_blessings ORDER BY number",null)){
      while(c.moveToNext()){
        int no=c.getInt(0),group=c.getInt(1);String groupTitle=c.getString(2),stanza=c.getString(3),title=c.getString(4),ex=c.getString(5),state=c.getString(6);
        if(group!=lastGroup){TextView gh=text("အုပ်စု "+group+"  ·  "+groupTitle,16,GREEN,true);list.addView(gh);lastGroup=group;}
        TextView card=text(String.format(java.util.Locale.ROOT,"%02d   %s\nပါဠိနှင့် မြန်မာရှင်းလင်းချက် ဖတ်ရန်  ›",no,title),17,INK,true);
        card.setBackground(bg(Color.WHITE,14));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(2),dp(4),dp(2),dp(6));list.addView(card,lp);
        card.setOnClickListener(v->showBlessing(no,stanza,title,ex,state));
      }
    }catch(Exception e){list.addView(text("စာရင်းဖတ်ရှုမှု အမှား: "+e.getMessage(),16,INK,false));}
  }
  private void showBlessing(int number,String stanza,String title,String explanation,String state){
    String pali="";
    try(Cursor c=db.rawQuery("SELECT pali_text FROM mangala_pali_stanzas WHERE stanza=?",new String[]{stanza})){
      if(c.moveToFirst())pali=c.getString(0);
    }
    LinearLayout box=new LinearLayout(this);box.setOrientation(LinearLayout.VERTICAL);box.setPadding(dp(8),dp(4),dp(8),dp(4));
    TextView label=text("ပါဠိမူရင်း ဂါထာ — "+stanza,14,GOLD,true);box.addView(label);
    TextView paliText=text(pali,19,INK,false);paliText.setLineSpacing(dp(5),1.1f);box.addView(paliText);
    TextView myLabel=text("မင်္ဂလာ "+number+" — မြန်မာအဓိပ္ပာယ်",15,GREEN,true);box.addView(myLabel);
    TextView myText=text(title+"\n\n"+explanation,18,INK,false);myText.setLineSpacing(dp(5),1.12f);box.addView(myText);
    TextView draft=text("မှတ်ချက် — မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက်သည် AI လေ့လာရေးမူကြမ်းဖြစ်ပြီး ပညာရှင်အတည်ပြုချက် မရသေးပါ။",13,GOLD,false);box.addView(draft);
    ScrollView scroll=new ScrollView(this);scroll.addView(box);
    new AlertDialog.Builder(this).setTitle("☸  မင်္ဂလာ "+number).setView(scroll).setPositiveButton("ဖတ်ပြီးပါပြီ",null).show();
  }
  @Override protected void onDestroy(){if(db!=null&&db.isOpen())db.close();super.onDestroy();}
}
