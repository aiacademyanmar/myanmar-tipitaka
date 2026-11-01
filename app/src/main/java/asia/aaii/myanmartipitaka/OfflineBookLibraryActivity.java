package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.io.File;
import java.util.Arrays;
import java.util.Comparator;

/** Local-only library for user-imported, app-owned books. */
public final class OfflineBookLibraryActivity extends Activity {
  private LinearLayout list;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private TextView label(String s,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(s);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(null,1);t.setPadding(dp(14),dp(11),dp(14),dp(11));return t;
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(0xff144638);getWindow().setNavigationBarColor(0xff144638);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(0xfffaf6e7);
    TextView head=label("☸ Offline စာအုပ်တိုက်",21,Color.WHITE,true);head.setBackgroundColor(0xff144638);root.addView(head);
    Button add=new Button(this);add.setText("＋ PDF / EPUB / TXT စာအုပ်ထည့်ရန်");root.addView(add);
    ScrollView sc=new ScrollView(this);list=new LinearLayout(this);list.setOrientation(1);sc.addView(list);
    root.addView(sc,new LinearLayout.LayoutParams(-1,0,1));
    Button close=new Button(this);close.setText("‹ Reader သို့ ပြန်ရန်");root.addView(close);close.setOnClickListener(v->finish());
    add.setOnClickListener(v->{Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("select_file",true);startActivity(i);});
    setContentView(root);refresh();
  }
  @Override protected void onResume(){super.onResume();if(list!=null)refresh();}
  private void refresh(){
    list.removeAllViews();File dir=new File(getFilesDir(),"reader_library");
    File[] files=dir.listFiles(f->f.isFile()&&(f.getName().toLowerCase().endsWith(".pdf")||f.getName().toLowerCase().endsWith(".epub")||f.getName().toLowerCase().endsWith(".txt")));
    if(files==null||files.length==0){
      TextView empty=label("Offline သိမ်းထားသော စာအုပ်မရှိသေးပါ။\nစာအုပ်ဖိုင်ကို ထည့်ပြီးနောက် Internet မလိုဘဲ ဖတ်နိုင်ပါသည်။",16,0xff29483c,false);
      list.addView(empty);return;
    }
    Arrays.sort(files,Comparator.comparingLong(File::lastModified).reversed());
    for(File file:files){
      LinearLayout card=new LinearLayout(this);card.setOrientation(1);card.setPadding(dp(8),dp(6),dp(8),dp(6));card.setBackgroundColor(Color.WHITE);
      TextView name=label(file.getName(),16,0xff144638,true);card.addView(name);
      TextView meta=label(String.format(java.util.Locale.US,"%.2f MB • Offline",file.length()/1048576d),12,0xff77684f,false);card.addView(meta);
      LinearLayout actions=new LinearLayout(this);actions.setGravity(Gravity.END);
      Button open=new Button(this);open.setText("ဖတ်ရန်");actions.addView(open);
      Button delete=new Button(this);delete.setText("ဖယ်ရှားရန်");actions.addView(delete);card.addView(actions);
      open.setOnClickListener(v->{Intent i=new Intent(this,BookReaderActivity.class);i.putExtra("local_path",file.getAbsolutePath());startActivity(i);});
      delete.setOnClickListener(v->new AlertDialog.Builder(this).setTitle("Offline စာအုပ်ဖယ်ရှားရန်")
        .setMessage(file.getName()+" ကို ဖုန်းထဲမှ ဖယ်ရှားမလား?")
        .setNegativeButton("မဖယ်ပါ",null).setPositiveButton("ဖယ်ရှားမည်",(d,w)->{if(file.delete())refresh();else Toast.makeText(this,"ဖယ်ရှား၍မရပါ",Toast.LENGTH_SHORT).show();}).show());
      LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(dp(8),dp(5),dp(8),dp(5));list.addView(card,lp);
    }
  }
}
