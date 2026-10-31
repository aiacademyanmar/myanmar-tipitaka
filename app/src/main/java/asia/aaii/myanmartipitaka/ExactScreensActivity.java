package asia.aaii.myanmartipitaka;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.view.*;
import android.widget.*;
import java.io.InputStream;
import java.util.Locale;

public class ExactScreensActivity extends Activity {
  private int page=1;
  private ImageView image;
  private float downX, downY;
  private void showScreen(int p) {
    page=Math.max(1,Math.min(20,p));
    String name=String.format(Locale.US,"screens/screen_%02d.png",page);
    try(InputStream stream=getAssets().open(name)){
      image.setImageBitmap(BitmapFactory.decodeStream(stream));
      image.setContentDescription("Myanmar Tipitaka screen "+page+" of 20");
    }catch(Exception e){ throw new IllegalStateException("Required original screenshot missing: "+name,e); }
  }
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(Color.BLACK);
    getWindow().setNavigationBarColor(Color.BLACK);
    image=new ImageView(this);
    image.setBackgroundColor(Color.BLACK);
    image.setScaleType(ImageView.ScaleType.FIT_CENTER);
    setContentView(image);
    showScreen(1);
    image.setOnTouchListener((v,event)->{
      if(event.getAction()==MotionEvent.ACTION_DOWN){downX=event.getX();downY=event.getY();return true;}
      if(event.getAction()==MotionEvent.ACTION_UP){
        float dx=event.getX()-downX;
        if(Math.abs(dx)>70){showScreen(page+(dx<0?1:-1));return true;}
        // Original screen artwork is displayed without redrawing, keeping its layout intact.
        // Touch regions can be mapped per original design after screenshot inspection.
        float x=event.getX()/Math.max(1,v.getWidth()), y=event.getY()/Math.max(1,v.getHeight());
        if(y<0.10 && x<0.20)showScreen(Math.max(1,page-1));
        else if(y>0.93){if(x<0.33)showScreen(1); else if(x>0.67)showScreen(Math.min(20,page+1));}
        return true;
      }
      return true;
    });
  }
  @Override public void onBackPressed(){if(page>1)showScreen(page-1);else super.onBackPressed();}
}