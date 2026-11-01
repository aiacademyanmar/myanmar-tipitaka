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
import java.util.*;
import java.util.zip.*;

/** Standalone reader with a private offline copy of every imported PDF/EPUB/TXT book. */
public final class BookReaderActivity extends Activity {
  private static final int PICK=101;
  private static final long MAX_IMPORT_BYTES=250L*1024L*1024L;
  private LinearLayout root,bar;
  private TextView body,label;
  private ImageView pdfImage;
  private ScrollView scroll;
  private PdfRenderer renderer;
  private ParcelFileDescriptor descriptor;
  private Bitmap currentBitmap;
  private String bookId="",bookText="";
  private int page=0,font=21;
  private float zoom=1f;
  private boolean pdf=false;
  private SharedPreferences prefs;

  @Override public void onCreate(Bundle saved) {
    super.onCreate(saved);
    prefs=getSharedPreferences("native_reader",MODE_PRIVATE);
    font=prefs.getInt("font",21);
    layout();
    String requested=getIntent().getStringExtra("local_path");
    String savedPath=prefs.getString("lastPath",null);
    String savedUri=prefs.getString("lastUri",null);
    boolean selectFile=getIntent().getBooleanExtra("select_file",false);
    try {
      if(requested!=null&&!requested.trim().isEmpty())openFile(new File(requested));
      else if(selectFile) {
        // Explicit import requests must win over the previous reading session.
        status("PDF / EPUB / UTF-8 TXT ဖိုင်ကို ရွေးချယ်ပါ");
        choose();
      } else if(savedPath!=null&&new File(savedPath).isFile())openFile(new File(savedPath));
      else if(savedUri!=null) {
        Uri uri=Uri.parse(savedUri);
        if("file".equalsIgnoreCase(uri.getScheme()))openFile(new File(uri.getPath()));
        else copyPickedUri(uri);
      } else {
        startActivity(new Intent(this,TipitakaLibraryActivity.class));
        finish();
      }
    } catch(Exception e) {
      status("စာအုပ်ဖိုင်ကို ပြန်ဖွင့်၍မရပါ။ Offline Library မှ စာအုပ်ကို ရွေးပါ။");
    }
  }

  private TextView button(String text,Runnable action) {
    TextView v=new TextView(this);v.setText(text);v.setTextColor(Color.rgb(247,229,184));v.setTextSize(14);
    v.setGravity(Gravity.CENTER);v.setPadding(12,12,12,12);v.setOnClickListener(w->action.run());return v;
  }
  private void layout() {
    root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);
    root.setBackgroundColor(Color.rgb(247,243,230));
    HorizontalScrollView topScroll=new HorizontalScrollView(this);topScroll.setHorizontalScrollBarEnabled(false);
    bar=new LinearLayout(this);bar.setBackgroundColor(Color.rgb(20,66,56));
    bar.addView(button("‹",()->finish()));
    bar.addView(button("Library",()->openLibrary()));
    bar.addView(button("Open",this::choose));
    bar.addView(button("A−",()->resize(-2)));
    bar.addView(button("A+",()->resize(2)));
    bar.addView(button("🔖 Save",this::bookmark));
    bar.addView(button("Marks",this::showBookmarks));
    topScroll.addView(bar);root.addView(topScroll);
    label=new TextView(this);label.setTextColor(Color.rgb(41,72,58));label.setTextSize(14);label.setPadding(18,12,12,12);root.addView(label);
    scroll=new ScrollView(this);
    LinearLayout pageBody=new LinearLayout(this);pageBody.setOrientation(LinearLayout.VERTICAL);
    body=new TextView(this);body.setTextColor(Color.rgb(37,47,39));body.setTextSize(font);body.setTextIsSelectable(true);body.setPadding(22,20,22,38);
    pdfImage=new ImageView(this);pdfImage.setAdjustViewBounds(true);pdfImage.setVisibility(View.GONE);
    pageBody.addView(body);pageBody.addView(pdfImage);
    scroll.addView(pageBody);root.addView(scroll,new LinearLayout.LayoutParams(-1,0,1));
    LinearLayout footer=new LinearLayout(this);footer.setBackgroundColor(Color.rgb(20,66,56));
    footer.addView(button("◀ Prev",()->turn(-1)),new LinearLayout.LayoutParams(0,-2,1));
    footer.addView(button("Next ▶",()->turn(1)),new LinearLayout.LayoutParams(0,-2,1));
    footer.addView(button("Find",this::search),new LinearLayout.LayoutParams(0,-2,1));
    footer.addView(button("Go to",this::goTo),new LinearLayout.LayoutParams(0,-2,1));
    root.addView(footer);setContentView(root);
  }
  private void status(String s){if(label!=null)label.setText(s);}
  private void openLibrary(){startActivity(new Intent(this,OfflineBookLibraryActivity.class));}
  private void choose(){
    Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT);
    i.setType("*/*");i.addCategory(Intent.CATEGORY_OPENABLE);
    i.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION|Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION);
    startActivityForResult(i,PICK);
  }
  @Override protected void onActivityResult(int request,int result,Intent data){
    super.onActivityResult(request,result,data);
    if(request==PICK&&result==RESULT_OK&&data!=null&&data.getData()!=null)copyPickedUri(data.getData());
  }
  private void copyPickedUri(Uri uri){
    ProgressDialog dialog=new ProgressDialog(this);dialog.setMessage("Offline Library ထဲသို့ သိမ်းဆည်းနေပါသည်…");
    dialog.setCancelable(false);dialog.show();
    new Thread(()->{
      File saved=null;Exception failure=null;
      try{saved=copyIntoOfflineLibrary(uri);}catch(Exception e){failure=e;}
      final File result=saved;final Exception error=failure;
      runOnUiThread(()->{
        if(isFinishing()){if(dialog.isShowing())dialog.dismiss();return;}
        if(dialog.isShowing())dialog.dismiss();
        if(error!=null){new AlertDialog.Builder(this).setTitle("စာအုပ်သိမ်း၍မရပါ").setMessage(error.getMessage()).setPositiveButton("OK",null).show();return;}
        try{openFile(result);Toast.makeText(this,"Offline Library ထဲ သိမ်းဆည်းပြီး",Toast.LENGTH_LONG).show();}
        catch(Exception e){status("စာအုပ်ဖွင့်၍မရပါ: "+e.getMessage());}
      });
    },"offline-book-import").start();
  }
  private File copyIntoOfflineLibrary(Uri uri)throws Exception{
    String name=getFileName(uri);String lower=name.toLowerCase(Locale.ROOT);
    if(!(lower.endsWith(".pdf")||lower.endsWith(".epub")||lower.endsWith(".txt")))
      throw new IOException("PDF, EPUB သို့မဟုတ် UTF-8 TXT ဖိုင်သာ ထည့်နိုင်ပါသည်။");
    File dir=new File(getFilesDir(),"reader_library");
    if(!dir.exists()&&!dir.mkdirs())throw new IOException("Offline Library folder ဖန်တီး၍မရပါ။");
    String safe=name.replaceAll("[^\\p{L}\\p{N}._-]+","_");
    if(safe.length()>110)safe=safe.substring(safe.length()-110);
    File destination=new File(dir,System.currentTimeMillis()+"_"+safe);
    File temp=File.createTempFile("import_",".part",dir);
    long total=0;
    try(InputStream in=getContentResolver().openInputStream(uri);FileOutputStream out=new FileOutputStream(temp)){
      if(in==null)throw new IOException("ရွေးချယ်ထားသော ဖိုင်ကို ဖတ်၍မရပါ။");
      byte[] buffer=new byte[65536];int n;
      while((n=in.read(buffer))!=-1){
        total+=n;if(total>MAX_IMPORT_BYTES)throw new IOException("ဖိုင်အရွယ်အစား 250 MB ထက်ကျော်နေပါသည်။");
        out.write(buffer,0,n);
      }
      out.flush();out.getFD().sync();
    }catch(Exception e){temp.delete();throw e;}
    if(total==0){temp.delete();throw new IOException("ရွေးချယ်ထားသော ဖိုင်သည် ဗလာဖြစ်နေပါသည်။");}
    if(!temp.renameTo(destination)){temp.delete();throw new IOException("Offline ဖိုင်ကို သိမ်းဆည်း၍မရပါ။");}
    return destination;
  }
  private String getFileName(Uri uri){
    if("file".equalsIgnoreCase(uri.getScheme()))return new File(uri.getPath()).getName();
    try(android.database.Cursor c=getContentResolver().query(uri,null,null,null,null)){
      if(c!=null&&c.moveToFirst()){
        int idx=c.getColumnIndex(android.provider.OpenableColumns.DISPLAY_NAME);
        if(idx>=0){String name=c.getString(idx);if(name!=null&&!name.trim().isEmpty())return name;}
      }
    }catch(Exception ignored){}
    return uri.getLastPathSegment()==null?"book.txt":uri.getLastPathSegment();
  }
  private void closePdf(){
    try{if(renderer!=null)renderer.close();}catch(Exception ignored){}renderer=null;
    try{if(descriptor!=null)descriptor.close();}catch(Exception ignored){}descriptor=null;
    if(currentBitmap!=null&&!currentBitmap.isRecycled()){currentBitmap.recycle();currentBitmap=null;}
  }
  private void openFile(File file)throws Exception{
    if(file==null||!file.isFile()||!file.canRead())throw new IOException("Offline စာအုပ်ဖိုင် မတွေ့ပါ။");
    closePdf();bookId=file.getAbsolutePath();pdf=false;bookText="";page=0;zoom=1f;
    String name=file.getName().toLowerCase(Locale.ROOT);
    if(name.endsWith(".pdf")){
      descriptor=ParcelFileDescriptor.open(file,ParcelFileDescriptor.MODE_READ_ONLY);
      renderer=new PdfRenderer(descriptor);pdf=true;
    }else if(name.endsWith(".txt")){
      try(InputStream in=new FileInputStream(file)){bookText=readLimited(in,12*1024*1024);}
    }else if(name.endsWith(".epub"))bookText=epubText(file);
    else throw new IOException("Supported formats: PDF, EPUB, UTF-8 TXT");
    page=Math.max(0,prefs.getInt("position_"+bookId,0));
    prefs.edit().putString("lastPath",bookId).putString("lastUri",Uri.fromFile(file).toString()).apply();
    showPage();
  }
  private String readLimited(InputStream in,int limit)throws IOException{
    if(in==null)throw new IOException("No document stream");
    ByteArrayOutputStream out=new ByteArrayOutputStream();byte[] buf=new byte[8192];int n;
    while((n=in.read(buf))!=-1){if(out.size()+n>limit)throw new IOException("Book exceeds 12 MB text limit");out.write(buf,0,n);}
    return out.toString("UTF-8");
  }
  private String epubText(File file)throws IOException{
    StringBuilder result=new StringBuilder();
    try(InputStream raw=new FileInputStream(file);ZipInputStream zip=new ZipInputStream(raw)){
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
        if((long)w*h>9000000L){double scale=Math.sqrt(9000000d/(w*(double)h));w=Math.max(1,(int)(w*scale));h=Math.max(1,(int)(h*scale));}
        Bitmap next=Bitmap.createBitmap(w,h,Bitmap.Config.ARGB_8888);
        next.eraseColor(Color.WHITE);p.render(next,null,null,PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
        Bitmap previous=currentBitmap;currentBitmap=next;pdfImage.setImageBitmap(next);
        if(previous!=null&&!previous.isRecycled())previous.recycle();
      }catch(Exception e){status("PDF render error: "+e.getMessage());return;}
    }else{
      int a=page*3000,b=Math.min(bookText.length(),a+3000);
      body.setText(bookText.substring(Math.min(a,b),b));
    }
    status(new File(bookId).getName()+"   •   "+(page+1)+" / "+pages()+"   •   Offline");
    scroll.scrollTo(0,0);prefs.edit().putInt("position_"+bookId,page).apply();
  }
  private void turn(int delta){if(bookId.isEmpty()){choose();return;}page+=delta;showPage();}
  private void resize(int delta){
    font=Math.max(14,Math.min(38,font+delta));prefs.edit().putInt("font",font).apply();body.setTextSize(font);
    if(pdf){zoom=Math.max(.65f,Math.min(2.5f,zoom+(delta>0?.15f:-.15f)));showPage();}
  }
  private String marksKey(){return "bookmarks_"+bookId;}
  private void bookmark(){
    if(bookId.isEmpty())return;
    Set<String> marks=new HashSet<>(prefs.getStringSet(marksKey(),Collections.emptySet()));
    marks.add(Integer.toString(page));
    prefs.edit().putStringSet(marksKey(),marks).apply();
    Toast.makeText(this,"စာမျက်နှာ "+(page+1)+" Bookmark သိမ်းဆည်းပြီး",Toast.LENGTH_SHORT).show();
  }
  private void showBookmarks(){
    if(bookId.isEmpty())return;
    Set<String> saved=prefs.getStringSet(marksKey(),Collections.emptySet());
    ArrayList<Integer> pages=new ArrayList<>();
    for(String value:saved)try{pages.add(Integer.parseInt(value));}catch(Exception ignored){}
    Collections.sort(pages);
    if(pages.isEmpty()){new AlertDialog.Builder(this).setTitle("Bookmarks").setMessage("သိမ်းထားသော Bookmark မရှိသေးပါ။").setPositiveButton("OK",null).show();return;}
    String[] labels=new String[pages.size()];for(int i=0;i<pages.size();i++)labels[i]="စာမျက်နှာ "+(pages.get(i)+1);
    new AlertDialog.Builder(this).setTitle("သိမ်းထားသော စာမျက်နှာများ").setItems(labels,(d,which)->{page=pages.get(which);showPage();})
      .setNegativeButton("ပိတ်ရန်",null).show();
  }
  private void goTo(){
    if(bookId.isEmpty()){choose();return;}
    EditText input=new EditText(this);input.setInputType(2);input.setHint("Page 1–"+pages());
    new AlertDialog.Builder(this).setTitle("Go to page").setView(input)
      .setPositiveButton("Go",(d,w)->{try{page=Integer.parseInt(input.getText().toString())-1;showPage();}catch(Exception ignored){}})
      .setNeutralButton("Bookmarks",(d,w)->showBookmarks()).setNegativeButton("Cancel",null).show();
  }
  private void search(){
    if(bookId.isEmpty()){choose();return;}
    if(pdf){new AlertDialog.Builder(this).setMessage("PDF text search is not supported by Android PdfRenderer. For full-text search, import a TXT or EPUB book.").setPositiveButton("OK",null).show();return;}
    EditText input=new EditText(this);input.setHint("မြန်မာ / Pāli search");
    new AlertDialog.Builder(this).setTitle("Find in book").setView(input).setPositiveButton("Find",(d,w)->{
      String q=input.getText().toString().trim();if(q.isEmpty())return;
      String hay=bookText.toLowerCase(Locale.ROOT),needle=q.toLowerCase(Locale.ROOT);
      int pos=hay.indexOf(needle,Math.min(bookText.length(),(page+1)*3000));
      if(pos<0)pos=hay.indexOf(needle);
      if(pos>=0){page=pos/3000;showPage();}else Toast.makeText(this,"No match",Toast.LENGTH_LONG).show();
    }).setNegativeButton("Cancel",null).show();
  }
  @Override protected void onPause(){
    if(!bookId.isEmpty())prefs.edit().putInt("position_"+bookId,page).putString("lastPath",bookId).apply();
    super.onPause();
  }
  @Override protected void onDestroy(){closePdf();super.onDestroy();}
}
