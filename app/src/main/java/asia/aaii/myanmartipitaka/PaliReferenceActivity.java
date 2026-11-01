package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.File;

/** Read-only offline Pali dictionary and actual imported CST/PTS reference lookup.
 * Dictionary entries appear only when a rights-cleared curated lexicon is bundled.
 * CST/PTS references are pointers, never made-up Aṭṭhakathā or Ṭīkā passages.
 */
public final class PaliReferenceActivity extends Activity {
 private SQLiteDatabase db;
 private EditText query;
 private Spinner mode;
 private LinearLayout results;
 private final int GREEN=0xff144638;
 private TextView note(String s){
  TextView t=new TextView(this);t.setText(s);t.setTextColor(GREEN);
  t.setTextSize(16);t.setPadding(18,18,18,18);results.addView(t);return t;
 }
 @Override public void onCreate(Bundle state){
  super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(0xfffaf6eb);
  TextView head=new TextView(this);head.setText("☸ ပါဠိဝေါဟာရနှင့် ကျမ်းညွှန်း");head.setTextSize(22);head.setTextColor(Color.WHITE);head.setPadding(18,22,18,22);head.setBackgroundColor(GREEN);root.addView(head);
  mode=new Spinner(this);
  mode.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,new String[]{"Pāli–Myanmar Dictionary","CST / PTS Reference Search"}));
  root.addView(mode);
  query=new EditText(this);query.setSingleLine(true);query.setHint("Pāli word / CST / PTS reference");root.addView(query);
  Button search=new Button(this);search.setText("Offline Search");root.addView(search);
  ScrollView scroll=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(LinearLayout.VERTICAL);
  scroll.addView(results);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  Button back=new Button(this);back.setText("‹ ပြန်ရန်");root.addView(back);back.setOnClickListener(v->finish());
  setContentView(root);
  note("စစ်ဆေးပြီးသော ဝေါဟာရအဘိဓာန် ဒေတာသာ ပြသပါမည်။ CST / PTS ကျမ်းညွှန်းသည် အဋ္ဌကထာ သို့မဟုတ် ဋီကာ၏ အဓိပ္ပာယ်ဖွင့်ဆိုချက် မဟုတ်ပါ။");
  new Thread(()->{
    try{
      File f=OfflineCorpusInstaller.prepare(getApplicationContext());
      SQLiteDatabase opened=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      runOnUiThread(()->{db=opened;note("Offline Database ဖွင့်ပြီး။");});
    }catch(Exception ex){runOnUiThread(()->note("Offline Database ဖွင့်၍မရပါ။"));}
  },"reference-database").start();
  search.setOnClickListener(v->doSearch());
 }
 private boolean table(String name){
  try(Cursor c=db.rawQuery("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",new String[]{name})){return c.moveToFirst();}
 }
 private void doSearch(){
  results.removeAllViews();
  if(db==null){note("Offline Database ပြင်ဆင်နေဆဲ သို့မဟုတ် မဖွင့်နိုင်ပါ။");return;}
  String q=query.getText().toString().trim();if(q.length()==0){query.setError("ရှာဖွေမည့်စာသား ထည့်ပါ");return;}
  if(mode.getSelectedItemPosition()==0){
    if(!table("pali_dictionary")){note("စိစစ်ပြီးသော ပါဠိ–မြန်မာ Dictionary မထည့်သွင်းရသေးပါ။");return;}
    try(Cursor c=db.rawQuery("SELECT headword,meaning_my,source_ref FROM pali_dictionary WHERE verified=1 AND (instr(headword,?)>0 OR instr(meaning_my,?)>0) ORDER BY headword LIMIT 80",new String[]{q,q})){
      int count=0;
      while(c.moveToNext()){
        note(c.getString(0)+"\n"+c.getString(1)+"\nရင်းမြစ်: "+c.getString(2));count++;
      }
      if(count==0)note("အတည်ပြုထားသော ဝေါဟာရ မတွေ့ပါ။");
    }catch(Exception e){note("Dictionary schema မကိုက်ညီပါ။");}
    return;
  }
  if(!table("cst_source_paragraphs")){note("CST / PTS Offline Reference Dataset မရရှိသေးပါ။");return;}
  String sql="SELECT cst_ref,pts_ref,page_title,source_url,pali_text FROM cst_source_paragraphs "+
     "WHERE instr(COALESCE(cst_ref,''),?)>0 OR instr(COALESCE(pts_ref,''),?)>0 OR instr(pali_text,?)>0 "+
     "ORDER BY source_path,page_paragraph_index LIMIT 80";
  try(Cursor c=db.rawQuery(sql,new String[]{q,q,q})){
    int count=0;
    while(c.moveToNext()){
      String pali=c.getString(4);if(pali.length()>350)pali=pali.substring(0,350)+"…";
      String text="CST: "+(c.isNull(0)?"—":c.getString(0))+" • PTS: "+(c.isNull(1)?"—":c.getString(1))+
        "\n"+c.getString(2)+"\n"+pali+"\nSource: "+c.getString(3);
      note(text);count++;
    }
    if(count==0)note("ကိုက်ညီသော CST / PTS reference မတွေ့ပါ။");
    else note("ရလဒ် "+count+" ခု (အများဆုံး ၈၀)။ ဤတို့သည် မူရင်းကျမ်းညွှန်းများသာ ဖြစ်သည်။");
  }catch(Exception e){note("Offline CST Reference ဖတ်၍မရပါ။");}
 }
 @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
