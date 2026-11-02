package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.os.Build;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.io.InputStream;
import java.util.Locale;

/** On-device read-only QA for the bundled *unmapped* Bilara source.
 * This activity does NOT imply verified MCU printed-edition 45-volume coverage.
 */
public final class PaliOfflineQaActivity extends Activity {
  private static final int GREEN=0xff144638;
  private TextView report;
  private boolean closed=false;
  private TextView text(String value,int sp,boolean strong){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(sp);
    t.setTextColor(GREEN);if(strong)t.setTypeface(null,1);
    t.setPadding(16,14,16,14);return t;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(0xfffaf6e7);
    TextView title=text("☸  Offline Pāli Reader QA",21,true);
    title.setTextColor(Color.WHITE);title.setBackgroundColor(GREEN);root.addView(title);
    ScrollView scroll=new ScrollView(this);
    report=text("စစ်ဆေးနေပါသည်…",15,false);scroll.addView(report);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    Button check=new Button(this);check.setText("↻  SQLite ထပ်စစ်ရန်");root.addView(check);
    Button browse=new Button(this);browse.setText("📜  Offline Pāli Source ဖတ်ရန်");root.addView(browse);
    Button back=new Button(this);back.setText("‹  App သို့ ပြန်ရန်");root.addView(back);
    setContentView(root);
    check.setOnClickListener(v->inspect());
    browse.setOnClickListener(v->startActivity(new Intent(this,PaliSourceLibraryActivity.class)));
    back.setOnClickListener(v->finish());
    inspect();
  }
  private void inspect(){
    report.setText("SQLite / စက်အချက်အလက် စစ်ဆေးနေသည်…");
    new Thread(()->{
      StringBuilder message=new StringBuilder();
      SQLiteDatabase db=null;
      try {
        message.append("Device: ").append(Build.MANUFACTURER).append(" ").append(Build.MODEL)
          .append("\nAndroid: ").append(Build.VERSION.RELEASE)
          .append("\nSDK: ").append(Build.VERSION.SDK_INT).append("\n\n");
        boolean bundled=false;
        try(InputStream asset=getAssets().open("pali_root_source.sqlite")){bundled=asset.read()!=-1;}
        message.append("APK Bundle SQLite: ").append(bundled?"PASS":"MISSING").append("\n");
        if(!bundled)throw new IllegalStateException("APK တွင် Pāli Source SQLite မပါပါ။");
        File local=new File(getFilesDir(),"pali_root_source.sqlite");
        message.append("Installed SQLite: ").append(local.isFile()?"YES":"NOT YET").append("\n");
        if(!local.isFile()){
          message.append("\nပထမဦးဆုံး 'Offline Pāli Source ဖတ်ရန်' ကိုဖွင့်ပြီး Database ကူးယူပါ။ ပြီးမှ QA ပြန်စစ်ပါ။");
        }else{
          message.append("SQLite Size: ").append(String.format(Locale.US,"%.2f MB",local.length()/1048576.0)).append("\n");
          db=SQLiteDatabase.openDatabase(local.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
          try(Cursor c=db.rawQuery("PRAGMA quick_check",null)){
            if(!c.moveToFirst()||!"ok".equalsIgnoreCase(c.getString(0)))throw new IllegalStateException("SQLite quick_check FAILED");
            message.append("SQLite quick_check: PASS\n");
          }
          long segments=0,files=0;
          try(Cursor c=db.rawQuery("SELECT COUNT(*),COUNT(DISTINCT source_file) FROM source_segments",null)){
            if(c.moveToFirst()){segments=c.getLong(0);files=c.getLong(1);}
          }
          if(segments<=0||files<=0)throw new IllegalStateException("Pāli Source အလွတ်ဖြစ်နေပါသည်။");
          message.append("Pāli Segments: ").append(segments).append("\nSource Files: ").append(files).append("\n");
          try(Cursor c=db.rawQuery("SELECT value FROM build_info WHERE name='commit' LIMIT 1",null)){
            if(!c.moveToFirst()||c.getString(0).length()!=40)throw new IllegalStateException("Source Commit Metadata မပြည့်စုံပါ။");
            message.append("Source Commit: ").append(c.getString(0)).append("\n");
          }
          try(Cursor c=db.rawQuery("SELECT source_file,segment_id,body FROM source_segments ORDER BY rowid LIMIT 1",null)){
            if(!c.moveToFirst()||c.getString(2)==null||c.getString(2).trim().isEmpty())
              throw new IllegalStateException("First Pāli Segment မဖတ်နိုင်ပါ။");
            message.append("First Segment: ").append(c.getString(1)).append("\n");
            message.append("Source File: ").append(c.getString(0)).append("\n");
          }
          message.append("\nOffline Pāli Source QA: PASS\n");
        }
      }catch(Exception e){
        message.append("\nOffline Pāli Source QA: FAILED\n").append(e.getMessage());
      }finally{if(db!=null)db.close();}
      message.append("\n\nMCU 45-Book Verified Mapping: 0 / 45")
        .append("\nApproved Myanmar Translation: 0%")
        .append("\nApproved Myanmar Explanation: 0%")
        .append("\nSamsung Manual QA: PENDING")
        .append("\n\nOffline မူရင်းပါဠိ Source QA သည် MCU ၄၅ ကျမ်း အတည်ပြုခြင်း မဟုတ်ပါ။");
      final String result=message.toString();
      runOnUiThread(()->{if(!closed&&!isFinishing())report.setText(result);});
    },"pali-offline-device-qa").start();
  }
  @Override protected void onDestroy(){closed=true;super.onDestroy();}
}
