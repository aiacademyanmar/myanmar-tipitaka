package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.View;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashSet;
import java.util.List;

/**
 * Offline reader for original Bilara Pali source file hierarchy.
 * This is NOT an MCU 45-volume edition reader; editorial book boundaries vary.
 * No invented translations or explanations are displayed.
 */
public final class PaliSourceLibraryActivity extends Activity {
  private static final int GREEN=Color.rgb(20,66,56), CREAM=Color.rgb(250,245,231);
  private static final String ASSET="pali_root_source.sqlite";
  private LinearLayout content;
  private SQLiteDatabase db;
  private final ArrayList<String> files=new ArrayList<>();
  private String prefix="", currentFile=null;
  private int currentPage=0;
  private SharedPreferences readingState;
  private PaliReadingState segments;
  private String sourceRevision="";
  private volatile boolean shuttingDown=false;
  private int dp(int d){return (int)(d*getResources().getDisplayMetrics().density+.5f);}
  private TextView label(String text,int sp,boolean bold){
    TextView v=new TextView(this);v.setText(text);v.setTextColor(GREEN);v.setTextSize(sp);
    if(bold)v.setTypeface(null,1);
    v.setPadding(dp(14),dp(12),dp(14),dp(12));
    return v;
  }
  private void addRow(String s,Runnable action){
    TextView item=label(s,16,true);
    GradientDrawable bg=new GradientDrawable();
    bg.setColor(Color.WHITE);bg.setCornerRadius(dp(12));item.setBackground(bg);
    LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);
    p.setMargins(dp(12),dp(5),dp(12),dp(5));
    content.addView(item,p);item.setOnClickListener(v->action.run());
  }
  private void note(String s){content.addView(label(s,15,false));}
  @Override public void onCreate(Bundle b){
    super.onCreate(b);
    readingState=getSharedPreferences("pali_source_reading",MODE_PRIVATE);
    segments=new PaliReadingState(this);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(CREAM);
    TextView header=label("☸  မူရင်းပါဠိ Offline Source Library",21,true);
    header.setTextColor(Color.WHITE);header.setBackgroundColor(GREEN);
    root.addView(header);
    ScrollView scroll=new ScrollView(this);
    content=new LinearLayout(this);content.setOrientation(LinearLayout.VERTICAL);
    scroll.addView(content);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TextView back=label("‹ ပြန်ရန် / Back",17,true);
    back.setTextColor(Color.WHITE);back.setBackgroundColor(GREEN);
    root.addView(back);back.setOnClickListener(v->goBack());
    setContentView(root);
    note("ပါဠိ Dataset ကို Offline ဖွင့်နေပါသည်။ ပထမအကြိမ်တွင် စာသား Database ကို ဖုန်းထဲသို့ ကူးယူပါမည်။");
    new Thread(this::initialize,"pali-source-init").start();
  }
  private void initialize(){
    SQLiteDatabase opened=null;
    try{
      PaliSourceInstaller.Result installed=PaliSourceInstaller.prepare(this);
      File dest=installed.file;
      sourceRevision=installed.revision;
      android.util.Log.i("PaliSourcePerformance","install_ms="+installed.elapsedMs+" copied="+installed.copied);
      opened=SQLiteDatabase.openDatabase(dest.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
      try(Cursor c=opened.rawQuery("SELECT DISTINCT source_file FROM source_segments ORDER BY source_file",null)){
        while(c.moveToNext())files.add(c.getString(0));
      }
      if(files.isEmpty())throw new IllegalStateException("Empty Pali source library");
      db=opened;
      runOnUiThread(()->{
        if(shuttingDown)return;
        String requested=getIntent().getStringExtra("source_file");
        String segment=getIntent().getStringExtra("source_segment_id");
        if(requested!=null && files.contains(requested)){
          int target=0;
          if(segment!=null){
            try(Cursor c=db.rawQuery("SELECT COUNT(*) FROM source_segments WHERE source_file=? AND rowid < (SELECT rowid FROM source_segments WHERE segment_id=? LIMIT 1)",new String[]{requested,segment})){
              if(c.moveToFirst())target=c.getInt(0)/50;
            }
          }
          showFile(requested,target);
        }else browse("");
      });
    }catch(Exception e){
      if(opened!=null && opened!=db)opened.close();
      final String message=e.getMessage()==null?"Database unavailable":e.getMessage();
      runOnUiThread(()->{if(!shuttingDown){content.removeAllViews();note("Offline ပါဠိ Dataset မဖွင့်နိုင်ပါ — "+message);}});
    }
  }
  private void browse(String p){
    if(shuttingDown)return;
    prefix=p;currentFile=null;content.removeAllViews();
    note("Bilara Pāli Source • Myanmar Tipitaka\nမူရင်းစာသားများသာ ပါဝင်သည်။ MCU ၄၅ ကျမ်း အုပ်ခွဲများ အတည်မပြုရသေးပါ။");
    if(p.isEmpty()){
      addRow("၁။ ဝိနည်းပိဋကတ် • Vinaya",()->browse("vinaya/"));
      addRow("၂။ သုတ္တပိဋကတ် • Sutta",()->browse("sutta/"));
      addRow("၃။ အဘိဓမ္မပိဋကတ် • Abhidhamma",()->browse("abhidhamma/"));
      addRow("⌕  Offline ပါဠိစာသား ရှာရန်",()->openSearch(null));
      String lastFile=readingState.getString("last_file",null);
      if(lastFile!=null&&files.contains(lastFile)){
        int lastPage=readingState.getInt("page_"+lastFile,0);
        addRow("▶ ဆက်လက်ဖတ်ရှုရန် • "+lastFile,()->showFile(lastFile,lastPage));
      }
      PaliReadingState.Entry last=segments.lastRead();
      if(last!=null&&files.contains(last.file))addRow("▶ စာပိုဒ်မှ ဆက်ဖတ်ရန် • "+last.segment,()->jumpToSegment(last.file,last.segment));
      addRow("🔖 စာပိုဒ် Bookmarks",this::showSegmentBookmarks);
      note("Source ဖိုင်အလိုက် ဖတ်ရှုနိုင်ပြီး အင်တာနက်မလိုပါ။");
      return;
    }
    note("Source Path: "+p);
    addRow("⌕  ယခု Source အတွင်း ရှာရန်",()->openSearch(null));
    LinkedHashSet<String> entries=new LinkedHashSet<>();
    for(String file:files){
      if(!file.startsWith(p))continue;
      String suffix=file.substring(p.length());int cut=suffix.indexOf('/');
      entries.add(cut>=0?suffix.substring(0,cut)+"/":suffix);
    }
    ArrayList<String> sorted=new ArrayList<>(entries);Collections.sort(sorted);
    if(sorted.isEmpty())note("ဒီအုပ်စုထဲတွင် စာသားမတွေ့ပါ။");
    for(String entry:sorted){
      if(entry.endsWith("/")){
        addRow("📚  "+entry,()->browse(p+entry));
      }else{
        addRow("📖  "+entry,()->showFile(p+entry,0));
      }
    }
  }
  private void showFile(String file,int page){
    if(db==null || shuttingDown)return;
    currentFile=file;currentPage=Math.max(0,page);content.removeAllViews();
    note("ဖတ်ရှုနေသည် • "+file+"\nPage "+(currentPage+1)+" · ပါဠိမူရင်းစာသား");
    addRow("‹ နောက်ပြန်စာမျက်နှာ",()->showFile(file,Math.max(0,currentPage-1)));
    ArrayList<String[]> results=new ArrayList<>();
    try(Cursor c=db.rawQuery("SELECT segment_id,body FROM source_segments WHERE source_file=? ORDER BY rowid LIMIT 50 OFFSET "+(currentPage*50),new String[]{file})){
      while(c.moveToNext())results.add(new String[]{c.getString(0),c.getString(1)});
    }catch(Exception e){note("စာသားဖတ်၍မရပါ: "+e.getMessage());return;}
    if(results.isEmpty())note("ယခုစာမျက်နှာတွင် စာသားမရှိပါ။");
    if(!results.isEmpty())segments.lastRead(file,results.get(0)[0],sourceRevision);
    for(String[] row:results){
      TextView v=label(row[0]+"\n"+row[1]+"\n🔖 Bookmark",16,false);
      v.setOnClickListener(view->{segments.add(file,row[0],sourceRevision);android.widget.Toast.makeText(this,"စာပိုဒ် Bookmark သိမ်းပြီး",android.widget.Toast.LENGTH_SHORT).show();});
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);
      lp.setMargins(dp(9),dp(4),dp(9),dp(4));content.addView(v,lp);
      View separator=new View(this);separator.setBackgroundColor(0xffd5c8ae);
      content.addView(separator,new LinearLayout.LayoutParams(-1,dp(1)));
    }
    if(results.size()==50)addRow("နောက်စာမျက်နှာ ›",()->showFile(file,currentPage+1));
    addRow("‹ Source File စာရင်း",()->browse(parent(file)));
  }
  private void jumpToSegment(String file,String segment){
    if(db==null)return;
    try(Cursor present=db.rawQuery("SELECT 1 FROM source_segments WHERE source_file=? AND segment_id=? LIMIT 1",new String[]{file,segment})){
      if(!present.moveToFirst()){
        new AlertDialog.Builder(this).setMessage("Source Revision ပြောင်းသွား၍ Bookmark ကျမ်းပိုဒ် မတွေ့ပါ။").setPositiveButton("OK",null).show();return;
      }
    }
    try(Cursor cursor=db.rawQuery("SELECT COUNT(*) FROM source_segments WHERE source_file=? AND rowid<(SELECT rowid FROM source_segments WHERE source_file=? AND segment_id=? LIMIT 1)",new String[]{file,file,segment})){
      if(cursor.moveToFirst())showFile(file,cursor.getInt(0)/50);
    }
  }
  private void showSegmentBookmarks(){
    java.util.List<PaliReadingState.Entry> saved=segments.bookmarks();
    if(saved.isEmpty()){new AlertDialog.Builder(this).setMessage("စာပိုဒ် Bookmark မရှိသေးပါ").setPositiveButton("OK",null).show();return;}
    String[] names=new String[saved.size()];
    for(int i=0;i<saved.size();i++)names[i]=saved.get(i).segment+" • "+saved.get(i).file;
    new AlertDialog.Builder(this).setTitle("စာပိုဒ် Bookmarks").setItems(names,(d,i)->{
      PaliReadingState.Entry e=saved.get(i);
      if(files.contains(e.file))jumpToSegment(e.file,e.segment);
    }).setNegativeButton("ပိတ်ရန်",null).show();
  }
  private void openSearch(String file){
    Intent i=new Intent(this,PaliOfflineSearchActivity.class);
    if(file!=null)i.putExtra("source_file",file);
    startActivity(i);
  }
  private void saveBookmark(String file,int page){
    String key="bookmark_"+file;
    java.util.Set<String> values=new java.util.HashSet<>(readingState.getStringSet(key,java.util.Collections.emptySet()));
    values.add(Integer.toString(page));
    readingState.edit().putStringSet(key,values).apply();
    android.widget.Toast.makeText(this,"Bookmark သိမ်းပြီး",android.widget.Toast.LENGTH_SHORT).show();
  }
  private void openBookmarks(){
    String file=currentFile==null?readingState.getString("last_file",null):currentFile;
    if(file==null){note("Bookmark မရှိသေးပါ။");return;}
    java.util.ArrayList<Integer> pages=new java.util.ArrayList<>();
    for(String v:readingState.getStringSet("bookmark_"+file,java.util.Collections.emptySet())){
      try{pages.add(Integer.parseInt(v));}catch(Exception ignored){}
    }
    java.util.Collections.sort(pages);
    if(pages.isEmpty()){new AlertDialog.Builder(this).setTitle("Bookmarks").setMessage("သိမ်းထားသော စာမျက်နှာ မရှိသေးပါ။").setPositiveButton("OK",null).show();return;}
    String[] names=new String[pages.size()];
    for(int i=0;i<pages.size();i++)names[i]="Page "+(pages.get(i)+1);
    String chosenFile=file;
    new AlertDialog.Builder(this).setTitle("Bookmarks • "+file).setItems(names,(d,i)->showFile(chosenFile,pages.get(i))).setNegativeButton("ပိတ်ရန်",null).show();
  }
  private String parent(String file){
    int n=file.lastIndexOf('/');
    return n<0?"":file.substring(0,n+1);
  }
  private void goBack(){
    if(currentFile!=null){browse(parent(currentFile));return;}
    if(prefix.isEmpty()){finish();return;}
    String trimmed=prefix.endsWith("/")?prefix.substring(0,prefix.length()-1):prefix;
    int n=trimmed.lastIndexOf('/');
    browse(n<0?"":trimmed.substring(0,n+1));
  }
  @Override public void onBackPressed(){goBack();}
  @Override protected void onDestroy(){
    shuttingDown=true;
    if(db!=null){try{db.close();}catch(Exception ignored){}}
    super.onDestroy();
  }
}
