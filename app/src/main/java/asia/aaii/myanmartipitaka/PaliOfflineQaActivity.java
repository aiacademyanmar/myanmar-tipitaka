package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Build;
import android.os.Bundle;
import android.os.SystemClock;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.InputStream;
import java.util.List;
import java.util.Locale;

/**
 * Device-measured, read-only content QA; the installer may copy the bundled Pali
 * source on first open. Does not make network calls or claim a physical Samsung
 * test without actual hardware execution.
 */
public final class PaliOfflineQaActivity extends Activity {
  private static final int GREEN=0xff144638;
  private TextView report;
  private Button run,share;
  private volatile boolean closed=false, running=false;
  private String lastReport="";
  private TextView text(String value,int size,boolean bold){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(GREEN);
    if(bold)t.setTypeface(null,1);
    t.setPadding(16,14,16,14);return t;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(0xfffaf6e7);
    TextView title=text("☸  Offline Pāli Reader QA • V2.3.7.5",20,true);
    title.setTextColor(Color.WHITE);title.setBackgroundColor(GREEN);root.addView(title);
    ScrollView scroll=new ScrollView(this);
    report=text("စက်ပေါ် QA တိုင်းတာရန်…",14,false);
    scroll.addView(report);
    root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    run=new Button(this);run.setText("↻  Offline QA စမ်းသပ်ရန်");root.addView(run);
    share=new Button(this);share.setText("↗  QA Report မျှဝေရန်");
    share.setEnabled(false);root.addView(share);
    Button browse=new Button(this);browse.setText("📜  Offline Pāli Source ဖတ်ရန်");root.addView(browse);
    Button back=new Button(this);back.setText("‹  App သို့ ပြန်ရန်");root.addView(back);
    setContentView(root);
    run.setOnClickListener(v->inspect());
    share.setOnClickListener(v->shareReport());
    browse.setOnClickListener(v->startActivity(new Intent(this,PaliSourceLibraryActivity.class)));
    back.setOnClickListener(v->finish());
    inspect();
  }
  private void shareReport(){
    if(lastReport.isEmpty())return;
    Intent send=new Intent(Intent.ACTION_SEND);
    send.setType("text/plain");
    send.putExtra(Intent.EXTRA_SUBJECT,"Myanmar Tipitaka V2.3.7.5 Offline Device QA");
    send.putExtra(Intent.EXTRA_TEXT,lastReport);
    startActivity(Intent.createChooser(send,"QA Report မျှဝေရန်"));
  }
  private void inspect(){
    if(running)return;
    running=true;run.setEnabled(false);share.setEnabled(false);
    report.setText("Offline SQLite • First-Open • Search • Bookmark ကို စက်ပေါ်တွင် စစ်ဆေးနေသည်…");
    new Thread(()->{
      StringBuilder result=new StringBuilder();
      SQLiteDatabase db=null;
      boolean passed=false;
      try{
        result.append("Myanmar Tipitaka — Offline Device QA V2.3.7.5\n")
          .append("Device: ").append(Build.MANUFACTURER).append(" ").append(Build.MODEL)
          .append("\nAndroid: ").append(Build.VERSION.RELEASE)
          .append(" (API ").append(Build.VERSION.SDK_INT).append(")")
          .append("\nHardware Samsung: ").append("samsung".equalsIgnoreCase(Build.MANUFACTURER)
            ?"Detected — test performed on this Samsung device":"NOT CONFIRMED — this device is not identified as Samsung")
          .append("\n\n");
        try(InputStream bundled=getAssets().open(PaliSourceInstaller.DB_FILE)){
          if(bundled.read()==-1)throw new IllegalStateException("Bundled Pali SQLite is empty");
        }
        result.append("[PASS] Bundled original Pali SQLite present\n");
        // Runs in the background thread; captures measured cold install or warm reuse.
        PaliSourceInstaller.Result installed=PaliSourceInstaller.prepare(getApplicationContext());
        result.append("[MEASURED] SQLite installer: ").append(installed.elapsedMs)
          .append(" ms | ").append(installed.copied?"COPIED FIRST/NEW REVISION":"REUSED EXISTING")
          .append("\n");
        long warmStart=SystemClock.elapsedRealtime();
        PaliSourceInstaller.Result warm=PaliSourceInstaller.prepare(getApplicationContext());
        long warmMs=SystemClock.elapsedRealtime()-warmStart;
        if(warm.copied)throw new IllegalStateException("Warm installer unnecessarily recopied database");
        result.append("[MEASURED] Second installer call: ").append(warmMs)
          .append(" ms | NO RECOPY\n");
        long openStart=SystemClock.elapsedRealtime();
        db=SQLiteDatabase.openDatabase(installed.file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        long openMs=SystemClock.elapsedRealtime()-openStart;
        result.append("[MEASURED] SQLite open: ").append(openMs).append(" ms\n");
        long checkStart=SystemClock.elapsedRealtime();
        try(Cursor c=db.rawQuery("PRAGMA quick_check",null)){
          if(!c.moveToFirst()||!"ok".equalsIgnoreCase(c.getString(0)))
            throw new IllegalStateException("SQLite quick_check failed");
        }
        result.append("[PASS] SQLite quick_check: ")
          .append(SystemClock.elapsedRealtime()-checkStart).append(" ms\n");
        long count=0,files=0;
        try(Cursor c=db.rawQuery("SELECT COUNT(*),COUNT(DISTINCT source_file) FROM source_segments",null)){
          if(c.moveToFirst()){count=c.getLong(0);files=c.getLong(1);}
        }
        if(count<=0||files<=0)throw new IllegalStateException("No readable Pali text/source files");
        result.append("[PASS] Pali Source Segments: ").append(count)
          .append("\n[PASS] Source Files: ").append(files)
          .append("\nSQLite size: ")
          .append(String.format(Locale.US,"%.2f MiB",installed.file.length()/1048576.0))
          .append("\n");
        String commit=null;
        try(Cursor c=db.rawQuery("SELECT value FROM build_info WHERE name='commit'",null)){
          if(c.moveToFirst())commit=c.getString(0);
        }
        if(commit==null||!commit.equalsIgnoreCase(installed.revision))
          throw new IllegalStateException("Source revision metadata does not match APK");
        result.append("[PASS] Source revision: ").append(commit).append("\n");
        String firstFile=null,firstSegment=null,firstBody=null;
        long sampleStart=SystemClock.elapsedRealtime();
        try(Cursor c=db.rawQuery("SELECT source_file,segment_id,body FROM source_segments ORDER BY rowid LIMIT 1",null)){
          if(c.moveToFirst()){firstFile=c.getString(0);firstSegment=c.getString(1);firstBody=c.getString(2);}
        }
        if(firstFile==null||firstSegment==null||firstBody==null||firstBody.trim().isEmpty())
          throw new IllegalStateException("Unable to read first original Pali paragraph");
        result.append("[PASS] First paragraph read: ")
          .append(SystemClock.elapsedRealtime()-sampleStart).append(" ms\n");
        long segmentStart=SystemClock.elapsedRealtime();boolean segmentHit=false;
        try(Cursor c=db.rawQuery(
          "SELECT source_file FROM source_segments WHERE segment_id=? LIMIT 1",
          new String[]{firstSegment})){
          segmentHit=c.moveToFirst()&&firstFile.equals(c.getString(0));
        }
        if(!segmentHit)throw new IllegalStateException("Exact segment ID search failed");
        result.append("[PASS] Exact segment search: ")
          .append(SystemClock.elapsedRealtime()-segmentStart).append(" ms\n");
        // Search a guaranteed text sample without relying on invented test content.
        String phrase=firstBody.substring(0,Math.min(firstBody.length(),10));
        long textStart=SystemClock.elapsedRealtime();boolean textHit=false;
        try(Cursor c=db.rawQuery(
          "SELECT segment_id FROM source_segments WHERE source_file=? AND instr(body,?)>0 LIMIT 1",
          new String[]{firstFile,phrase})){
          textHit=c.moveToFirst();
        }
        if(!textHit)throw new IllegalStateException("Offline text search failed");
        result.append("[PASS] Offline text search: ")
          .append(SystemClock.elapsedRealtime()-textStart).append(" ms\n");
        List<PaliReadingState.Entry> saved=new PaliReadingState(this).bookmarks();
        int sample=Math.min(10,saved.size()),reachable=0;
        for(int i=0;i<sample;i++){
          PaliReadingState.Entry bookmark=saved.get(i);
          try(Cursor c=db.rawQuery(
            "SELECT 1 FROM source_segments WHERE source_file=? AND segment_id=? LIMIT 1",
            new String[]{bookmark.file,bookmark.segment})){
            if(c.moveToFirst())reachable++;
          }
        }
        result.append("[MEASURED] Saved Segment Bookmarks: ").append(saved.size())
          .append("\n[MEASURED] Tested bookmarks present: ").append(reachable).append("/")
          .append(sample).append("\n");
        if(reachable!=sample)result.append("[WARN] Some saved bookmarks are stale after source update\n");
        result.append("\n[AUTO-QA PASS] Real source SQLite + search tests passed.\n");
        passed=true;
      }catch(Exception e){
        result.append("\n[AUTO-QA FAIL] ").append(e.getMessage()==null?e.getClass().getSimpleName():e.getMessage()).append("\n");
      }finally{
        if(db!=null)db.close();
      }
      result.append("\n--- MANUAL DEVICE CHECKLIST ---\n")
        .append("[PENDING] Enable Airplane Mode; reopen source and read 3 pages\n")
        .append("[PENDING] Turn Wi-Fi and mobile data OFF; search a Pali word\n")
        .append("[PENDING] Add bookmark; exit and reopen; resume exact paragraph\n")
        .append("[PENDING] Repeat test after APK upgrade (bookmarks retained)\n")
        .append("[PENDING] Check Myanmar Unicode rendering and touch responsiveness\n")
        .append("[PENDING] Record battery, device storage and crash behavior\n")
        .append("\n--- EDITORIAL RELEASE ---\n")
        .append("MCU 45-volume edition mapping: 0/45 VERIFIED\n")
        .append("Human-approved Myanmar translations: 0%\n")
        .append("Human-approved Myanmar explanations: 0%\n")
        .append("This is an UNMAPPED Pali source PREVIEW, not a final 45-book release.\n");
      final String text=result.toString();
      runOnUiThread(()->{
        if(closed||isFinishing())return;
        running=false;lastReport=text;run.setEnabled(true);share.setEnabled(true);
        report.setText(text);
      });
    },"pali-offline-qa-metrics").start();
  }
  @Override protected void onDestroy(){closed=true;super.onDestroy();}
}
