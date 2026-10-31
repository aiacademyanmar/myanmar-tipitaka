package asia.aaii.myanmartipitaka;
import android.app.*;
import android.content.*;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.*;
import android.widget.*;

/** Built-in offline study notes; explanatory text is educational, not canonical scripture. */
public class OfflineDhammaActivity extends Activity {
 private final int green=Color.rgb(16,65,55),gold=Color.rgb(178,128,45),cream=Color.rgb(249,245,232);
 private final String[] titles={"တရားတော်ကို လေ့လာခြင်း","သီလ (Sīla)","သမာဓိ (Samādhi)","ပညာ (Paññā)","အနိစ္စ (Anicca)","ဒုက္ခ (Dukkha)","အနတ္တ (Anattā)","မေတ္တာ (Mettā)"};
 private final String[] descriptions={
 "ဓမ္မကို လေ့လာရာတွင် စာဖတ်ခြင်း၊ အဓိပ္ပာယ်ကို ဆင်ခြင်ခြင်းနှင့် နေ့စဉ်ဘဝတွင် ကျင့်သုံးခြင်းကို ချိတ်ဆက်စဉ်းစားနိုင်သည်။",
 "သီလဆိုသည်မှာ မိမိ၏ ကိုယ်နှုတ်အပြုအမူများကို သတိထားထိန်းသိမ်း၍ မိမိနှင့် အခြားသူများကို မထိခိုက်စေရန် လေ့ကျင့်ခြင်းဖြစ်သည်။",
 "သမာဓိဆိုသည်မှာ စိတ်ကို အာရုံတစ်ခုအပေါ် တည်ငြိမ်စွာ ထားနိုင်ရန် လေ့ကျင့်မှုဖြစ်ပြီး သတိနှင့် ပေါင်းစပ်လေ့လာနိုင်သည်။",
 "ပညာဆိုသည်မှာ ဖြစ်ပေါ်နေသော အရာများ၏ သဘောသဘာဝကို သတိဖြင့် စိစစ်နားလည်ရန် လေ့ကျင့်ခြင်းဖြစ်သည်။",
 "အနိစ္စသည် ဖြစ်ပေါ်လာသော အခြေအနေများ အမြဲတည်မနေဘဲ ပြောင်းလဲသွားနိုင်ခြင်းကို ရည်ညွှန်းသည်။",
 "ဒုက္ခကို နားလည်ရာတွင် မတည်မြဲသောအရာများကို အမြဲတည်စေလိုသည့် စွဲလမ်းမှုနှင့် မကျေနပ်နိုင်မှုကိုလည်း ဆင်ခြင်နိုင်သည်။",
 "အနတ္တသည် အရာများကို အမြဲတမ်း မပြောင်းလဲသည့် မိမိပိုင်အနှစ်သာရတစ်ခုအဖြစ် မယူဆရန် လေ့လာသည့် သဘောတရားဖြစ်သည်။",
 "မေတ္တာသည် မိမိနှင့် အခြားသူများ ချမ်းသာကောင်းမွန်စေလိုသော စိတ်ထားကို မွေးမြူလေ့ကျင့်ခြင်းဖြစ်သည်။"};
 private final String[] examples={
 "ဥပမာ — စိတ်မငြိမ်သောအခါ စိတ်အခြေအနေကို သတိထားကြည့်ခြင်းမှ စတင်လေ့လာနိုင်သည်။",
 "ဥပမာ — စကားမပြောမီ ထိုစကားကြောင့် တစ်ဦးဦး ထိခိုက်မည်လား စဉ်းစားခြင်း။",
 "ဥပမာ — အသက်ရှူဝင်ထွက်ကို ခဏတာ သတိထားလေ့ကျင့်ခြင်း။",
 "ဥပမာ — စိတ်တိုနေကြောင်း သိပြီး ထိုခံစားချက်ကို မလိုက်ပါဘဲ ဆင်ခြင်ခြင်း။",
 "ဥပမာ — ပန်းတစ်ပွင့် ပွင့်ပြီးနောက် ညှိုးနွမ်းသွားပုံကို ဆင်ခြင်ခြင်း။",
 "ဥပမာ — မျှော်လင့်ထားသလို မဖြစ်သည့်အခါ ခံစားရသည့် မကျေနပ်မှုကို စူးစမ်းခြင်း။",
 "ဥပမာ — စိတ်ခံစားချက်တစ်ခုကို အမြဲတည်မည့် ကိုယ့်အတ္တဟု မစွဲဘဲ ပြောင်းလဲမှုကို သိမှတ်ခြင်း။",
 "ဥပမာ — အခက်အခဲကြုံနေသူတစ်ဦးအတွက် ကောင်းကျိုးလိုလားစိတ်ထားခြင်း။"};
 private int dp(int v){return (int)(v*getResources().getDisplayMetrics().density+.5f);}
 private GradientDrawable bg(int color,int r){GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(r));return d;}
 private TextView text(String str,int size,int color){TextView t=new TextView(this);t.setText(str);t.setTextSize(size);t.setTextColor(color);t.setPadding(dp(17),dp(13),dp(17),dp(13));return t;}
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().setStatusBarColor(green);getWindow().setNavigationBarColor(green);
 LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(cream);
 TextView header=text("☸  Offline Dhamma Study",22,Color.WHITE);header.setBackgroundColor(green);root.addView(header);
 ScrollView scroll=new ScrollView(this);LinearLayout list=new LinearLayout(this);list.setOrientation(LinearLayout.VERTICAL);list.setPadding(dp(14),dp(10),dp(14),dp(20));
 scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
 TextView intro=text("အင်တာနက်မလိုဘဲ ဖတ်ရှုနိုင်သော ဓမ္မသဘောတရား မိတ်ဆက်ရှင်းလင်းချက်များ။\nဤစာသားများသည် လေ့လာရေးအတွက် ရေးသားထားသော ရှင်းလင်းချက်များသာဖြစ်ပြီး မူရင်းပိဋကတ်တော်စာသားဟု မသတ်မှတ်ပါ။",16,green);list.addView(intro);
 for(int i=0;i<titles.length;i++){final int j=i;TextView tile=text("☸  "+titles[i]+"\n   မြန်မာဘာသာ ရှင်းလင်းချက်ကြည့်ရန် ›",18,green);tile.setBackground(bg(Color.WHITE,15));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(6),0,dp(6));list.addView(tile,lp);tile.setOnClickListener(v->popup(j));}
 LinearLayout footer=new LinearLayout(this);footer.setBackgroundColor(green);
 TextView back=text("‹ App သို့ ပြန်ရန်",16,Color.WHITE);footer.addView(back);back.setOnClickListener(v->finish());
 TextView open=text("PDF / EPUB ဖတ်ရန်",16,Color.WHITE);footer.addView(open);open.setOnClickListener(v->startActivity(new Intent(this,BookReaderActivity.class)));
 root.addView(footer);setContentView(root);}
 private void popup(int n){
 LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setBackground(bg(cream,18));panel.setPadding(dp(16),dp(12),dp(16),dp(12));
 TextView ornament=text("☸  ဓမ္မအကြောင်း ရှင်းလင်းချက်",19,gold);ornament.setTypeface(null,Typeface.BOLD);panel.addView(ornament);
 TextView title=text(titles[n],23,green);title.setTypeface(null,Typeface.BOLD);panel.addView(title);
 panel.addView(text(descriptions[n],18,green));
 panel.addView(text(examples[n],16,gold));
 panel.addView(text("မှတ်ချက် — သင်ယူရေးဆိုင်ရာ အနှစ်ချုပ်ဖြစ်ပြီး ပါဠိကျမ်းစာ မူရင်းကိုးကားချက်မဟုတ်ပါ။",13,green));
 AlertDialog dialog=new AlertDialog.Builder(this).setView(panel).setPositiveButton("ပိတ်မည်",(d,w)->{}).create();
 dialog.setOnShowListener(v->{dialog.getButton(AlertDialog.BUTTON_POSITIVE).setTextColor(green);});dialog.show();
 }
}
