package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import java.io.File;
import java.util.ArrayList;

/**
 * Accessible, native offline Dhammapada reading screen.
 * Contains original Pali sourced from the bundled licensed SQLite.
 * Myanmar study drafts are unreviewed and never mislabelled "approved".
 */
public final class DhammapadaYamakavaggaActivity extends Activity {
  private static final String PREFS="dhammapada_reader_v238";
  private static final int GREEN=0xff144638, GOLD=0xffa77a29, CREAM=0xfffaf6eb;
  private static final int INK=0xff20372e, MUTED=0xff685f50;
  private static final int PAGE_COUNT=26;
  private static final String[] NAMES={
    "ယမကဝဂ်","အပ္ပမာဒဝဂ်","စိတ္တဝဂ်","ပုပ္ဖဝဂ်","ဗာလဝဂ်",
    "ပဏ္ဍိတဝဂ်","အရဟန္တဝဂ်","သဟဿဝဂ်","ပါပဝဂ်","ဒဏ္ဍဝဂ်",
    "ဇရာဝဂ်","အတ္တဝဂ်","လောကဝဂ်","ဗုဒ္ဓဝဂ်","သုခဝဂ်",
    "ပိယဝဂ်","ကောဓဝဂ်","မလဝဂ်","ဓမ္မဋ္ဌဝဂ်","မဂ္ဂဝဂ်",
    "ပကိဏ္ဏကဝဂ်","နိရယဝဂ်","နာဂဝဂ်","တဏှာဝဂ်",
    "ဘိက္ခုဝဂ်","ဗြာဟ္မဏဝဂ်"
  };
  private SQLiteDatabase db;
  private ScrollView readerScroll;
  private LinearLayout rows;
  private Spinner chapters;
  private TextView indicator;
  private int chapter, fontSize;
  private volatile boolean destroyed=false;

  private int dp(int n){return (int)(getResources().getDisplayMetrics().density*n+0.5f);}
  private GradientDrawable background(int color,int radius){
    GradientDrawable d=new GradientDrawable();
    d.setColor(color);d.setCornerRadius(dp(radius));return d;
  }
  private TextView label(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(14),dp(12),dp(14),dp(12));return t;
  }
  private TextView action(String name,LinearLayout bar,Runnable callback){
    TextView b=label(name,16,Color.WHITE,true);
    b.setGravity(Gravity.CENTER);b.setOnClickListener(v->callback.run());
    bar.addView(b,new LinearLayout.LayoutParams(0,dp(52),1));return b;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    SharedPreferences p=getSharedPreferences(PREFS,MODE_PRIVATE);
    chapter=Math.max(1,Math.min(PAGE_COUNT,p.getInt("selectedChapter",1)));
    fontSize=Math.max(16,Math.min(32,p.getInt("fontSize",22)));
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);

    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(CREAM);
    TextView title=label("☸  ဓမ္မပဒ — Dhammapada",23,Color.WHITE,true);
    title.setBackgroundColor(GREEN);root.addView(title);
    TextView subtitle=label("ပါဠိ ၄၂၃ ဂါထာ • ၂၆ ဝဂ် • Internet မလိုသော စာဖတ်စနစ်",14,MUTED,false);
    root.addView(subtitle);

    chapters=new Spinner(this);
    String[] chapterLabels=new String[PAGE_COUNT];
    for(int i=0;i<PAGE_COUNT;i++)chapterLabels[i]=String.format(java.util.Locale.US,"%02d",i+1)+"  "+NAMES[i];
    chapters.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,chapterLabels));
    root.addView(chapters);
    chapters.setSelection(chapter-1);
    chapters.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){
      @Override public void onNothingSelected(android.widget.AdapterView<?> parent){}
      @Override public void onItemSelected(android.widget.AdapterView<?> parent,View view,int position,long id){
        int changed=position+1;
        if(chapter!=changed){chapter=changed;saveSelectedChapter();if(db!=null)showChapter();}
      }
    });
    LinearLayout tools=new LinearLayout(this);tools.setBackground(background(0xffe9e3d4,12));
    TextView minus=label("A−",17,GREEN,true);minus.setGravity(Gravity.CENTER);
    TextView plus=label("A+",17,GREEN,true);plus.setGravity(Gravity.CENTER);
    TextView resume=label("↪ ဆက်ဖတ်ရန်",15,GREEN,true);resume.setGravity(Gravity.CENTER);
    tools.addView(minus,new LinearLayout.LayoutParams(0,dp(50),1));
    tools.addView(plus,new LinearLayout.LayoutParams(0,dp(50),1));
    tools.addView(resume,new LinearLayout.LayoutParams(0,dp(50),2));
    root.addView(tools);
    minus.setOnClickListener(v->changeFont(-2));
    plus.setOnClickListener(v->changeFont(2));
    resume.setOnClickListener(v->resumeReading());

    indicator=label("ဝဂ် "+chapter+" / ၂၆",14,GOLD,true);root.addView(indicator);
    readerScroll=new ScrollView(this);readerScroll.setFillViewport(true);
    rows=new LinearLayout(this);rows.setOrientation(LinearLayout.VERTICAL);
    rows.setPadding(dp(10),0,dp(10),dp(16));
    readerScroll.addView(rows);root.addView(readerScroll,new LinearLayout.LayoutParams(-1,0,1));

    LinearLayout footer=new LinearLayout(this);footer.setBackgroundColor(GREEN);
    action("‹ ရှေ့ဝဂ်",footer,()->changeChapter(-1));
    action("နောက်ဝဂ် ›",footer,()->changeChapter(1));root.addView(footer);
    setContentView(root);
    message("Offline ပါဠိကျမ်းစာဒေတာကို ဖွင့်နေပါသည်…");
    new Thread(this::openDatabase,"dhammapada-reader-init").start();
  }
  private void message(String s){rows.addView(label(s,17,INK,false));}
  private void saveSelectedChapter(){
    getSharedPreferences(PREFS,MODE_PRIVATE).edit().putInt("selectedChapter",chapter).apply();
  }
  private void openDatabase(){
    SQLiteDatabase opened=null;
    try{
      File file=OfflineCorpusInstaller.prepare(getApplicationContext());
      opened=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      try(Cursor c=opened.rawQuery("SELECT COUNT(*),COUNT(DISTINCT chapter),MIN(verse),MAX(verse) FROM dhammapada_verses",null)){
        if(!c.moveToFirst() || c.getInt(0)!=423 || c.getInt(1)!=26 || c.getInt(2)!=1 || c.getInt(3)!=423)
          throw new IllegalStateException("Incomplete offline Dhammapada corpus");
      }
      if(destroyed){opened.close();return;}
      db=opened;
      runOnUiThread(()->{if(!destroyed)showChapter();});
    }catch(Exception e){
      if(opened!=null && opened!=db)opened.close();
      final String reason=e.getMessage()==null?"Unknown error":e.getMessage();
      runOnUiThread(()->{if(destroyed)return;rows.removeAllViews();
        message("ကျမ်းစာဖွင့်မရပါ — "+reason);
        Button retry=new Button(this);retry.setText("ပြန်စမ်းမည်");rows.addView(retry);
        retry.setOnClickListener(v->recreate());
      });
    }
  }
  private void showChapter(){
    if(db==null||destroyed)return;
    rows.removeAllViews();
    indicator.setText("ဝဂ် "+chapter+" / ၂၆ • "+NAMES[chapter-1]);
    saveSelectedChapter();
    int total=0;
    try(Cursor c=db.rawQuery(
        "SELECT verse,pali_text,my_draft FROM dhammapada_verses WHERE chapter=? ORDER BY verse",
        new String[]{Integer.toString(chapter)})){
      while(c.moveToNext()){
        final int verse=c.getInt(0);
        final String pali=c.getString(1);
        final String myDraft=c.isNull(2)?null:c.getString(2);
        LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
        card.setBackground(background(Color.WHITE,16));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(dp(2),dp(5),dp(2),dp(7));rows.addView(card,lp);
        TextView heading=label("ဓမ္မပဒ • ဂါထာ "+verse,14,GOLD,true);card.addView(heading);
        TextView text=label(pali,fontSize,INK,false);
        text.setTextIsSelectable(true);text.setLineSpacing(dp(5),1.08f);
        card.addView(text);
        TextView popupLink=label(myDraft==null?"မြန်မာဘာသာပြန် မရရှိသေးပါ • ပါဠိကိုကြည့်ရန် ›":
          "မြန်မာဘာသာပြန် Draft ကြည့်ရန် ›",15,GREEN,true);
        card.addView(popupLink);popupLink.setOnClickListener(v->{
          getSharedPreferences(PREFS,MODE_PRIVATE).edit().putInt("lastChapter",chapter).putInt("lastVerse",verse).apply();
          popup(verse,pali,myDraft);
        });
        total++;
      }
    }catch(Exception e){message("ကျမ်းစာ SQL ဖတ်၍မရပါ — "+e.getMessage());}
    if(total==0)message("ဤဝဂ်အတွက် ကျမ်းစာသား မတွေ့ပါ။");
    readerScroll.post(()->readerScroll.scrollTo(0,0));
  }
  private void popup(int verse,String pali,String draft){
    ScrollView popupScroll=new ScrollView(this);
    LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);
    panel.setPadding(dp(12),dp(12),dp(12),dp(14));
    TextView paliText=label("ပါဠိမူရင်း\n"+pali,fontSize,INK,false);
    paliText.setLineSpacing(dp(5),1.08f);paliText.setTextIsSelectable(true);panel.addView(paliText);
    TextView draftLabel=label(draft==null?"မြန်မာဘာသာပြန် မရှိသေးပါ":
      "မြန်မာဘာသာပြန် မူကြမ်း — ပညာရှင်အတည်မပြုရသေးပါ",14,GOLD,true);
    panel.addView(draftLabel);
    panel.addView(label(draft==null?"ဤဂါထာအတွက် မြန်မာဘာသာပြန် မရရှိသေးပါ။":draft,
      Math.max(18,fontSize-1),INK,false));
    panel.addView(label("မူရင်းပါဠိ — SuttaCentral/Bilara. မြန်မာမူကြမ်းသည် လေ့လာရေးအတွက်သာဖြစ်ပြီး စိစစ်အတည်ပြုထားသော တရားဝင်ဘာသာပြန် မဟုတ်ပါ။",13,MUTED,false));
    popupScroll.addView(panel);
    new AlertDialog.Builder(this).setTitle("☸ ဓမ္မပဒ ဂါထာ "+verse).setView(popupScroll)
      .setPositiveButton("ပိတ်မည်",null).show();
  }
  private void changeChapter(int delta){
    int target=chapter+delta;
    if(target>=1 && target<=PAGE_COUNT)chapters.setSelection(target-1);
  }
  private void changeFont(int delta){
    int next=Math.max(16,Math.min(32,fontSize+delta));
    if(next==fontSize)return;
    fontSize=next;
    getSharedPreferences(PREFS,MODE_PRIVATE).edit().putInt("fontSize",fontSize).apply();
    if(db!=null)showChapter();
  }
  private void resumeReading(){
    SharedPreferences p=getSharedPreferences(PREFS,MODE_PRIVATE);
    int lastChapter=p.getInt("lastChapter",0),lastVerse=p.getInt("lastVerse",0);
    if(lastChapter<1 || lastChapter>26 || lastVerse<1){
      Toast.makeText(this,"ဖတ်နေရာမှတ်တမ်း မရှိသေးပါ။",Toast.LENGTH_SHORT).show();return;
    }
    if(chapter!=lastChapter){
      chapters.setSelection(lastChapter-1);
      // Spinner callback renders the requested chapter before the posted search.
    }
    final String match="ဓမ္မပဒ • ဂါထာ "+lastVerse;
    rows.post(()->{
      for(int i=0;i<rows.getChildCount();i++){
        View card=rows.getChildAt(i);
        if(!(card instanceof LinearLayout))continue;
        LinearLayout c=(LinearLayout)card;
        if(c.getChildCount()==0 || !(c.getChildAt(0) instanceof TextView))continue;
        if(match.equals(((TextView)c.getChildAt(0)).getText().toString())){
          readerScroll.smoothScrollTo(0,card.getTop());return;
        }
      }
    });
  }
  @Override protected void onDestroy(){
    destroyed=true;
    if(db!=null)try{db.close();}catch(Exception ignored){}
    super.onDestroy();
  }
}
