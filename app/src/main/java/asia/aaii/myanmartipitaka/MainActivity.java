package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.os.Bundle;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.widget.*;
import java.util.List;
import java.util.Locale;

/** Myanmar Tipitaka 20-screen offline catalog / approved-only reader. */
public class MainActivity extends Activity {
    private static final int BG=Color.rgb(7,27,32), PANEL=Color.rgb(15,48,54), GOLD=Color.rgb(234,196,124), WHITE=Color.rgb(248,239,220);
    private static final String[] MM={
        "မူလစာမျက်နှာ","ပိဋကတ်တော် မိတ်ဆက်","ပိဋကတ်တော် အမျိုးအစားများ",
        "ပိဋကတ်စာအုပ် အမျိုးအစား","စာအုပ်စာရင်း","စာအုပ်အသေးစိတ်",
        "ပိဋကတ်စာအုပ်ဖတ်စက်","ပါဠိနှင့် မြန်မာစာ နှိုင်းယှဉ်ဖတ်ရှု",
        "စာဖတ်စက် အပြင်အဆင်","စာလုံး/အကြောင်းအရာ ရှာဖွေမှု",
        "အကြိုက်ဆုံးစာအုပ်များ","စာမှတ်များနှင့် မှတ်စု","ဖတ်ရှုမှုမှတ်တမ်း",
        "အဆင့်မြင့် ရှာဖွေမှု","အဘိဓမ္မာစာအုပ်များ","အဘိဓမ္မာ ဖတ်စက်",
        "ဓမ္မသင်ခန်းစာများ","မင်္ဂလသုတ်နှင့် နိဗ္ဗာန်","နိကာယ်ငါးရပ်","အက်ပ်အကြောင်း / အကူအညီ"
    };
    private static final String[] EN={"Home","Introduction","Collections","Book Categories","Library","Book Detail","Native Reader","Pali & Myanmar","Reader Settings","Search","Favorites","Bookmarks & Notes","History","Advanced Search","Abhidhamma Books","Abhidhamma Reader","Dhamma Learning","Mangala & Nibbana","Five Nikayas","About"};
    private SharedPreferences pref;
    private TipitakaRepository repo;
    private LinearLayout root;
    private int page=0,volume=1,font=18;
    @Override public void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        getWindow().setStatusBarColor(BG);getWindow().setNavigationBarColor(BG);
        pref=getSharedPreferences("tipitaka_2377",MODE_PRIVATE);
        volume=pref.getInt("volume",1);font=pref.getInt("font",18);
        try {repo=new TipitakaRepository(this);} catch(Exception e) {
            Toast.makeText(this,"Offline database error: "+e.getMessage(),Toast.LENGTH_LONG).show();
        }
        show(0);
    }
    private TextView txt(String s,int size,int color) {
        TextView v=new TextView(this);v.setText(s);v.setTextSize(size);v.setTextColor(color);v.setPadding(18,13,18,13);return v;
    }
    private void line(String s){root.addView(txt(s,font,WHITE));}
    private void button(String s,Runnable r){
        TextView v=txt(s,17,WHITE);v.setBackgroundColor(PANEL);v.setMinHeight(52);
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.setMargins(7,5,7,5);root.addView(v,p);
        v.setOnClickListener(w->r.run());
    }
    private void select(int n,int target){volume=n;pref.edit().putInt("volume",volume).apply();show(target);}
    private void library(String pitaka){
        if(repo==null){line("Offline Database မဖွင့်နိုင်ပါ။");return;}
        List<TipitakaRepository.Volume> books=repo.volumes(pitaka);
        line("MCU 45-volume metadata · "+books.size()+" ကျမ်း");
        for(TipitakaRepository.Volume b:books)
            button(String.format(Locale.US,"%02d · %s",b.number,b.title),()->select(b.number,5));
    }
    private void detail(){
        if(repo==null)return;
        for(TipitakaRepository.Volume b:repo.volumes(null))if(b.number==volume){
            line(String.format(Locale.US,"ကျမ်း %02d · %s",b.number,b.title));
            line(b.pitaka+" / "+b.nikaya);break;
        }
        button("📖 Offline Reader",()->show(6));
        button("ပါဠိ / မြန်မာ နှိုင်းယှဉ်",()->show(7));
        line("ကျမ်းစာအပြည့်အစုံ မပါသေးပါ။ အတည်ပြုစာသားများကိုသာ ပြသပါမည်။");
    }
    private void reader(){
        if(repo==null){line("SQLite database မရရှိပါ။");return;}
        line("ကျမ်း "+volume+" · Offline Reader");
        List<TipitakaRepository.Passage> passages=repo.passages(volume);
        if(passages.isEmpty())line("ဤကျမ်းအတွက် စစ်ဆေးပြီးသော ပါဠိစာပိုဒ် မထည့်သွင်းရသေးပါ။ ကျမ်းအမည်စာရင်းသာ Offline ရရှိပါသည်။");
        for(TipitakaRepository.Passage p:passages){
            line("§ "+p.ref);line("ပါဠိ — "+p.pali);
            line("မြန်မာဘာသာပြန် — "+(p.translation==null?"အတည်ပြုစာသား မရှိသေးပါ":p.translation));
            line("မြန်မာရှင်းလင်းချက် — "+(p.explanation==null?"အတည်ပြုစာသား မရှိသေးပါ":p.explanation));
        }
        button("A−",()->{font=Math.max(14,font-2);pref.edit().putInt("font",font).apply();show(page);});
        button("A+",()->{font=Math.min(34,font+2);pref.edit().putInt("font",font).apply();show(page);});
        button("🔖 Bookmark",()->{pref.edit().putInt("bookmark",volume).apply();Toast.makeText(this,"စာမှတ်ထားပြီး",Toast.LENGTH_SHORT).show();});
        pref.edit().putInt("lastRead",page).apply();
    }
    private void search(){
        if(repo==null)return;
        EditText q=new EditText(this);q.setHint("မြန်မာဘာသာပြန် / ရှင်းလင်းချက် ရှာရန်");
        q.setSingleLine(true);q.setTextColor(WHITE);q.setHintTextColor(GOLD);root.addView(q);
        button("ရှာမည်",()->{
            String term=q.getText().toString().trim();
            if(term.isEmpty())return;
            List<TipitakaRepository.Result> rows=repo.searchApproved(term,50);
            if(rows.isEmpty()){Toast.makeText(this,"Approved content မရှိသေးပါ",Toast.LENGTH_LONG).show();return;}
            root.removeView(q);
            for(TipitakaRepository.Result r:rows) button(r.volume+" · "+r.ref+" · "+r.excerpt,()->select(r.volume,6));
        });
    }
    private void show(int i){
        if(i<0||i>=20)return;page=i;
        ScrollView scroll=new ScrollView(this);scroll.setBackgroundColor(BG);
        root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setPadding(8,16,8,54);scroll.addView(root);setContentView(scroll);
        TextView logo=txt("☸ Myanmar Tipitaka",24,GOLD);logo.setTypeface(null,Typeface.BOLD);root.addView(logo);
        root.addView(txt(String.format(Locale.US,"V2.3.7.7 · Page %02d / 20",i+1),13,GOLD));
        TextView head=txt(MM[i]+"\n"+EN[i],22,WHITE);head.setTypeface(null,Typeface.BOLD);root.addView(head);
        if(i==0){
            line("ပိဋကတ်သုံးပုံ · ၄၅ ကျမ်း (Offline Catalog)");
            line("သတိ: ပါဠိကျမ်းစာအပြည့်အစုံ မပါဝင်သေးပါ။");
            if(repo!=null)line("Approved Translation: "+repo.approvedCount("translation")+" · Explanation: "+repo.approvedCount("explanation"));
            button("📚 ကျမ်းဖတ်ခန်း (45)",()->show(4));
            button("ဆက်ဖတ်ရန်",()->show(pref.getInt("lastRead",6)));
            for(int j=1;j<MM.length;j++){final int k=j;button(String.format(Locale.US,"%02d · %s",j+1,MM[j]),()->show(k));}
            return;
        }
        if(i==4)library(null);
        else if(i==5)detail();
        else if(i==6||i==7||i==15)reader();
        else if(i==14)library("Abhidhamma");
        else if(i==9||i==13)search();
        else if(i==11){
            EditText note=new EditText(this);note.setHint("မှတ်စုရေးရန်");note.setTextColor(WHITE);note.setHintTextColor(GOLD);
            note.setText(pref.getString("note",""));root.addView(note);
            button("မှတ်စုသိမ်းမည်",()->{pref.edit().putString("note",note.getText().toString()).apply();Toast.makeText(this,"သိမ်းပြီး",Toast.LENGTH_SHORT).show();});
            button("Bookmark ဖွင့်မည်",()->select(pref.getInt("bookmark",1),6));
        }
        else if(i==12)button("ဆက်လက်ဖတ်ရှုရန်",()->show(pref.getInt("lastRead",6)));
        else if(i==18)line("ဒီဃနိကာယ် · မဇ္ဈိမနိကာယ် · သံယုတ္တနိကာယ် · အင်္ဂုတ္တရနိကာယ် · ခုဒ္ဒကနိကာယ်");
        else if(i==19)line("Verified index 45/45 · Approved translation 0 · Approved explanation 0. Paragraph crosswalk and canonical texts are pending.");
        else line("အတည်ပြုထားသော အကြောင်းအရာများကို ထည့်သွင်းရန် ကျန်ရှိပါသည်။");
        button("⌂ Home",()->show(0));button("‹ Back",()->show(page-1));if(i<19)button("Next ›",()->show(page+1));
    }
    @Override public void onBackPressed(){if(page>0)show(0);else super.onBackPressed();}
    @Override protected void onDestroy(){if(repo!=null)repo.close();super.onDestroy();}
}