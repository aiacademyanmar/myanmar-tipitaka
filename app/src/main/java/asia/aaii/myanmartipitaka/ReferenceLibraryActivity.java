package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;

/** Curated external online reading links. This screen opens source publishers directly;
 * it does not download, mirror, or import copyrighted books into the APK. */
public final class ReferenceLibraryActivity extends Activity {
  private static final int GREEN=0xff144638, GOLD=0xffba8730, CREAM=0xfffaf6e7, INK=0xff203a2f;
  private LinearLayout list;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
  private TextView label(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(12),dp(8),dp(12),dp(8));return t;
  }
  private void section(String title,String subtitle){
    TextView h=label(title,20,GREEN,true);h.setPadding(dp(4),dp(18),dp(4),dp(2));list.addView(h);
    TextView sub=label(subtitle,13,INK,false);sub.setPadding(dp(4),0,dp(4),dp(8));list.addView(sub);
  }
  private void open(String url){
    try{
      Intent i=new Intent(this,OnlineBookReaderActivity.class);
      i.putExtra("url",url);
      i.putExtra("source_title","Myanmar Tipitaka Reference");
      startActivity(i);
    }catch(Exception e){Toast.makeText(this,"In-App Reader ဖွင့်၍မရပါ",Toast.LENGTH_LONG).show();}
  }
  private void source(String title,String description,String status,String url){
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.VERTICAL);
    card.setPadding(dp(13),dp(10),dp(13),dp(10));card.setBackground(bg(Color.WHITE,16));card.setElevation(dp(2));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(5),0,dp(5));
    TextView name=label(title,17,GREEN,true);name.setPadding(0,0,0,dp(3));card.addView(name);
    TextView desc=label(description,14,INK,false);desc.setPadding(0,0,0,dp(5));card.addView(desc);
    TextView tag=label(status,12,GOLD,true);tag.setPadding(0,0,0,dp(6));card.addView(tag);
    TextView action=label("↗  Online တွင် တိုက်ရိုက်ဖတ်ရှုရန်",15,Color.WHITE,true);
    action.setGravity(Gravity.CENTER);action.setBackground(bg(GREEN,12));card.addView(action);
    card.setOnClickListener(v->open(url));action.setOnClickListener(v->open(url));
    list.addView(card,lp);
  }
  private void linkButton(String title,String url){
    TextView b=label(title,14,GREEN,true);b.setGravity(Gravity.CENTER);
    b.setBackground(bg(0xffeee6d3,12));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-2,1);lp.setMargins(dp(2),dp(3),dp(2),dp(3));
    b.setOnClickListener(v->open(url));list.addView(b,lp);
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    TextView head=label("☸  Online Reference Library",22,Color.WHITE,true);head.setBackgroundColor(GREEN);
    head.setPadding(dp(18),dp(20),dp(18),dp(20));root.addView(head);
    ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);
    list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);list.setPadding(dp(16),dp(8),dp(16),dp(24));
    scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    section("၁။ အစိုးရနှင့် တက္ကသိုလ် စာကြည့်တိုက်များ","မြန်မာပြန် ပိဋကတ်စာအုပ်များအတွက် ဦးစားပေးရင်းမြစ်");
    source("ကမ္ဘာအေး ဗုဒ္ဓသုတေသနစာကြည့်တိုက် — KBRL",
      "ဆဋ္ဌမူ ပိဋကတ်သုံးပုံ ပါဠိတော် မြန်မာပြန် Catalog • စာအုပ် ၃၂ ခု စာရင်းပြထားသည်။ စာအုပ်တစ်အုပ်ချင်းတွင် Preview / Download ကို ရွေးနိုင်သည်။",
      "Official Library • Online Preview / Download • အသုံးပြုခွင့် သီးခြားစစ်ဆေးရန်",
      "https://www.kbrl.gov.mm/catalog/index/5");
    TextView kbrlPages=label("KBRL စာရင်းစာမျက်နှာများ",14,GREEN,true);list.addView(kbrlPages);
    LinearLayout pages=new LinearLayout(this);pages.setOrientation(LinearLayout.HORIZONTAL);
    list.addView(pages);
    for(int i=1;i<=3;i++){
      final int page=i;
      TextView b=label("စာမျက်နှာ "+i,14,GREEN,true);b.setGravity(Gravity.CENTER);b.setBackground(bg(0xffeee6d3,12));
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(0,-2,1);lp.setMargins(dp(2),dp(3),dp(2),dp(3));pages.addView(b,lp);
      b.setOnClickListener(v->open(page==1?"https://www.kbrl.gov.mm/catalog/index/5":page==2?"https://www.kbrl.gov.mm/catalog/Index/5?page=2":"https://www.kbrl.gov.mm/catalog/Index/5?page=3"));
    }
    source("နိုင်ငံတော် ပရိယတ္တိသာသနာ့တက္ကသိုလ် စာကြည့်တိုက်",
      "ဆဋ္ဌမူ ပိဋကတ်သုံးပုံ ပါဠိမြန်မာပြန် Catalog • စာအုပ် ၃၁ ခု စာရင်းပြထားပြီး စာအုပ်စာမျက်နှာတွင် Download လင့်ခ်များရှိသည်။",
      "University Library • Catalog / Download • Permission စစ်ဆေးရန်",
      "https://spsuygn.edu.mm/book/reference/2");
    TextView catalog=label("📚 KBRL မြန်မာပြန်စာအုပ်များကို App အတွင်းရှာရန်",15,Color.WHITE,true);
    catalog.setGravity(Gravity.CENTER);catalog.setBackground(bg(GREEN,12));
    catalog.setOnClickListener(v->startActivity(new Intent(this,KbrlBookCatalogActivity.class)));
    list.addView(catalog,new LinearLayout.LayoutParams(-1,-2));
    section("၂။ မြန်မာပြန် PDF / Online Text","စာအုပ်အလိုက် ရင်းမြစ်ကို ရှာဖွေဖတ်ရှုရန်");
    source("Sariputta — Myanmar Tipitaka PDF",
      "ဝိနည်း၊ သုတ္တန်၊ အဘိဓမ္မာနှင့် ဓမ္မပဒ အပါအဝင် မြန်မာ PDF စာအုပ်များကို တစ်အုပ်ချင်း ရွေးချယ်နိုင်သည်။",
      "Myanmar PDF Collection • တစ်အုပ်ချင်း PDF Link",
      "https://www.sariputta.com/tipitaka/myanmar");
    source("Myanmar Sutta — သုတ္တန်ပိဋကတ်",
      "ဒီဃ၊ မဇ္ဈိမ၊ သံယုတ္တ၊ အင်္ဂုတ္တရနှင့် ခုဒ္ဒကနိကာယ်မှ သုတ္တန်များကို Online ဖတ်ရှုနိုင်သည်။ Website က သုတ္တန် ၁,၀၀၀ ကျော် စုစည်းထားကြောင်း ဖော်ပြထားသည်။",
      "Sutta Reference • သုတ္တန်အပိုင်းသာ • ၄၅ ကျမ်းအပြည့်မဟုတ်",
      "https://myanmarsutta.net/");
    source("Win Metta — Dhamma Download Resources",
      "မြန်မာပိဋကတ် PDF ZIP နှင့် အခြားစာကြည့်တိုက်များသို့ ချိတ်ဆက်ထားသော Resource Directory ဖြစ်သည်။",
      "Resource Directory • Download Link များ",
      "https://winmetta.org/dhamma-download/");
    section("၃။ ပါဠိနှင့် ဘာသာပြန် နှိုင်းယှဉ်ဖတ်ရှုရန်","အောက်ပါ AI ဘာသာပြန်များကို အတည်ပြုမြန်မာပြန်အဖြစ် မယူဆရ");
    source("E-Piṭaka — Myanmar Translation",
      "ဆဋ္ဌသင်္ဂါယနာ ပိဋကတ်ကို ဘာသာစကားများစွာဖြင့် စာကြောင်းအလိုက် ဖတ်ရှုနိုင်သည်။ Project က မြန်မာဘာသာပြန်ကို AI-assisted study aid ဟု ရှင်းလင်းထားသည်။",
      "AI-Assisted Reference • ပညာရှင်အတည်ပြု မြန်မာပြန်မဟုတ်",
      "https://epitaka.org/my/");
    source("Tipitaka.cloud — Online Pāli Library",
      "ပိဋကတ် ၄၅ ကျမ်း၏ ပါဠိ/ထိုင်း Edition နှင့် ဓမ္မပဒ၊ မင်္ဂလသုတ်၊ နိဗ္ဗာန်၊ သတိပဋ္ဌာန် စာမျက်နှာများကို ဖတ်ရှုရန်။",
      "Pāli / Thai Reference • မြန်မာအတည်ပြုဘာသာပြန် မဟုတ်",
      "https://tipitaka.cloud/library");
    source("Tipiṭaka Online — CST / Pāli Reference",
      "CST ပါဠိမူရင်းနှင့် ကျမ်းညွှန်းများကို နှိုင်းယှဉ်ရန်။ မြန်မာ AI output ကို အတည်ပြုစာသားအဖြစ် မသတ်မှတ်ရန်။",
      "Pāli Reference • Myanmar AI text is not verified",
      "https://tipitakaonline.org/");
    section("၄။ ကျမ်းကိုးစာရင်းနှင့် ပညာရေးဆိုင်ရာ အထောက်အထား","စာရေးသူ၊ ထုတ်ဝေသူ၊ Edition နှင့် Bibliography စစ်ဆေးရန်");
    source("University of Global Peace — Tipitaka Referencing Guide",
      "မြန်မာနှင့် PTS Edition များ၏ စာအုပ်အမည်၊ ထုတ်ဝေသူ၊ ထုတ်ဝေခုနှစ် စသည့် Bibliography ကို စစ်ဆေးရန်။",
      "Bibliography Only • စာအုပ်ဖတ်ရှုရာမဟုတ်",
      "https://ugp.edu.mm/online-resources/");
    source("International Theravada Buddhist Missionary University — Library",
      "မြန်မာဘာသာ ပိဋကတ်စာအုပ်များ အပါအဝင် စာကြည့်တိုက်စုဆောင်းမှုကို စုံစမ်းရန်။ ဤစာမျက်နှာသည် Physical Library အချက်အလက်ဖြစ်သည်။",
      "Physical Library Information • Online full-text မဟုတ်",
      "https://itbmu.org.mm/librarys");
    TextView policy=label("သတိပြုရန် — ဤလင့်ခ်များသည် မူရင်းထုတ်ဝေသူ/စာကြည့်တိုက် Website များသို့ တိုက်ရိုက်ချိတ်ဆက်ခြင်းသာ ဖြစ်သည်။ App ထဲသို့ စာအုပ်ဖိုင်များကို ကူးယူထည့်သွင်းထားခြင်း မဟုတ်ပါ။ PDF Download, Offline APK ထည့်သွင်းခြင်းနှင့် ပြန်လည်ဖြန့်ဝေခြင်းမပြုမီ မူပိုင်ခွင့်နှင့် ခွင့်ပြုချက်ကို စစ်ဆေးပါ။",
      13,INK,false);policy.setBackground(bg(0xffeee6d3,12));list.addView(policy);
    Button back=new Button(this);back.setText("‹  App သို့ ပြန်ရန်");root.addView(back);back.setOnClickListener(v->finish());
    setContentView(root);
  }
}
