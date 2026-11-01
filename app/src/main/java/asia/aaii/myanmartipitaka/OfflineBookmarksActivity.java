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
 private LinearLayout list; private SQLiteDatabase db; private EditText query; private Spinner filter;
 @Override public void onCreate(Bundle state){super.onCreate(state);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6eb);
  TextView header=new TextView(this);header.setText("☸ သိမ်းထားသော ကျမ်းပိုဒ်များ");header.setTextColor(-1);header.setTextSize(21);header.setPadding(20,20,20,20);header.setBackgroundColor(0xff144638);root.addView(header);
  query=new EditText(this);query.setSingleLine(true);query.setHint("Bookmark စာသားရှာရန်");root.addView(query);
  String[] options=new String[46];options[0]="ကျမ်းအားလုံး";for(int i=1;i<=45;i++)options[i]="ကျမ်း "+i;
  filter=new Spinner(this);filter.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,options));root.addView(filter);
  query.addTextChangedListener(new android.text.TextWatcher(){public void beforeTextChanged(CharSequence s,int start,int count,int after){}public void onTextChanged(CharSequence s,int start,int before,int count){refresh();}public void afterTextChanged(android.text.Editable e){}});
  filter.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener(){public void onNothingSelected(android.widget.AdapterView<?> parent){}public void onItemSelected(android.widget.AdapterView<?> parent,View v,int position,long id){refresh();}});
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
        if(filter!=null&&filter.getSelectedItemPosition()>0&&filter.getSelectedItemPosition()!=volume)continue;
        String needle=query==null?"":query.getText().toString().trim();
        if(!needle.isEmpty()&&!body.contains(needle)&&!id.contains(needle))continue;
        String preview=body.length()>160?body.substring(0,160)+"…":body;
        TextView item=new TextView(this);item.setText("🔖 ကျမ်း "+volume+" · §"+id+"\n"+preview);
        item.setTextSize(17);item.setTextColor(0xff17493c);item.setPadding(22,16,22,16);list.addView(item);
        item.setOnLongClickListener(v->{new android.app.AlertDialog.Builder(this).setTitle("Bookmark ဖယ်ရှားရန်").setMessage("ကျမ်း "+volume+" · §"+id+" ကို Bookmark မှ ဖယ်မလား?")
          .setNegativeButton("မဖယ်ပါ",null).setPositiveButton("ဖယ်ရှားမည်",(d,w)->{prefs.edit().remove("bookmark_"+id).apply();refresh();}).show();return true;});
        item.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",volume);i.putExtra("paragraph_id",id);startActivity(i);});
        shown++;
      }
    }
    // Reading history and per-paragraph notes are stored locally in the same preferences.
    int historyShown=0,notesShown=0;
    TextView historyHeader=new TextView(this);historyHeader.setText("🕘 ဖတ်ရှုမှုမှတ်တမ်း");historyHeader.setTextSize(19);historyHeader.setTextColor(0xff144638);historyHeader.setPadding(18,18,18,10);list.addView(historyHeader);
    for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
      if(!e.getKey().startsWith("history_")||!(e.getValue() instanceof String))continue;
      String[] parts=((String)e.getValue()).split("\\|",3);if(parts.length<2)continue;
      int vol;try{vol=Integer.parseInt(parts[0]);}catch(Exception ex){continue;}
      if(filter!=null&&filter.getSelectedItemPosition()>0&&filter.getSelectedItemPosition()!=vol)continue;
      String id=e.getKey().substring("history_".length());
      try(Cursor c=db.rawQuery("SELECT body FROM paragraphs WHERE id=?",new String[]{id})){
        if(!c.moveToFirst())continue;
        String body=c.getString(0);String needle=query==null?"":query.getText().toString().trim();
        if(!needle.isEmpty()&&!body.contains(needle)&&!id.contains(needle))continue;
        TextView item=new TextView(this);item.setText("🕘 ကျမ်း "+vol+" · §"+parts[1]+"\\n"+(body.length()>130?body.substring(0,130)+"…":body));
        item.setTextSize(16);item.setTextColor(0xff17493c);item.setPadding(22,14,22,14);list.addView(item);
        item.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",vol);i.putExtra("paragraph_id",id);startActivity(i);});
        historyShown++;
      }
    }
    TextView notesHeader=new TextView(this);notesHeader.setText("📝 ကျမ်းပိုဒ်အလိုက် ကိုယ်ပိုင်မှတ်စု");notesHeader.setTextSize(19);notesHeader.setTextColor(0xff144638);notesHeader.setPadding(18,18,18,10);list.addView(notesHeader);
    for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
      if(!e.getKey().startsWith("note_")||!(e.getValue() instanceof String)||((String)e.getValue()).trim().isEmpty())continue;
      String id=e.getKey().substring("note_".length());
      try(Cursor c=db.rawQuery("SELECT volume,body FROM paragraphs WHERE id=?",new String[]{id})){
        if(!c.moveToFirst())continue;int vol=c.getInt(0);
        if(filter!=null&&filter.getSelectedItemPosition()>0&&filter.getSelectedItemPosition()!=vol)continue;
        String note=(String)e.getValue(),body=c.getString(1);String needle=query==null?"":query.getText().toString().trim();
        if(!needle.isEmpty()&&!note.contains(needle)&&!body.contains(needle)&&!id.contains(needle))continue;
        TextView item=new TextView(this);item.setText("📝 ကျမ်း "+vol+" · §"+id+"\\n"+(note.length()>180?note.substring(0,180)+"…":note));
        item.setTextSize(16);item.setTextColor(0xff55422a);item.setPadding(22,14,22,14);list.addView(item);
        item.setOnClickListener(v->{Intent i=new Intent(this,ParagraphExplanationActivity.class);i.putExtra("volume",vol);i.putExtra("paragraph_id",id);startActivity(i);});
        notesShown++;
      }
    }
    if(shown==0&&historyShown==0&&notesShown==0)notice("Bookmark၊ ဖတ်ရှုမှုမှတ်တမ်း သို့မဟုတ် မှတ်စု မတွေ့ပါ။");

  }catch(Exception e){notice("Bookmark အတွက် Offline Database ဖတ်၍မရပါ။");}
 }
 private void notice(String s){TextView t=new TextView(this);t.setText(s);t.setTextSize(17);t.setPadding(20,20,20,20);list.addView(t);}
 @Override public void onDestroy(){if(db!=null)db.close();super.onDestroy();}
}
