package asia.aaii.myanmartipitaka;
import android.app.*;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.content.Intent;
import android.view.*;
import android.widget.*;
import android.graphics.Color;
import java.io.File;
/** Local-only paged search. No network requests or invented match results. */
public class OfflineSearchActivity extends Activity {
 private SQLiteDatabase db;private LinearLayout results;private EditText term;private Spinner volume;
 @Override public void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e9);
  TextView header=new TextView(this);header.setText("☸ Offline ကျမ်းပိုဒ် ရှာဖွေရန်");header.setTextColor(-1);header.setTextSize(22);header.setPadding(20,22,16,22);header.setBackgroundColor(0xff144638);root.addView(header);
  term=new EditText(this);term.setSingleLine(true);term.setHint("ပါဠိ / မြန်မာ စာသား");root.addView(term);
  String[] options=new String[46];options[0]="ကျမ်းအားလုံး";for(int i=1;i<=45;i++)options[i]="ကျမ်း "+i;
  volume=new Spinner(this);volume.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,options));root.addView(volume);
  Button find=new Button(this);find.setText("Offline ရှာဖွေမည်");root.addView(find);
  ScrollView scroll=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(1);scroll.addView(results);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  setContentView(root);
  try{File f=new File(getFilesDir(),"tipitaka_offline.sqlite");if(f.exists())db=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);}catch(Exception ignored){}
  if(db==null)notice("မူရင်းစာသား Database မပါသေးပါ။ ရှာဖွေမှုကို အသုံးမပြုနိုင်သေးပါ။");
  find.setOnClickListener(v->search());
 }
 private void notice(String msg){TextView t=new TextView(this);t.setText(msg);t.setTextSize(17);t.setTextColor(0xff17483d);t.setPadding(18,16,18,16);results.addView(t);}
 private void search(){
  results.removeAllViews();if(db==null){notice("Offline ကျမ်းစာ Database မရှိသေးပါ။");return;}
  String q=term.getText().toString().trim();if(q.isEmpty()){term.setError("ရှာဖွေစာသားထည့်ပါ");return;}
  // Use instr() rather than LIKE to treat % and _ as literal characters.
  int chosen=volume.getSelectedItemPosition();
  String sql="SELECT id,volume,body FROM paragraphs WHERE instr(body,?)>0"+(chosen>0?" AND volume=?":"")+" ORDER BY volume,id LIMIT 100";
  String[] args=chosen>0?new String[]{q,String.valueOf(chosen)}:new String[]{q};
  try(Cursor c=db.rawQuery(sql,args)){
    int count=0;while(c.moveToNext()){
      final String id=c.getString(0);final int vol=c.getInt(1);
      String body=c.getString(2);if(body.length()>260)body=body.substring(0,260)+"…";
      TextView t=new TextView(this);t.setText("ကျမ်း "+vol+" · §"+id+"\n"+body+"\nမြန်မာရှင်းလင်းချက် →");t.setTextColor(0xff17483d);t.setTextSize(16);t.setPadding(18,18,18,18);results.addView(t);
      t.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",vol);i.putExtra("paragraph_id",id);startActivity(i);});count++;
    }
    if(count==0)notice("ကိုက်ညီသော ကျမ်းပိုဒ် မတွေ့ပါ။");
    if(count==100)notice("ပထမဆုံး ရလဒ် ၁၀၀ ကိုသာ ပြသထားပါသည်။");
  }catch(Exception e){notice("Offline Database ကို ဖတ်၍မရပါ။");}
 }
 @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
