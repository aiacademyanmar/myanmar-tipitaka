package asia.aaii.myanmartipitaka;
import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.widget.*;
import org.json.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.Locale;

/** Honest project progress dashboard: source verification and actual local
 * content are measured separately. Never equate a compile success to full corpus. */
public final class ProjectProgressActivity extends Activity {
 private LinearLayout body;
 private int dp(int a){return (int)(a*getResources().getDisplayMetrics().density+.5f);}
 private void label(String text,int size){TextView t=new TextView(this);t.setText(text);t.setTextSize(size);t.setTextColor(0xff144638);t.setPadding(dp(10),dp(8),dp(10),dp(8));body.addView(t);}
 private void bar(String title,int done,int total){
  int percentage=total==0?0:(int)Math.min(100,100L*done/total);
  label(title+"  —  "+done+" / "+total+" ("+percentage+"%)",15);
  ProgressBar b=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);b.setMax(Math.max(1,total));b.setProgress(done);
  LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,dp(10));p.setMargins(dp(12),0,dp(12),dp(12));body.addView(b,p);
 }
 private JSONObject readAsset(String name)throws Exception{
  try(InputStream in=getAssets().open(name);ByteArrayOutputStream out=new ByteArrayOutputStream()){
   byte[] b=new byte[8192];int n;while((n=in.read(b))!=-1)out.write(b,0,n);
   return new JSONObject(new String(out.toByteArray(),StandardCharsets.UTF_8));
  }
 }
 @Override public void onCreate(Bundle b){super.onCreate(b);
  LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e7);
  TextView h=new TextView(this);h.setText("☸ Project Progress — Myanmar Tipitaka");h.setTextColor(Color.WHITE);h.setTextSize(21);h.setBackgroundColor(0xff144638);h.setPadding(dp(16),dp(18),dp(16),dp(18));root.addView(h);
  ScrollView sc=new ScrollView(this);body=new LinearLayout(this);body.setOrientation(1);sc.addView(body);root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
  Button refresh=new Button(this);refresh.setText("↻ Progress ပြန်စစ်ရန်");root.addView(refresh);refresh.setOnClickListener(v->render());
  Button source=new Button(this);source.setText("📖 Online Source References");root.addView(source);source.setOnClickListener(v->startActivity(new Intent(this,ReferenceLibraryActivity.class)));
  setContentView(root);render();
 }
 private void render(){
  body.removeAllViews();label("Progress သည် လက်ရှိဖုန်း၏ SQLite ဒေတာနှင့် Source Evidence ကိုသာ အခြေခံသည်။",14);
  try{
   JSONObject catalog=readAsset("verified_source_acquisition_catalog.json");
   JSONArray books=catalog.getJSONArray("volumes");int verified=0;
   for(int i=0;i<books.length();i++)if(books.getJSONObject(i).optBoolean("source_verified"))verified++;
   bar("ရင်းမြစ် Edition + အသုံးပြုခွင့် အတည်ပြု",verified,45);
  }catch(Exception e){bar("Source Acquisition (မစစ်ဆေးရသေး)",0,45);}
  label("Offline Corpus + မြန်မာဘာသာပြန် Coverage",18);
  File pali=null;SQLiteDatabase db=null,overlay=null;
  try{
   pali=OfflineCorpusInstaller.prepare(this);
   db=SQLiteDatabase.openDatabase(pali.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
   int[] paragraphs=new int[46];int[] translations=new int[46];int[] explanations=new int[46];
   try(Cursor c=db.rawQuery("SELECT volume,COUNT(*) FROM paragraphs GROUP BY volume",null)){
    while(c.moveToNext()){int v=c.getInt(0);if(v>=1&&v<=45)paragraphs[v]=c.getInt(1);}
   }
   File local=getDatabasePath(MyanmarContentStore.DB_NAME);
   if(local.isFile()){
    overlay=SQLiteDatabase.openDatabase(local.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    // Each local entry is joined to its actual Pali volume, never inferred.
    db.execSQL("ATTACH DATABASE ? AS local_my",new Object[]{local.getAbsolutePath()});
    try(Cursor c=db.rawQuery("SELECT p.volume,m.content_type,COUNT(*) FROM paragraphs p JOIN local_my.paragraph_myanmar_content m ON m.paragraph_id=p.id WHERE m.reviewed=1 AND length(trim(m.text_my))>0 GROUP BY p.volume,m.content_type",null)){
     while(c.moveToNext()){int v=c.getInt(0);if(v<1||v>45)continue;
      if("translation".equals(c.getString(1)))translations[v]=c.getInt(2);
      if("explanation".equals(c.getString(1)))explanations[v]=c.getInt(2);
     }
    }
   }
   int books=0,total=0,tr=0,ex=0;
   for(int v=1;v<=45;v++){if(paragraphs[v]>0)books++;total+=paragraphs[v];tr+=translations[v];ex+=explanations[v];}
   bar("ပါဠိကျမ်းစာပါသော Volumes",books,45);
   bar("မြန်မာအတည်ပြုဘာသာပြန်",tr,total);
   bar("မြန်မာအတည်ပြုရှင်းလင်းချက်",ex,total);
   label("ကျမ်းတစ်ကျမ်းချင်းစီ",18);
   for(int v=1;v<=45;v++){
    if(paragraphs[v]==0){label(String.format(Locale.US,"ကျမ်း %02d — Offline Pāli မရှိသေး",v),13);continue;}
    bar(String.format(Locale.US,"ကျမ်း %02d · Translation",v),translations[v],paragraphs[v]);
    bar(String.format(Locale.US,"ကျမ်း %02d · Explanation",v),explanations[v],paragraphs[v]);
   }
  }catch(Exception e){
   bar("Offline Pāli ကျမ်းဒေတာ (မရရှိသေး)",0,45);
   label("BLOCKED: ဖုန်းအတွင်း Full SQLite မရှိသေးပါ။ Compiler APK အောင်မြင်မှုကို Content ပြည့်စုံမှုအဖြစ် မရောပါ။",14);
  }finally{if(overlay!=null)overlay.close();if(db!=null)db.close();}
 }
}
