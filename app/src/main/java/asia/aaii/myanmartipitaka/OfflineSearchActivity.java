package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import java.io.File;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.Normalizer;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Map;

/**
 * Read-only offline search over Pali paragraphs and the standalone publisher's
 * separately verified-at-import local content overlay. No data is created.
 * All SQLite searches run off the UI thread to prevent ANRs on large corpora.
 */
public final class OfflineSearchActivity extends Activity {
  private static final int GREEN=0xff144638, INK=0xff17483d;
  private LinearLayout results;
  private EditText term;
  private Spinner volumes;
  private Button searchButton;
  private TextView status;
  private String filterName;
  private volatile boolean searching=false;

  private static final class Match {
    long id;int volume;String segment,body,translation="",explanation="",kind;
    Match(long i,int v,String s,String b,String k){id=i;volume=v;segment=s;body=b;kind=k;}
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e9);
    TextView header=new TextView(this);header.setText("☸ Offline ကျမ်းပိုဒ် ရှာဖွေရန်");header.setTextColor(Color.WHITE);
    header.setTextSize(22);header.setPadding(18,22,16,22);header.setBackgroundColor(GREEN);root.addView(header);
    term=new EditText(this);term.setSingleLine(true);term.setHint("ပါဠိ / မြန်မာဘာသာပြန် / ရှင်းလင်းချက်");
    String query=getIntent().getStringExtra("query");term.setText(query==null?"":query);root.addView(term);
    String[] options=new String[46];options[0]="ကျမ်းအားလုံး";
    for(int i=1;i<=45;i++)options[i]="ကျမ်း "+i;
    volumes=new Spinner(this);volumes.setAdapter(new ArrayAdapter<String>(this,android.R.layout.simple_spinner_dropdown_item,options));root.addView(volumes);
    filterName=getIntent().getStringExtra("pitaka_filter");
    searchButton=new Button(this);searchButton.setText("Offline ရှာဖွေမည်");root.addView(searchButton);
    status=new TextView(this);status.setText("ပါဠိနှင့် Local Publisher မှ စစ်ဆေးထည့်သွင်းထားသော မြန်မာစာသားကို Offline ရှာဖွေမည်။");
    status.setTextColor(0xff66553b);status.setTextSize(14);status.setPadding(16,8,16,8);root.addView(status);
    ScrollView sc=new ScrollView(this);results=new LinearLayout(this);results.setOrientation(1);sc.addView(results);
    root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));setContentView(root);
    searchButton.setOnClickListener(v->search());
    term.setOnEditorActionListener((v,action,event)->{search();return true;});
    if(query!=null&&!query.trim().isEmpty())search();
  }
  private String normalized(String s){return Normalizer.normalize(s,Normalizer.Form.NFC);}
  private static String digest(String s){
    try{
      byte[] bytes=MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
      StringBuilder b=new StringBuilder();for(byte x:bytes)b.append(String.format(Locale.US,"%02x",x&255));return b.toString();
    }catch(Exception e){return "";}
  }
  private String volumeFilter(int chosen){
    if(chosen>0)return " AND p.volume="+chosen;
    if(filterName!=null&&filterName.contains("ဝိနည်း"))return " AND p.volume BETWEEN 1 AND 8";
    if(filterName!=null&&filterName.contains("သုတ္တန်"))return " AND p.volume BETWEEN 9 AND 33";
    if(filterName!=null&&filterName.contains("အဘိဓမ္မာ"))return " AND p.volume BETWEEN 34 AND 45";
    return "";
  }
  private boolean within(int volume,int selected){
    if(selected>0)return selected==volume;
    if(filterName!=null&&filterName.contains("ဝိနည်း"))return volume>=1&&volume<=8;
    if(filterName!=null&&filterName.contains("သုတ္တန်"))return volume>=9&&volume<=33;
    if(filterName!=null&&filterName.contains("အဘိဓမ္မာ"))return volume>=34&&volume<=45;
    return true;
  }
  private String preview(String value,int max){
    if(value==null)return "";
    String s=value.trim();return s.length()>max?s.substring(0,max)+"…":s;
  }
  private boolean contains(String value,String q,boolean exact){
    return value!=null&&(exact?value.equals(q):value.contains(q));
  }
  private void search(){
    if(searching)return;
    String q=normalized(term.getText().toString().trim());
    if(q.isEmpty()){term.setError("ရှာဖွေစာသား ထည့်ပါ");return;}
    final int chosen=volumes.getSelectedItemPosition();
    final boolean exact=getIntent().getBooleanExtra("exact_match",false);
    searching=true;searchButton.setEnabled(false);
    status.setText("Offline Database ရှာဖွေနေသည်…");results.removeAllViews();
    new Thread(()->{
      LinkedHashMap<Long,Match> found=new LinkedHashMap<>();
      String issue=null;int publisherMatches=0;boolean hasPali=false,hasPublisher=false;
      SQLiteDatabase pali=null,local=null;
      try{
        File file=OfflineCorpusInstaller.prepare(getApplicationContext());
        pali=SQLiteDatabase.openDatabase(file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
        hasPali=true;
        String f=volumeFilter(chosen);
        String paliSql="SELECT p.id,p.volume,COALESCE(p.segment_id,CAST(p.id AS TEXT)),p.body"+
          " FROM paragraphs p WHERE "+(exact?"p.body=?":"instr(p.body,?)>0")+f+" ORDER BY p.volume,p.id LIMIT 100";
        try(Cursor c=pali.rawQuery(paliSql,new String[]{q})){
          while(c.moveToNext()){
            long id=c.getLong(0);found.put(id,new Match(id,c.getInt(1),c.getString(2),c.getString(3),"ပါဠိမူရင်း"));
          }
        }
        File localFile=getDatabasePath(MyanmarContentStore.DB_NAME);
        if(localFile.isFile()){
          local=SQLiteDatabase.openDatabase(localFile.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
          hasPublisher=true;
          String sql="SELECT DISTINCT paragraph_id FROM paragraph_myanmar_content "+
            "WHERE reviewed=1 AND "+(exact?"text_my=?":"instr(text_my,?)>0")+" ORDER BY paragraph_id LIMIT 100";
          try(Cursor c=local.rawQuery(sql,new String[]{q})){
            while(c.moveToNext()&&found.size()<100){
              long pid=c.getLong(0);
              if(found.containsKey(pid))continue;
              try(Cursor p=pali.rawQuery("SELECT id,volume,COALESCE(segment_id,CAST(id AS TEXT)),body FROM paragraphs WHERE id=? LIMIT 1",
                  new String[]{Long.toString(pid)})){
                if(p.moveToFirst()&&within(p.getInt(1),chosen)){
                  found.put(pid,new Match(pid,p.getInt(1),p.getString(2),p.getString(3),"Local Publisher"));
                  publisherMatches++;
                }
              }
            }
          }
          // Materialize only locally published records whose stored Pali hash
          // still matches the source corpus after any APK/content update.
          for(Match match:found.values()){
            String hash=digest(match.body);
            try(Cursor c=local.rawQuery(
              "SELECT content_type,text_my,source_pali_sha256 FROM paragraph_myanmar_content "+
              "WHERE paragraph_id=? AND reviewed=1 AND length(trim(text_my))>0",new String[]{Long.toString(match.id)})){
              while(c.moveToNext()){
                if(!hash.equalsIgnoreCase(c.getString(2)))continue;
                if("translation".equals(c.getString(0)))match.translation=c.getString(1);
                if("explanation".equals(c.getString(0)))match.explanation=c.getString(1);
              }
            }
          }
          // A stale published row must not masquerade as a Myanmar search hit.
          ArrayList<Long> drop=new ArrayList<>();
          for(Map.Entry<Long,Match> e:found.entrySet()){
            Match m=e.getValue();
            if("Local Publisher".equals(m.kind)&&
               !contains(m.translation,q,exact)&&!contains(m.explanation,q,exact))drop.add(e.getKey());
          }
          for(Long id:drop)found.remove(id);
        }
      }catch(Exception e){
        issue="Offline ကျမ်းစာ Database မရှိသေးပါ၊ သို့မဟုတ် Integrity Check မအောင်မြင်ပါ။ "+
          (e.getMessage()==null?"":e.getMessage());
      }finally{if(local!=null)local.close();if(pali!=null)pali.close();}
      final ArrayList<Match> matches=new ArrayList<>(found.values());
      final String error=issue;final boolean sourceReady=hasPali,publisherReady=hasPublisher;
      runOnUiThread(()->{
        if(isFinishing()||isDestroyed())return;
        searching=false;searchButton.setEnabled(true);results.removeAllViews();
        if(error!=null){status.setText(error);notice(error);return;}
        status.setText("ပါဠိ Database: "+(sourceReady?"ဖတ်နိုင်":"မရှိ")+
          " • Local Published Myanmar: "+(publisherReady?"ချိတ်ဆက်ပြီး":"မရှိသေး")+
          " • ရလဒ် "+matches.size()+" ခု");
        int count=0;
        for(Match m:matches){
          String text="ကျမ်း "+m.volume+" · "+m.segment+"\nကိုက်ညီသည့်နေရာ: "+m.kind+
            "\nပါဠိ: "+preview(m.body,220);
          if(!m.translation.isEmpty())text+="\nLocal Published မြန်မာဘာသာပြန်: "+preview(m.translation,180);
          if(!m.explanation.isEmpty())text+="\nLocal Published မြန်မာရှင်းလင်းချက်: "+preview(m.explanation,180);
          TextView row=new TextView(this);row.setText(text);row.setTextSize(16);row.setTextColor(INK);
          row.setPadding(18,16,18,16);row.setBackgroundColor(count%2==0?Color.WHITE:0xfff2ecdd);
          LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(8,4,8,4);
          results.addView(row,lp);
          row.setOnClickListener(v->{
            Intent i=new Intent(this,ParagraphExplanationActivity.class);
            i.putExtra("volume",m.volume);i.putExtra("paragraph_id",Long.toString(m.id));startActivity(i);
          });
          count++;
        }
        if(count==0)notice("ကိုက်ညီသော ကျမ်းပိုဒ် မတွေ့ပါ။ အတည်ပြုထားသော Local Publisher စာသားများ မထည့်ရသေးပါက ပါဠိမူရင်းသာ ရှာဖွေနိုင်ပါမည်။");
        else notice("ပထမ ရလဒ် ၁၀၀ ခုအထိ ပြသထားပါသည်။");
      });
    },"tipitaka-offline-search").start();
  }
  private void notice(String message){
    TextView t=new TextView(this);t.setText(message);t.setTextSize(14);t.setTextColor(INK);
    t.setPadding(18,16,18,16);results.addView(t);
  }
}
