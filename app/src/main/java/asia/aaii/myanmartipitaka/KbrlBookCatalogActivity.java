package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
public final class KbrlBookCatalogActivity extends Activity{
 private LinearLayout list; private JSONArray books=new JSONArray(); private EditText search;
 private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
 private void open(JSONObject b){Intent i=new Intent(this,OnlineBookReaderActivity.class);i.putExtra("url",b.optString("detail_url"));i.putExtra("source_title",b.optString("title_my"));startActivity(i);}
 private void load(){
  try(InputStream in=getAssets().open("kbrl_reference_books.json");ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] buf=new byte[4096];int n;while((n=in.read(buf))>0)out.write(buf,0,n);
   books=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8)).getJSONArray("books");
  }catch(Exception e){Toast.makeText(this,"KBRL Catalog မဖတ်နိုင်ပါ",Toast.LENGTH_LONG).show();}
 }
 private void draw(String query){
  list.removeAllViews();String q=query==null?"":query.toLowerCase();
  for(int x=0;x<books.length();x++){JSONObject b=books.optJSONObject(x);if(b==null)continue;
   String title=b.optString("title_my");if(!title.toLowerCase().contains(q))continue;
   LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(14),dp(12),dp(14),dp(12));card.setBackgroundColor(Color.WHITE);
   TextView t=new TextView(this);t.setText(title);t.setTextSize(17);t.setTextColor(0xff144638);t.setTypeface(null,1);card.addView(t);
   TextView p=new TextView(this);p.setText("KBRL · "+b.optString("book_id")+" · "+b.optString("publisher"));p.setTextSize(12);p.setTextColor(0xff766b58);card.addView(p);
   TextView a=new TextView(this);a.setText("မူရင်းစာကြည့်တိုက်တွင် ဖတ်ရှုရန် ↗");a.setTextColor(0xff144638);a.setPadding(0,dp(8),0,0);card.addView(a);
   card.setOnClickListener(v->open(b));LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(4),0,dp(4));list.addView(card,lp);
  }
  if(list.getChildCount()==0){TextView empty=new TextView(this);empty.setText("ရှာဖွေမှုနှင့် ကိုက်ညီသော စာအုပ်မရှိပါ");empty.setPadding(dp(12),dp(20),dp(12),dp(20));list.addView(empty);}
 }
 @Override public void onCreate(Bundle b){super.onCreate(b);getWindow().setStatusBarColor(0xff144638);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e7);
  TextView h=new TextView(this);h.setText("☸ KBRL မြန်မာပြန်စာအုပ်များ");h.setTextColor(Color.WHITE);h.setTextSize(20);h.setPadding(dp(16),dp(18),dp(16),dp(18));h.setBackgroundColor(0xff144638);root.addView(h);
  search=new EditText(this);search.setSingleLine(true);search.setHint("စာအုပ်အမည် ရှာရန်");root.addView(search);
  ScrollView sc=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);list.setPadding(dp(12),dp(8),dp(12),dp(20));sc.addView(list);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
  TextView note=new TextView(this);note.setText("မှတ်ချက် — ဤစာရင်းတွင် KBRL detail page ကို အတည်ပြုတွေ့ရှိထားသော စာအုပ်များသာ ပါဝင်သည်။ PDF Preview URL ကို မခန့်မှန်းထားပါ။ Download နှင့် ပြန်လည်ဖြန့်ဝေခွင့်ကို မူရင်းထုတ်ဝေသူထံ စစ်ဆေးပါ။");note.setTextSize(12);note.setPadding(dp(12),dp(8),dp(12),dp(8));root.addView(note);
  setContentView(root);load();draw("");search.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int c,int a){}public void onTextChanged(CharSequence s,int st,int before,int count){draw(s.toString());}public void afterTextChanged(android.text.Editable e){}});
 }
}