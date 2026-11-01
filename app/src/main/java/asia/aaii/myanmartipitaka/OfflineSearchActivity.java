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

/**
 * Offline search across Pali originals and independently reviewed Myanmar
 * translations/explanations. Unreviewed candidate material is never searched
 * or displayed as approved Myanmar content.
 */
public class OfflineSearchActivity extends Activity {
 private SQLiteDatabase db;
 private LinearLayout results;
 private EditText term;
 private Spinner volume;
 private boolean hasReviewedMyanmar=false;

 @Override public void onCreate(Bundle b){
  super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e9);
  TextView header=new TextView(this);header.setText("☸ Offline ကျမ်းပိုဒ် ရှာဖွေရန်");header.setTextColor(-1);header.setTextSize(22);header.setPadding(20,22,16,22);header.setBackgroundColor(0xff144638);root.addView(header);
  term=new EditText(this);term.setSingleLine(true);term.setHint("ပါဠိ / မြန်မာဘာသာပြန် / ရှင်းလင်းချက်");
  term.setText(getIntent().getStringExtra("query")==null?"":getIntent().getStringExtra("query"));root.addView(term);
  String[] options=new String[46];options[0]="ကျမ်းအားလုံး";for(int i=1;i<=45;i++)options[i]="ကျမ်း "+i;
  volume=new Spinner(this);volume.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,options));root.addView(volume);
  String filterName=getIntent().getStringExtra("pitaka_filter");
  if(filterName!=null){if(filterName.contains("ဝိနည်း"))volume.setSelection(1);else if(filterName.contains("သုတ္တန်"))volume.setSelection(9);else if(filterName.contains("အဘိဓမ္မာ"))volume.setSelection(34);}
  Button find=new Button(this);find.setText("Offline ရှာဖွေမည်");root.addView(find);
  TextView scope=new TextView(this);scope.setText("ရှာဖွေမည့်အမျိုးအစား — ပါဠိမူရင်း + စိစစ်အတည်ပြုထားသော မြန်မာစာသားများ");scope.setTextColor(0xff66553b);scope.setPadding(16,8,16,8);root.addView(scope);
  ScrollView scroll=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(1);scroll.addView(results);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  setContentView(root);
  try{
   File f=new File(getFilesDir(),"tipitaka_offline.sqlite");
   if(f.exists()){
    db=SQLiteDatabase.openDatabase(f.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    try(Cursor c=db.rawQuery("SELECT 1 FROM sqlite_master WHERE type='table' AND name='paragraph_myanmar_content'",null)){hasReviewedMyanmar=c.moveToFirst();}
   }
  }catch(Exception ignored){if(db!=null){db.close();db=null;}}
  if(db==null)notice("မူရင်းစာသား Database မပါသေးပါ။ ရှာဖွေမှုကို အသုံးမပြုနိုင်သေးပါ။");
  else notice(hasReviewedMyanmar?
    "မြန်မာအတည်ပြုဘာသာပြန်နှင့် ရှင်းလင်းချက်ပါ ရှာဖွေနိုင်ပါသည်။":
    "လက်ရှိတွင် ပါဠိမူရင်းကို ရှာဖွေနိုင်ပါသည်။ အတည်ပြုမြန်မာစာသား မထည့်ရသေးပါ။");
  find.setOnClickListener(v->search());
  term.setOnEditorActionListener((v,action,event)->{search();return true;});
 }
 private void notice(String msg){TextView t=new TextView(this);t.setText(msg);t.setTextSize(16);t.setTextColor(0xff17483d);t.setPadding(18,16,18,16);results.addView(t);}
 private String preview(String value,int max){if(value==null)return "";String s=value.trim();return s.length()>max?s.substring(0,max)+"…":s;}
 private void search(){
  results.removeAllViews();
  if(db==null){notice("Offline ကျမ်းစာ Database မရှိသေးပါ။");return;}
  String q=term.getText().toString().trim();if(q.isEmpty()){term.setError("ရှာဖွေစာသားထည့်ပါ");return;}
  int chosen=volume.getSelectedItemPosition();
  String filter=chosen>0?(chosen==1?" AND p.volume BETWEEN 1 AND 8":chosen==9?" AND p.volume BETWEEN 9 AND 33":chosen==34?" AND p.volume BETWEEN 34 AND 45":" AND p.volume=?"):"";
  String sql;
  String[] args;
  if(hasReviewedMyanmar){
   sql="SELECT p.id,p.volume,p.segment_id,p.body,"+
     "(SELECT text_my FROM paragraph_myanmar_content m WHERE m.segment_id=p.segment_id AND m.content_type='translation' AND m.reviewed=1 LIMIT 1),"+
     "(SELECT text_my FROM paragraph_myanmar_content x WHERE x.segment_id=p.segment_id AND x.content_type='explanation' AND x.reviewed=1 LIMIT 1),"+
     "CASE WHEN instr(p.body,?)>0 THEN 'ပါဠိမူရင်း' "+
     "WHEN EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.segment_id=p.segment_id AND m.content_type='translation' AND m.reviewed=1 AND instr(m.text_my,?)>0) THEN 'မြန်မာအတည်ပြုဘာသာပြန်' "+
     "ELSE 'မြန်မာအတည်ပြုရှင်းလင်းချက်' END "+
     "FROM paragraphs p WHERE (instr(p.body,?)>0 OR "+
     "EXISTS(SELECT 1 FROM paragraph_myanmar_content m WHERE m.segment_id=p.segment_id AND m.reviewed=1 AND instr(m.text_my,?)>0))"+
     filter+" ORDER BY p.volume,p.id LIMIT 100";
   args=chosen>0?(chosen==1||chosen==9||chosen==34?new String[]{q,q,q,q}:new String[]{q,q,q,q,String.valueOf(chosen)}):new String[]{q,q,q,q};
  }else{
   sql="SELECT p.id,p.volume,p.segment_id,p.body,NULL,NULL,'ပါဠိမူရင်း' FROM paragraphs p WHERE instr(p.body,?)>0"+
     filter+" ORDER BY p.volume,p.id LIMIT 100";
   args=chosen>0?(chosen==1||chosen==9||chosen==34?new String[]{q}:new String[]{q,String.valueOf(chosen)}):new String[]{q};
  }
  try(Cursor c=db.rawQuery(sql,args)){
   int count=0;
   while(c.moveToNext()){
    final String id=c.getString(0);final int vol=c.getInt(1);
    final String segment=c.getString(2);
    String pali=preview(c.getString(3),220);
    String translation=preview(c.isNull(4)?null:c.getString(4),180);
    String explanation=preview(c.isNull(5)?null:c.getString(5),180);
    String matched=c.getString(6);
    TextView t=new TextView(this);
    String text="ကျမ်း "+vol+" · "+segment+"\nကိုက်ညီသည့်နေရာ: "+matched+"\nပါဠိ: "+pali;
    if(!translation.isEmpty())text+="\nမြန်မာဘာသာပြန်: "+translation;
    if(!explanation.isEmpty())text+="\nမြန်မာရှင်းလင်းချက်: "+explanation;
    t.setText(text);t.setTextColor(0xff17483d);t.setTextSize(16);t.setPadding(18,18,18,18);
    t.setBackgroundColor(count%2==0?0xffffffff:0xfff2ecdd);
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(8,4,8,4);results.addView(t,lp);
    t.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",vol);i.putExtra("paragraph_id",id);startActivity(i);});
    count++;
   }
   if(count==0)notice("ကိုက်ညီသော ကျမ်းပိုဒ် မတွေ့ပါ။");
   else notice("ရှာဖွေတွေ့ရှိမှု "+count+" ခု။ ရလဒ် ၁၀၀ ခုအထိ ပြသထားပါသည်။");
  }catch(Exception e){notice("Offline Database ကို ဖတ်၍မရပါ။ Database Version နှင့် Search Schema ကို စစ်ဆေးပါ။");}
 }
 @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
