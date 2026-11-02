package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.view.inputmethod.EditorInfo;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.util.ArrayList;
import java.util.Locale;

/** Offline search for genuine Bilara Pali SOURCE segments, not 45 printed MCU volumes.
 * Searches are run on a worker thread and limited to 60 displayed results.
 */
public final class PaliOfflineSearchActivity extends Activity {
  private static final int GREEN=0xff144638, GOLD=0xffad873d, MAX_RESULTS=60;
  private EditText query;
  private TextView status;
  private Button search;
  private LinearLayout results;
  private String fileFilter="";
  private volatile int generation=0;
  private boolean destroyed=false;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+0.5f);}
  private TextView label(String value,int size,boolean bold){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(GREEN);
    if(bold)t.setTypeface(null,1);t.setPadding(dp(12),dp(12),dp(12),dp(12));return t;
  }
  private static class Hit {
    final String path,segment,body;
    Hit(String p,String s,String b){path=p;segment=s;body=b;}
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    fileFilter=getIntent().getStringExtra("source_file");
    if(fileFilter==null)fileFilter="";
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(0xfffaf6e7);
    TextView head=label("☸  Offline Pāli Search",21,true);
    head.setBackgroundColor(GREEN);head.setTextColor(Color.WHITE);root.addView(head);
    TextView scope=label(fileFilter.isEmpty()?"Pāli မူရင်း Source အားလုံးတွင် ရှာရန်":
      "Source File: "+fileFilter,13,false);root.addView(scope);
    query=new EditText(this);query.setSingleLine(true);query.setHint("ပါဠိစာသား သို့မဟုတ် Segment ID");
    query.setImeOptions(EditorInfo.IME_ACTION_SEARCH);root.addView(query);
    search=new Button(this);search.setText("⌕  Offline ရှာရန်");root.addView(search);
    status=label("မူရင်းပါဠိစာသားများအတွင်းသာ ရှာဖွေမည်။ မြန်မာအတည်ပြုဘာသာပြန် မပါသေးပါ။",13,false);root.addView(status);
    ScrollView sc=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(LinearLayout.VERTICAL);
    sc.addView(results);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
    Button back=new Button(this);back.setText("‹  Reader သို့ပြန်ရန်");root.addView(back);
    back.setOnClickListener(v->finish());search.setOnClickListener(v->runSearch());
    query.setOnEditorActionListener((t,action,event)->{runSearch();return true;});
    setContentView(root);
    String initial=getIntent().getStringExtra("query");
    if(initial!=null){query.setText(initial);if(!initial.trim().isEmpty())runSearch();}
  }
  private void runSearch(){
    String q=query.getText().toString().trim();
    if(q.isEmpty()){query.setError("ရှာရန်စာသား ထည့်ပါ");return;}
    if(q.length()>100){query.setError("စာလုံးရေ ၁၀၀ ထက်မပိုရ");return;}
    int token=++generation;
    search.setEnabled(false);status.setText("Offline Source SQLite ရှာဖွေနေသည်…");
    results.removeAllViews();
    new Thread(()->{
      ArrayList<Hit> hits=new ArrayList<>();
      String failure=null;long started=android.os.SystemClock.elapsedRealtime();
      SQLiteDatabase db=null;
      try{
        File local=new File(getFilesDir(),"pali_root_source.sqlite");
        if(!local.isFile())throw new IllegalStateException("Offline Pāli Source ကို Reader မှ အရင်ဖွင့်ပါ။");
        db=SQLiteDatabase.openDatabase(local.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        final String sql;
        final String[] args;
        if(fileFilter.isEmpty()){
          sql="SELECT source_file,segment_id,body FROM source_segments "+
              "WHERE segment_id=? OR instr(body,?)>0 LIMIT "+MAX_RESULTS;
          args=new String[]{q,q};
        }else{
          sql="SELECT source_file,segment_id,body FROM source_segments "+
              "WHERE source_file=? AND (segment_id=? OR instr(body,?)>0) LIMIT "+MAX_RESULTS;
          args=new String[]{fileFilter,q,q};
        }
        try(Cursor c=db.rawQuery(sql,args)){
          while(c.moveToNext())hits.add(new Hit(c.getString(0),c.getString(1),c.getString(2)));
        }
      }catch(Exception e){failure=e.getMessage()==null?"Offline Search မအောင်မြင်":e.getMessage();}
      finally{if(db!=null)db.close();}
      long elapsed=android.os.SystemClock.elapsedRealtime()-started;
      String error=failure;
      runOnUiThread(()->{
        if(destroyed||isFinishing()||token!=generation)return;
        search.setEnabled(true);
        results.removeAllViews();
        if(error!=null){status.setText("ရှာဖွေမှု မအောင်မြင်ပါ: "+error);return;}
        status.setText("တွေ့ရှိမှု "+hits.size()+" ခု (အများဆုံး "+MAX_RESULTS+") • "+elapsed+" ms");
        if(hits.isEmpty()){results.addView(label("ကိုက်ညီသော ပါဠိစာသား မတွေ့ပါ။",15,false));return;}
        for(Hit h:hits){
          String snippet=h.body==null?"":h.body;
          if(snippet.length()>280)snippet=snippet.substring(0,280)+"…";
          TextView item=label("§ "+h.segment+"\n"+h.path+"\n\n"+snippet+"\n\nဖတ်ရန် →",15,false);
          item.setBackgroundColor(Color.WHITE);
          LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(10),dp(5),dp(10),dp(5));
          results.addView(item,lp);
          item.setOnClickListener(v->{
            Intent i=new Intent(this,PaliSourceLibraryActivity.class);
            i.putExtra("source_file",h.path);
            i.putExtra("source_segment_id",h.segment);
            startActivity(i);
          });
        }
      });
    },"offline-pali-source-search").start();
  }
  @Override protected void onDestroy(){destroyed=true;++generation;super.onDestroy();}
}
