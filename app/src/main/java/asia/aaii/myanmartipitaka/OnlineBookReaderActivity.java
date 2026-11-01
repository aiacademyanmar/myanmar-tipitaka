package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.webkit.DownloadListener;
import android.webkit.SafeBrowsingResponse;
import android.webkit.SslErrorHandler;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.SslError;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import java.util.Arrays;
import java.util.HashSet;
import java.util.Set;

/** Secure in-app online reader for curated reference-library publishers.
 * Only HTTPS pages on explicitly approved publisher domains stay in this WebView.
 * Unknown domains and file downloads are handed to the user's external browser.
 * This screen does not bypass publisher access controls or redistribute book files.
 */
public final class OnlineBookReaderActivity extends Activity {
  private static final int GREEN=0xff144638, CREAM=0xfffaf6e7, INK=0xff203a2f;
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
  private String progressKey(String url){return "scroll_"+Integer.toHexString(url.hashCode());}
  private void openExternal(String url){
    try{startActivity(new Intent(Intent.ACTION_VIEW,Uri.parse(url)));}
    catch(Exception e){Toast.makeText(this,"ဤ Link ကို Browser ဖြင့် မဖွင့်နိုင်ပါ",Toast.LENGTH_LONG).show();}
  }
  private void showDownload(String url,String mime){
    new AlertDialog.Builder(this)
      .setTitle("စာအုပ်ဖိုင် / Download")
      .setMessage("ဤဖိုင်ကို မူရင်း Website မှ ရယူရန် ပြင်ပ Browser သို့ လွှဲပေးပါမည်။ မူပိုင်ခွင့်နှင့် Download ခွင့်ပြုချက်ကို မူရင်း Website တွင် စစ်ဆေးပါ။")
      .setNegativeButton("မလုပ်တော့ပါ",null)
      .setPositiveButton("Browser ဖွင့်ရန်",(d,w)->openExternal(url))
      .show();
  }
  private void updateStatus(String value){if(statusView!=null)statusView.setText(value);}
  private void loadPublisherUrl(String url){
    Uri uri=Uri.parse(url);
    if(!isAllowed(uri)){updateStatus("ခွင့်ပြုထားသော Reference Website မဟုတ်ပါ။ Browser ဖြင့်ဖွင့်ပါ။");return;}
    startUrl=url;pageTitle=getIntent().getStringExtra("source_title");
    if(pageTitle==null||pageTitle.trim().isEmpty())pageTitle="Online Reference";
    titleView.setText(pageTitle);
    web.loadUrl(url);
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);getWindow().setStatusBarColor(GREEN);getWindow().setNavigationBarColor(GREEN);
    startUrl=getIntent().getStringExtra("url");
    if(startUrl==null)startUrl="";
    if(state!=null)restoredScroll=state.getInt("reader_scroll",0);
    else if(!startUrl.isEmpty())restoredScroll=getSharedPreferences("online_reference_reader",MODE_PRIVATE).getInt(progressKey(startUrl),0);

    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setBackgroundColor(CREAM);
    LinearLayout header=new LinearLayout(this);header.setOrientation(LinearLayout.VERTICAL);header.setBackgroundColor(GREEN);
    titleView=text("Online Reference Reader",18,Color.WHITE,true);header.addView(titleView);
    statusView=text("မူရင်းစာကြည့်တိုက် Website ကို ဖွင့်နေသည်…",12,0xfff4e6c8,false);statusView.setPadding(dp(12),0,dp(12),dp(7));header.addView(statusView);
    root.addView(header);
    progress=new ProgressBar(this,null,android.R.attr.progressBarStyleHorizontal);
    progress.setMax(100);progress.setProgress(0);root.addView(progress,new LinearLayout.LayoutParams(-1,dp(3)));

    web=new WebView(this);web.setBackgroundColor(Color.WHITE);web.setOverScrollMode(View.OVER_SCROLL_IF_CONTENT_SCROLLS);
    WebSettings settings=web.getSettings();
    settings.setJavaScriptEnabled(false);
    settings.setDomStorageEnabled(false);
    settings.setDatabaseEnabled(false);
    settings.setAllowFileAccess(false);
    settings.setAllowContentAccess(false);
    settings.setAllowFileAccessFromFileURLs(false);
    settings.setAllowUniversalAccessFromFileURLs(false);
    settings.setSupportZoom(true);settings.setBuiltInZoomControls(true);settings.setDisplayZoomControls(false);
    settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
    settings.setCacheMode(WebSettings.LOAD_DEFAULT);
    if(Build.VERSION.SDK_INT>=26)settings.setSafeBrowsingEnabled(true);

    web.setWebViewClient(new WebViewClient(){
      @Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){
        Uri uri=request.getUrl();
        if(isAllowed(uri))return false;
        if("https".equalsIgnoreCase(uri.getScheme()))openExternal(uri.toString());
        else updateStatus("လုံခြုံရေးအတွက် ဤ Link အမျိုးအစားကို ပိတ်ထားသည်။");
        return true;
      }
      @Override public boolean shouldOverrideUrlLoading(WebView view,String url){
        Uri uri=Uri.parse(url);
        if(isAllowed(uri))return false;
        if("https".equalsIgnoreCase(uri.getScheme()))openExternal(url);
        else updateStatus("လုံခြုံရေးအတွက် ဤ Link အမျိုးအစားကို ပိတ်ထားသည်။");
        return true;
      }
      @Override public void onPageStarted(WebView view,String url,android.graphics.Bitmap favicon){
        Uri uri=Uri.parse(url);
        if(!isAllowed(uri)){view.stopLoading();if("https".equalsIgnoreCase(uri.getScheme()))openExternal(url);return;}
        progress.setVisibility(View.VISIBLE);progress.setProgress(5);updateStatus("စာမျက်နှာ ဖွင့်နေသည်…");
      }
      @Override public void onPageFinished(WebView view,String url){
        if(!isAllowed(Uri.parse(url)))return;
        progress.setProgress(100);progress.setVisibility(View.GONE);
        String t=view.getTitle();if(t!=null&&!t.trim().isEmpty())titleView.setText(t);
        updateStatus("Online • Pinch / Zoom ဖြင့် ဖတ်ရှုနိုင်သည်");
        if(firstPage){firstPage=false;view.postDelayed(()->view.scrollTo(0,restoredScroll),350);}
        getPreferences(MODE_PRIVATE).edit().putString("last_url",url).putString("last_title",view.getTitle()).apply();
      }
      @Override public void onReceivedError(WebView view,WebResourceRequest request,WebResourceError error){
        if(request.isForMainFrame())updateStatus("Website မဖွင့်နိုင်ပါ။ Internet ချိတ်ဆက်မှု သို့မဟုတ် Browser ဖြင့် စမ်းကြည့်ပါ။");
      }
      @Override public void onReceivedSslError(WebView view,SslErrorHandler handler,SslError error){
        handler.cancel();updateStatus("လုံခြုံသော SSL ချိတ်ဆက်မှု မအောင်မြင်ပါ။ ဖွင့်ခြင်းကို ပိတ်ထားသည်။");
      }
    });
    web.setWebChromeClient(new WebChromeClient(){
      @Override public void onProgressChanged(WebView view,int value){progress.setProgress(value);if(value>=100)progress.setVisibility(View.GONE);else progress.setVisibility(View.VISIBLE);}
      @Override public void onReceivedTitle(WebView view,String title){if(title!=null&&!title.trim().isEmpty())titleView.setText(title);}
    });
    web.setDownloadListener((url,userAgent,contentDisposition,mimeType,contentLength)->showDownload(url,mimeType));
    root.addView(web,new LinearLayout.LayoutParams(-1,0,1));

    LinearLayout controls=new LinearLayout(this);controls.setGravity(Gravity.CENTER);controls.setBackgroundColor(0xffeee6d3);
    Button back=new Button(this);back.setText("‹ Back");controls.addView(back,new LinearLayout.LayoutParams(0,-2,1));
    Button refresh=new Button(this);refresh.setText("↻ Reload");controls.addView(refresh,new LinearLayout.LayoutParams(0,-2,1));
    Button browser=new Button(this);browser.setText("Browser ↗");controls.addView(browser,new LinearLayout.LayoutParams(0,-2,1));
    root.addView(controls);setContentView(root);
    back.setOnClickListener(v->{if(web.canGoBack())web.goBack();else finish();});
    refresh.setOnClickListener(v->web.reload());
    browser.setOnClickListener(v->openExternal(web.getUrl()==null?startUrl:web.getUrl()));

    if(startUrl.isEmpty()){
      updateStatus("ဖွင့်ရန် Reference Link မရှိပါ။");browser.setEnabled(false);
    }else if(!isAllowed(Uri.parse(startUrl))){
      updateStatus("ဤ Website ကို In-App Reader မှ မဖွင့်နိုင်ပါ။ Browser ဖြင့်ဖွင့်ပါ။");openExternal(startUrl);
    }else loadPublisherUrl(startUrl);
  }
  @Override protected void onPause(){
    if(web!=null&&!startUrl.isEmpty()){
      getSharedPreferences("online_reference_reader",MODE_PRIVATE).edit()
        .putInt(progressKey(startUrl),web.getScrollY()).putString("last_url",web.getUrl()).apply();
      web.onPause();
    }
    super.onPause();
  }
  @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
  @Override protected void onSaveInstanceState(Bundle out){
    if(web!=null)out.putInt("reader_scroll",web.getScrollY());
    super.onSaveInstanceState(out);
  }
  @Override public void onBackPressed(){if(web!=null&&web.canGoBack())web.goBack();else super.onBackPressed();}
  @Override protected void onDestroy(){
    if(web!=null){web.stopLoading();web.setWebChromeClient(null);web.setWebViewClient(null);web.destroy();web=null;}
    super.onDestroy();
  }
}
