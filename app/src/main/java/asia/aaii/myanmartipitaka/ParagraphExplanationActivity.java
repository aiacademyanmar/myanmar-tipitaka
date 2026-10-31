package asia.aaii.myanmartipitaka;
import android.app.*;
import android.content.*;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import java.io.File;

/** Paragraph-by-paragraph explanation browser. It never substitutes fabricated Myanmar explanation for missing records. */
public class ParagraphExplanationActivity extends Activity {
 private SQLiteDatabase db; private LinearLayout rows; private int volume;
 @Override public void onCreate(Bundle state){super.onCreate(state);
  volume=getIntent().getIntExtra("volume",1);LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6eb);
  TextView title=new TextView(this);title.setText("☸ ကျမ်း "+volume+" — ကျမ်းပိုဒ်နှင့် မြန်မာရှင်းလင်းချက်");title.setTextSize(21);title.setTextColor(-1);title.setPadding(18,22,16,22);title.setBackgroundColor(0xff144638);root.addView(title);
  ScrollView scroll=new ScrollView(this);rows=new LinearLayout(this);rows.setOrientation(1);scroll.addView(rows);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);
  File file=new File(getFilesDir(),"tipitaka_offline.sqlite");
  if(!file.exists()){notice("မူရင်းကျမ်းစာသား Database ကို APK ထဲ မထည့်သွင်းရသေးပါ။");return;}
  try{db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    Cursor c=db.rawQuery("SELECT p.id,p.body,e.explanation_my,e.source_ref FROM paragraphs p LEFT JOIN paragraph_explanations e ON e.paragraph_id=p.id AND e.language='my' WHERE p.volume=? ORDER BY p.id LIMIT 200",new String[]{String.valueOf(volume)});
    int count=0;while(c.moveToNext()){final String id=c.getString(0),body=c.getString(1),explain=c.isNull(2)?null:c.getString(2),ref=c.isNull(3)?"":c.getString(3);
      TextView t=new TextView(this);t.setText("§"+id+"\n"+body+"\n\n☸ မြန်မာရှင်းလင်းချက် ကြည့်ရန်");t.setTextSize(18);t.setTextColor(0xff17493c);
      t.setPadding(22,18,22,18);rows.addView(t);t.setOnClickListener(v->popup(body,explain,ref));count++;}
    c.close();if(count==0)notice("ဤကျမ်းအတွက် Offline ကျမ်းပိုဒ်များ မတွေ့ပါ။");
  }catch(Exception e){notice("Offline Database တွင် paragraph_explanations Table သို့မဟုတ် သက်ဆိုင်ရာ Data မရှိသေးပါ။");}
 }
 private void notice(String s){TextView t=new TextView(this);t.setText(s);t.setTextSize(18);t.setPadding(22,24,22,24);rows.addView(t);}
 private void popup(String pali,String my,String ref){
  LinearLayout box=new LinearLayout(this);box.setOrientation(1);box.setPadding(20,18,20,18);box.setBackgroundColor(0xfffaf6eb);
  TextView original=new TextView(this);original.setText("မူရင်းကျမ်းပိုဒ်\n"+pali);original.setTextSize(18);original.setTextColor(0xff194b3d);box.addView(original);
  TextView explanation=new TextView(this);explanation.setPadding(0,20,0,10);explanation.setTextSize(18);explanation.setTextColor(0xff55422a);
  explanation.setText(my==null||my.trim().isEmpty()?"ဤကျမ်းပိုဒ်အတွက် အတည်ပြုထားသော မြန်မာရှင်းလင်းချက် မထည့်သွင်းရသေးပါ။":my);box.addView(explanation);
  if(!ref.isEmpty()){TextView source=new TextView(this);source.setText("ရင်းမြစ်: "+ref);source.setTextSize(13);box.addView(source);}
  new AlertDialog.Builder(this).setTitle("☸ မြန်မာဘာသာ ရှင်းလင်းချက်").setView(box).setPositiveButton("ပိတ်မည်",null).show();
 }
 @Override protected void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
