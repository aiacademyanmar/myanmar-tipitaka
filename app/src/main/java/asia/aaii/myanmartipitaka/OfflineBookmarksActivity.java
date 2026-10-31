package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.os.Bundle;
import android.view.*;
import android.widget.*;
import java.io.File;
import java.util.Map;
/** Bookmark index reads only local confirmed paragraph IDs; no fabricated text. */
public class OfflineBookmarksActivity extends Activity {
 private LinearLayout list; private SQLiteDatabase db;
 @Override public void onCreate(Bundle state){super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6eb);
  TextView header=new TextView(this);header.setText("☸ သိမ်းထားသော ကျမ်းပိုဒ်များ");header.setTextColor(-1);header.setTextSize(21);header.setPadding(20,20,20,20);header.setBackgroundColor(0xff144638);root.addView(header);
  ScrollView scroll=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);scroll.addView(list);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);
 }
 @Override public void onResume(){super.onResume();refresh();}
 private void refresh(){
  list.removeAllViews();if(db!=null){db.close();db=null;}
  File file=new File(getFilesDir(),"tipitaka_offline.sqlite");
  if(!file.exists()){notice("Offline ကျမ်းစာ Database မပါသေးပါ။");return;}
  try{db=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    SharedPreferences prefs=getSharedPreferences("tipitaka_paragraph_progress",MODE_PRIVATE);int shown=0;
    for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
      if(!e.getKey().startsWith("bookmark_")||!Boolean.TRUE.equals(e.getValue()))continue;
      String id=e.getKey().substring("bookmark_".length());
      try(Cursor c=db.rawQuery("SELECT volume,body FROM paragraphs WHERE id=?",new String[]{id})){
        if(!c.moveToFirst())continue;
        int volume=c.getInt(0);String body=c.getString(1);
        String preview=body.length()>160?body.substring(0,160)+"…":body;
        TextView item=new TextView(this);item.setText("🔖 ကျမ်း "+volume+" · §"+id+"\n"+preview);
        item.setTextSize(17);item.setTextColor(0xff17493c);item.setPadding(22,16,22,16);list.addView(item);
        item.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",volume);i.putExtra("paragraph_id",id);startActivity(i);});
        shown++;
      }
    }
    if(shown==0)notice("Bookmark မရှိသေးပါ။ ကျမ်းပိုဒ် Popup ထဲမှ သိမ်းနိုင်ပါသည်။");
  }catch(Exception e){notice("Bookmark အတွက် Offline Database ဖတ်၍မရပါ။");}
 }
 private void notice(String s){TextView t=new TextView(this);t.setText(s);t.setTextSize(17);t.setPadding(20,20,20,20);list.addView(t);}
 @Override public void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
