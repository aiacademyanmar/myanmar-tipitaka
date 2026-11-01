package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.Map;

/** User-controlled SAF backup/restore for local reader progress. No storage permission required. */
public final class ReaderStateBackupActivity extends Activity {
  private static final int CREATE_BACKUP=8101,OPEN_BACKUP=8102;
  private static final String PREF="tipitaka_paragraph_progress";
  private static final String FORMAT="myanmar-tipitaka-reader-state";
  private TextView status;

  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(24,24,24,24);root.setBackgroundColor(0xfffaf6eb);
    TextView title=new TextView(this);title.setText("☸ Reader Backup & Restore");title.setTextSize(23);title.setTextColor(0xff144638);root.addView(title);
    status=new TextView(this);status.setText("Bookmark၊ Notes၊ History နှင့် Reader Settings များကို ဖုန်းပြင်ပသို့ Backup လုပ်နိုင်ပါသည်။");status.setTextSize(16);status.setPadding(0,18,0,18);root.addView(status);
    Button export=new Button(this);export.setText("⬆ Backup ဖိုင် ထုတ်မည်");root.addView(export);export.setOnClickListener(v->createBackup());
    Button restore=new Button(this);restore.setText("⬇ Backup ဖိုင် ပြန်ထည့်မည်");root.addView(restore);restore.setOnClickListener(v->openBackup());
    Button back=new Button(this);back.setText("ပြန်သွားမည်");root.addView(back);back.setOnClickListener(v->finish());
    setContentView(root);
  }
  private void createBackup(){
    Intent i=new Intent(Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);
    i.setType("application/json");i.putExtra(Intent.EXTRA_TITLE,"MyanmarTipitaka-ReaderBackup.json");
    startActivityForResult(i,CREATE_BACKUP);
  }
  private void openBackup(){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType("application/json");
    startActivityForResult(i,OPEN_BACKUP);
  }
  private boolean allowed(String key){
    return key.startsWith("bookmark_")||key.startsWith("history_")||key.startsWith("note_")||
      key.equals("reader_font")||key.equals("last_volume")||key.equals("last_paragraph_id")||
      key.equals("last_read_at")||key.matches("volume_[0-9]+_page");
  }
  @Override protected void onActivityResult(int request,int result,Intent data){
    super.onActivityResult(request,result,data);
    if(result!=RESULT_OK||data==null||data.getData()==null)return;
    Uri uri=data.getData();
    try{
      if(request==CREATE_BACKUP)writeBackup(uri);
      else if(request==OPEN_BACKUP)readBackup(uri);
    }catch(Exception e){status.setText("လုပ်ဆောင်၍မရပါ: "+e.getMessage());}
  }
  private void writeBackup(Uri uri)throws Exception{
    android.content.SharedPreferences prefs=getSharedPreferences(PREF,MODE_PRIVATE);
    JSONObject values=new JSONObject();int count=0;
    for(Map.Entry<String,?> e:prefs.getAll().entrySet()){
      if(!allowed(e.getKey()))continue;
      Object value=e.getValue();
      if(value instanceof String||value instanceof Integer||value instanceof Long||value instanceof Boolean){
        values.put(e.getKey(),value);count++;
      }
    }
    JSONObject root=new JSONObject();root.put("format",FORMAT);root.put("schema_version",1);
    root.put("created_at",System.currentTimeMillis());root.put("item_count",count);root.put("values",values);
    try(OutputStream out=getContentResolver().openOutputStream(uri,"w")){
      if(out==null)throw new IllegalStateException("Backup ဖိုင်ကို ဖွင့်၍မရပါ");
      out.write(root.toString(2).getBytes(StandardCharsets.UTF_8));out.flush();
    }
    status.setText("✓ Backup အောင်မြင်ပါသည်။ "+count+" ခု သိမ်းဆည်းပြီး။");
    Toast.makeText(this,"Reader Backup ပြီးပါပြီ",Toast.LENGTH_LONG).show();
  }
  private void readBackup(Uri uri)throws Exception{
    ByteArrayOutputStream bytes=new ByteArrayOutputStream();
    try(InputStream in=getContentResolver().openInputStream(uri)){
      if(in==null)throw new IllegalStateException("Backup ဖိုင်ကို ဖတ်၍မရပါ");
      byte[] buf=new byte[8192];int n;
      while((n=in.read(buf))!=-1){bytes.write(buf,0,n);if(bytes.size()>5*1024*1024)throw new IllegalArgumentException("Backup ဖိုင်အရွယ်အစား 5 MB ကျော်နေပါသည်");}
    }
    JSONObject root=new JSONObject(new String(bytes.toByteArray(),StandardCharsets.UTF_8));
    if(!FORMAT.equals(root.optString("format"))||root.optInt("schema_version")!=1)
      throw new IllegalArgumentException("Myanmar Tipitaka Reader Backup ဖိုင်မဟုတ်ပါ သို့မဟုတ် Version မကိုက်ညီပါ");
    JSONObject values=root.getJSONObject("values");
    android.content.SharedPreferences prefs=getSharedPreferences(PREF,MODE_PRIVATE);
    android.content.SharedPreferences.Editor edit=prefs.edit();int restored=0;
    java.util.Iterator<String> keys=values.keys();
    while(keys.hasNext()){
      String key=keys.next();if(!allowed(key))continue;
      Object v=values.get(key);
      if(v instanceof String)edit.putString(key,(String)v);
      else if(v instanceof Boolean)edit.putBoolean(key,(Boolean)v);
      else if(v instanceof Integer)edit.putInt(key,(Integer)v);
      else if(v instanceof Long)edit.putLong(key,(Long)v);
      else if(v instanceof Number)edit.putLong(key,((Number)v).longValue());
      else continue;
      restored++;
    }
    if(restored==0)throw new IllegalArgumentException("ပြန်ထည့်နိုင်သော Reader Data မတွေ့ပါ");
    if(!edit.commit())throw new IllegalStateException("ဖုန်းထဲသို့ Restore မအောင်မြင်ပါ");
    status.setText("✓ Restore အောင်မြင်ပါသည်။ "+restored+" ခု ပြန်ထည့်ပြီး။");
    Toast.makeText(this,"Reader Data Restore ပြီးပါပြီ",Toast.LENGTH_LONG).show();
  }
}
