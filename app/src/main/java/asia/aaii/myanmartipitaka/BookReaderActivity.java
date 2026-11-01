package asia.aaii.myanmartipitaka;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.pdf.PdfRenderer;
import android.net.Uri;
import android.text.Html;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.*;

public class BookReaderActivity extends Activity {
  private static final int PICK=101;
  private LinearLayout root,bar;
  private TextView body,label;
  private ImageView pdfImage;
  private ScrollView scroll;
  private PdfRenderer renderer;
  private ParcelFileDescriptor descriptor;
  private String bookId="",bookText="";
  private int page=0,font=21;
  private float zoom=1f;
  private boolean pdf=false;
  private android.content.SharedPreferences prefs;
  @Override public void onCreate(Bundle saved) {
    super.onCreate(saved);
    prefs=getSharedPreferences("native_reader",MODE_PRIVATE);
    font=prefs.getInt("font",21);
    layout();
    String savedUri=prefs.getString("lastUri",null);
    boolean selectFile=getIntent().getBooleanExtra("select_file",false);
    if(savedUri!=null) {
      try { open(Uri.parse(savedUri)); }
      catch(Exception e){status("စာအုပ်ဖိုင်ကို ပြန်ဖွင့်၍မရပါ။ Offline Library မှ ကျမ်းစာကို ရွေးနိုင်ပါသည်။");}
    } else if(selectFile) {
      status("PDF / EPUB / UTF-8 TXT ဖိုင်ကို ရွေးချယ်ပါ");
      choose();
    } else {
      // The old Five-Nikaya cards opened this generic file picker without a document.
      // Route a normal Reader launch to the bundled 45-volume offline Tipitaka instead.
      startActivity(new Intent(this,TipitakaLibraryActivity.class));
      finish();
    }
  }
  private TextView button(String text,Runnable action) {
    TextView v=new TextView(this);v.setText(text);v.setTextColor(Color.rgb(247,229,184));v.setTextSize(16);
    v.setPadding(14,14,14,14);v.setOnClickListener(w->action.run());return v;
  }
  private void layout() {
    root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(Color.rgb(247,243,230));
    bar=new LinearLayout(this);bar.setBackgroundColor(Color.rgb(20,66,56));
    bar.addView(button("‹",()->finish()));
    bar.addView(button("Open Book",this::choose));
    bar.addView(button("A−",()->resize(-2)));
    bar.addView(button("A+",()->resize(2)));
    bar.addView(button("🔖",this::bookmark));
    root.addView(bar);
    label=new TextView(this);label.setTextColor(Color.rgb(41,72,58));label.setTextSize(14);label.setPadding(18,12,12,12);root.addView(label);
    scroll=new ScrollView(this);
    LinearLayout pageBody=new LinearLayout(this);pageBody.setOrientation(LinearLayout.VERTICAL);
    body=new TextView(this);body.setTextColor(Color.rgb(37,47,39));body.setTextSize(font);body.setTextIsSelectable(true);body.setPadding(22,20,22,38);
    pdfImage=new ImageView(this);pdfImage.setAdjustViewBounds(true);pdfImage.setVisibility(View.GONE);
    pageBody.addView(body);pageBody.addView(pdfImage);
    scroll.addView(pageBody);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    LinearLayout footer=new LinearLayout(this);footer.setBackgroundColor(Color.rgb(20,66,56));
    footer.addView(button("◀ Prev",()->turn(-1)));
    footer.addView(button("Next ▶",()->turn(1)));
    footer.addView(button("Find",this::search));
    footer.addView(button("Go to",this::goTo));
    root.addView(footer);
    setContentView(root);
  }
  private void status(String s){label.setText(s);}
  private void choose(){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
    i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);
    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
    startActivityForResult(i,PICK);
  }
  @Override protected void onActivityResult(int request,int result,Intent data){
    super.onActivityResult(request,result,data);
    if(request==PICK&&result==RESULT_OK&&data!=null){
      Uri uri=data.getData();if(uri==null)return;
      try{getContentResolver().takePersistableUriPermission(uri,Intent.FLAG_GRANT_READ_URI_PERMISSION);}catch(Exception ignored){}
      try{open(uri);}catch(Exception e){new AlertDialog.Builder(this).setTitle("Cannot open book").setMessage(e.getMessage()).setPositiveButton("OK",null).show();}
    }
  }
  private void closePdf(){try{if(renderer!=null)renderer.close();}catch(Exception ignored){}renderer=null;try{if(descriptor!=null)descriptor.close();}catch(Exception ignored){}descriptor=null;}
  private void open(Uri uri)throws Exception{
    closePdf();bookId=uri.toString();pdf=false;bookText="";page=0;
    String name=getFileName(uri).toLowerCase(Locale.ROOT);
    if(name.endsWith(".pdf")){
      descriptor=getContentResolver().openFileDescriptor(uri,"r");
      if(descriptor==null)throw new IOException("PDF file not readable");
      renderer=new PdfRenderer(descriptor);pdf=true;
    }else if(name.endsWith(".txt")){
      try(InputStream in=getContentResolver().openInputStream(uri)){bookText=readLimited(in,12*1024*1024);}
    }else if(name.endsWith(".epub")){
      bookText=epubText(uri);
    }else throw new IOException("Supported formats: PDF, EPUB, UTF-8 TXT");
    page=prefs.getInt("position_"+bookId,0);
    prefs.edit().putString("lastUri",bookId).apply();showPage();
  }
  private String getFileName(Uri uri){
    try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){
      if(c!=null&&c.moveToFirst()){
        int idx=c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
        if(idx>=0)return c.getString(idx);
      }
    }catch(Exception ignored){}
    return uri.getLastPathSegment()==null?"":uri.getLastPathSegment();
  }
  private String readLimited(InputStream in,int limit)throws IOException{
    if(in==null)throw new IOException("No document stream");
    ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[8192];int n;
    while((n=in.read(buf))!=-1){if(out.size()+n>limit)throw new IOException("Book exceeds 12 MB text limit");out.write(buf,0,n);}
    return out.toString("UTF-8");
  }
  private String epubText(Uri uri)throws IOException{
    StringBuilder result=new StringBuilder();
    try(InputStream raw=getContentResolver().openInputStream(uri);ZipInputStream zip=new ZipInputStream(raw)){
      ZipEntry entry;int files=0;
      while((entry=zip.getNextEntry())!=null){
        String name=entry.getName().toLowerCase(Locale.ROOT);
        if(!entry.isDirectory()&&(name.endsWith(".xhtml")||name.endsWith(".html")||name.endsWith(".htm"))){
          if(++files>500)throw new IOException("EPUB too many chapters");
          String html=readLimited(zip,2*1024*1024);
          String clean=Html.fromHtml(html,Html.FROM_HTML_MODE_LEGACY).toString().trim();
          if(!clean.isEmpty())result.append(clean).append("\n\n");
          if(result.length()>8_000_000)throw new IOException("EPUB text too large");
        }
        zip.closeEntry();
      }
    }
    if(result.length()==0)throw new IOException("No readable EPUB chapters");
    return result.toString();
  }
  private int pages(){return pdf?renderer.getPageCount():Math.max(1,(bookText.length()+2999)/3000);}
  private void showPage(){
    if(bookId.isEmpty())return;
    page=Math.max(0,Math.min(page,pages()-1));
    body.setVisibility(pdf?View.GONE:View.VISIBLE);pdfImage.setVisibility(pdf?View.VISIBLE:View.GONE);
    if(pdf){
      try(PdfRenderer.Page p=renderer.openPage(page)){
        int w=Math.max(1,(int)(getResources().getDisplayMetrics().widthPixels*zoom));
        int h=Math.max(1,(int)(w*(double)p.getHeight()/p.getWidth()));
        if((long)w*h>9000000L){double s=Math.sqrt(9000000d/(w*(double)h));w=Math.max(1,(int)(w*s));h=Math.max(1,(int)(h*s));}
        Bitmap b=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        b.eraseColor(Color.WHITE);p.render(b,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
        pdfImage.setImageBitmap(b);
      }catch(Exception e){status("PDF render error: "+e.getMessage());return;}
    }else{
      int a=page*3000,b=Math.min(bookText.length(),a+3000);
      body.setText(bookText.substring(Math.min(a,b),b));
    }
    status(getFileName(Uri.parse(bookId))+"   •   "+(page+1)+" / "+pages());
    scroll.scrollTo(0,0);
    prefs.edit().putInt("position_"+bookId,page).apply();
  }
  private void turn(int d){if(bookId.isEmpty()){choose();return;}page+=d;showPage();}
  private void resize(int d){font=Math.max(14,Math.min(38,font+d));prefs.edit().putInt("font",font).apply();body.setTextSize(font);if(pdf){zoom=Math.max(.65f,Math.min(2.5f,zoom+(d>0?.15f:-.15f)));showPage();}}
  private void bookmark(){if(bookId.isEmpty())return;prefs.edit().putInt("bookmark_"+bookId,page).apply();Toast.makeText(this,"Bookmark saved",Toast.LENGTH_SHORT).show();}
  private void goTo(){
    if(bookId.isEmpty()){choose();return;}
    EditText input=new EditText(this);input.setInputType(2);input.setHint("Page 1–"+pages());
    new AlertDialog.Builder(this).setTitle("Go to page").setView(input).setPositiveButton("Go",(d,w)->{
      try{page=Integer.parseInt(input.getText().toString())-1;showPage();}catch(Exception ignored){}
    }).setNeutralButton("Bookmark",(d,w)->{page=prefs.getInt("bookmark_"+bookId,0);showPage();})
      .setNegativeButton("Cancel",null).show();
  }
  private void search(){
    if(bookId.isEmpty()){choose();return;}
    if(pdf){new AlertDialog.Builder(this).setMessage("PDF text search is not supported by Android PdfRenderer. For full-text search, import a TXT or EPUB book.").setPositiveButton("OK",null).show();return;}
    EditText input=new EditText(this);input.setHint("မြန်မာ / Pāli search");
    new AlertDialog.Builder(this).setTitle("Find in book").setView(input).setPositiveButton("Find",(d,w)->{
      String q=input.getText().toString().trim();if(q.isEmpty())return;
      int pos=bookText.toLowerCase(Locale.ROOT).indexOf(q.toLowerCase(Locale.ROOT),(page+1)*3000);
      if(pos<0)pos=bookText.toLowerCase(Locale.ROOT).indexOf(q.toLowerCase(Locale.ROOT));
      if(pos>=0){page=pos/3000;showPage();}else Toast.makeText(this,"No match",Toast.LENGTH_LONG).show();
    }).setNegativeButton("Cancel",null).show();
  }
  @Override protected void onDestroy(){closePdf();super.onDestroy();}
}
