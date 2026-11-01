package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.graphics.Color;
import android.widget.*;
import java.io.File;
public final class OfflineDatabaseQaActivity extends Activity {
 private LinearLayout body;
 private void line(String text){TextView t=new TextView(this);t.setText(text);t.setTextSize(16);t.setTextColor(0xff144638);t.setPadding(16,12,16,12);body.addView(t);}
 @Override public void onCreate(Bundle state){super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e7);
  TextView head=new TextView(this);head.setText("☸ Offline Database QA");head.setTextSize(22);head.setTextColor(Color.WHITE);head.setBackgroundColor(0xff144638);head.setPadding(20,20,20,20);root.addView(head);
  ScrollView scroll=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);scroll.addView(body);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
  Button check=new Button(this);check.setText("SQLite ထပ်မံစစ်ဆေးရန်");root.addView(check);check.setOnClickListener(v->inspect());setContentView(root);inspect();
 }
 private void inspect(){body.removeAllViews();new Thread(()->{
   StringBuilder result=new StringBuilder();SQLiteDatabase db=null;
   try{
     File file=OfflineCorpusInstaller.prepare(getApplicationContext());
     db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
     try(Cursor c=db.rawQuery("PRAGMA quick_check",null)){result.append("SQLite quick_check: ").append(c.moveToFirst()?c.getString(0):"FAILED").append("\n");}
     try(Cursor c=db.rawQuery("SELECT COUNT(*),COUNT(DISTINCT volume) FROM paragraphs",null)){if(c.moveToFirst())result.append("Pāli စာပိုဒ်: ").append(c.getLong(0)).append("\nကျမ်းအရေအတွက်: ").append(c.getInt(1)).append("/45\n");}
     for(int vol=1;vol<=45;vol++){
       try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM paragraphs WHERE volume=?",new String[]{Integer.toString(vol)})){
         result.append("ကျမ်း ").append(vol).append(" — ").append(c.moveToFirst()?c.getLong(0):0).append(" စာပိုဒ်\n");
       }
     }
     File local=getDatabasePath(MyanmarContentStore.DB_NAME);
     if(local.isFile()){
       try(SQLiteDatabase overlay=SQLiteDatabase.openDatabase(local.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
           Cursor c=overlay.rawQuery("SELECT content_type,COUNT(*) FROM paragraph_myanmar_content WHERE reviewed=1 GROUP BY content_type",null)){
         result.append("\nLocal Publisher မြန်မာစာသား:\n");
         while(c.moveToNext())result.append(c.getString(0)).append(": ").append(c.getLong(1)).append("\n");
       }
     }else result.append("\nLocal Publisher Myanmar database: မရှိသေး\n");
     result.append("\nမှတ်ချက်: ၄၅ ကျမ်း Crosswalk နှင့် Publisher Rights မစစ်ဆေးဘဲ Final Release မပြုလုပ်ပါ။");
   }catch(Exception e){result.append("BLOCKED — ").append(e.getMessage()==null?"SQLite မရှိ သို့မဟုတ် မပြည့်စုံ":" "+e.getMessage());}
   finally{if(db!=null)db.close();}
   final String text=result.toString();runOnUiThread(()->{if(!isFinishing()){body.removeAllViews();line(text);}});
  },"tipitaka-db-qa").start();}
}
