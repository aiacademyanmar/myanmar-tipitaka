package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.os.Bundle;
import android.text.InputType;
import android.view.MotionEvent;
import android.view.View;
import android.widget.*;
import java.io.InputStream;
import java.util.Locale;

/**
 * Pixel-preserving screen artwork with practical, accessible native interaction overlays.
 * Artwork is displayed unchanged; actions and navigation are Android-native.
 */
public class ExactScreensActivity extends Activity {
    private int page=1;
    private ImageView image;
    private float downX,downY;
    private final boolean[] bookmarks=new boolean[21];
    private final String[] names={
      "","Welcome","Home","Navigation","Categories","Books","Native Reader",
      "Library","Reading","Learning","Search","Results","Bookmarks & Notes",
      "History","Advanced Search","Abhidhamma","Abhidhamma Reader",
      "Dhamma","Mangala Sutta","Five Nikayas","About & Help"};
    private void showScreen(int next){
        if(next>=1&&next<=9){Intent nativePage=new Intent(this,NativeFrontPagesActivity.class);nativePage.putExtra("openPage",next);startActivity(nativePage);finish();return;}
        page=Math.min(20,Math.max(7,next));
        String file=String.format(Locale.US,"screens/screen_%02d.png",page);
        try(InputStream stream=getAssets().open(file)){
            Bitmap bmp=BitmapFactory.decodeStream(stream);
            if(bmp==null)throw new IllegalArgumentException("Invalid screen artwork");
            image.setImageBitmap(bmp);
            image.setContentDescription("Myanmar Tipitaka — "+names[page]+" ("+page+" of 20)");
            getPreferences(MODE_PRIVATE).edit().putInt("lastPage",page).apply();
        }catch(Exception e){
            new AlertDialog.Builder(this).setTitle("Screen artwork unavailable")
              .setMessage(file+"\n"+e.getMessage()).setPositiveButton("OK",null).show();
        }
    }
    @Override public void onCreate(Bundle saved){
        super.onCreate(saved);
        getWindow().setStatusBarColor(Color.BLACK);
        getWindow().setNavigationBarColor(Color.BLACK);
        image=new ImageView(this);
        image.setBackgroundColor(Color.BLACK);
        image.setScaleType(ImageView.ScaleType.FIT_CENTER);
        setContentView(image);
        int start=saved==null?getIntent().getIntExtra("openPage",getPreferences(MODE_PRIVATE).getInt("lastPage",4)):saved.getInt("page",4);
        showScreen(start);
        image.setOnTouchListener((v,e)->{
            if(e.getAction()==MotionEvent.ACTION_DOWN){downX=e.getX();downY=e.getY();return true;}
            if(e.getAction()==MotionEvent.ACTION_UP){
                float dx=e.getX()-downX,dy=e.getY()-downY;
                if(Math.abs(dx)>85&&Math.abs(dx)>Math.abs(dy)*1.3f){showScreen(page+(dx<0?1:-1));return true;}
                if(Math.abs(dx)<35&&Math.abs(dy)<35){
                    // FIT_CENTER means coordinates need to be mapped to the actual artwork.
                    float viewW=v.getWidth(),viewH=v.getHeight();
                    if(image.getDrawable()==null)return true;
                    float artW=image.getDrawable().getIntrinsicWidth();
                    float artH=image.getDrawable().getIntrinsicHeight();
                    float scale=Math.min(viewW/artW,viewH/artH);
                    float left=(viewW-artW*scale)/2f,top=(viewH-artH*scale)/2f;
                    float x=(e.getX()-left)/(artW*scale),y=(e.getY()-top)/(artH*scale);
                    if(x>=0&&x<=1&&y>=0&&y<=1)tap(x,y);
                }
                return true;
            }
            return true;
        });
    }
    private void tap(float x,float y){
        if(y<0.13f){
            if(x<0.18f){if(page==1)menu();else showScreen(page-1);return;}
            if(x>0.82f){
                if(page==6||page==16)toggleBookmark();else menu();
                return;
            }
        }
        // Native navigation actions are mapped without changing any source pixels.
        if(page==3){menu();return;}
        if(page==10||page==14){
            if(y>0.19f&&y<0.45f){search();return;}
            if(y>0.50f&&y<0.90f){showScreen(6);return;}
        }
        if(page==6||page==16){
            if(y>0.27f&&y<0.86f){startActivity(new android.content.Intent(this,BookReaderActivity.class));return;}
            if(y>0.86f){
                if(x<0.19f)showScreen(Math.max(1,page-1));
                else if(x<0.40f)showScreen(4);
                else if(x<0.62f)readerSettings();
                else if(x<0.81f)readerSettings();
                else showScreen(Math.min(20,page+1));
                return;
            }
            if(y<0.23f&&x>0.22f&&x<0.80f){choosePage();return;}
        }
        if(page==12&&y>0.35f&&y<0.89f){showScreen(6);return;}
        if(page==13&&y>0.30f&&y<0.90f){showScreen(getPreferences(MODE_PRIVATE).getInt("lastPage",6));return;}
        if(y>0.90f){
            if(x<0.22f)showScreen(2);
            else if(x<0.45f)showScreen(4);
            else if(x<0.70f)showScreen(10);
            else showScreen(20);
            return;
        }
        if(page==1)showScreen(2);
        else if(page==2&&y>0.15f&&y<0.89f)showScreen(4);
        else if(page==4&&y>0.20f&&y<0.89f)showScreen(5);
        else if(page==5&&y>0.20f&&y<0.89f)showScreen(6);
    }
    private void menu(){
        String[] labels=new String[20];
        for(int i=0;i<20;i++)labels[i]=String.format(Locale.US,"%02d · %s",i+1,names[i+1]);
        new AlertDialog.Builder(this).setTitle("Myanmar Tipitaka — Menu")
            .setItems(labels,(d,which)->showScreen(which+1))
            .setNegativeButton("Close",null).show();
    }
    private void search(){
        EditText term=new EditText(this);term.setSingleLine(true);term.setHint("ရှာဖွေရန် စာသား");
        term.setInputType(InputType.TYPE_CLASS_TEXT);
        int pad=(int)(18*getResources().getDisplayMetrics().density);
        LinearLayout wrapper=new LinearLayout(this);
        wrapper.setPadding(pad,0,pad,0);wrapper.addView(term);
        new AlertDialog.Builder(this).setTitle("Tipitaka Search")
            .setView(wrapper).setPositiveButton("Search",(d,w)->{
                String q=term.getText().toString().trim();
                if(q.isEmpty()){Toast.makeText(this,"Enter search text",Toast.LENGTH_SHORT).show();return;}
                // Screenshot-only mode has no indexed Tipitaka database yet.
                new AlertDialog.Builder(this).setTitle("Search: "+q)
                  .setMessage("The original Search UI is preserved. Search results require an indexed Tipitaka text database; none is bundled with this screenshot-based build.")
                  .setPositiveButton("Open results UI",(dialog,button)->showScreen(11))
                  .setNegativeButton("Close",null).show();
            }).setNegativeButton("Cancel",null).show();
    }
    private void choosePage(){
        String[] options={"Books","Native Reader","Search","Advanced Search","Bookmarks","Reading History"};
        int[] pages={5,6,10,14,12,13};
        new AlertDialog.Builder(this).setTitle("Go to")
          .setItems(options,(d,i)->showScreen(pages[i])).show();
    }
    private void readerSettings(){
        String[] options={"Default artwork size","Fit screen","Bookmark this page","Go to Search"};
        new AlertDialog.Builder(this).setTitle("Reader controls")
          .setItems(options,(d,i)->{
              if(i==0)image.setScaleType(ImageView.ScaleType.FIT_CENTER);
              if(i==1)image.setScaleType(ImageView.ScaleType.FIT_XY);
              if(i==2)toggleBookmark();
              if(i==3)showScreen(10);
          }).show();
    }
    private void toggleBookmark(){
        bookmarks[page]=!bookmarks[page];
        getPreferences(MODE_PRIVATE).edit().putBoolean("bookmark_"+page,bookmarks[page]).apply();
        Toast.makeText(this,bookmarks[page]?"Bookmarked page "+page:"Bookmark removed",Toast.LENGTH_SHORT).show();
    }
    @Override protected void onSaveInstanceState(Bundle out){out.putInt("page",page);super.onSaveInstanceState(out);}
    @Override public void onBackPressed(){if(page>1)showScreen(page-1);else super.onBackPressed();}
}
