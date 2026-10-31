package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.os.Bundle;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.View;
import android.widget.*;
import java.util.Locale;

public class MainActivity extends Activity {
    private static final int BG = Color.rgb(7,27,32);
    private static final int PANEL = Color.rgb(15,48,54);
    private static final int GOLD = Color.rgb(234,196,124);
    private static final int WHITE = Color.rgb(248,239,220);
    private static final String[] SCREENS = {
        "မူလစာမျက်နှာ", "ပိဋကတ်တော် မိတ်ဆက်", "ပိဋကတ်တော် အမျိုးအစားများ",
        "ပိဋကတ်စာအုပ် အမျိုးအစား", "စာအုပ်စာရင်း", "စာအုပ်အသေးစိတ်",
        "ပိဋကတ်စာအုပ်ဖတ်စက်", "ပါဠိနှင့် မြန်မာစာ နှိုင်းယှဉ်ဖတ်ရှု",
        "စာဖတ်စက် အပြင်အဆင်", "စာလုံး/အကြောင်းအရာ ရှာဖွေမှု",
        "အကြိုက်ဆုံးစာအုပ်များ", "စာမှတ်များနှင့် မှတ်စု", "ဖတ်ရှုမှုမှတ်တမ်း",
        "အဆင့်မြင့် ရှာဖွေမှု", "အဘိဓမ္မာစာအုပ်များ", "အဘိဓမ္မာ ဖတ်စက်",
        "ဓမ္မသင်ခန်းစာများ", "မင်္ဂလသုတ်နှင့် နိဗ္ဗာန်",
        "နိကာယ်ငါးရပ်", "အက်ပ်အကြောင်း / အကူအညီ"
    };
    private static final String[] EN = {
        "Home", "Tipitaka Introduction", "Tipitaka Collections",
        "Book Categories", "Book Library", "Book Details", "Native Reader",
        "Pali & Myanmar", "Reader Settings", "Content Search", "Favorites",
        "Bookmarks & Notes", "Reading History", "Advanced Search",
        "Abhidhamma Books", "Abhidhamma Reader", "Dhamma Learning",
        "Mangala Sutta & Nibbana", "Five Nikayas", "About & Help"
    };
    private int current = 0, fontSize = 18;
    private LinearLayout content;
    private SharedPreferences prefs;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().setStatusBarColor(BG);
        getWindow().setNavigationBarColor(BG);
        prefs = getSharedPreferences("tipitaka_v22", MODE_PRIVATE);
        fontSize = prefs.getInt("font", 18);
        show(0);
    }
    private TextView text(String value, int size, int color) {
        TextView v = new TextView(this);
        v.setText(value);
        v.setTextSize(size);
        v.setTextColor(color);
        v.setPadding(18, 14, 18, 14);
        return v;
    }
    private void line(String value) { content.addView(text(value, fontSize, WHITE)); }
    private void button(String value, Runnable action) {
        TextView v = text(value, 17, WHITE);
        v.setBackgroundColor(PANEL);
        v.setMinHeight(55);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(-1, -2);
        lp.setMargins(8, 6, 8, 6);
        content.addView(v, lp);
        v.setOnClickListener(w -> action.run());
    }
    private void show(int i) {
        current = i;
        prefs.edit().putInt("lastScreen", i).apply();
        ScrollView scroll = new ScrollView(this);
        scroll.setBackgroundColor(BG);
        content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(10, 16, 10, 55);
        scroll.addView(content);
        setContentView(scroll);
        TextView brand = text("☸  Myanmar Tipitaka", 24, GOLD);
        brand.setTypeface(null, Typeface.BOLD);
        content.addView(brand);
        content.addView(text(String.format(Locale.US, "V2.2  •  Page %02d / 20", i+1), 13, GOLD));
        TextView heading = text(SCREENS[i] + "\n" + EN[i], 22, WHITE);
        heading.setTypeface(null, Typeface.BOLD);
        content.addView(heading);
        if (i == 0) {
            line("မြန်မာ ပိဋကတ်တော် လေ့လာဖတ်ရှုရန် စာမျက်နှာများ");
            button("ဆက်လက်ဖတ်ရှုရန်", () -> show(prefs.getInt("lastRead", 6)));
            for (int j=1; j<SCREENS.length; j++) {
                final int target=j;
                button(String.format(Locale.US, "%02d · %s", j+1, SCREENS[j]), () -> show(target));
            }
        } else {
            if (i == 6 || i == 7 || i == 15) {
                line("ပါဠိ / မြန်မာ — Reader demonstration");
                line("ဤနေရာတွင် စစ်ဆေးပြီးသော ပိဋကတ်စာအုပ်အကြောင်းအရာများ ထည့်သွင်းရန် လိုအပ်ပါသည်။");
                button("A− စာလုံးလျှော့", () -> { fontSize=Math.max(14,fontSize-2); prefs.edit().putInt("font",fontSize).apply(); show(current); });
                button("A+ စာလုံးချဲ့", () -> { fontSize=Math.min(34,fontSize+2); prefs.edit().putInt("font",fontSize).apply(); show(current); });
                button("🔖 စာမှတ်ထားမည်", () -> { prefs.edit().putInt("bookmark",current).apply(); Toast.makeText(this,"စာမှတ်ထားပြီး",Toast.LENGTH_SHORT).show(); });
                prefs.edit().putInt("lastRead",i).apply();
            } else if (i == 11) {
                EditText note = new EditText(this);
                note.setHint("စာမှတ် / မှတ်စု ရေးပါ");
                note.setTextColor(WHITE);
                note.setHintTextColor(GOLD);
                note.setText(prefs.getString("note",""));
                content.addView(note);
                button("မှတ်စု သိမ်းမည်", () -> { prefs.edit().putString("note",note.getText().toString()).apply(); Toast.makeText(this,"သိမ်းဆည်းပြီး",Toast.LENGTH_SHORT).show(); });
                button("စာမှတ်ထားသော စာမျက်နှာ", () -> show(prefs.getInt("bookmark",6)));
            } else if (i == 12) {
                button("နောက်ဆုံးဖတ်ရှုခဲ့သည့် စာမျက်နှာ", () -> show(prefs.getInt("lastRead",6)));
            } else if (i == 9 || i == 13) {
                EditText search = new EditText(this);
                search.setHint("စာမျက်နှာအမည် ရှာဖွေရန်");
                search.setTextColor(WHITE);
                search.setHintTextColor(GOLD);
                search.setSingleLine(true);
                content.addView(search);
                button("ရှာရန်", () -> {
                    String q=search.getText().toString().toLowerCase(Locale.ROOT).trim();
                    if(q.isEmpty()){ Toast.makeText(this,"ရှာဖွေမည့်စာသား ထည့်ပါ",Toast.LENGTH_SHORT).show(); return; }
                    for(int j=0;j<20;j++) if(SCREENS[j].contains(q)||EN[j].toLowerCase(Locale.ROOT).contains(q)){show(j);return;}
                    Toast.makeText(this,"Demo တွင် စာမျက်နှာအမည်သာ ရှာနိုင်သည်",Toast.LENGTH_LONG).show();
                });
            } else if (i == 18) {
                line("ဒီဃနိကာယ် • မဇ္ဈိမနိကာယ် • သံယုတ္တနိကာယ် • အင်္ဂုတ္တရနိကာယ် • ခုဒ္ဒကနိကာယ်");
            } else if (i == 19) {
                line("Myanmar Tipitaka V2.2 — Native Android Starter");
                line("မူရင်းစာအုပ်များ၊ အတည်ပြုထားသော ပိဋကတ်စာသားနှင့် ယခင် UI ဒီဇိုင်းများ မပါဝင်သေးပါ။");
            } else line("ဤစာမျက်နှာတွင် အတည်ပြုထားသော စာအုပ်နှင့်သင်ခန်းစာအချက်အလက်များ ဖြည့်သွင်းရန် လိုအပ်ပါသည်။");
            button("⌂ မူလစာမျက်နှာ", () -> show(0));
            button("‹ အရင်စာမျက်နှာ", () -> show(current-1));
            if(i<19) button("နောက်စာမျက်နှာ ›", () -> show(current+1));
        }
    }
    @Override public void onBackPressed() { if(current!=0)show(0); else super.onBackPressed(); }
}
