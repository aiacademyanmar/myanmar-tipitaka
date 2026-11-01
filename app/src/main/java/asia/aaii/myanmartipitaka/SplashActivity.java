package asia.aaii.myanmartipititaka;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.widget.LinearLayout;
import android.widget.TextView;

/** Lightweight native splash. Uses local artwork/text only; no network dependency. */
public final class SplashActivity extends Activity {
  private final Handler handler=new Handler(Looper.getMainLooper());
  private final Runnable openHome=()->{
    startActivity(new Intent(this,NativeFrontPagesActivity.class));
    finish();
    overridePendingTransition(android.R.anim.fade_in,android.R.anim.fade_out);
  };
  private int dp(int n){return (int)(n*getResources().getDisplayMetrics().density+.5f);}
  @Override public void onCreate(Bundle state){
    super.onCreate(state);
    getWindow().setStatusBarColor(0xff102f2a);getWindow().setNavigationBarColor(0xff102f2a);
    LinearLayout root=new LinearLayout(this);root.setOrientation(LinearLayout.VERTICAL);root.setGravity(Gravity.CENTER);
    root.setPadding(dp(28),dp(24),dp(28),dp(24));
    GradientDrawable gradient=new GradientDrawable(GradientDrawable.Orientation.TL_BR,new int[]{0xff0c2823,0xff174638,0xff102f2a});root.setBackground(gradient);
    TextView wheel=new TextView(this);wheel.setText("☸");wheel.setTextSize(76);wheel.setTextColor(0xfff2d99b);wheel.setGravity(Gravity.CENTER);wheel.setTypeface(Typeface.SERIF,Typeface.BOLD);
    root.addView(wheel,new LinearLayout.LayoutParams(-1,dp(125)));
    TextView my=new TextView(this);my.setText("မြန်မာ့ပိဋကတ်တော်");my.setTextSize(29);my.setTextColor(0xffffe8b2);my.setTypeface(Typeface.DEFAULT,Typeface.BOLD);my.setGravity(Gravity.CENTER);
    root.addView(my);
    TextView en=new TextView(this);en.setText("MYANMAR TIPITAKA");en.setTextSize(19);en.setTextColor(Color.WHITE);en.setGravity(Gravity.CENTER);root.addView(en);
    TextView detail=new TextView(this);detail.setText("ထေရဝါဒ ပါဠိတော်များ  •  ၄၅ ကျမ်း");detail.setTextSize(14);detail.setTextColor(0xffe5dcc6);detail.setGravity(Gravity.CENTER);detail.setPadding(0,dp(14),0,dp(35));root.addView(detail);
    TextView progress=new TextView(this);progress.setText("OFFLINE DHAMMA LIBRARY\nV2.3.4.8");progress.setTextSize(13);progress.setTextColor(0xfff2d99b);progress.setGravity(Gravity.CENTER);root.addView(progress);
    setContentView(root);
    handler.postDelayed(openHome,1100);
  }
  @Override protected void onDestroy(){handler.removeCallbacks(openHome);super.onDestroy();}
}
