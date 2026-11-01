package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.util.ArrayList;

/** Offline Nibbāna reader backed by a private SQLite database imported from the packaged JSON asset. */
public final class NibbanaActivity extends Activity {
  private static final int GREEN=0xff144638,CREAM=0xfffaf6eb,INK=0xff193b30,GOLD=0xff96702b;
  private NibbanaDatabaseHelper store;private LinearLayout body;private ScrollView scroll;
  private String selectedId=null,selectedTitle="";private String selectedNote="",selectedSourceIds="[]";
  private int selectedOrder=0;private boolean showPali=true,showMyanmar=true;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int c,int r){GradientDrawable d=new GradientDrawable();d.setColor(c);d.setCornerRadius(dp(r));return d;}
  private TextView text(String s,int size,int color,boolean bold){TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);t.setPadding(dp(13),dp(10),dp(13),dp(10));t.setLineSpacing(dp(3),1.05f);return t;}
  @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);store=new NibbanaDatabaseHelper(this);
    try{store.ensureImported();if(store.topicCount()!=12||store.sourceCount()!=6)throw new IllegalStateException("SQLite Content အရေအတွက် မကိုက်ညီပါ");}
    catch(Exception e){new android.app.AlertDialog.Builder(this).setTitle("Offline Nibbāna မဖွင့်နိုင်ပါ").setMessage(e.getMessage()).setPositiveButton("ပြန်သွားရန်",(d,w)->finish()).show();return;}
    render();
  }
  private void render(){
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setBackgroundColor(GREEN);
    TextView back=text("‹",29,Color.WHITE,true);back.setOnClickListener(v->{if(selectedId!=null){selectedId=null;renderBody();}else finish();});header.addView(back);
    header.addView(text("☸  နိဗ္ဗာန် (Nibbāna)",20,Color.WHITE,true),new LinearLayout.LayoutParams(0,-2,1));
    header.addView(text("Offline",12,0xffffdf9a,true));root.addView(header);
    scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);body.setPadding(dp(15),dp(12),dp(15),dp(22));scroll.addView(body);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    LinearLayout footer=new LinearLayout(this);footer.setGravity(Gravity.CENTER);footer.setBackgroundColor(GREEN);
    footer.addView(footerItem("⌂\nပင်မ",()->{Intent i=new Intent(this,NativeFrontPagesActivity.class);i.putExtra("openPage",18);i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(i);finish();}),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("☷\nမာတိကာ",()->{selectedId=null;renderBody();}),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("★\nမှတ်သား",()->bookmark()),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("⌕\nရင်းမြစ်",()->{if(selectedId!=null)showSources();else Toast.makeText(this,"ခေါင်းစဉ်တစ်ခုကို ရွေးပါ",Toast.LENGTH_SHORT).show();}),new LinearLayout.LayoutParams(0,dp(58),1));
    root.addView(footer);setContentView(root);renderBody();
  }
  private TextView footerItem(String s,Runnable a){TextView t=text(s,12,Color.WHITE,true);t.setGravity(Gravity.CENTER);t.setOnClickListener(v->a.run());return t;}
  private void renderBody(){
    body.removeAllViews();
    body.addView(text("Nibbāna · ဒုက္ခနိရောဓသစ္စာနှင့် အသင်္ခတဓာတ်",13,GOLD,true));
    body.addView(text("နိဗ္ဗာန်တရား လေ့လာရေး",25,GREEN,true));
    TextView warn=text("မြန်မာရှင်းလင်းချက်များသည် လေ့လာရေးမူကြမ်းများဖြစ်ပြီး ပညာရှင်အတည်ပြုချက် မရသေးပါ။",13,0xff80551c,true);warn.setBackground(bg(0xffffedc2,12));body.addView(warn);
    if(selectedId==null){
      body.addView(text("ပါဠိကျမ်းကိုးကားချက်များနှင့်အတူ ခေါင်းစဉ် ၁၂ ခုကို Offline လေ့လာနိုင်ပါသည်။",15,INK,false));
      try(Cursor c=store.topics()){while(c.moveToNext()){
        String id=c.getString(0);int order=c.getInt(1);String title=c.getString(2),note=c.getString(3),ids=c.getString(4);
        TextView card=text(String.format(java.util.Locale.ROOT,"%02d  %s\n%s\nလေ့လာရန်  ›",order,title,note),16,INK,true);card.setBackground(bg(Color.WHITE,14));
        LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(4),0,dp(5));body.addView(card,lp);
        card.setOnClickListener(v->{selectedId=id;selectedTitle=title;selectedNote=note;selectedSourceIds=ids;selectedOrder=order;renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});
      }}catch(Exception e){body.addView(text("SQLite ဖတ်ရှုမှု အမှား: "+e.getMessage(),14,Color.RED,false));}
    }else renderTopic();
  }
  private void renderTopic(){
    body.addView(text("ခေါင်းစဉ် "+selectedOrder+" / ၁၂",14,GOLD,true));
    body.addView(text(selectedTitle,22,GREEN,true));
    TextView note=text("လေ့လာရေးရှင်းလင်းချက် (မူကြမ်း)\n"+selectedNote,16,INK,false);note.setBackground(bg(Color.WHITE,14));body.addView(note);
    body.addView(text("အတည်ပြုမှု: ပညာရှင်စစ်ဆေးရန် ကျန်ရှိသည်",12,GOLD,true));
    LinearLayout toggles=new LinearLayout(this);
    TextView p=text(showPali?"✓ ပါဠိမူရင်း":"ပါဠိမူရင်း",13,showPali?Color.WHITE:GREEN,true);p.setGravity(Gravity.CENTER);p.setBackground(bg(showPali?GREEN:Color.WHITE,12));
    TextView m=text(showMyanmar?"✓ မြန်မာမူကြမ်း":"မြန်မာမူကြမ်း",13,showMyanmar?Color.WHITE:GREEN,true);m.setGravity(Gravity.CENTER);m.setBackground(bg(showMyanmar?GREEN:Color.WHITE,12));
    toggles.addView(p,new LinearLayout.LayoutParams(0,-2,1));toggles.addView(m,new LinearLayout.LayoutParams(0,-2,1));body.addView(toggles);
    p.setOnClickListener(v->{showPali=!showPali;renderBody();});m.setOnClickListener(v->{showMyanmar=!showMyanmar;renderBody();});
    if(showMyanmar)body.addView(text("မြန်မာဘာသာပြန် အတည်ပြုစာသား မရရှိသေးပါ။ လက်ရှိရှင်းလင်းချက်သည် Draft ဖြစ်သည်။",14,INK,false));
    if(showPali)showSources();
  }
  private void showSources(){
    body.addView(text("ပါဠိကျမ်းရင်းမြစ်များ",18,GREEN,true));
    try(Cursor c=store.sourcesFor(selectedSourceIds)){while(c.moveToNext()){
      String id=c.getString(0),ref=c.getString(1),title=c.getString(2),url=c.getString(3),theme=c.getString(5);
      TextView row=text(ref+" — "+title+"\n"+theme+"\nပါဠိမူရင်းကို ဖတ်ရန် ↗",14,INK,true);row.setBackground(bg(Color.WHITE,12));body.addView(row);
      row.setOnClickListener(v->{if(url!=null&&!url.isEmpty())try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}catch(Exception e){Toast.makeText(this,"Link ဖွင့်မရပါ",Toast.LENGTH_SHORT).show();}});
      try(Cursor ex=store.excerptsFor(id)){while(ex.moveToNext()){
        body.addView(text("ပါဠိမူရင်း — "+ref,14,GOLD,true));body.addView(text(ex.getString(0),16,INK,false));
        body.addView(text("မြန်မာအဓိပ္ပာယ်မူကြမ်း: "+ex.getString(1),14,INK,false));
      }}
    }}catch(Exception e){body.addView(text("ရင်းမြစ်ဖတ်ရှုမှု အမှား: "+e.getMessage(),14,Color.RED,false));}
  }
  private void bookmark(){if(selectedId==null){Toast.makeText(this,"မှတ်သားရန် ခေါင်းစဉ်ရွေးပါ",Toast.LENGTH_SHORT).show();return;}store.toggleBookmark(selectedId);Toast.makeText(this,store.isBookmarked(selectedId)?"မှတ်သားပြီး":"မှတ်သားမှု ဖယ်ရှားပြီး",Toast.LENGTH_SHORT).show();}
  @Override protected void onDestroy(){super.onDestroy();if(store!=null)store.close();}
}
