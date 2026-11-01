package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.ContentValues;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.net.Uri;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.text.SimpleDateFormat;
import java.util.*;

/** Standalone publisher and verified CSV importer. No server/admin dashboard required. */
public final class MyanmarPublisherActivity extends Activity {
  private static final int PICK_IMPORT=5101,PICK_BACKUP=5102,PICK_RESTORE=5103;
  private MyanmarContentStore store;
  private String publisher="";
  private TextView status;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private void toast(String s){Toast.makeText(this,s,Toast.LENGTH_LONG).show();}
  private String now(){return new SimpleDateFormat("yyyy-MM-dd HH:mm:ss",Locale.US).format(new Date());}
  private String sha(String s)throws Exception{
    byte[] b=MessageDigest.getInstance("SHA-256").digest(s.getBytes(StandardCharsets.UTF_8));
    StringBuilder x=new StringBuilder();for(byte v:b)x.append(String.format(Locale.US,"%02x",v&255));return x.toString();
  }
  @Override public void onCreate(Bundle b){
    super.onCreate(b);getWindow().setStatusBarColor(0xff144638);getWindow().setNavigationBarColor(0xff144638);
    store=new MyanmarContentStore(this);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setPadding(dp(16),dp(12),dp(16),dp(24));root.setBackgroundColor(0xfffaf6eb);
    TextView title=new TextView(this);title.setText("☸ Standalone Publisher");title.setTextSize(23);title.setTextColor(-1);title.setPadding(dp(16),dp(18),dp(16),dp(18));title.setBackgroundColor(0xff144638);root.addView(title);
    EditText name=new EditText(this);name.setSingleLine(true);name.setHint("Publisher အမည်");root.addView(name);
    status=new TextView(this);status.setText("Local SQLite Publisher • Internet မလိုပါ");status.setTextSize(14);status.setPadding(0,dp(8),0,dp(8));root.addView(status);
    add(root,"📥 Verified Candidate CSV Import",()->{publisher=name.getText().toString().trim();if(publisher.isEmpty()){name.setError("Publisher အမည်ဖြည့်ပါ");return;}pick(PICK_IMPORT,"text/csv");});
    add(root,"📊 Published Content Coverage",()->showCoverage());
    add(root,"📤 Published Content Backup",()->pick(PICK_BACKUP,"application/octet-stream"));
    add(root,"📥 Restore Published Content Backup",()->pick(PICK_RESTORE,"application/octet-stream"));
    add(root,"✍ Editorial Draft & Reviewer Workbench",()->startActivity(new Intent(this,MyanmarEditorialActivity.class)));
    add(root,"📚 Offline Reader ဖွင့်ရန်",()->startActivity(new Intent(this,TipitakaLibraryActivity.class)));
    root.addView(new TextView(this){{setText("မှတ်ချက် — Import မတိုင်မီ Pāli SHA-256၊ Myanmar Unicode၊ source/rights evidence၊ Reviewer နှစ်ဦးနှင့် duplicate rows တို့ကို စစ်ဆေးသည်။ Imported content သည် local publisher database တွင်သာ သိမ်းမည်။");setTextSize(13);setPadding(0,dp(12),0,0);}});
    setContentView(root);
  }
  private void add(LinearLayout root,String label,Runnable run){Button b=new Button(this);b.setText(label);root.addView(b);b.setOnClickListener(v->run.run());}
  private void pick(int request,String type){Intent i=new Intent(request==PICK_IMPORT||request==PICK_RESTORE?Intent.ACTION_OPEN_DOCUMENT:Intent.ACTION_CREATE_DOCUMENT);i.addCategory(Intent.CATEGORY_OPENABLE);i.setType(type);if(request==PICK_BACKUP)i.putExtra(Intent.EXTRA_TITLE,"myanmar_tipitaka_published_backup.json");startActivityForResult(i,request);}
  @Override protected void onActivityResult(int req,int result,Intent data){
    super.onActivityResult(req,result,data);if(result!=RESULT_OK||data==null||data.getData()==null)return;
    Uri uri=data.getData();
    try{
      if(req==PICK_IMPORT){int[] counts=importCsv(uri);status.setText("Import အောင်မြင် • ဘာသာပြန် "+counts[0]+" • ရှင်းလင်းချက် "+counts[1]);toast("Verified content ကို Local Publisher Database ထဲ ထည့်သွင်းပြီးပါပြီ။");}
      else if(req==PICK_BACKUP){writeBackup(uri);toast("Publisher Database Backup ပြီးပါပြီ။");}
      else if(req==PICK_RESTORE){restoreBackup(uri);toast("Publisher Database Restore ပြီးပါပြီ။");}
    }catch(Exception e){toast("လုပ်ဆောင်မှု မအောင်မြင်ပါ: "+e.getMessage());}
  }
  private int[] importCsv(Uri uri)throws Exception{
    File temp=new File(getCacheDir(),"publisher_import.csv");
    try(InputStream in=getContentResolver().openInputStream(uri);OutputStream out=new FileOutputStream(temp)){if(in==null)throw new IOException("CSV ဖိုင်ဖတ်မရပါ");byte[] b=new byte[32768];int n;while((n=in.read(b))!=-1)out.write(b,0,n);}
    SQLiteDatabase pali=SQLiteDatabase.openDatabase(OfflineCorpusInstaller.prepare(this).getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
    SQLiteDatabase local=store.getWritableDatabase();int[] count={0,0};
    local.beginTransaction();
    try(BufferedReader reader=new BufferedReader(new InputStreamReader(new FileInputStream(temp),StandardCharsets.UTF_8))){
      String header=reader.readLine();String expected="segment_id,content_type,text_my,source_ref,rights_evidence,reviewer_1,reviewer_2,review_reference,reviewed_at,source_pali_sha256";
      if(header==null||!header.replace("\ufeff","").equals(expected))throw new IOException("CSV Header မကိုက်ညီပါ");
      String line;int lineNo=1;Set<String> seen=new HashSet<>();
      while((line=reader.readLine())!=null){lineNo++;if(line.trim().isEmpty())continue;List<String> v=parseCsv(line);
        if(v.size()!=10)throw new IOException("Row "+lineNo+": column 10 ခု လိုအပ်သည်");
        String seg=v.get(0),kind=v.get(1),text=v.get(2),src=v.get(3),rights=v.get(4),r1=v.get(5),r2=v.get(6),ref=v.get(7),date=v.get(8),hash=v.get(9);
        if(!kind.equals("translation")&&!kind.equals("explanation"))throw new IOException("Row "+lineNo+": content type မမှန်ပါ");
        if(text.trim().isEmpty()||!text.matches("(?s).*[\u1000-\u109F].*"))throw new IOException("Row "+lineNo+": မြန်မာ Unicode စာသားလိုအပ်သည်");
        if(src.isEmpty()||rights.isEmpty()||r1.isEmpty()||r2.isEmpty()||r1.equalsIgnoreCase(r2)||ref.isEmpty())throw new IOException("Row "+lineNo+": source/rights/reviewer evidence မပြည့်စုံပါ");
        if(!hash.matches("[0-9a-fA-F]{64}"))throw new IOException("Row "+lineNo+": SHA-256 format မမှန်ပါ");
        if(!seen.add(seg+"|"+kind))throw new IOException("Row "+lineNo+": duplicate segment/type");
        String paliText=null;long pid=-1;
        try(Cursor p=pali.rawQuery("SELECT id,body FROM paragraphs WHERE CAST(id AS TEXT)=? OR segment_id=? LIMIT 1",new String[]{seg,seg})){if(p.moveToFirst()){pid=p.getLong(0);paliText=p.getString(1);}}
        if(paliText==null||!sha(paliText).equalsIgnoreCase(hash))throw new IOException("Row "+lineNo+": Pāli SHA-256 မကိုက်ညီပါ");
        try{java.time.LocalDate.parse(date);}catch(Exception e){throw new IOException("Row "+lineNo+": review date မမှန်ပါ");}
        ContentValues cv=new ContentValues();cv.put("paragraph_id",pid);cv.put("segment_id",seg);cv.put("content_type",kind);cv.put("text_my",text);cv.put("source_ref",src);cv.put("rights_evidence",rights);cv.put("reviewer_1",r1);cv.put("reviewer_2",r2);cv.put("review_reference",ref);cv.put("reviewed_at",date);cv.put("source_pali_sha256",hash.toLowerCase(Locale.US));cv.put("reviewed",1);cv.put("publisher_name",publisher);cv.put("published_at",now());
        local.insertWithOnConflict(MyanmarContentStore.TABLE,null,cv,SQLiteDatabase.CONFLICT_REPLACE);
        count[kind.equals("translation")?0:1]++;
      }
      ContentValues log=new ContentValues();log.put("source_type","verified_csv");log.put("source_name","CSV document");log.put("publisher_name",publisher);log.put("imported_at",now());log.put("translation_rows",count[0]);log.put("explanation_rows",count[1]);local.insert("publisher_import_log",null,log);
      local.setTransactionSuccessful();
    }finally{local.endTransaction();pali.close();temp.delete();}
    return count;
  }
  private List<String> parseCsv(String line)throws IOException{
    ArrayList<String> out=new ArrayList<>();StringBuilder cell=new StringBuilder();boolean quoted=false;
    for(int i=0;i<line.length();i++){char c=line.charAt(i);if(quoted){if(c=='"'){if(i+1<line.length()&&line.charAt(i+1)=='"'){cell.append('"');i++;}else quoted=false;}else cell.append(c);}else if(c=='"'){if(cell.length()!=0)throw new IOException("CSV quote error");quoted=true;}else if(c==','){out.add(cell.toString());cell.setLength(0);}else cell.append(c);}
    if(quoted)throw new IOException("CSV quote မပိတ်ထားပါ");out.add(cell.toString());return out;
  }
  private void showCoverage(){
    SQLiteDatabase db=store.getReadableDatabase();long tr=0,ex=0;
    try(Cursor c=db.rawQuery("SELECT content_type,COUNT(*) FROM paragraph_myanmar_content GROUP BY content_type",null)){while(c.moveToNext()){if(c.getString(0).equals("translation"))tr=c.getLong(1);else ex=c.getLong(1);}}
    new AlertDialog.Builder(this).setTitle("Local Published Coverage").setMessage("မြန်မာဘာသာပြန်: "+tr+"\nမြန်မာရှင်းလင်းချက်: "+ex+"\n\nဤစာရင်းသည် ဤစက်၏ Publisher Database ကိုသာ ဖော်ပြသည်။").setPositiveButton("ပိတ်မည်",null).show();
  }
  private void writeBackup(Uri uri)throws Exception{
    SQLiteDatabase db=store.getReadableDatabase();org.json.JSONArray rows=new org.json.JSONArray();
    try(Cursor c=db.rawQuery("SELECT paragraph_id,segment_id,content_type,text_my,source_ref,rights_evidence,reviewer_1,reviewer_2,review_reference,reviewed_at,source_pali_sha256,reviewed,publisher_name,published_at FROM paragraph_myanmar_content",null)){
      while(c.moveToNext()){org.json.JSONObject o=new org.json.JSONObject();for(int i=0;i<c.getColumnCount();i++)o.put(c.getColumnName(i),c.getString(i));rows.put(o);}
    }
    org.json.JSONObject root=new org.json.JSONObject();root.put("format","myanmar-tipitaka-publisher-backup-v1");root.put("created_at",now());root.put("content",rows);
    try(OutputStream out=getContentResolver().openOutputStream(uri,"w")){out.write(root.toString(2).getBytes(StandardCharsets.UTF_8));}
  }
  private void restoreBackup(Uri uri)throws Exception{
    StringBuilder s=new StringBuilder();try(BufferedReader r=new BufferedReader(new InputStreamReader(getContentResolver().openInputStream(uri),StandardCharsets.UTF_8))){String line;while((line=r.readLine())!=null)s.append(line);}
    org.json.JSONObject root=new org.json.JSONObject(s.toString());if(!"myanmar-tipitaka-publisher-backup-v1".equals(root.getString("format")))throw new IOException("Backup format မကိုက်ညီပါ");
    SQLiteDatabase pali=SQLiteDatabase.openDatabase(OfflineCorpusInstaller.prepare(this).getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY),db=store.getWritableDatabase();db.beginTransaction();
    try{org.json.JSONArray rows=root.getJSONArray("content");for(int i=0;i<rows.length();i++){org.json.JSONObject o=rows.getJSONObject(i);String seg=o.getString("segment_id"),hash=o.getString("source_pali_sha256"),text=o.getString("text_my"),kind=o.getString("content_type");String original=null;long pid=-1;
      try(Cursor p=pali.rawQuery("SELECT id,body FROM paragraphs WHERE CAST(id AS TEXT)=? OR segment_id=? LIMIT 1",new String[]{seg,seg})){if(p.moveToFirst()){pid=p.getLong(0);original=p.getString(1);}}
      if(original==null||!sha(original).equalsIgnoreCase(hash)||!text.matches("(?s).*[\u1000-\u109F].*"))throw new IOException("Backup row "+i+" verification failed");
      ContentValues v=new ContentValues();v.put("paragraph_id",pid);v.put("segment_id",seg);v.put("content_type",kind);v.put("text_my",text);v.put("source_ref",o.getString("source_ref"));v.put("rights_evidence",o.getString("rights_evidence"));v.put("reviewer_1",o.getString("reviewer_1"));v.put("reviewer_2",o.getString("reviewer_2"));v.put("review_reference",o.getString("review_reference"));v.put("reviewed_at",o.getString("reviewed_at"));v.put("source_pali_sha256",hash);v.put("reviewed",1);v.put("publisher_name",o.getString("publisher_name"));v.put("published_at",o.getString("published_at"));db.insertWithOnConflict(MyanmarContentStore.TABLE,null,v,SQLiteDatabase.CONFLICT_REPLACE);
    }db.setTransactionSuccessful();}finally{db.endTransaction();pali.close();}
  }
  @Override protected void onDestroy(){if(store!=null)store.close();super.onDestroy();}
}
