package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.*;
import android.widget.*;

/** Native, accessible first three screens; no bitmap screenshot is used. */
public class NativeFrontPagesActivity extends Activity {
  private static final int GREEN=Color.rgb(18,69,58),GOLD=Color.rgb(186,135,48),CREAM=Color.rgb(250,246,231),INK=Color.rgb(32,58,47);
  private LinearLayout root,content,menuPanel;
  private int page=1;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));return g;}
  private TextView text(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(12),dp(12),dp(12),dp(12));return t;
  }
  private void addText(String s,int size,int color,boolean bold){content.addView(text(s,size,color,bold));}
  private void button(String title,int target){
    TextView b=text(title,18,INK,true);b.setBackground(bg(Color.WHITE,18));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(4),dp(6),dp(4),dp(6));
    content.addView(b,lp);b.setElevation(dp(2));b.setOnClickListener(v->go(target));
  }
  private void go(int p){
    if(p==3){toggleMenu();return;}
    if(p<=12){render(p);return;}
    Intent i=new Intent(this,ExactScreensActivity.class);i.putExtra("openPage",p);startActivity(i);
  }
  @Override public void onCreate(Bundle state){super.onCreate(state);page=state==null?getIntent().getIntExtra("openPage",1):state.getInt("page",1);render(Math.max(1,Math.min(12,page)));}
  private void render(int n){
    page=n;getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    LinearLayout head=new LinearLayout(this);head.setOrientation(LinearLayout.HORIZONTAL);head.setGravity(Gravity.CENTER_VERTICAL);head.setBackgroundColor(GREEN);
    TextView brand=text("☸  မြန်မာ့ပိဋကတ်တော်",21,Color.WHITE,true);
    head.addView(brand,new LinearLayout.LayoutParams(0,-2,1));
    TextView menu=text("☰",27,Color.WHITE,true);head.addView(menu);menu.setOnClickListener(v->toggleMenu());
    root.addView(head);
    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
    content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);content.setPadding(dp(18),dp(15),dp(18),dp(28));
    scroll.addView(content);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    if(n==10){
      addText("ပိဋကတ်တော် ရှာဖွေရန်",26,GREEN,true);
      addText("Search • မြန်မာ / Pāli",16,GOLD,false);
      EditText query=new EditText(this);query.setSingleLine(true);query.setTextSize(19);
      query.setHint("ရှာဖွေလိုသော စကားလုံး");query.setText(getPreferences(MODE_PRIVATE).getString("searchQuery",""));
      query.setBackground(bg(Color.WHITE,14));query.setPadding(dp(16),dp(13),dp(16),dp(13));
      content.addView(query);
      String[] filters={"အားလုံး","သုတ္တန်","ဝိနည်း","အဘိဓမ္မာ"};
      Spinner filter=new Spinner(this);ArrayAdapter<String> adapter=new ArrayAdapter<>(this,android.R.layout.simple_spinner_dropdown_item,filters);
      filter.setAdapter(adapter);content.addView(filter);
      TextView find=text("⌕   ရှာဖွေရန်",19,Color.WHITE,true);find.setBackground(bg(GREEN,16));content.addView(find);
      find.setOnClickListener(v->{String q=query.getText().toString().trim();
        if(q.isEmpty()){query.setError("စာသားထည့်ပါ");return;}
        getPreferences(MODE_PRIVATE).edit().putString("searchQuery",q).putString("searchFilter",filters[filter.getSelectedItemPosition()]).apply();
        go(11);
      });
      addText("မှတ်ချက် — လက်ရှိတွင် Menu/ခေါင်းစဉ်များကိုသာ ရှာနိုင်ပါသည်။ ပိဋကတ်တော် စာသားအပြည့်အစုံ Search အတွက် Index Database လိုအပ်ပါသည်။",14,INK,false);
    }else if(n==11){
      String q=getPreferences(MODE_PRIVATE).getString("searchQuery","");
      addText("ရှာဖွေမှုရလဒ်",26,GREEN,true);
      addText("Search Results • "+q,16,GOLD,true);
      if(q.isEmpty()){addText("ရှာဖွေမည့် စကားလုံးမရှိသေးပါ။",16,INK,false);button("ရှာဖွေရန်",10);}
      else{
        String[] titles={"ဝိနည်းပိဋကတ်","သုတ္တန်ပိဋကတ်","အဘိဓမ္မာပိဋကတ်","နိကာယ်ငါးရပ်","မင်္ဂလသုတ်","ဓမ္မစာအုပ်တိုက်","PDF EPUB TXT Reader"};
        int[] targets={4,4,15,19,18,7,6};int count=0;
        for(int i=0;i<titles.length;i++)if(titles[i].toLowerCase(java.util.Locale.ROOT).contains(q.toLowerCase(java.util.Locale.ROOT))){button(titles[i],targets[i]);count++;}
        if(count==0)addText("အက်ပ်၏ လက်ရှိခေါင်းစဉ်များတွင် ကိုက်ညီမှုမရှိပါ။ ပိဋကတ်တော် Full-text Index မထည့်သွင်းရသေးပါ။",16,INK,false);
        button("ရှာဖွေမှု ပြန်ပြင်ရန်",10);
      }
    }else if(n==12){
      addText("စာမှတ်များနှင့် မှတ်စု",26,GREEN,true);
      addText("Bookmarks & Notes",16,GOLD,true);
      String old=getPreferences(MODE_PRIVATE).getString("note","");
      EditText note=new EditText(this);note.setText(old);note.setTextSize(18);note.setMinLines(5);
      note.setGravity(Gravity.TOP);note.setHint("မိမိမှတ်စု ရေးသားရန်...");
      note.setBackground(bg(Color.WHITE,14));note.setPadding(dp(16),dp(13),dp(16),dp(13));
      content.addView(note);
      TextView save=text("✓   မှတ်စု သိမ်းမည်",18,Color.WHITE,true);save.setBackground(bg(GREEN,14));content.addView(save);
      save.setOnClickListener(v->{getPreferences(MODE_PRIVATE).edit().putString("note",note.getText().toString()).apply();
        Toast.makeText(this,"မှတ်စု သိမ်းဆည်းပြီး",Toast.LENGTH_SHORT).show();});
      button("စာအုပ်ဖတ်စက် (Reader Bookmark)",6);
      button("ဆက်လက်ဖတ်ရှုရန်",8);
      addText("စာမှတ်များကို Reader အတွင်း သိမ်းဆည်းထားနိုင်ပြီး စာမှတ်တစ်ခုချင်းကို Reader ၏ Go to → Bookmark ဖြင့် ဖွင့်နိုင်ပါသည်။",14,INK,false);
    }else if(n==7){
      addText("ဓမ္မစာအုပ်တိုက်",26,GREEN,true);
      addText("My Offline Library",16,GOLD,false);
      addText("ဖုန်းအတွင်းရှိ PDF, EPUB နှင့် UTF-8 TXT စာအုပ်များကို ရွေးချယ်ဖတ်ရှုနိုင်ပါသည်။",16,INK,false);
      TextView open=text("＋  စာအုပ်ဖိုင်ရွေးပြီး ဖတ်ရန်",19,Color.WHITE,true);
      open.setBackground(bg(GREEN,18));content.addView(open);
      open.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
      button("နောက်ဆုံးဖတ်ခဲ့သော စာအုပ်",8);
      button("ပိဋကတ်တော် အမျိုးအစားများ",4);
      button("သုတ် • ဝိနည်း • အဘိဓမ္မာ",5);
      addText("မှတ်ချက် — စာအုပ်စာရင်း Database မပါသေးပါ။ ဖိုင်ရွေးချယ်ခြင်းကို Android System Picker ဖြင့် ပြုလုပ်ပါသည်။",14,INK,false);
    }else if(n==8){
      addText("စာဖတ်ခြင်းနှင့် ဆက်လက်ဖတ်ရှုရန်",25,GREEN,true);
      addText("Reading & Continue",16,GOLD,true);
      addText("Reader အတွင်း နောက်ဆုံးဖွင့်ခဲ့သော PDF, EPUB သို့မဟုတ် TXT စာအုပ်နှင့် ဖတ်နေရာကို အလိုအလျောက် မှတ်သားထားပါသည်။",16,INK,false);
      TextView resume=text("▶  ဆက်လက်ဖတ်ရှုရန်",19,Color.WHITE,true);
      resume.setBackground(bg(GREEN,18));content.addView(resume);
      resume.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
      button("စာအုပ်အသစ်ဖွင့်ရန်",7);
      button("Native Reader Settings",6);
      button("စာမှတ်များနှင့် မှတ်စု",12);
    }else if(n==9){
      addText("ဓမ္မလေ့လာရေး",27,GREEN,true);
      addText("Dhamma Learning",16,GOLD,true);
      addText("ပိဋကတ်တော်ကို အကြောင်းအရာအလိုက် လေ့လာရန် လမ်းညွှန်",16,INK,false);
      button("၁။ သုံးပုံပိဋကတ်ကို လေ့လာရန်",4);
      button("၂။ သုတ္တန်နှင့် နိကာယ်ငါးရပ်",19);
      button("၃။ အဘိဓမ္မာကို လေ့လာရန်",15);
      button("၄။ မင်္ဂလသုတ် လေ့လာရန်",18);
      button("၅။ မိမိစာအုပ်ကို ဖွင့်ဖတ်ရန်",6);
      addText("သင်ခန်းစာစာသား၊ မေးခွန်းနှင့် အဖြေဒေတာကို နောက်ဆက်တွဲ ထည့်သွင်းရန် လိုအပ်ပါသည်။",14,INK,false);
    }else if(n==4){
      addText("ပိဋကတ်တော် အမျိုးအစားများ",26,GREEN,true);
      addText("သုံးပုံပိဋကတ် • Tipitaka Collections",16,GOLD,false);
      button("☸  ဝိနည်းပိဋကတ် — Vinaya Pitaka",5);
      button("☸  သုတ္တန်ပိဋကတ် — Sutta Pitaka",5);
      button("☸  အဘိဓမ္မာပိဋကတ် — Abhidhamma Pitaka",15);
      addText("စာအုပ်အုပ်စုတစ်ခုကို ရွေးပြီး ဖတ်ရှုနိုင်ပါသည်။",15,INK,false);
    }else if(n==5){
      addText("ပိဋကတ်တော် စာအုပ်များ",26,GREEN,true);
      addText("စာအုပ်ဖတ်စက်အတွက် ဖိုင်ရွေးချယ်ပါ",16,GOLD,false);
      button("📖  PDF / EPUB / TXT ဖိုင်ဖွင့်ရန်",6);
      button("သုတ္တန်ပိဋကတ် — နိကာယ်ငါးရပ်",19);
      button("ဝိနည်းပိဋကတ်",6);
      button("အဘိဓမ္မာပိဋကတ်",16);
      addText("မူရင်းစာအုပ်ဒေတာဘေ့စ် မထည့်သွင်းရသေးသဖြင့် မိမိဖုန်းရှိ စာအုပ်ဖိုင်များကို ဖွင့်ဖတ်နိုင်ပါသည်။",15,INK,false);
    }else if(n==6){
      addText("Native Book Reader",27,GREEN,true);
      addText("မြန်မာ • ပါဠိ စာဖတ်စက်",18,GOLD,true);
      addText("Offline PDF / EPUB / TXT Reader",16,INK,false);
      TextView open=text("📖   စာအုပ်ဖိုင် ရွေးချယ်ဖွင့်ရန်",19,Color.WHITE,true);
      open.setBackground(bg(GREEN,18));content.addView(open);
      open.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
      button("စာအုပ်စာရင်းသို့ ပြန်သွားရန်",5);
      button("စာမှတ်များနှင့် မှတ်စု",12);
    }else if(n==1){
      addText("☸",70,GOLD,true);
      addText("မြန်မာ့ပိဋကတ်တော်",28,GREEN,true);
      addText("Myanmar Tipitaka",21,GOLD,true);
      addText("ဗုဒ္ဓမြတ်စွာဘုရား၏ တရားတော်များကို လေ့လာဖတ်ရှုရန်",17,INK,false);
      button("စတင်လေ့လာရန်  →",2);button("စာအုပ်ဖတ်ရန်",6);button("ပိဋကတ်တော် ရှာဖွေရန်",10);
      addText("ပါဠိ • မြန်မာ • Offline Reader",14,GREEN,false);
    }else if(n==2){
      addText("ကြိုဆိုပါသည်",27,GREEN,true);
      addText("ပိဋကတ်တော် လေ့လာရေး",18,INK,false);
      button("☸   ပိဋကတ်တော် အမျိုးအစားများ",4);
      button("▤   စာအုပ်များ",5);button("📖   စာအုပ်ဖတ်စက်",6);
      button("⌕   အကြောင်းအရာ ရှာဖွေရန်",10);
      button("🔖   စာမှတ်များနှင့် မှတ်စု",12);
      button("◷   ဆက်လက်ဖတ်ရှုရန်",13);
      addText("သုတ် • ဝိနည်း • အဘိဓမ္မာ",18,GOLD,true);
      button("နိကာယ်ငါးရပ်",19);
    }else{
      addText("လမ်းညွှန် မီနူး",27,GREEN,true);
      addText("Navigation Menu",16,GOLD,false);
      String[] names={"မူလစာမျက်နှာ","ပိဋကတ်တော် မိတ်ဆက်","ပိဋကတ် အမျိုးအစားများ","စာအုပ်များ","Native Reader","စာအုပ်တိုက်","စာဖတ်ခြင်း","လေ့လာရန်","Search","Search Results","စာမှတ်များ","History","Advanced Search","အဘိဓမ္မာ","အဘိဓမ္မာ Reader","ဓမ္မသင်ခန်းစာ","မင်္ဂလသုတ်","နိကာယ်ငါးရပ်","About & Help"};
      int[] targets={2,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20};
      for(int i=0;i<targets.length;i++)button(String.format(java.util.Locale.US,"%02d  %s",targets[i],names[i]),targets[i]);
    }
    menuPanel=new LinearLayout(this);menuPanel.setOrientation(LinearLayout.VERTICAL);menuPanel.setBackground(bg(Color.WHITE,18));menuPanel.setVisibility(View.GONE);
    ScrollView menuScroll=new ScrollView(this);LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);String[] menuTitles={"Home","Categories","Books","Native Reader","Library","Continue Reading","Learning","Search","Search Results","Bookmarks","Reading History","About"};int[] menuTargets={2,4,5,6,7,8,9,10,11,12,13,20};
    for(int i=0;i<menuTitles.length;i++){final int target=menuTargets[i];TextView item=text(menuTitles[i],17,GREEN,true);items.addView(item);item.setOnClickListener(v->go(target));}
    menuScroll.addView(items);menuPanel.addView(menuScroll,new LinearLayout.LayoutParams(-1,dp(235)));
    root.addView(menuPanel);
    LinearLayout nav=new LinearLayout(this);nav.setGravity(Gravity.CENTER);nav.setBackgroundColor(GREEN);
    String[] keys={"⌂ Home","▤ Books","☰ Menu","⌕ Search"};
    int[] targets={2,5,3,10};
    for(int i=0;i<4;i++){final int target=targets[i];TextView v=text(keys[i],13,Color.WHITE,false);
      v.setGravity(Gravity.CENTER);nav.addView(v,new LinearLayout.LayoutParams(0,dp(55),1));v.setOnClickListener(w->go(target));}
    root.addView(nav);setContentView(root);
  }
  private void toggleMenu(){if(menuPanel!=null)menuPanel.setVisibility(menuPanel.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE);}
  @Override public void onBackPressed(){if(page!=1)render(1);else super.onBackPressed();}
  @Override protected void onSaveInstanceState(Bundle b){b.putInt("page",page);super.onSaveInstanceState(b);}
}
