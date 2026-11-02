package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.widget.*;
import java.util.ArrayList;
import java.util.Locale;

/**
 * Complete inventory of the bundled Bilara published Mahasangiti VINAYA source.
 * All source files are read locally from the SQLite APK asset. It is NOT an
 * independently verified crosswalk to the 8 printed MCU Vinaya volumes.
 */
public final class VinayaOfflineActivity extends Activity {
  private static final int GREEN=0xff174e3c, GOLD=0xffe7bd67, CREAM=0xfffaf7ec, INK=0xff234a3a;
  private static final String[] NAMES={
    "ဘိက္ခုပါဋိမောက်","ဘိက္ခုနီပါဋိမောက်","ဘိက္ခုဝိဘင်း",
    "ဘိက္ခုနီဝိဘင်း","ခန္ဓက","ပရိဝါ"
  };
  private static final String[] LATIN={
    "Bhikkhu Pātimokkha","Bhikkhunī Pātimokkha",
    "Bhikkhu Vibhaṅga","Bhikkhunī Vibhaṅga","Khandhaka","Parivāra"
  };
  private static final String[] EMOJI={"📜","📜","📖","📖","☸","📚"};
  private static final class Book {
    final String file;final int segments,group;
    Book(String f,int s,int g){file=f;segments=s;group=g;}
  }
  private final ArrayList<Book> books=new ArrayList<>();
  private final int[] counts=new int[6],segments=new int[6];
  private ScrollView scroll;
  private LinearLayout content;
  private int selected=-1;
  private boolean stopped=false;
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private GradientDrawable bg(int color,int radius){
    GradientDrawable d=new GradientDrawable();d.setColor(color);d.setCornerRadius(dp(radius));return d;
  }
  private TextView label(String s,int size,int color,boolean strong){
    TextView t=new TextView(this);t.setText(s);t.setTextColor(color);t.setTextSize(size);
    t.setTypeface(null,strong?Typeface.BOLD:Typeface.NORMAL);
    t.setPadding(dp(13),dp(10),dp(13),dp(10));return t;
  }
  private void add(String value,int size,int color,boolean bold){content.addView(label(value,size,color,bold));}
  private void card(String icon,String name,String description,Runnable action){
    LinearLayout line=new LinearLayout(this);line.setGravity(Gravity.CENTER_VERTICAL);
    line.setBackground(bg(Color.WHITE,15));line.setPadding(dp(7),dp(4),dp(7),dp(4));
    TextView ic=label(icon,22,GREEN,true);line.addView(ic);
    LinearLayout texts=new LinearLayout(this);texts.setOrientation(1);
    texts.addView(label(name,16,GREEN,true));
    TextView sub=label(description,11,0xff78847b,false);sub.setPadding(dp(13),0,dp(13),dp(8));
    texts.addView(sub);line.addView(texts,new LinearLayout.LayoutParams(0,-2,1));
    line.addView(label("›",20,GOLD,true));
    LinearLayout.LayoutParams lp=new LinearLayout.LayoutParams(-1,-2);lp.setMargins(0,dp(4),0,dp(5));
    content.addView(line,lp);line.setOnClickListener(v->action.run());
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    LinearLayout root=new LinearLayout(this);root.setOrientation(1);root.setBackgroundColor(CREAM);
    TextView title=label("☸  ဝိနည်းပိဋကတ် • Offline",20,Color.WHITE,true);
    title.setBackgroundColor(GREEN);root.addView(title);
    scroll=new ScrollView(this);
    content=new LinearLayout(this);content.setOrientation(1);content.setPadding(dp(13),dp(12),dp(13),dp(18));
    scroll.addView(content);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    TipitakaFooter.attach(this,root,-1);
    setContentView(root);
    add("Offline Pāli Database ဖွင့်နေပါသည်…",15,GREEN,true);
    new Thread(this::load,"vinaya-catalog").start();
  }
  private int group(String path){
    if(path.startsWith("vinaya/pli-tv-bu-pm_"))return 0;
    if(path.startsWith("vinaya/pli-tv-bi-pm_"))return 1;
    if(path.startsWith("vinaya/pli-tv-bu-vb/"))return 2;
    if(path.startsWith("vinaya/pli-tv-bi-vb/"))return 3;
    if(path.startsWith("vinaya/pli-tv-kd/"))return 4;
    if(path.startsWith("vinaya/pli-tv-pvr/"))return 5;
    return -1;
  }
  private void load(){
    ArrayList<Book> items=new ArrayList<>();
    int[] fileCount=new int[6],paragraphCount=new int[6];
    String error=null;
    try{
      PaliSourceInstaller.Result installed=PaliSourceInstaller.prepare(this);
      try(SQLiteDatabase db=SQLiteDatabase.openDatabase(installed.file.getAbsolutePath(),null,SQLiteDatabase.OPEN_READONLY);
          Cursor c=db.rawQuery("SELECT source_file,count(*) FROM source_segments WHERE source_file LIKE 'vinaya/%' GROUP BY source_file ORDER BY source_file",null)){
        while(c.moveToNext()){
          String file=c.getString(0);
          int n=c.getInt(1),g=group(file);
          if(g<0)throw new IllegalStateException("Uncategorized Vinaya source: "+file);
          fileCount[g]++;paragraphCount[g]+=n;items.add(new Book(file,n,g));
        }
      }
      for(int i=0;i<6;i++)if(fileCount[i]==0)throw new IllegalStateException("Missing Vinaya section: "+LATIN[i]);
    }catch(Exception e){error=e.getMessage();}
    String failure=error;
    runOnUiThread(()->{
      if(stopped)return;
      if(failure!=null){content.removeAllViews();add("Offline Vinaya ဖွင့်၍မရပါ — "+failure,14,Color.RED,false);return;}
      books.clear();books.addAll(items);
      System.arraycopy(fileCount,0,counts,0,6);
      System.arraycopy(paragraphCount,0,segments,0,6);
      render();
    });
  }
  private void openSource(String sourceFile){
    Intent i=new Intent(this,PaliSourceLibraryActivity.class);
    i.putExtra("source_file",sourceFile);
    startActivity(i);
  }
  private void openSourceRoot(){
    Intent i=new Intent(this,PaliSourceLibraryActivity.class);
    i.putExtra("source_prefix","vinaya/");
    startActivity(i);
  }
  private void render(){
    content.removeAllViews();
    int total=0,files=0;for(int i=0;i<6;i++){total+=segments[i];files+=counts[i];}
    add(selected<0?"ဝိနည်းကျမ်းစာဖတ်ခန်း":NAMES[selected],23,GREEN,true);
    add(selected<0?"Vinaya Piṭaka · Original Pāli · Without Internet":LATIN[selected],13,0xff9e7832,false);
    add(String.format(Locale.US,"%d Pāli source files · %,d စာပိုဒ်",files,total),14,GREEN,true);
    add("SuttaCentral/Bilara အရင်းအမြစ်ကို ဖုန်းထဲသို့ တိုက်ရိုက်ထည့်ထားပါသည်။ MCU ပုံနှိပ်ဝိနည်း ၈ ကျမ်း၏ အုပ်ခွဲနှင့် အတိအကျ တူညီကြောင်း မစစ်ဆေးရသေးပါ။",12,0xff84562a,false);
    add("ဝိနည်းမြန်မာဘာသာပြန်အပြည့်အစုံနှင့် အတည်ပြုရှင်းလင်းချက်များ မပါဝင်သေးပါ။",12,0xff84562a,false);
    card("🔎","ဝိနည်းစာပိုဒ် ရှာရန်","Offline Pāli Search",()->startActivity(new Intent(this,PaliOfflineSearchActivity.class)));
    if(selected<0){
      for(int k=0;k<6;k++){
        final int index=k;
        card(EMOJI[k],NAMES[k],LATIN[k]+" · "+counts[k]+" files · "+segments[k]+" paragraphs",()->{selected=index;render();});
      }
      card("📚","Vinaya Source Folder","အားလုံးကို Source Hierarchy ဖြင့် ဖတ်ရန်",this::openSourceRoot);
    }else{
      card("‹","ဝိနည်းအုပ်စုများသို့ ပြန်ရန်","Back to Vinaya sections",()->{selected=-1;render();});
      int n=0;
      for(Book item:books)if(item.group==selected){
        n++;
        String fileName=item.file.substring(item.file.lastIndexOf('/')+1).replace("_root-pli-ms.json","");
        card("📖",fileName,item.segments+" စာပိုဒ် · Offline Pāli",()->openSource(item.file));
      }
      if(n!=counts[selected])add("စာအုပ်စာရင်း မပြည့်စုံပါ!",14,Color.RED,true);
    }
    scroll.scrollTo(0,0);
  }
  @Override public void onBackPressed(){
    if(selected>=0){selected=-1;render();}else super.onBackPressed();
  }
  @Override protected void onDestroy(){stopped=true;super.onDestroy();}
}
