package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;

/** Native offline Maṅgala Sutta reader. Myanmar text is visibly marked as an unapproved study draft. */
public final class MangalaSuttaActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6eb, INK=0xff193b30, GOLD=0xff96702b;
  private JSONObject corpus;
  private JSONArray items;
  private LinearLayout body;
  private ScrollView scroll;
  private int selected=-1;
  private boolean showPali=true,showMyanmar=true;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;}
  private TextView text(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(Typeface.DEFAULT,Typeface.BOLD);
    t.setPadding(dp(14),dp(11),dp(14),dp(11));t.setLineSpacing(dp(4),1.05f);return t;
  }
  private String asset(String name)throws Exception{
    try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
      byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
      return out.toString("UTF-8");
    }
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    try{
      corpus=new JSONObject(asset("mangala_sutta_my.json"));
      items=corpus.getJSONArray("blessings");
      if(items.length()!=38)throw new IllegalStateException("မင်္ဂလာ ၃၈ ပါး မပြည့်စုံပါ");
    }catch(Exception e){
      new AlertDialog.Builder(this).setTitle("Offline မင်္ဂလသုတ် မဖွင့်နိုင်ပါ")
        .setMessage(e.getMessage()).setPositiveButton("ပြန်သွားရန်",(d,w)->finish()).show();return;
    }
    selected=state==null?-1:state.getInt("selected",-1);
    render();
  }
  @Override protected void onSaveInstanceState(Bundle out){super.onSaveInstanceState(out);out.putInt("selected",selected);}
  private void render(){
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    LinearLayout header=new LinearLayout(this);header.setGravity(Gravity.CENTER_VERTICAL);header.setBackgroundColor(GREEN);
    TextView back=text("‹",29,Color.WHITE,true);back.setOnClickListener(v->finish());header.addView(back);
    TextView title=text("☸  မင်္ဂလသုတ်",20,Color.WHITE,true);header.addView(title,new LinearLayout.LayoutParams(0,-2,1));
    header.addView(text("၃၈ ပါး",14,0xffffdf9a,true));root.addView(header);
    scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(LinearLayout.VERTICAL);
    body.setPadding(dp(15),dp(12),dp(15),dp(20));scroll.addView(body);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    LinearLayout footer=new LinearLayout(this);footer.setGravity(Gravity.CENTER);footer.setBackgroundColor(GREEN);
    footer.addView(footerItem("⌂\nပင်မ",()->{Intent i=new Intent(this,NativeFrontPagesActivity.class);i.putExtra("openPage",2);i.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);startActivity(i);finish();}),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("☷\nမာတိကာ",()->{selected=-1;renderBody();}),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("★\nမှတ်သား",()->bookmark()),new LinearLayout.LayoutParams(0,dp(58),1));
    footer.addView(footerItem("Aa\nစာသား",()->toggleText()),new LinearLayout.LayoutParams(0,dp(58),1));
    root.addView(footer);setContentView(root);renderBody();
  }
  private TextView footerItem(String s,Runnable action){TextView t=text(s,12,Color.WHITE,true);t.setGravity(Gravity.CENTER);t.setOnClickListener(v->action.run());return t;}
  private void renderBody(){
    body.removeAllViews();
    body.addView(text("Maṅgala Sutta · Sutta Nipāta 2.4 (Sn 258–269)",13,GOLD,true));
    body.addView(text("မင်္ဂလာတရား ၃၈ ပါး",25,GREEN,true));
    TextView warning=text("အရေးကြီးချက် — မြန်မာစာသားများသည် လေ့လာရေးမူကြမ်းဖြစ်ပြီး ပညာရှင်အတည်ပြုချက် မရသေးပါ။",13,0xff80551c,true);
    warning.setBackground(bg(0xffffedc2,12));body.addView(warning);
    if(selected<0){
      body.addView(text("အောက်ပါ မင်္ဂလာတစ်ပါးချင်းကို နှိပ်၍ လေ့လာနိုင်ပါသည်။",15,INK,false));
      for(int i=0;i<items.length();i++){
        JSONObject item=items.optJSONObject(i);final int ix=i;
        TextView card=text(String.format(java.util.Locale.ROOT,"%02d  %s\n%s\nဖတ်ရှုရန်  ›",i+1,item.optString("myanmar_title"),item.optString("pali_term")),16,INK,true);
        card.setBackground(bg(Color.WHITE,14));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(4),0,dp(5));body.addView(card,lp);
        card.setOnClickListener(v->{selected=ix;renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});
      }
      TextView pali=text("📜  ပါဠိသုတ်တော် အပြည့်အစုံ ဖတ်ရန်",16,GREEN,true);pali.setBackground(bg(Color.WHITE,14));body.addView(pali);
      pali.setOnClickListener(v->{selected=38;renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});
    }else if(selected==38){
      body.addView(text("ပါဠိမူရင်း — Sutta Nipāta 2.4",18,GREEN,true));
      body.addView(text(corpus.optString("pali_text"),17,INK,false));
      body.addView(text("ရင်းမြစ်: "+corpus.optJSONObject("source").optString("url"),12,GOLD,false));
      addBackToIndex();
    }else{
      JSONObject item=items.optJSONObject(selected);
      body.addView(text("မင်္ဂလာ "+(selected+1)+" / ၃၈",14,GOLD,true));
      body.addView(text(item.optString("myanmar_title"),23,GREEN,true));
      body.addView(text(item.optString("pali_term"),18,INK,true));
      if(showMyanmar){
        TextView draft=text("မြန်မာရှင်းလင်းချက် (မူကြမ်း)\n"+item.optString("myanmar_explanation_draft"),17,INK,false);
        draft.setBackground(bg(Color.WHITE,14));body.addView(draft);
        body.addView(text("အတည်ပြုမှု: ပညာရှင်စစ်ဆေးရန် ကျန်ရှိသည်",12,GOLD,true));
      }
      if(showPali){
        body.addView(text("ပါဠိမူရင်း သုတ်တော်",18,GREEN,true));
        body.addView(text(corpus.optString("pali_text"),16,INK,false));
        body.addView(text("မှတ်ချက် — သုတ်တော်အပြည့်အစုံကို ဖော်ပြထားခြင်းဖြစ်ပြီး မင်္ဂလာတစ်ပါးချင်းနှင့် ပါဠိစာပိုဒ်အလိုက် တိကျသော mapping ကို ပညာရှင်ဖြင့် ထပ်မံစစ်ဆေးရန် လိုအပ်သည်။",13,GOLD,false));
      }
      LinearLayout nav=new LinearLayout(this);
      TextView prev=text("← ယခင်",15,GREEN,true);prev.setGravity(Gravity.CENTER);
      TextView next=text("နောက် →",15,GREEN,true);next.setGravity(Gravity.CENTER);
      nav.addView(prev,new LinearLayout.LayoutParams(0,-2,1));nav.addView(next,new LinearLayout.LayoutParams(0,-2,1));body.addView(nav);
      prev.setOnClickListener(v->{selected=Math.max(0,selected-1);renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});
      next.setOnClickListener(v->{selected=Math.min(37,selected+1);renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});
      addBackToIndex();
    }
  }
  private void addBackToIndex(){TextView t=text("☷  မင်္ဂလာ ၃၈ ပါး မာတိကာသို့",15,GREEN,true);t.setGravity(Gravity.CENTER);body.addView(t);t.setOnClickListener(v->{selected=-1;renderBody();scroll.post(()->scroll.smoothScrollTo(0,0));});}
  private void bookmark(){
    String key="mangala_bookmark_"+selected;boolean old=getPreferences(MODE_PRIVATE).getBoolean(key,false);
    getPreferences(MODE_PRIVATE).edit().putBoolean(key,!old).apply();
    Toast.makeText(this,!old?"မှတ်သားပြီး":"မှတ်သားမှု ဖယ်ရှားပြီး",Toast.LENGTH_SHORT).show();
  }
  private void toggleText(){showPali=!showPali;showMyanmar=!showMyanmar;renderBody();}
}
