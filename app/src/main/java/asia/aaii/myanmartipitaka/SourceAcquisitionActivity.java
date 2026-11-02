package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.graphics.Color;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Local, read-only acquisition status. No unsupported source is shown as verified. */
public final class SourceAcquisitionActivity extends Activity {
  private LinearLayout list;
  private void openCatalog(){startActivity(new Intent(this,ReferenceLibraryActivity.class));}
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e9);
    TextView h=new TextView(this);h.setText("☸ မြန်မာပြန် ရင်းမြစ်စစ်ဆေးမှု — 45 ကျမ်း");h.setTextSize(20);h.setTextColor(Color.WHITE);h.setPadding(20,20,20,20);h.setBackgroundColor(0xff144638);root.addView(h);
    Button catalog=new Button(this);catalog.setText("Online Reference Library ဖွင့်ရန်");root.addView(catalog);catalog.setOnClickListener(v->openCatalog());
    ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    try(InputStream in=getAssets().open("verified_source_acquisition_catalog.json");ByteArrayOutputStream out=new ByteArrayOutputStream()){
      byte[] buf=new byte[4096];int n;while((n=in.read(buf))!=-1)out.write(buf,0,n);
      JSONObject data=new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
      JSONArray books=data.getJSONArray("volumes");
      TextView note=new TextView(this);note.setText("ရင်းမြစ်လင့်ခ်များသည် ရှာဖွေလေ့လာရန်သာ ဖြစ်ပြီး မူပိုင်ခွင့်နှင့် Edition တိုက်ဆိုင်စစ်ဆေးပြီးဟု မဆိုလိုပါ။");note.setPadding(16,16,16,16);note.setTextColor(0xff695638);list.addView(note);
      for(int i=0;i<books.length();i++){
        JSONObject b=books.getJSONObject(i);
        TextView t=new TextView(this);t.setText(String.format(java.util.Locale.US,"%02d",b.getInt("volume_id"))+" · "+b.getString("title_my")+"\n"+(b.getBoolean("source_verified")?"ရင်းမြစ်အတည်ပြုပြီး":"ရင်းမြစ်နှင့် ပြန်လည်ဖြန့်ဝေခွင့် စစ်ဆေးရန်ကျန်ရှိ"));
        t.setTextSize(16);t.setTextColor(0xff144638);t.setPadding(20,14,20,14);list.addView(t);
        String url=b.optString("source_book_url","");
        if(url.startsWith("https://"))t.setOnClickListener(v->{Intent intent=new Intent(this,OnlineBookReaderActivity.class);intent.putExtra("url",url);intent.putExtra("source_title",b.optString("title_my"));startActivity(intent);});
      }
    }catch(Exception e){TextView msg=new TextView(this);msg.setText("Source Catalog မရရှိပါ။ QA Build ကို စစ်ဆေးပါ။");list.addView(msg);}
    setContentView(root);
  }
}
