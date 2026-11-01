package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.widget.*;
import java.io.File;
import java.text.SimpleDateFormat;
import java.util.Arrays;
import java.util.Comparator;
import java.util.Date;
import java.util.Locale;

/** Local-only searchable library for user-imported, app-owned books. */
public final class OfflineBookLibraryActivity extends Activity {
  private LinearLayout list;
  private EditText search;
  private TextView summary;
  private File[] allFiles=new File[0];
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private TextView label(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(null,1);t.setPadding(dp(14),dp(10),dp(14),dp(10));return t;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(0xff144638);getWindow().setNavigationBarColor(0xff144638);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e7);
    TextView head=label("☸ Offline စာအုပ်တိုက်",21,Color.WHITE,true);head.setBackgroundColor(0xff144638);root.addView(head);
    Button add=new Button(this);add.setText("＋ PDF / EPUB / TXT စာအုပ်ထည့်ရန်");root.addView(add);
    search=new EditText(this);search.setSingleLine(true);search.setHint("သိမ်းထားသော စာအုပ်အမည် ရှာရန်");root.addView(search);
    summary=label("စာအုပ်စာရင်း ပြင်ဆင်နေသည်…",13,0xff66553b,false);root.addView(summary);
    ScrollView sc=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);sc.addView(list);
    root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
    Button close=new Button(this);close.setText("‹ Reader သို့ ပြန်ရန်");root.addView(close);close.setOnClickListener(v->finish());
    add.setOnClickListener(v->{Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("select_file",true);startActivity(i);});
    search.addTextChangedListener(new TextWatcher(){
      public void beforeTextChanged(CharSequence s,int start,int count,int after){}
      public void onTextChanged(CharSequence s,int start,int before,int count){draw(s.toString());}
      public void afterTextChanged(Editable e){}
    });
    setContentView(root);refresh();
  }
  @Override protected void onResume(){super.onResume();if(list!=null)refresh();}
  private void refresh(){
    File dir=new File(getFilesDir(),"reader_library");
    File[] files=dir.listFiles(f->f.isFile()&&(f.getName().toLowerCase(Locale.ROOT).endsWith(".pdf")||f.getName().toLowerCase(Locale.ROOT).endsWith(".epub")||f.getName().toLowerCase(Locale.ROOT).endsWith(".txt")));
    allFiles=files==null?new File[0]:files;
    Arrays.sort(allFiles,Comparator.comparingLong(File::lastModified).reversed());
    long total=0;for(File f:allFiles)total+=f.length();
    summary.setText("စာအုပ် "+allFiles.length+" အုပ်  •  "+String.format(Locale.US,"%.1f MB",total/1048576d)+"  •  နောက်ဆုံးဖတ်ထားသည့်အချိန်အလိုက်");
    draw(search==null?"":search.getText().toString());
  }
  private void draw(String query){
    list.removeAllViews();String q=query==null?"":query.trim().toLowerCase(Locale.ROOT);int shown=0;
    for(File file:allFiles){
      if(!file.getName().toLowerCase(Locale.ROOT).contains(q))continue;
      shown++;
      LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(8),dp(6),dp(8),dp(6));card.setBackgroundColor(Color.WHITE);
      String ext=file.getName().toLowerCase(Locale.ROOT);
      String type=ext.endsWith(".pdf")?"PDF":ext.endsWith(".epub")?"EPUB":"TXT";
      TextView name=label((type.equals("PDF")?"📕 ":type.equals("EPUB")?"📘 ":"📄 ")+file.getName(),16,0xff144638,true);card.addView(name);
      String when=new SimpleDateFormat("yyyy-MM-dd HH:mm",Locale.getDefault()).format(new Date(file.lastModified()));
      TextView meta=label(String.format(Locale.US,"%.2f MB • Offline • နောက်ဆုံးဖတ်ရှု %s",file.length()/1048576d,when),12,0xff77684f,false);card.addView(meta);
      LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.END);
      Button open=new Button(this);open.setText("ဖတ်ရန်");actions.addView(open);
      Button delete=new Button(this);delete.setText("ဖယ်ရှားရန်");actions.addView(delete);card.addView(actions);
      open.setOnClickListener(v->{Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("local_path",file.getAbsolutePath());startActivity(i);});
      delete.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Offline စာအုပ်ဖယ်ရှားရန်")
        .setMessage(file.getName()+" ကို ဖုန်းထဲမှ ဖယ်ရှားမလား?")
        .setNegativeButton("မဖယ်ပါ",null).setPositiveButton("ဖယ်ရှားမည်",(d,w)->removeBook(file)).show());
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(8),dp(5),dp(8),dp(5));list.addView(card,lp);
    }
    if(shown==0){
      TextView empty=label(q.isEmpty()?"Offline သိမ်းထားသော စာအုပ်မရှိသေးပါ။\nစာအုပ်ဖိုင်ထည့်ပြီး Internet မလိုဘဲ ဖတ်နိုင်ပါသည်။":"ရှာဖွေမှုနှင့် ကိုက်ညီသော စာအုပ်မရှိပါ။",16,0xff29483c,false);
      list.addView(empty);
    }
  }
  private void removeBook(File file){
    String path=file.getAbsolutePath();
    if(file.delete()){
      SharedPreferences prefs=getSharedPreferences("native_reader",MODE_PRIVATE);
      SharedPreferences.Editor edit=prefs.edit().remove("position_"+path).remove("bookmarks_"+path);
      if(path.equals(prefs.getString("lastPath",null)))edit.remove("lastPath").remove("lastUri");
      edit.apply();refresh();Toast.makeText(this,"Offline စာအုပ်ကို ဖယ်ရှားပြီး",Toast.LENGTH_SHORT).show();
    }else Toast.makeText(this,"ဖယ်ရှား၍မရပါ",Toast.LENGTH_SHORT).show();
  }
}
