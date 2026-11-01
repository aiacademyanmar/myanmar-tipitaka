package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.HorizontalScrollView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import org.json.JSONArray;
import org.json.JSONObject;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Secure in-app reader for curated Buddhist reference publishers.
 * Publisher HTML pages stay in WebView; PDF files are handed to the system browser/viewer.
 * No publisher access controls are bypassed and no copyrighted book is mirrored into the APK.
 */
public final class OnlineBookReaderActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6e7, INK=0xff203a2f;
  private static final String PREFS="online_reference_reader";
  private static final Set<String> ALLOWED_HOSTS=new HashSet<>(Arrays.asList(
    "kbrl.gov.mm","spsuygn.edu.mm","sariputta.com","myanmarsutta.net",
    "winmetta.org","epitaka.org","tipitaka.cloud","tipitakaonline.org",
    "ugp.edu.mm","itbmu.org.mm"
  ));
  private WebView web;
  private ProgressBar progress;
  private TextView titleView,statusView;
  private String startUrl="",pageTitle="";
  private int restoredScroll=0;
  private boolean firstPage=true;

  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  private TextView text(String value,int size,int color,boolean bold){
    TextView t=new TextView(this);t.setText(value);t.setTextSize(size);t.setTextColor(color);
    if(bold)t.setTypeface(android.graphics.Typeface.DEFAULT,android.graphics.Typeface.BOLD);
    t.setPadding(dp(8),dp(7),dp(8),dp(7));return t;
  }
  private boolean isAllowed(Uri uri){
    if(uri==null||!"https".equalsIgnoreCase(uri.getScheme()))return false;
    String host=uri.getHost();if(host==null)return false;host=host.toLowerCase(java.util.Locale.US);
    for(String domain:ALLOWED_HOSTS)if(host.equals(domain)||host.endsWith("."+domain))return true;
    return false;
  }
  private boolean isPdfUrl(String url){
    if(url==null)return false;
    String path=Uri.parse(url).getPath();
    return path!=null&&path.toLowerCase(java.util.Locale.ROOT).endsWith(".pdf");
  }
  private String progressKey(String url){return "scroll_"+Integer.toHexString(url.hashCode());}
  private void updateStatus(String value){if(statusView!=null)statusView.setText(value);}
  private void openExternal(String url){
    try{
      Uri uri=Uri.parse(url);
      if(!"https".equalsIgnoreCase(uri.getScheme()))throw new IllegalArgumentException("HTTPS required");
      startActivity(new Intent(Intent.ACTION_VIEW,uri));
    }catch(Exception e){Toast.makeText(this,"ဤ Link ကို Browser / PDF Reader ဖြင့် မဖွင့်နိုင်ပါ",Toast.LENGTH_LONG).show();}
  }
  private void loadAllowedUrl(String url,String title){
    Uri uri=Uri.parse(url);
    if(!isAllowed(uri)){updateStatus("ခွင့်ပြုထားသော Reference Website မဟုတ်ပါ။");return;}
    if(isPdfUrl(url)){updateStatus("PDF ဖိုင်ကို ဖုန်း၏ PDF Viewer ဖြင့် ဖွင့်နေသည်…");openExternal(url);return;}
    startUrl=url;pageTitle=(title==null||title.trim().isEmpty())?"Online Reference":title;
    titleView.setText(pageTitle);web.loadUrl(url);
  }
  private JSONArray readEntries(String key){
    try{return new JSONArray(getSharedPreferences(PREFS,MODE_PRIVATE).getString(key,"[]"));}
    catch(Exception e){return new JSONArray();}
  }
  private void saveEntry(String key,String url,String title,int max){
    if(url==null||!isAllowed(Uri.parse(url)))return;
    JSONArray old=readEntries(key),next=new JSONArray();
    try{
      for(int i=0;i<old.length();i++){
        JSONObject item=old.optJSONObject(i);
        if(item!=null&&!url.equals(item.optString("url")))next.put(item);
      }
      JSONObject current=new JSONObject();current.put("url",url);current.put("title",title==null?url:title);
      current.put("saved_at",System.currentTimeMillis());JSONArray result=new JSONArray();result.put(current);
      for(int i=0;i<next.length()&&i<max-1;i++)result.put(next.get(i));
      getSharedPreferences(PREFS,MODE_PRIVATE).edit().putString(key,result.toString()).apply();
    }catch(Exception ignored){}
  }
  private void showEntries(String key,String heading){
    JSONArray entries=readEntries(key);String[] labels=new String[entries.length()];
    for(int i=0;i<entries.length();i++){
      JSONObject item=entries.optJSONObject(i);labels[i]=item==null?"":item.optString("title");
    }
    if(labels.length==0){new AlertDialog.Builder(this).setTitle(heading).setMessage("သိမ်းထားသော စာရင်းမရှိသေးပါ။").setPositiveButton("ပိတ်ရန်",null).show();return;}
    new AlertDialog.Builder(this).setTitle(heading).setItems(labels,(dialog,which)->{
      JSONObject item=entries.optJSONObject(which);if(item==null)return;
      String url=item.optString("url");
      if(isPdfUrl(url))openExternal(url);else loadAllowedUrl(url,item.optString("title"));
    }).setNegativeButton("ပိတ်ရန်",null).show();
  }
  private void saveCurrentBookmark(){
    String url=web==null?startUrl:web.getUrl();String title=web==null?pageTitle:web.getTitle();
    if(url==null||url.isEmpty())url=startUrl;
    saveEntry("bookmarks",url,title,100);
    Toast.makeText(this,"Bookmark သိမ်းဆည်းပြီး",Toast.LENGTH_SHORT).show();
  }
  private void showFindDialog(){
    EditText q=new EditText(this);q.setSingleLine(true);q.setHint("ရှာဖွေလိုသော စာသား");
    new AlertDialog.Builder(this).setTitle("စာမျက်နှာအတွင်း ရှာရန်").setView(q)
      .setNegativeButton("ပိတ်ရန်",null)
      .setPositiveButton("ရှာရန်",(d,w)->{String term=q.getText().toString().trim();if(!term.isEmpty())web.findAllAsync(term);})
      .show();
  }
  private void showDownload(String url){
    new AlertDialog.Builder(this).setTitle("PDF / စာအုပ်ဖိုင်")
      .setMessage("ဖိုင်ကို မူရင်း Website မှ Browser သို့ လွှဲပေးပါမည်။ Download နှင့် ပြန်လည်ဖြန့်ဝေခွင့်ကို မူရင်းထုတ်ဝေသူထံ စစ်ဆေးပါ။")
      .setNegativeButton("မလုပ်တော့ပါ",null)
      .setPositiveButton("ဖွင့်ရန်",(d,w)->openExternal(url)).show();
  }
  private void addControl(LinearLayout row,String label,Runnable action){
    Button b=new Button(this);b.setText(label);b.setTextSize(12);row.addView(b,new LinearLayout.LayoutParams(-2,-2));
    b.setOnClickListener(v->action.run());
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    startUrl=getIntent().getStringExtra("url");if(startUrl==null)startUrl="";
    pageTitle=getIntent().getStringExtra("source_title");
    if(state!=null)restoredScroll=state.getInt("reader_scroll",0);
    else if(!startUrl.isEmpty())restoredScroll=getSharedPreferences(PREFS,MODE_PRIVATE).getInt(progressKey(startUrl),0);

    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    LinearLayout header=new LinearLayout(this);header.setOrientation(LinearLayout.VERTICAL);header.setBackgroundColor(GREEN);
    titleView=text("Online Reference Reader",18,Color.WHITE,true);header.addView(titleView);
    statusView=text("မူရင်းစာကြည့်တိုက် Website ကို ဖွင့်နေသည်…",12,0xfff4e6c8,false);
    statusView.setPadding(dp(12),0,dp(12),dp(7));header.addView(statusView);root.addView(header);
    progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
    progress.setMax(100);progress.setProgress(0);root.addView(progress,new LinearLayout.LayoutParams(-1,dp(3)));

    web=new WebView(this);web.setBackgroundColor(Color.WHITE);web.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    WebSettings settings=web.getSettings();
    settings.setJavaScriptEnabled(false);settings.setDomStorageEnabled(false);settings.setDatabaseEnabled(false);
    settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);
    settings.setAllowFileAccessFromFileURLs(false);settings.setAllowUniversalAccessFromFileURLs(false);
    settings.setSupportZoom(true);settings.setBuiltInZoomControls(true);settings.setDisplayZoomControls(false);
    settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);settings.setCacheMode(WebSettings.LOAD_DEFAULT);
    if(Build.VERSION.SDK_INT>=26)settings.setSafeBrowsingEnabled(true);
    web.setWebViewClient(new WebViewClient(){
      @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
        Uri uri=request.getUrl();String url=uri.toString();
        if(!isAllowed(uri)){if("https".equalsIgnoreCase(uri.getScheme()))openExternal(url);else updateStatus("လုံခြုံရေးအတွက် ဤ Link ကို ပိတ်ထားသည်။");return true;}
        if(isPdfUrl(url)){showDownload(url);return true;}
        return false;
      }
      @Override public boolean shouldOverrideUrlLoading(WebView view,String url){
        Uri uri=Uri.parse(url);
        if(!isAllowed(uri)){if("https".equalsIgnoreCase(uri.getScheme()))openExternal(url);else updateStatus("လုံခြုံရေးအတွက် ဤ Link ကို ပိတ်ထားသည်။");return true;}
        if(isPdfUrl(url)){showDownload(url);return true;}
        return false;
      }
      @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap favicon){
        Uri uri=Uri.parse(url);
        if(!isAllowed(uri)){view.stopLoading();if("https".equalsIgnoreCase(uri.getScheme()))openExternal(url);return;}
        progress.setVisibility(View.VISIBLE);progress.setProgress(5);updateStatus("စာမျက်နှာ ဖွင့်နေသည်…");
      }
      @Override public void onPageFinished(WebView view,String url){
        if(!isAllowed(Uri.parse(url)))return;
        progress.setProgress(100);progress.setVisibility(View.GONE);
        String title=view.getTitle();if(title!=null&&!title.trim().isEmpty())titleView.setText(title);
        updateStatus("Online • Zoom ဖြင့် ဖတ်ရှုနိုင်သည် • PDF ဖိုင်များကို PDF Viewer ဖြင့်ဖွင့်မည်");
        if(firstPage){firstPage=false;view.postDelayed(()->view.scrollTo(0,restoredScroll),300);}
        saveEntry("history",url,title,30);
      }
      @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error){
        if(request.isForMainFrame())updateStatus("Website မဖွင့်နိုင်ပါ။ Internet ချိတ်ဆက်မှု သို့မဟုတ် Browser ဖြင့် စမ်းကြည့်ပါ။");
      }
      @Override public void onReceivedSslError(WebView view,SslErrorHandler handler,SslError error){
        handler.cancel();updateStatus("SSL လုံခြုံရေးစစ်ဆေးမှု မအောင်မြင်ပါ။ ဖွင့်ခြင်းကို ပိတ်ထားသည်။");
      }
    });
    web.setWebChromeClient(new WebChromeClient(){
      @Override public void onProgressChanged(WebView view,int value){progress.setProgress(value);if(value>=100)progress.setVisibility(View.GONE);else progress.setVisibility(View.VISIBLE);}
      @Override public void onReceivedTitle(WebView view,String title){if(title!=null&&!title.trim().isEmpty())titleView.setText(title);}
    });
    web.setDownloadListener((url,userAgent,contentDisposition,mimeType,contentLength)->showDownload(url));
    root.addView(web,new LinearLayout.LayoutParams(-1,0,1));

    HorizontalScrollView bar=new HorizontalScrollView(this);bar.setHorizontalScrollBarEnabled(false);
    LinearLayout controls=new LinearLayout(this);controls.setGravity(Gravity.CENTER_VERTICAL);controls.setBackgroundColor(0xffeee6d3);
    addControl(controls,"‹ Back",()->{if(web.canGoBack())web.goBack();else finish();});
    addControl(controls,"↻ Reload",()->web.reload());
    addControl(controls,"Find",this::showFindDialog);
    addControl(controls,"🔖 Save",this::saveCurrentBookmark);
    addControl(controls,"Saved",()->showEntries("bookmarks","Bookmarks"));
    addControl(controls,"History",()->showEntries("history","Reading History"));
    addControl(controls,"Browser ↗",()->openExternal(web.getUrl()==null?startUrl:web.getUrl()));
    bar.addView(controls);root.addView(bar);
    setContentView(root);

    if(startUrl.isEmpty()){updateStatus("ဖွင့်ရန် Reference Link မရှိပါ။");}
    else if(!isAllowed(Uri.parse(startUrl))){updateStatus("ဤ Website ကို In-App Reader မှ မဖွင့်နိုင်ပါ။");openExternal(startUrl);}
    else loadAllowedUrl(startUrl,pageTitle);
  }
  @Override protected void onPause(){
    if(web!=null&&!startUrl.isEmpty()){
      getSharedPreferences(PREFS,MODE_PRIVATE).edit().putInt(progressKey(startUrl),web.getScrollY()).apply();
      web.onPause();
    }
    super.onPause();
  }
  @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
  @Override protected void onSaveInstanceState(Bundle out){
    if(web!=null)out.putInt("reader_scroll",web.getScrollY());super.onSaveInstanceState(out);
  }
  @Override public void onBackPressed(){if(web!=null&&web.canGoBack())web.goBack();else super.onBackPressed();}
  @Override protected void onDestroy(){
    if(web!=null){web.stopLoading();web.setWebChromeClient(null);web.setWebViewClient(null);web.destroy();web=null;}
    super.onDestroy();
  }
}
