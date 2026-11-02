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
  private void sourceLink(String title,String url){
    TextView item=text("↗  "+title+"  (Online Source)",16,GREEN,true);
    item.setBackground(bg(Color.WHITE,14));content.addView(item);
    item.setOnClickListener(v->{try{startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url)));}catch(Exception e){Toast.makeText(this,"Browser ဖွင့်၍မရပါ",Toast.LENGTH_SHORT).show();}});
  }
  private void openLink(String url){
    try{startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse(url)));}
    catch(Exception e){Toast.makeText(this,"Link ဖွင့်၍မရပါ",Toast.LENGTH_SHORT).show();}
  }
  private void menuCard(String icon,String title,String subtitle,Runnable action){
    LinearLayout card=new LinearLayout(this);card.setOrientation(LinearLayout.HORIZONTAL);
    card.setGravity(Gravity.CENTER_VERTICAL);card.setPadding(dp(12),dp(9),dp(12),dp(9));
    card.setBackground(bg(Color.WHITE,18));card.setElevation(dp(2));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(6),0,dp(6));
    TextView symbol=text(icon,23,GREEN,true);symbol.setGravity(Gravity.CENTER);
    symbol.setBackground(bg(0xfff3ead4,14));
    card.addView(symbol,new LinearLayout.LayoutParams(dp(52),dp(52)));
    LinearLayout labels=new LinearLayout(this);labels.setOrientation(LinearLayout.VERTICAL);
    labels.setPadding(dp(12),0,dp(6),0);
    TextView heading=text(title,17,GREEN,true);heading.setPadding(0,0,0,dp(3));
    TextView detail=text(subtitle,13,INK,false);detail.setPadding(0,0,0,0);
    detail.setLineSpacing(dp(2),1.0f);
    labels.addView(heading);labels.addView(detail);
    card.addView(labels,new LinearLayout.LayoutParams(0,-2,1));
    TextView arrow=text("→",25,GOLD,true);arrow.setGravity(Gravity.CENTER);
    card.addView(arrow,new LinearLayout.LayoutParams(dp(28),-2));
    content.addView(card,lp);card.setOnClickListener(v->action.run());
  }
  private void openVolumes(int start,int end){
    Intent i=new Intent(this,TipitakaLibraryActivity.class);
    i.putExtra("start_volume",start);i.putExtra("end_volume",end);startActivity(i);
  }
  private void go(int p){
    if(p==22){startActivity(new Intent(this,DhammapadaYamakavaggaActivity.class));return;}
    if(p==23){startActivity(new Intent(this,OfflineBookmarksActivity.class));return;}
    if(p==24){startActivity(new Intent(this,OfflineSearchActivity.class));return;}
    if(p==25){startActivity(new Intent(this,ReaderStateBackupActivity.class));return;}
    if(p==26){startActivity(new Intent(this,ReferenceLibraryActivity.class));return;}
    if(p==27){startActivity(new Intent(this,OfflineBookLibraryActivity.class));return;}
    if(p==3){toggleMenu();return;}
    if(p<=21){render(p);return;}
    Intent i=new Intent(this,ExactScreensActivity.class);i.putExtra("openPage",p);startActivity(i);
  }
  @Override public void onCreate(Bundle state){super.onCreate(state);page=state==null?getIntent().getIntExtra("openPage",1):state.getInt("page",1);render(Math.max(1,Math.min(21,page)));}
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
    if(n==16){
      addText("အဘိဓမ္မာ — Native Reader",26,GREEN,true);
      addText("Pāli • မြန်မာ • Offline Reader",16,GOLD,true);
      addText("အဘိဓမ္မာစာအုပ် PDF, EPUB သို့မဟုတ် TXT ဖိုင်ကို ရွေးချယ်ပြီး အမှန်တကယ် ဖတ်ရှုနိုင်ပါသည်။",16,INK,false);
      TextView open=text("📖  အဘိဓမ္မာစာအုပ် ဖွင့်ဖတ်ရန်",19,Color.WHITE,true);open.setBackground(bg(GREEN,16));content.addView(open);
      open.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
      button("အဘိဓမ္မာ ၇ ကျမ်းစာရင်း",15);
      button("Reading History",13);
      button("Bookmarks & Notes",12);
      addText("စာအုပ်ဖိုင်ကို ကိုယ်တိုင်ရွေးပေးရန်လိုပြီး ပါဠိ/မြန်မာ စာသားနှစ်မျိုး အလိုအလျောက် ယှဉ်ပြမှု မပါသေးပါ။",14,INK,false);
    }else if(n==17){
      addText("ဓမ္မသင်ခန်းစာများ",27,GREEN,true);
      addText("Dhamma Learning • Study Hub",16,GOLD,true);
      TextView offline=text("☸  Offline ဓမ္မစာများနှင့် မြန်မာရှင်းလင်းချက် Popup",19,Color.WHITE,true);offline.setBackground(bg(GREEN,16));content.addView(offline);offline.setOnClickListener(v->startActivity(new Intent(this,OfflineDhammaActivity.class)));
      sourceLink("၄၅ ကျမ်း မူရင်းစာအုပ်တိုက်","https://tipitaka.cloud/library/");
      sourceLink("ဓမ္မပဒ • Dhammapada","https://tipitaka.cloud/en/learn/suttas/dhammapada");
      sourceLink("သတိပဋ္ဌာန် • Satipaṭṭhāna","https://tipitaka.cloud/en/learn/topics/satipatthana");
      button("ပိဋကတ်တော် အခြေခံမိတ်ဆက်",4);
      button("နိကာယ်ငါးရပ်ကို လေ့လာရန်",19);
      button("အဘိဓမ္မာ ၇ ကျမ်း",15);
      button("မင်္ဂလသုတ်နှင့် နိဗ္ဗာန်",18);
      button("စာအုပ်ဖတ်ပြီး မှတ်စုရေးရန်",12);
      addText("ဤစာမျက်နှာတွင် သင်ခန်းစာ Navigation အလုပ်လုပ်ပြီး သင်ရိုးစာသားနှင့် စာမေးပွဲဒေတာ မထည့်သွင်းရသေးပါ။",14,INK,false);
    }else if(n==18){
      addText("မင်္ဂလသုတ်နှင့် နိဗ္ဗာန်",26,GREEN,true);
      addText("Maṅgala Sutta & Nibbāna Learning",16,GOLD,true);
      addText("မင်္ဂလာတရား ၃၈ ပါးကို လေ့လာရန် အကြောင်းအရာများ",17,INK,false);
      TextView dhamma=text("☸  Offline ဓမ္မရှင်းလင်းချက်များ",18,Color.WHITE,true);dhamma.setBackground(bg(GREEN,16));content.addView(dhamma);dhamma.setOnClickListener(v->startActivity(new Intent(this,OfflineDhammaActivity.class)));
      sourceLink("မင်္ဂလသုတ် • Maṅgala Sutta","https://tipitaka.cloud/learn/suttas/mangala");
      sourceLink("နိဗ္ဗာန် • Nibbāna","https://tipitaka.cloud/en/learn/topics/nibbana");
      menuCard("☸","နိဗ္ဗာန် — Nibbāna Offline Reader","ခေါင်းစဉ် ၁၂ ခု • ပါဠိရင်းမြစ် • SQLite Offline",()->startActivity(new Intent(this,NibbanaActivity.class)));
      menuCard("📖","မင်္ဂလာ ၃၈ ပါး — Offline စာအုပ်ဖတ်ရန်","ပါဠိမူရင်းနှင့် မြန်မာရှင်းလင်းချက် Popup",()->startActivity(new Intent(this,MangalaSuttaActivity.class)));
      button("ဓမ္မသင်ခန်းစာများ",17);
      button("မှတ်စုများရေးရန်",12);
      addText("ပါဠိမူရင်းကို Sutta Nipāta 2.4 မှ ချိတ်ဆက်ထားပြီး မြန်မာရှင်းလင်းချက်သည် AI လေ့လာရေးမူကြမ်းဖြစ်သည်။",14,INK,false);
    }else if(n==19){
      addText("နိကာယ်ငါးရပ်",27,GREEN,true);
      button("ဓမ္မပဒ — ယမကဝဂ် (ဂါထာ ၁–၂၀)",22);
      addText("Five Nikāyas",16,GOLD,true);
      sourceLink("နိကာယ်ငါးရပ် မူရင်းရင်းမြစ်","https://tipitaka.cloud/learn/structure/suttanta");
      String[] nikayas={"ဒီဃနိကာယ် — Dīgha Nikāya","မဇ္ဈိမနိကာယ် — Majjhima Nikāya",
        "သံယုတ္တနိကာယ် — Saṃyutta Nikāya","အင်္ဂုတ္တရနိကာယ် — Aṅguttara Nikāya",
        "ခုဒ္ဒကနိကာယ် — Khuddaka Nikāya"};
      for(String name:nikayas){
        TextView row=text("☸  "+name+"\n      ဖိုင်ရွေးဖတ်ရန်",17,INK,true);
        row.setBackground(bg(Color.WHITE,16));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
        lp.setMargins(dp(4),dp(6),dp(4),dp(6));content.addView(row,lp);
        row.setOnClickListener(v->{
          if(name.startsWith("ဒီဃ"))openVolumes(9,11);
          else if(name.startsWith("မဇ္ဈိမ"))openVolumes(12,14);
          else if(name.startsWith("သံယုတ္တ"))openVolumes(15,19);
          else if(name.startsWith("အင်္ဂုတ္တရ"))openVolumes(20,24);
          else openVolumes(25,33);
        });
      }
      addText("နိကာယ်အလိုက် Offline ပါဠိကျမ်းစာရင်းကို ဖွင့်နိုင်ပါသည်။",14,INK,false);
    }else if(n==20){
      addText("သတိပဋ္ဌာန် လေ့လာရေး",27,GREEN,true);
      addText("Satipaṭṭhāna Learning • သတိပဋ္ဌာန်သုတ်",16,GOLD,true);
      addText("သတိပဋ္ဌာန် ၄ ပါးကို ပါဠိမူရင်း၊ မြန်မာဘာသာပြန်နှင့် လေ့လာရေးရှင်းလင်းချက်များဖြင့် သီးခြားလေ့လာရန်။",16,INK,false);
      menuCard("၁","ကာယာနုပဿနာ — Kāyānupassanā","ကိုယ်ခန္ဓာကို ရှုမှတ်ခြင်း",()->openLink("https://tipitaka.cloud/en/learn/topics/satipatthana"));
      menuCard("၂","ဝေဒနာနုပဿနာ — Vedanānupassanā","ဝေဒနာကို ရှုမှတ်ခြင်း",()->openLink("https://tipitaka.cloud/en/learn/topics/satipatthana"));
      menuCard("၃","စိတ္တာနုပဿနာ — Cittānupassanā","စိတ်ကို ရှုမှတ်ခြင်း",()->openLink("https://tipitaka.cloud/en/learn/topics/satipatthana"));
      menuCard("၄","ဓမ္မာနုပဿနာ — Dhammānupassanā","ဓမ္မသဘောတရားများကို ရှုမှတ်ခြင်း",()->openLink("https://tipitaka.cloud/en/learn/topics/satipatthana"));
      sourceLink("သတိပဋ္ဌာန်သုတ် — MN 10","https://suttacentral.net/mn10/pli/ms");
      sourceLink("မဟာသတိပဋ္ဌာန်သုတ် — DN 22","https://suttacentral.net/dn22/pli/ms");
      addText("မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက်များကို ပညာရှင်အတည်ပြုမပြီးမချင်း Draft အဖြစ်သာ ဖော်ပြမည်။ လက်ရှိတွင် ဤစာမျက်နှာသည် Native Navigation နှင့် ရင်းမြစ်လင့်ခ်များကို ပံ့ပိုးထားပြီး ကျမ်းစာအပြည့်အစုံ Offline ထည့်သွင်းမှု မပြီးသေးပါ။",14,INK,false);
    }else if(n==21){
      addText("Myanmar Tipitaka",28,GREEN,true);
      addText("About • Help • App Information",16,GOLD,true);
      addText("မြန်မာ့ပိဋကတ်တော် လေ့လာရေး Native Android Application",17,INK,false);
      addText("Version 2.3.5.2  •  by AAII",16,GREEN,true);
      addText("ပါဝင်သောလုပ်ဆောင်ချက်များ",19,GREEN,true);
      addText("• ၄၅ ကျမ်း Offline Pāli Reader\n• ကျမ်းပိုဒ်အလိုက် စာဖတ်ခြင်းနှင့် စာမျက်နှာပြောင်းခြင်း\n• Bookmark နှင့် Continue Reading\n• Offline PDF / EPUB / TXT Reader\n• မြန်မာဘာသာပြန်နှင့် ရှင်းလင်းချက် Popup",16,INK,false);
      TextView offlineHelp=text("☸  Offline ဓမ္မစာများ ဖတ်ရန်",18,Color.WHITE,true);offlineHelp.setBackground(bg(GREEN,16));content.addView(offlineHelp);offlineHelp.setOnClickListener(v->startActivity(new Intent(this,OfflineDhammaActivity.class)));
      button("☸  ပိဋကတ် ၄၅ ကျမ်း Offline Library",4);
      button("စာအုပ်ဖွင့်ဖတ်ရန်",6);
      button("Advanced Search",14);
      button("သတိပဋ္ဌာန် လေ့လာရေး",20);
      button("Help — စာအုပ်ရွေးနည်း",7);
      addText("Online Reference Edition — Chaṭṭha Saṅgāyana Tipiṭaka (CST), digitized by VRI.",14,INK,false);
      addText("tipitakaonline.org ၏ မြန်မာဘာသာပြန်သည် AI-generated ဖြစ်ပြီး လူပညာရှင်များက မစိစစ်ရသေးပါ။ Offline APK ထဲသို့ အတည်ပြုပြီးသား မြန်မာရှင်းလင်းချက်အဖြစ် မထည့်သွင်းထားပါ။",14,INK,false);
      TextView sourceLink=text("🌐  Tipiṭaka Online — CST / VRI Reference",16,Color.WHITE,true);sourceLink.setBackground(bg(GREEN,16));content.addView(sourceLink);
      sourceLink.setOnClickListener(v->startActivity(new Intent(Intent.ACTION_VIEW,android.net.Uri.parse("https://tipitakaonline.org/"))));
    }else if(n==13){
      addText("ဖတ်ရှုမှုမှတ်တမ်း",26,GREEN,true);
      addText("Reading History & Continue",16,GOLD,true);
      android.content.SharedPreferences reader=getSharedPreferences("native_reader",MODE_PRIVATE);
      String last=reader.getString("lastUri",null);
      if(last==null){
        addText("ဖတ်ရှုထားသော စာအုပ်မရှိသေးပါ။",17,INK,false);
        button("စာအုပ်ဖိုင် ဖွင့်ဖတ်ရန်",6);
      }else{
        addText("နောက်ဆုံးဖတ်ခဲ့သော စာအုပ်",18,GREEN,true);
        addText(android.net.Uri.parse(last).getLastPathSegment(),15,INK,false);
        int position=reader.getInt("position_"+last,0)+1;
        addText("ဖတ်ခဲ့သည့် စာမျက်နှာ: "+position,17,GOLD,true);
        TextView resume=text("▶ ဆက်လက်ဖတ်ရှုရန်",19,Color.WHITE,true);
        resume.setBackground(bg(GREEN,16));content.addView(resume);
        resume.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
        button("စာအုပ်အသစ် ဖွင့်ရန်",7);
      }
      android.content.SharedPreferences paliProgress=getSharedPreferences("tipitaka_paragraph_progress",MODE_PRIVATE);
      String lastParagraph=paliProgress.getString("last_paragraph_id",null);
      int lastVolume=paliProgress.getInt("last_volume",0);
      if(lastParagraph!=null&&lastVolume>0){
        addText("နောက်ဆုံးဖတ်ခဲ့သော ပိဋကတ်ကျမ်းပိုဒ်",18,GREEN,true);
        addText("ကျမ်း "+lastVolume+" · §"+lastParagraph,16,GOLD,true);
        TextView resumePali=text("☸  နောက်ဆုံးဖတ်ခဲ့သည့် ကျမ်းပိုဒ်သို့ ပြန်သွားရန်",17,Color.WHITE,true);
        resumePali.setBackground(bg(GREEN,16));content.addView(resumePali);
        resumePali.setOnClickListener(v->{Intent pi=new Intent(this,ParagraphExplanationActivity.class);pi.putExtra("volume",lastVolume);pi.putExtra("paragraph_id",lastParagraph);startActivity(pi);});
      }
      button("Bookmark / Notes / History စာရင်း",12);
      addText("ဖတ်ရှုမှုနေရာကို ဖုန်းအတွင်းတွင် အလိုအလျောက် သိမ်းဆည်းထားသည်။",14,INK,false);
    }else if(n==14){
      addText("အဆင့်မြင့် ရှာဖွေရန်",26,GREEN,true);
      addText("Advanced Search & Filter",16,GOLD,true);
      EditText term=new EditText(this);term.setSingleLine(true);term.setTextSize(18);
      term.setHint("ရှာဖွေလိုသော စာသား");term.setText(getPreferences(MODE_PRIVATE).getString("searchQuery",""));
      term.setBackground(bg(Color.WHITE,14));term.setPadding(dp(15),dp(14),dp(15),dp(14));content.addView(term);
      String[] choices={"အားလုံး","ဝိနည်း","သုတ္တန်","အဘိဓမ္မာ"};
      Spinner pitaka=new Spinner(this);
      pitaka.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,choices));
      content.addView(pitaka);
      CheckBox exact=new CheckBox(this);exact.setText("Exact phrase");exact.setTextColor(INK);content.addView(exact);
      TextView run=text("⌕  Filter နှင့် ရှာမည်",19,Color.WHITE,true);
      run.setBackground(bg(GREEN,16));content.addView(run);
      run.setOnClickListener(v->{String q=term.getText().toString().trim();if(q.isEmpty()){term.setError("စာသားထည့်ပါ");return;}
        getPreferences(MODE_PRIVATE).edit().putString("searchQuery",q)
          .putString("searchFilter",choices[pitaka.getSelectedItemPosition()])
          .putBoolean("exactMatch",exact.isChecked()).apply();
        Intent searchIntent=new Intent(this,OfflineSearchActivity.class);searchIntent.putExtra("query",q);
        searchIntent.putExtra("pitaka_filter",choices[pitaka.getSelectedItemPosition()]);
        searchIntent.putExtra("exact_match",exact.isChecked());startActivity(searchIntent);
      });
      addText("၄၅ ကျမ်း Offline SQLite ထဲရှိ ပါဠိမူရင်းနှင့် စိစစ်အတည်ပြုထားသော မြန်မာစာသားများကို ရှာဖွေရန် အသုံးပြုပါ။",14,INK,false);
    }else if(n==15){
      addText("အဘိဓမ္မာပိဋကတ်",27,GREEN,true);
      addText("Abhidhamma Books • အဘိဓမ္မာ ၇ ကျမ်း",16,GOLD,true);
      String[] books={"ဓမ္မသင်္ဂဏီ — Dhammasaṅgaṇī","ဝိဘင်္ဂ — Vibhaṅga","ဓာတုကထာ — Dhātukathā",
        "ပုဂ္ဂလပညတ္တိ — Puggalapaññatti","ကထာဝတ္ထု — Kathāvatthu",
        "ယမက — Yamaka","ပဋ္ဌာန်း — Paṭṭhāna"};
      for(String name:books){
        TextView row=text("▤  "+name+"\n       ဖိုင်ရွေး၍ ဖတ်ရှုရန်",16,INK,true);
        row.setBackground(bg(Color.WHITE,16));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(4),dp(5),dp(4),dp(5));
        content.addView(row,lp);
        row.setOnClickListener(v->openVolumes(34,45));
      }
      addText("အဘိဓမ္မာ ၇ ကျမ်း၏ Offline ပါဠိစာပိုဒ်များကို ရွေးဖတ်နိုင်ပါသည်။",14,INK,false);
      button("အဘိဓမ္မာ Native Reader",16);
    }else if(n==10){
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
        Intent searchIntent=new Intent(this,OfflineSearchActivity.class);searchIntent.putExtra("query",q);
        searchIntent.putExtra("pitaka_filter",filters[filter.getSelectedItemPosition()]);startActivity(searchIntent);
      });
      addText("Advanced Search သည် Offline ကျမ်းပိုဒ် Search ကို အသုံးပြုသည်။ Exact phrase option သည် လက်ရှိ Search Engine တွင် မသက်ရောက်သေးပါ။",14,INK,false);
    }else if(n==11){
      String q=getPreferences(MODE_PRIVATE).getString("searchQuery","");
      addText("ရှာဖွေမှုရလဒ်",26,GREEN,true);
      addText("Offline Search Results • "+q,16,GOLD,true);
      addText("ကျမ်းပိုဒ်အမှန်တကယ် ရှာဖွေမှုကို Offline SQLite Search Engine မှ ဆောင်ရွက်ပါသည်။",15,INK,false);
      TextView openResults=text("⌕  Offline ကျမ်းပိုဒ်ရလဒ်များ ဖွင့်ရန်",18,Color.WHITE,true);
      openResults.setBackground(bg(GREEN,16));content.addView(openResults);
      openResults.setOnClickListener(v->{Intent si=new Intent(this,OfflineSearchActivity.class);si.putExtra("query",q);
        si.putExtra("pitaka_filter",getPreferences(MODE_PRIVATE).getString("searchFilter","အားလုံး"));startActivity(si);});
      button("ရှာဖွေမှု ပြန်ပြင်ရန်",10);
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
      button("ကျမ်းပိုဒ် Bookmark စာရင်း",23);
      button("⬆⬇ Reader Backup / Restore",25);
      button("စာအုပ်ဖတ်စက် (Reader Bookmark)",6);
      button("ဆက်လက်ဖတ်ရှုရန်",8);
      addText("စာမှတ်များကို Reader အတွင်း သိမ်းဆည်းထားနိုင်ပြီး စာမှတ်တစ်ခုချင်းကို Reader ၏ Go to → Bookmark ဖြင့် ဖွင့်နိုင်ပါသည်။",14,INK,false);
    }else if(n==7){
      addText("ဓမ္မစာအုပ်တိုက်",26,GREEN,true);
      addText("My Offline Library",16,GOLD,false);
      addText("ဖုန်းအတွင်းရှိ PDF, EPUB နှင့် UTF-8 TXT စာအုပ်များကို ရွေးချယ်ဖတ်ရှုနိုင်ပါသည်။",16,INK,false);
      button("📚  Offline သိမ်းထားသော စာအုပ်များ",27);
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
      button("ကျမ်းပိုဒ် Bookmark စာရင်း",23);
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
      addText("ပိဋကတ်သုံးပုံ",28,GREEN,true);
      addText("Tipiṭaka  ·  45 ကျမ်း  ·  အခမဲ့",16,GOLD,true);
      addText("ထေရဝါဒ ပါဠိဘာသာ ပိဋကတ်သုံးပုံ (တိပိဋကတ်) ကို အောက်ပါ Menu များမှတစ်ဆင့် ဖတ်ရှုနိုင်ပါသည်။ ဝိနည်းပိဋကတ်၊ သုတ္တပိဋကတ်နှင့် အဘိဓမ္မပိဋကတ်တို့ကို လေ့လာနိုင်ပါသည်။",15,INK,false);
      menuCard("📚","ကျမ်းဖတ်ခန်း (45 ကျမ်း)","ပိဋကတ် ၄၅ ကျမ်း • Native Offline Reader",()->startActivity(new Intent(this,TipitakaLibraryActivity.class)));
      menuCard("🛡","Offline Pāli QA","SQLite • Device • Offline Reader Check",()->startActivity(new Intent(this,PaliOfflineQaActivity.class)));
      menuCard("📚","MCU ၄၅ ကျမ်း Offline Index","ကျမ်းအမည်စာရင်း ၄၅ ကျမ်း • Pāli Source သီးခြားဖတ်ရှုနိုင်",()->startActivity(new Intent(this,Mcu45CatalogActivity.class)));
      menuCard("📜","မူရင်းပါဠိ Offline Source","SuttaCentral Bilara • စာအုပ်အုပ်ခွဲ ၄၅ ကျမ်း မအတည်ပြုသေး",()->startActivity(new Intent(this,PaliSourceLibraryActivity.class)));
      menuCard("🌐","Reference စာအုပ်များ Online ဖတ်ရန်","မြန်မာပြန်စာအုပ်များ • PDF • University Libraries",()->startActivity(new Intent(this,ReferenceLibraryActivity.class)));
      menuCard("📈","Project Progress Bar","ကျမ်း ၄၅ ကျမ်း • Source + SQLite + Myanmar Coverage",()->startActivity(new Intent(this,ProjectProgressActivity.class)));
      menuCard("📋","Source Acquisition","ကျမ်း ၄၅ ကျမ်း • ရင်းမြစ်အတည်ပြုမှု",()->startActivity(new Intent(this,SourceAcquisitionActivity.class)));
      menuCard("🛡","Offline Database QA","SQLite Integrity • ကျမ်း ၄၅ ကျမ်း စစ်ဆေးရန်",()->startActivity(new Intent(this,OfflineDatabaseQaActivity.class)));
      menuCard("📊","မြန်မာဘာသာပြန် တိုးတက်မှု","ကျမ်း ၄၅ ကျမ်း • အတည်ပြုဘာသာပြန်နှင့် ရှင်းလင်းချက် Coverage",()->startActivity(new Intent(this,MyanmarCoverageActivity.class)));
      menuCard("✍","မြန်မာစာတည်းဖြတ်ရေးခန်း","ဘာသာပြန်နှင့် ရှင်းလင်းချက် Draft • Reviewer Workflow",()->startActivity(new Intent(this,MyanmarEditorialActivity.class)));
      menuCard("📦","Standalone Publisher","Direct SQLite Publish • Coverage • Backup / Restore",()->startActivity(new Intent(this,MyanmarPublisherActivity.class)));
      menuCard("📖","Online ဖတ်ရှုရန်","Tipitaka.cloud • ပါဠိနှင့် ထိုင်းဘာသာ Edition",()->openLink("https://tipitaka.cloud/?panes=en_translation"));
      addText("အထူးလေ့လာရန်",19,GREEN,true);
      menuCard("📜","ဓမ္မပဒ (Dhammapada)","ဂါထာ ၄၂၃ ပါဒ  ·  ဝဂ် ၂၆ ခု",()->openLink("https://tipitaka.cloud/en/learn/suttas/dhammapada"));
      menuCard("☸","မင်္ဂလသုတ် (Maṅgala Sutta)","မင်္ဂလာ ၃၈ ပါး  ·  Offline စာအုပ်",()->startActivity(new Intent(this,MangalaSuttaActivity.class)));
      menuCard("🪷","နိဗ္ဗာန် (Nibbāna)","နိဗ္ဗာန်ဆိုင်ရာ ဓမ္မလေ့လာရေး",()->openLink("https://tipitaka.cloud/en/learn/topics/nibbana"));
      menuCard("🧘","သတိပဋ္ဌာန် (Satipaṭṭhāna)","သတိပဋ္ဌာန် ၄ ပါး",()->openLink("https://tipitaka.cloud/en/learn/topics/satipatthana"));
      menuCard("📚","နိကာယ် ၅ မျိုး","ဒီဃ · မဇ္ဈိမ · သံယုတ္တ · အင်္ဂုတ္တရ · ခုဒ္ဒက",()->render(19));
      addText("ရင်းမြစ် — Tipitaka.cloud  |  Offline ဖတ်ရှုမှုအတွက် ကျမ်းဖတ်ခန်းကို ရွေးချယ်ပါ။",13,GOLD,false);
    }else if(n==5){
      addText("ပိဋကတ်တော် စာအုပ်များ",26,GREEN,true);
      addText("ပိဋကတ် ၄၅ ကျမ်း Offline Library နှင့် ကိုယ်ပိုင်စာအုပ်ဖိုင်များ",16,GOLD,false);
      button("☸  ပိဋကတ် ၄၅ ကျမ်း Offline ဖတ်ရန်",4);
      button("🌐  မြန်မာပြန် Reference စာအုပ်များ Online",26);
      button("📖  PDF / EPUB / TXT ဖိုင်ဖွင့်ရန်",6);
      button("သုတ္တန်ပိဋကတ် — နိကာယ်ငါးရပ်",19);
      button("ဝိနည်းပိဋကတ်",6);
      button("အဘိဓမ္မာပိဋကတ်",16);
      addText("Offline ကျမ်းစာသားများကို ၄၅ ကျမ်း Library မှ ရွေးချယ်ဖတ်ရှုနိုင်ပါသည်။",15,INK,false);
    }else if(n==6){
      addText("Native Book Reader",27,GREEN,true);
      addText("မြန်မာ • ပါဠိ စာဖတ်စက်",18,GOLD,true);
      addText("၄၅ ကျမ်း ပါဠိ Offline Reader • PDF / EPUB / TXT Reader",16,INK,false);
      button("☸  ပိဋကတ် ၄၅ ကျမ်း Offline Library ဖွင့်ရန်",4);
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
      button("☸   ပိဋကတ်သုံးပုံ Menu",4);
      button("▤   စာအုပ်များ",5);button("📖   စာအုပ်ဖတ်စက်",6);
      button("⌕   အကြောင်းအရာ ရှာဖွေရန်",10);
      button("🔖   စာမှတ်များနှင့် မှတ်စု",12);
      button("◷   ဆက်လက်ဖတ်ရှုရန်",13);
      addText("သုတ် • ဝိနည်း • အဘိဓမ္မာ",18,GOLD,true);
      button("နိကာယ်ငါးရပ်",19);
      button("☸ ဓမ္မပဒ ယမကဝဂ် (ဂါထာ ၁–၂၀)",22);
    }else{
      addText("လမ်းညွှန် မီနူး",27,GREEN,true);
      addText("Navigation Menu",16,GOLD,false);
      String[] names={"မူလစာမျက်နှာ","ပိဋကတ်တော် မိတ်ဆက်","ပိဋကတ် အမျိုးအစားများ","စာအုပ်များ","Native Reader","စာအုပ်တိုက်","စာဖတ်ခြင်း","လေ့လာရန်","Search","Search Results","စာမှတ်များ","History","Advanced Search","အဘိဓမ္မာ","အဘိဓမ္မာ Reader","ဓမ္မသင်ခန်းစာ","မင်္ဂလသုတ်","နိကာယ်ငါးရပ်","သတိပဋ္ဌာန်","About & Help"};
      int[] targets={2,2,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21};
      for(int i=0;i<targets.length;i++)button(String.format(java.util.Locale.US,"%02d  %s",targets[i],names[i]),targets[i]);
    }
    menuPanel=new LinearLayout(this);menuPanel.setOrientation(LinearLayout.VERTICAL);menuPanel.setBackground(bg(Color.WHITE,18));menuPanel.setVisibility(View.GONE);
    ScrollView menuScroll=new ScrollView(this);LinearLayout items=new LinearLayout(this);items.setOrientation(LinearLayout.VERTICAL);String[] menuTitles={"Home","Categories","Books","Online Reference Library","Native Reader","Library","Continue Reading","Learning","Search","Search Results","Bookmarks","Reading History","Advanced Search","Abhidhamma Books","Abhidhamma Reader","Dhamma Learning","Mangala Sutta","Five Nikayas","Satipaṭṭhāna","About"};int[] menuTargets={2,4,5,26,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21};
    for(int i=0;i<menuTitles.length;i++){final int target=menuTargets[i];TextView item=text(menuTitles[i],17,GREEN,true);items.addView(item);item.setOnClickListener(v->go(target));}
    menuScroll.addView(items);menuPanel.addView(menuScroll,new LinearLayout.LayoutParams(-1,dp(235)));
    root.addView(menuPanel);
    LinearLayout nav=new LinearLayout(this);nav.setGravity(Gravity.CENTER);nav.setBackgroundColor(GREEN);
    String[] keys={"⌂ Home","▤ Books","⌕ Search","▦ Modules","▣ Saved","⚙ Help"};
    int[] targets={2,5,10,17,12,21};
    for(int i=0;i<6;i++){final int target=targets[i];TextView v=text(keys[i],12,Color.WHITE,false);
      v.setGravity(Gravity.CENTER);nav.addView(v,new LinearLayout.LayoutParams(0,dp(55),1));v.setOnClickListener(w->go(target));}
    root.addView(nav);setContentView(root);
  }
  private void toggleMenu(){if(menuPanel!=null)menuPanel.setVisibility(menuPanel.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE);}
  @Override public void onBackPressed(){if(page!=1)render(1);else super.onBackPressed();}
  @Override protected void onSaveInstanceState(Bundle b){b.putInt("page",page);super.onSaveInstanceState(b);}
}
