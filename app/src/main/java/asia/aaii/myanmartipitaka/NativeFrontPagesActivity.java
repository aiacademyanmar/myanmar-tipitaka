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
    if(p<=6){render(p);return;}
    Intent i=new Intent(this,ExactScreensActivity.class);i.putExtra("openPage",p);startActivity(i);
  }
  @Override public void onCreate(Bundle state){super.onCreate(state);page=state==null?getIntent().getIntExtra("openPage",1):state.getInt("page",1);render(Math.max(1,Math.min(6,page)));}
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
    if(n==4){
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
    ScrollView menuScroll=new ScrollView(this);LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);String[] menuTitles={"Home","Categories","Books","Native Reader","Search","Bookmarks","Reading History","About"};int[] menuTargets={2,4,5,6,10,12,13,20};
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
