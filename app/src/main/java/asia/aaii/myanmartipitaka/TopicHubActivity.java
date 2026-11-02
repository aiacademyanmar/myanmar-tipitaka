package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.content.res.ColorStateList;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.graphics.drawable.RippleDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

/**
 * Native 5-topic menu integrating bundled offline study readers with the
 * reference links provided by the user. Website links require internet.
 *
 * No claim that the topic-specific Myanmar study drafts have received
 * independent academic review. MCU 45-volume exact crosswalk is also pending.
 */
public final class TopicHubActivity extends Activity {
  public static final String EXTRA_TOPIC="topic_index";
  private static final int GREEN=0xff174b3b, CREAM=0xfffaf7ec, GOLD=0xffe9c06e, INK=0xff284b3a;
  private static final String[] TITLE={
      "ဓမ္မပဒ (Dhammapada)",
      "မင်္ဂလသုတ် (Maṅgala Sutta)",
      "နိဗ္ဗာန် (Nibbāna)",
      "သတိပဋ္ဌာန် (Satipaṭṭhāna)",
      "နိကာယ် ၅ မျိုး"
  };
  private static final String[] SUBTITLE={
      "ဂါထာ ၄၂၃ ပုဒ် · ဝဂ် ၂၆ ခု",
      "မင်္ဂလာ ၃၈ ပါး",
      "ဒုက္ခနိဋ္ဌောဟူသော နိဗ္ဗာန်",
      "သတိပဋ္ဌာန် ၄ ပါး",
      "ဒီဃ၊ မဇ္ဈိမ၊ သံယုတ္တ၊ အင်္ဂုတ္တရ၊ ခုဒ္ဒက"
  };
  private static final String[] URL={
      "https://tipitaka.cloud/en/learn/suttas/dhammapada",
      "https://tipitaka.cloud/learn/suttas/mangala",
      "https://tipitaka.cloud/en/learn/topics/nibbana",
      "https://tipitaka.cloud/en/learn/topics/satipatthana",
      "https://tipitaka.cloud/learn/structure/suttanta"
  };
  private static final String[] ICON={"📖","🌸","🪷","🧘","📚"};
  private static final String[] NIKAYA={"ဒီဃနိကာယ် · Dīgha","မဇ္ဈိမနိကာယ် · Majjhima","သံယုတ္တနိကာယ် · Saṃyutta","အင်္ဂုတ္တရနိကာယ် · Aṅguttara","ခုဒ္ဒကနိကာယ် · Khuddaka"};
  private static final String[] NIKAYA_PREFIX={"sutta/dn/","sutta/mn/","sutta/sn/","sutta/an/","sutta/kn/"};
  private LinearLayout body;
  private int topic=-1;
  private int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){
    GradientDrawable g=new GradientDrawable();g.setColor(color);g.setCornerRadius(dp(radius));return g;
  }
  private TextView txt(String value,int sp,int color,boolean bold){
    TextView t=new TextView(this);
    t.setText(value);t.setTextColor(color);t.setTextSize(sp);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(12),dp(12),dp(12),dp(12));
    return t;
  }
  private void label(String s,int sp,int color,boolean bold){body.addView(txt(s,sp,color,bold));}
  private void card(String icon,String title,String subtitle,Runnable run){
    LinearLayout container=new LinearLayout(this);
    container.setGravity(Gravity.CENTER_VERTICAL);
    container.setPadding(dp(9),dp(6),dp(9),dp(6));
    GradientDrawable background=bg(Color.WHITE,16);
    container.setBackground(new RippleDrawable(ColorStateList.valueOf(0x33185039),background,null));
    TextView emoji=txt(icon,23,GREEN,false);emoji.setBackground(bg(0xffecf1e5,11));
    container.addView(emoji);
    LinearLayout words=new LinearLayout(this);words.setOrientation(1);
    TextView head=txt(title,16,GREEN,true);
    words.addView(head);
    TextView sub=txt(subtitle,12,0xff718376,false);
    sub.setPadding(dp(12),0,dp(12),dp(8));
    words.addView(sub);
    container.addView(words,new LinearLayout.LayoutParams(0,-2,1));
    container.addView(txt("›",23,0xffaa8444,true));
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
    p.setMargins(0,dp(5),0,dp(5));
    body.addView(container,p);
    container.setClickable(true);container.setFocusable(true);
    container.setOnClickListener(v->run.run());
  }
  public static Intent intent(Activity owner,int t){
    return new Intent(owner,TopicHubActivity.class).putExtra(EXTRA_TOPIC,t);
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    topic=state!=null?state.getInt(EXTRA_TOPIC,-1):getIntent().getIntExtra(EXTRA_TOPIC,-1);
    if(topic<-1||topic>=TITLE.length)topic=-1;
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    TextView head=txt("☸  အခြားခေါင်းစဉ်များ",22,Color.WHITE,true);head.setBackgroundColor(GREEN);root.addView(head);
    ScrollView scroll=new ScrollView(this);
    body=new LinearLayout(this);body.setOrientation(1);
    body.setPadding(dp(12),dp(12),dp(12),dp(18));
    scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TipitakaFooter.attach(this,root,-1);
    setContentView(root);
    render();
  }
  private void goSource(String prefix){
    Intent i=new Intent(this,PaliSourceLibraryActivity.class);
    i.putExtra("source_prefix",prefix);
    startActivity(i);
  }
  private void goSegment(String file){
    Intent i=new Intent(this,PaliSourceLibraryActivity.class);
    i.putExtra("source_file",file);
    startActivity(i);
  }
  private void goOnline(int i){
    if(i<0||i>=URL.length)return;
    Intent link=new Intent(Intent.ACTION_VIEW,Uri.parse(URL[i]));
    try{startActivity(link);}
    catch(ActivityNotFoundException e){
      Toast.makeText(this,"Browser မရှိပါ။ URL: "+URL[i],Toast.LENGTH_LONG).show();
    }
  }
  private void switchTopic(int i){topic=i;render();}
  private void render(){
    body.removeAllViews();
    if(topic==-1){
      label("၂။ အခြားခေါင်းစဉ်များ",23,GREEN,true);
      label("Dhamma Learning • Offline Reader + Online Reference",13,0xff977332,false);
      for(int i=0;i<TITLE.length;i++){
        final int k=i;
        card(ICON[i],TITLE[i],SUBTITLE[i],()->switchTopic(k));
      }
      label("Offline မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက် အပြည့်အစုံ မပြည့်စုံသေးပါ။",12,0xff866033,false);
      return;
    }
    final int current=topic;
    card("‹","အခြားခေါင်းစဉ်များသို့ ပြန်ရန်","Back to five topics",()->switchTopic(-1));
    label(ICON[current]+" "+TITLE[current],23,GREEN,true);
    label(SUBTITLE[current],15,0xff977332,true);
    if(current==0){
      label("ဓမ္မပဒ ၂၆ ဝဂ်၊ ၄၂၃ ဂါထာ Reader တွင် ပါဠိမူရင်းကို Offline ဖတ်နိုင်ပါသည်။ မြန်မာစာမူကြမ်းသည် အတည်ပြုစာသားမဟုတ်ပါ။",13,INK,false);
      card("📖","Offline ဓမ္မပဒ Reader","ဂါထာ ၄၂၃ · ဝဂ် ၂၆",()->startActivity(new Intent(this,DhammapadaYamakavaggaActivity.class)));
    }else if(current==1){
      label("မင်္ဂလာတရား ၃၈ ပါး လေ့လာရေး Reader ပါဝင်ပါသည်။ မြန်မာရှင်းလင်းချက်များကို မူကြမ်းအဖြစ်သာ သတ်မှတ်ပါသည်။",13,INK,false);
      card("🌸","Offline မင်္ဂလသုတ် Reader","မင်္ဂလာ ၃၈ ပါး · Native Reader",()->startActivity(new Intent(this,MangalaSuttaActivity.class)));
    }else if(current==2){
      label("နိဗ္ဗာန်အကြောင်း Offline လေ့လာရေးစာသားများပါရှိပြီး အတည်ပြုမြန်မာကျမ်းပြန်အပြည့်အစုံ မဟုတ်သေးပါ။",13,INK,false);
      card("🪷","Offline နိဗ္ဗာန် Reader","Topic Reader · SQLite Offline",()->startActivity(new Intent(this,NibbanaActivity.class)));
    }else if(current==3){
      label("သတိပဋ္ဌာန် ၄ ပါး — ကာယ၊ ဝေဒနာ၊ စိတ္တ၊ ဓမ္မ။ ပါဠိမူရင်းသုတ်ကို Offline ဖတ်နိုင်ပါသည်။",13,INK,false);
      card("📜","MN 10 — Satipaṭṭhāna (Pāli Offline)","Majjhima Nikāya · မူရင်းပါဠိ",()->goSegment("sutta/mn/mn10_root-pli-ms.json"));
      card("📜","DN 22 — Mahāsatipaṭṭhāna (Pāli Offline)","Dīgha Nikāya · မူရင်းပါဠိ",()->goSegment("sutta/dn/dn22_root-pli-ms.json"));
    }else{
      label("နိကာယ် ၅ မျိုးကို အောက်ပါအတိုင်း မူရင်းပါဠိ Source Folder အလိုက် Offline ဖတ်နိုင်ပါသည်။",13,INK,false);
      for(int j=0;j<NIKAYA.length;j++){final int k=j;card("📚",NIKAYA[j],NIKAYA_PREFIX[j]+" · Offline Pāli",()->goSource(NIKAYA_PREFIX[k]));}
    }
    card("🌐","မူရင်း Reference Website ဖွင့်ရန်","tipitaka.cloud · Internet လိုအပ်ပါသည်",()->goOnline(current));
    label("သတိ: Reference Website အကြောင်းအရာတစ်ခုလုံးကို Offline ကူးယူထားခြင်းမဟုတ်ပါ။",12,0xff856338,false);
  }
  @Override public void onBackPressed(){
    if(topic>=0){topic=-1;render();}else super.onBackPressed();
  }
  @Override protected void onSaveInstanceState(Bundle out){
    out.putInt(EXTRA_TOPIC,topic);
    super.onSaveInstanceState(out);
  }
}
